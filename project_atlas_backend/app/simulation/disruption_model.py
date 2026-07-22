"""
app/simulation/disruption_model.py
===================================
Stochastic disruption generator for Monte Carlo simulation.

Mathematical Foundation
-----------------------
Each disruption type d ∈ {1, …, D} is parameterised by:

    Occurrence:   D_i ~ Bernoulli(p_d)
                  where p_d = 1 - (1 - p_annual)^(T/365)
                  T = simulation time horizon in days

    Severity:     S_d ~ Triangular(s_min, s_mode, s_max)
                  applied only when D_i = 1

    Duration:     T_d ~ Triangular(t_min, t_mode, t_max)
                  applied only when D_i = 1

Correlated Disruptions (Compound Events)
-----------------------------------------
When disruption A occurs, it can trigger disruption B with conditional
probability P(B|A) = cascading_probability_A.

This is modelled via an upper-triangular cascade matrix:
    cascade[a, b] = P(B occurs | A occurred)

Applied post-sampling:
    if disruption_matrix[i, a] and random < cascade[a, b]:
        disruption_matrix[i, b] = 1

Spatial Propagation
--------------------
If node n fails, adjacent nodes get elevated failure probability:
    P(adjacent | n fails) = base_p_adjacent × propagation_factor / distance_factor
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class DisruptionConfig:
    """
    Holds all parameters for one disruption type as used by the engine.

    Populated from the database row in disruption_types + any scenario overrides
    from scenario_disruptions (probability_override etc.).
    """
    disruption_type_id:   str
    name:                 str
    category:             str

    # Occurrence probability (annual; converted to per-simulation in __post_init__)
    annual_probability:   float   # 0.0 – 1.0

    # Triangular distribution parameters for severity (fraction of capacity lost)
    severity_min:         float   # 0.0 – 1.0
    severity_mode:        float
    severity_max:         float

    # Triangular distribution parameters for duration (days)
    duration_min:         float   # days
    duration_mode:        float
    duration_max:         float

    # Cascade: probability that this disruption triggers each other disruption
    # Key = disruption_type_id of the potential downstream disruption
    cascade_targets:      dict[str, float] = field(default_factory=dict)

    # Cost multiplier when disruption is active (multiplied against baseline transport cost)
    cost_multiplier_min:  float = 1.0
    cost_multiplier_max:  float = 2.5

    # Recovery time distribution parameters (days)
    recovery_min:         float = 1.0
    recovery_max:         float = 30.0

    # Scope: which node_ids and link_ids this disruption can affect
    # Empty → network-wide (affects all matching node/link types)
    target_node_ids:      list[str] = field(default_factory=list)
    target_link_ids:      list[str] = field(default_factory=list)
    affected_node_types:  list[str] = field(default_factory=list)
    affected_link_types:  list[str] = field(default_factory=list)

    # Index within the disruption array (set by DisruptionModel during init)
    index:                int = -1

    def effective_probability(self, time_horizon_days: int) -> float:
        """
        Convert annual probability to per-simulation-horizon probability.

        P(at least one occurrence in T days)
            = 1 − (1 − p_annual)^(T / 365)

        This is the exact Bernoulli trial probability for T days given
        an annual Poisson rate λ = -ln(1 - p_annual).
        """
        if self.annual_probability <= 0.0:
            return 0.0
        if self.annual_probability >= 1.0:
            return 1.0
        return 1.0 - (1.0 - self.annual_probability) ** (time_horizon_days / 365.0)


class DisruptionModel:
    """
    Vectorised stochastic disruption generator.

    All sampling operations produce matrices of shape
    (n_iterations × n_disruptions) using a single PRNG call per variable
    type — no Python loops over iterations.

    Parameters
    ----------
    disruption_configs : list[DisruptionConfig]
        Ordered list of disruption parameters. Index position in this list
        determines the column index in all output matrices.
    time_horizon_days : int
        Simulation time horizon; used to scale annual probabilities.
    rng : np.random.Generator
        NumPy random generator (must be pre-seeded for reproducibility).
    """

    def __init__(
        self,
        disruption_configs: list[DisruptionConfig],
        time_horizon_days: int,
        rng: np.random.Generator,
    ) -> None:
        self.configs = disruption_configs
        self.n_disruptions = len(disruption_configs)
        self.time_horizon_days = time_horizon_days
        self.rng = rng

        # Assign contiguous indices to each config
        for idx, cfg in enumerate(self.configs):
            cfg.index = idx

        # Pre-compute per-horizon probabilities as a 1-D array [n_disruptions]
        self._horizon_probs = np.array(
            [cfg.effective_probability(time_horizon_days) for cfg in self.configs],
            dtype=np.float64,
        )

        # Pre-compute triangular distribution parameters as 1-D arrays
        self._sev_min  = np.array([c.severity_min  for c in self.configs], dtype=np.float64)
        self._sev_mode = np.array([c.severity_mode for c in self.configs], dtype=np.float64)
        self._sev_max  = np.array([c.severity_max  for c in self.configs], dtype=np.float64)

        self._dur_min  = np.array([c.duration_min  for c in self.configs], dtype=np.float64)
        self._dur_mode = np.array([c.duration_mode for c in self.configs], dtype=np.float64)
        self._dur_max  = np.array([c.duration_max  for c in self.configs], dtype=np.float64)

        # Build cascade matrix [n_disruptions × n_disruptions]
        # cascade_matrix[a, b] = P(b fires | a fires)
        id_to_idx = {cfg.disruption_type_id: cfg.index for cfg in self.configs}
        self._cascade_matrix = np.zeros(
            (self.n_disruptions, self.n_disruptions), dtype=np.float64
        )
        for cfg in self.configs:
            for target_id, prob in cfg.cascade_targets.items():
                if target_id in id_to_idx:
                    self._cascade_matrix[cfg.index, id_to_idx[target_id]] = prob

        logger.info(
            "disruption_model.initialised",
            n_disruptions=self.n_disruptions,
            time_horizon_days=time_horizon_days,
            mean_horizon_probability=float(self._horizon_probs.mean()),
        )

    # ── Public interface ──────────────────────────────────────────────────────

    def sample_all(
        self, n_iterations: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Sample disruption occurrences, severities, and durations for all
        iterations simultaneously.

        Returns
        -------
        occurrence_matrix : np.ndarray, shape (n_iterations, n_disruptions), dtype bool
            True where a disruption fires in that iteration.
        severity_matrix : np.ndarray, shape (n_iterations, n_disruptions), dtype float64
            Severity [0, 1] where disruption fires; 0.0 elsewhere.
        duration_matrix : np.ndarray, shape (n_iterations, n_disruptions), dtype float64
            Duration in days where disruption fires; 0.0 elsewhere.
        """
        # Step 1: Primary occurrence — vectorised Bernoulli trials
        # Shape: [n_iterations, n_disruptions]
        uniform_draws = self.rng.random((n_iterations, self.n_disruptions))
        occurrence_matrix = uniform_draws < self._horizon_probs[np.newaxis, :]

        # Step 2: Apply cascade effects (compound disruptions)
        if self._cascade_matrix.any():
            occurrence_matrix = self._apply_cascades(occurrence_matrix)

        # Step 3: Sample severities — Triangular(min, mode, max) per disruption
        raw_severities = self.rng.triangular(
            left=self._sev_min,
            mode=self._sev_mode,
            right=self._sev_max,
            size=(n_iterations, self.n_disruptions),
        )
        # Zero out where disruption did not fire
        severity_matrix = np.where(occurrence_matrix, raw_severities, 0.0)

        # Step 4: Sample durations — Triangular(min, mode, max) per disruption
        raw_durations = self.rng.triangular(
            left=self._dur_min,
            mode=self._dur_mode,
            right=self._dur_max,
            size=(n_iterations, self.n_disruptions),
        )
        duration_matrix = np.where(occurrence_matrix, raw_durations, 0.0)

        return occurrence_matrix, severity_matrix, duration_matrix

    # ── Private methods ───────────────────────────────────────────────────────

    def _apply_cascades(self, occurrence_matrix: np.ndarray) -> np.ndarray:
        """
        Apply cascade (compound disruption) effects post primary sampling.

        For each active disruption a in each iteration i, we draw a Bernoulli
        trial for each potential cascade target b:
            P(b fires | a fires) = cascade_matrix[a, b]

        The implementation uses NumPy broadcasting to avoid Python loops
        over iterations. We iterate only over disruption pairs that have
        non-zero cascade probability (typically very few).

        Parameters
        ----------
        occurrence_matrix : ndarray, shape (n_iter, n_disruptions)

        Returns
        -------
        Updated occurrence_matrix with cascades applied (in-place copy).
        """
        result = occurrence_matrix.copy()
        n_iter = occurrence_matrix.shape[0]

        # Find non-zero cascade pairs
        cascade_pairs = np.argwhere(self._cascade_matrix > 0)

        for (a, b) in cascade_pairs:
            cascade_prob = self._cascade_matrix[a, b]
            # Iterations where disruption a already fired
            a_fired = result[:, a]  # shape (n_iter,)
            # Draw cascade Bernoulli for those iterations
            cascade_draws = self.rng.random(n_iter) < cascade_prob
            # Trigger b where a fired AND cascade draw succeeded
            result[:, b] = result[:, b] | (a_fired & cascade_draws)

        return result

    def build_disruption_summary(
        self,
        occurrence_matrix: np.ndarray,
        severity_matrix: np.ndarray,
        duration_matrix: np.ndarray,
        iteration_indices: Optional[np.ndarray] = None,
    ) -> list[list[dict]]:
        """
        Build a human-readable disruption summary for the disruptions_triggered
        JSONB column in simulation_results.

        Returns a list of length n_iterations, where each element is a list of
        dicts describing the disruptions that fired in that iteration.

        Parameters
        ----------
        iteration_indices : optional array of iteration indices to summarise.
            If None, summarises all iterations (expensive for 10k — use sparingly).
        """
        indices = (
            iteration_indices
            if iteration_indices is not None
            else np.arange(occurrence_matrix.shape[0])
        )

        summaries = []
        for i in indices:
            fired = np.where(occurrence_matrix[i])[0]
            iter_summary = []
            for d_idx in fired:
                cfg = self.configs[d_idx]
                iter_summary.append({
                    "disruption_type_id": cfg.disruption_type_id,
                    "name":               cfg.name,
                    "category":           cfg.category,
                    "severity":           float(severity_matrix[i, d_idx]),
                    "duration_days":      float(duration_matrix[i, d_idx]),
                })
            summaries.append(iter_summary)

        return summaries
