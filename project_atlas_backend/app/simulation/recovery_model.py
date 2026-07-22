"""
app/simulation/recovery_model.py
=================================
Post-disruption recovery dynamics model.

Mathematical Foundation
-----------------------
Recovery time R is modelled as:

    R_base ~ Exponential(λ)    where λ = 1 / mean_recovery_time

mean_recovery_time is computed from disruption parameters:
    mean_recovery = (recovery_min + recovery_max) / 2
                  × (1 + severity_factor × severity)
                  × zone_difficulty_factor

Factors applied after base sampling:
    1. Severity scaling:   severe disruptions take longer to repair
       scale_factor = 1 + (1 − redundancy_score) × severity × 2.0

    2. Zone difficulty:    Niger Delta (SS) vs. inland zones
       zone_factor: {SS: 1.3, NE: 1.2, NW: 1.1, NC: 1.0, SW: 0.9, SE: 1.0}

    3. Mitigation effect:  active mitigations reduce recovery time
       R_mitigated = R_base × (1 − reduces_recovery_time_by_pct)

Resilience Score (per iteration)
---------------------------------
    resilience_i = 1 − (time_degraded_i / time_horizon)

where time_degraded = min(R_i, time_horizon)
"""

from __future__ import annotations

import numpy as np
import structlog

logger = structlog.get_logger(__name__)

# Zone-specific recovery difficulty multipliers
# SS = South-South (Niger Delta): access challenges, security, swamp terrain
ZONE_DIFFICULTY: dict[str, float] = {
    "SS": 1.30,
    "NE": 1.20,
    "NW": 1.10,
    "NC": 1.00,
    "SE": 1.00,
    "SW": 0.90,
}


class RecoveryModel:
    """
    Vectorised recovery time and resilience calculator.

    Parameters
    ----------
    recovery_min : float
        Minimum recovery time in days (from disruption_types).
    recovery_max : float
        Maximum recovery time in days.
    mean_redundancy : float
        Mean redundancy score of affected nodes [0, 1].
    primary_zone : str
        Primary geopolitical zone of affected nodes (drives zone_factor).
    rng : np.random.Generator
        Seeded NumPy generator for reproducibility.
    """

    def __init__(
        self,
        recovery_min: float,
        recovery_max: float,
        mean_redundancy: float,
        primary_zone: str,
        rng: np.random.Generator,
    ) -> None:
        self.recovery_min = max(0.0, recovery_min)
        self.recovery_max = max(recovery_min, recovery_max)
        self.mean_redundancy = np.clip(mean_redundancy, 0.0, 1.0)
        self.zone_factor = ZONE_DIFFICULTY.get(primary_zone, 1.0)
        self.rng = rng

        # Mean of triangular(min, mode, max) = (min + mode + max) / 3
        # Approximate mode as midpoint for recovery time (no mode in DB)
        mode = (recovery_min + recovery_max) / 2.0
        self.mean_recovery_days = (recovery_min + mode + recovery_max) / 3.0

    # ── Public interface ──────────────────────────────────────────────────────

    def sample_recovery_times(
        self,
        severity_per_iteration: np.ndarray,  # (n_iter,) — max severity per iteration
        n_iterations: int,
    ) -> np.ndarray:
        """
        Sample recovery time for each iteration.

        Parameters
        ----------
        severity_per_iteration : ndarray (n_iter,)
            Maximum disruption severity realised in each iteration [0, 1].
        n_iterations : int

        Returns
        -------
        recovery_times : ndarray (n_iter,), values ≥ 0, in days
        """
        # Base recovery ~ Exponential(λ = 1/mean_recovery)
        if self.mean_recovery_days <= 0:
            return np.zeros(n_iterations, dtype=np.float64)

        base_recovery = self.rng.exponential(
            scale=self.mean_recovery_days, size=n_iterations
        )

        # Severity scaling: high severity + low redundancy → longer recovery
        # scale = 1 + (1 − redundancy) × severity × 2.0
        severity_scale = 1.0 + (1.0 - self.mean_redundancy) * severity_per_iteration * 2.0

        # Zone difficulty scaling
        recovery_times = base_recovery * severity_scale * self.zone_factor

        # Floor at recovery_min for iterations where disruption fired
        disrupted = severity_per_iteration > 0
        recovery_times = np.where(
            disrupted,
            np.maximum(recovery_times, self.recovery_min),
            0.0,
        )

        return recovery_times

    def apply_mitigation_effect(
        self,
        recovery_times: np.ndarray,            # (n_iter,)
        mitigation_reduction_pct: float,        # 0.0–1.0
    ) -> np.ndarray:
        """
        Apply active mitigation strategies to reduce recovery times.

        R_mitigated = R_base × (1 − reduces_recovery_time_by_pct)

        Parameters
        ----------
        recovery_times : ndarray (n_iter,)
        mitigation_reduction_pct : float
            Combined reduction fraction from all active mitigations.
            Capped at 0.90 (cannot reduce to zero by mitigation alone).
        """
        reduction = np.clip(mitigation_reduction_pct, 0.0, 0.90)
        return recovery_times * (1.0 - reduction)

    def compute_resilience_scores(
        self,
        recovery_times: np.ndarray,  # (n_iter,)
        time_horizon_days: int,
    ) -> np.ndarray:
        """
        Compute resilience score per iteration.

        resilience_i = 1 − (time_degraded_i / time_horizon)

        where time_degraded = min(recovery_time_i, time_horizon_days)

        Higher resilience = faster recovery relative to horizon.
        resilience = 1.0 means full recovery before horizon ends.
        resilience = 0.0 means the chain never recovered within the horizon.

        Returns
        -------
        resilience : ndarray (n_iter,), values in [0.0, 1.0]
        """
        time_degraded = np.minimum(recovery_times, float(time_horizon_days))
        resilience = 1.0 - (time_degraded / float(time_horizon_days))
        return np.clip(resilience, 0.0, 1.0)

    def compute_distribution_summary(
        self,
        recovery_times: np.ndarray,
    ) -> dict[str, float]:
        """
        Summarise the recovery time distribution.

        Returns
        -------
        dict with mean, median, p95, max, and prob_exceeds_30_days
        """
        return {
            "mean_recovery_days":         float(recovery_times.mean()),
            "median_recovery_days":       float(np.median(recovery_times)),
            "p95_recovery_days":          float(np.percentile(recovery_times, 95)),
            "max_recovery_days":          float(recovery_times.max()),
            "prob_exceeds_30_days":       float((recovery_times > 30).mean()),
            "prob_exceeds_90_days":       float((recovery_times > 90).mean()),
        }
