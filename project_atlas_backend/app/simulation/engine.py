"""
app/simulation/engine.py
========================
Main Monte Carlo simulation orchestrator for Project Atlas.

Mathematical Framework
-----------------------
For each iteration i ∈ {1, …, N}:

    1. Sample disruptions: D_i ~ Bernoulli(p_d) ∀d
    2. Sample severity:    S_d_i ~ Triangular(s_min, s_mode, s_max) if D_d_i=1
    3. Sample duration:    T_d_i ~ Triangular(t_min, t_mode, t_max) if D_d_i=1
    4. Apply cascades:     D_b_i |= Bernoulli(p_cascade_ab) if D_a_i=1
    5. Compute flow:       F_i = MaxFlow(G with reduced capacities) / F_baseline
    6. Compute costs:      C_i = f(F_i, S_i, T_i)
    7. Compute recovery:   R_i ~ Exponential(λ) × severity_factor × zone_factor

Output: Empirical distribution of {C_i, F_i, R_i} for i=1..N

Risk Measures:
    VaR_95(C)   = percentile(C_i, 95)
    CVaR_95(C)  = E[C_i | C_i ≥ VaR_95]
    P(failure)  = P(F_i < threshold_flow)

Engine Version: 1.0.0
"""

from __future__ import annotations

import time
import traceback
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import structlog

from app.simulation.disruption_model import DisruptionConfig, DisruptionModel
from app.simulation.flow_model import FlowModel
from app.simulation.cost_model import CostModel, LinkCostData, NetworkCostConstants
from app.simulation.recovery_model import RecoveryModel

logger = structlog.get_logger(__name__)

ENGINE_VERSION = "1.0.0"

# Threshold below which the supply chain is considered "failed"
FAILURE_FLOW_THRESHOLD = 0.50  # < 50% of normal flow = supply chain failure


# ── Result dataclasses ────────────────────────────────────────────────────────

@dataclass
class AggregateMetrics:
    """
    Statistical summary of one metric across all N iterations.
    Maps to one row in public.simulation_aggregates.
    """
    metric_name:   str
    mean_value:    float
    std_deviation: float
    percentile_5:  float
    percentile_25: float
    median_value:  float
    percentile_75: float
    percentile_95: float
    min_value:     float
    max_value:     float
    var_95:        float    # Value at Risk (95th percentile)
    cvar_95:       float    # Conditional VaR / Expected Shortfall
    skewness:      float
    kurtosis:      float    # Excess kurtosis (Fisher definition)

    @classmethod
    def from_array(cls, name: str, arr: np.ndarray) -> "AggregateMetrics":
        """
        Compute all statistical measures from a 1-D NumPy array.
        Uses pure NumPy (no scipy) for speed.
        """
        if len(arr) == 0:
            raise ValueError(f"Cannot compute aggregates for empty array: {name}")

        percs = np.percentile(arr, [5, 25, 50, 75, 95])
        var95 = percs[4]
        tail_mask = arr >= var95
        cvar95 = float(arr[tail_mask].mean()) if tail_mask.any() else float(var95)

        mean = float(arr.mean())
        std  = float(arr.std())

        # Skewness and kurtosis (Fisher / excess) via NumPy moments
        if std > 0:
            normalised = (arr - mean) / std
            skewness   = float(np.mean(normalised ** 3))
            kurtosis   = float(np.mean(normalised ** 4) - 3.0)
        else:
            skewness = 0.0
            kurtosis = 0.0

        return cls(
            metric_name=name,
            mean_value=mean,
            std_deviation=std,
            percentile_5=float(percs[0]),
            percentile_25=float(percs[1]),
            median_value=float(percs[2]),
            percentile_75=float(percs[3]),
            percentile_95=float(percs[4]),
            min_value=float(arr.min()),
            max_value=float(arr.max()),
            var_95=float(var95),
            cvar_95=float(cvar95),
            skewness=skewness,
            kurtosis=kurtosis,
        )


@dataclass
class VulnerabilityScore:
    """Vulnerability assessment for one node or link."""
    entity_id:          str           # node_id or link_id (UUID string)
    entity_type:        str           # "node" or "link"
    vulnerability_score: float
    criticality_rank:   int
    failure_frequency:  float
    avg_impact_cost_usd: float
    avg_impact_delay_days: float
    bottleneck_score:   float
    betweenness_centrality: Optional[float] = None
    degree_centrality:      Optional[float] = None
    closeness_centrality:   Optional[float] = None


@dataclass
class SimulationOutput:
    """Complete output of a Monte Carlo simulation run."""
    run_id:              str
    engine_version:      str = ENGINE_VERSION
    n_iterations:        int = 0
    elapsed_seconds:     float = 0.0

    # Per-iteration arrays (shape: n_iterations each)
    total_cost_usd:          Optional[np.ndarray] = None
    total_delay_days:        Optional[np.ndarray] = None
    production_loss_barrels: Optional[np.ndarray] = None
    nodes_affected:          Optional[np.ndarray] = None
    links_disrupted:         Optional[np.ndarray] = None
    supply_chain_flow_pct:   Optional[np.ndarray] = None
    recovery_time_days:      Optional[np.ndarray] = None
    disruptions_triggered:   Optional[list[list[dict]]] = None  # per-iteration JSONB

    # Aggregated statistics
    aggregates:       list[AggregateMetrics] = field(default_factory=list)
    vulnerabilities:  list[VulnerabilityScore] = field(default_factory=list)

    # Key risk metrics (for quick dashboard display)
    probability_of_failure: float = 0.0
    mean_flow_fraction:      float = 1.0

    def to_result_rows(self) -> list[dict]:
        """
        Convert per-iteration arrays to a list of dicts for bulk DB insert.
        Each dict maps to one row in public.simulation_results.
        """
        rows = []
        for i in range(self.n_iterations):
            rows.append({
                "run_id":                  self.run_id,
                "iteration_number":        i + 1,
                "total_cost_usd":          float(self.total_cost_usd[i]),
                "total_delay_days":        float(self.total_delay_days[i]),
                "production_loss_barrels": float(self.production_loss_barrels[i]),
                "nodes_affected":          int(self.nodes_affected[i]),
                "links_disrupted":         int(self.links_disrupted[i]),
                "supply_chain_flow_pct":   float(self.supply_chain_flow_pct[i]),
                "recovery_time_days":      float(self.recovery_time_days[i]),
                "disruptions_triggered":   (
                    self.disruptions_triggered[i]
                    if self.disruptions_triggered
                    else []
                ),
            })
        return rows


# ── Main Engine Class ─────────────────────────────────────────────────────────

class MonteCarloEngine:
    """
    Project Atlas Monte Carlo simulation engine.

    Executes N stochastic iterations of the Nigerian oil & gas supply chain
    under configurable disruption scenarios, computing the empirical
    probability distributions of cost, flow loss, delay, and recovery time.

    Parameters
    ----------
    run_id : str
        UUID string of the simulation_runs row (written before engine starts).
    n_iterations : int
        Number of Monte Carlo iterations (default 10,000).
    time_horizon_days : int
        Simulation horizon in days.
    random_seed : int | None
        Fixed seed for reproducibility. None = non-deterministic.
    disruption_configs : list[DisruptionConfig]
        Ordered disruption parameters from the database.
    network_data : dict
        Node and link data from the database (for NetworkX graph construction).
    cost_constants : NetworkCostConstants
        Economic parameters for cost model.
    progress_callback : callable | None
        Called with (completed_iterations: int) after each batch.
        Used by the worker to update simulation_runs.completed_iterations.
    batch_size : int
        Number of iterations to process before flushing results to DB.
    """

    BATCH_SIZE = 1000  # Flush results every N iterations

    def __init__(
        self,
        run_id: str,
        n_iterations: int,
        time_horizon_days: int,
        random_seed: Optional[int],
        disruption_configs: list[DisruptionConfig],
        network_data: dict,
        cost_constants: NetworkCostConstants,
        progress_callback=None,
    ) -> None:
        self.run_id = run_id
        self.n_iterations = n_iterations
        self.time_horizon_days = time_horizon_days
        self.random_seed = random_seed
        self.disruption_configs = disruption_configs
        self.network_data = network_data
        self.cost_constants = cost_constants
        self.progress_callback = progress_callback

        # Initialise PRNG — single source of randomness for reproducibility
        self.rng = np.random.default_rng(random_seed)

        logger.info(
            "monte_carlo.init",
            run_id=run_id,
            n_iterations=n_iterations,
            time_horizon_days=time_horizon_days,
            n_disruptions=len(disruption_configs),
            seeded=random_seed is not None,
        )

    def run(self) -> SimulationOutput:
        """
        Execute the full Monte Carlo simulation.

        Returns a SimulationOutput containing per-iteration arrays
        and pre-computed aggregate statistics.

        Raises
        ------
        RuntimeError : If any sub-model fails to initialise.
        """
        t_start = time.perf_counter()
        output = SimulationOutput(run_id=self.run_id, n_iterations=self.n_iterations)

        try:
            # ── Phase 1: Initialise sub-models ──────────────────────────────
            logger.info("monte_carlo.phase1.init_models", run_id=self.run_id)

            disruption_model = DisruptionModel(
                disruption_configs=self.disruption_configs,
                time_horizon_days=self.time_horizon_days,
                rng=self.rng,
            )

            flow_model, link_cost_data = self._build_flow_model()
            cost_model = CostModel(
                link_cost_data=link_cost_data,
                constants=self.cost_constants,
            )
            # Build node-disruption and link-disruption mapping matrices
            node_disruption_map, link_disruption_map = self._build_scope_matrices(
                disruption_model, flow_model
            )

            # ── Phase 2: Sample all disruptions (fully vectorised) ───────────
            logger.info("monte_carlo.phase2.sampling", run_id=self.run_id)
            t_sample = time.perf_counter()

            occurrence_matrix, severity_matrix, duration_matrix = (
                disruption_model.sample_all(self.n_iterations)
            )

            logger.info(
                "monte_carlo.phase2.done",
                elapsed_ms=(time.perf_counter() - t_sample) * 1000,
                mean_disruptions_per_iter=float(occurrence_matrix.sum(axis=1).mean()),
            )

            # ── Phase 3: Compute flow fractions ─────────────────────────────
            logger.info("monte_carlo.phase3.flow", run_id=self.run_id)
            t_flow = time.perf_counter()

            # Link severity per iteration: (n_iter, n_links)
            link_severity_matrix = np.clip(
                severity_matrix @ link_disruption_map, 0.0, 1.0
            )

            flow_fractions = flow_model.compute_flow_fractions(
                occurrence_matrix=occurrence_matrix,
                severity_matrix=severity_matrix,
                node_disruption_map=node_disruption_map,
                link_disruption_map=link_disruption_map,
            )

            logger.info(
                "monte_carlo.phase3.done",
                elapsed_ms=(time.perf_counter() - t_flow) * 1000,
                mean_flow_pct=float(flow_fractions.mean()),
                p_failure=float((flow_fractions < FAILURE_FLOW_THRESHOLD).mean()),
            )

            # ── Phase 4: Compute costs ───────────────────────────────────────
            logger.info("monte_carlo.phase4.costs", run_id=self.run_id)

            # Cost multiplier per disruption per iteration
            cost_mult_matrix = np.array(
                [
                    [c.cost_multiplier_min +
                     self.rng.random() * (c.cost_multiplier_max - c.cost_multiplier_min)
                     for c in self.disruption_configs]
                    for _ in range(self.n_iterations)
                ],
                dtype=np.float64,
            ) if self.disruption_configs else np.ones((self.n_iterations, 1))

            cost_dict = cost_model.compute_all_costs(
                flow_fractions=flow_fractions,
                duration_matrix=duration_matrix,
                occurrence_matrix=occurrence_matrix,
                link_severity_matrix=link_severity_matrix,
                cost_multiplier_matrix=cost_mult_matrix,
            )

            # ── Phase 5: Compute recovery times ─────────────────────────────
            logger.info("monte_carlo.phase5.recovery", run_id=self.run_id)

            # Use mean recovery parameters across all disruption types
            if self.disruption_configs:
                mean_rec_min = np.mean([c.recovery_min for c in self.disruption_configs
                                        if hasattr(c, 'recovery_min')])
                mean_rec_max = np.mean([c.recovery_max for c in self.disruption_configs
                                        if hasattr(c, 'recovery_max')])
            else:
                mean_rec_min, mean_rec_max = 1.0, 30.0

            # Fallback attribute access (DisruptionConfig may not have recovery fields)
            recovery_mins = [getattr(c, 'recovery_min', 1.0) for c in self.disruption_configs]
            recovery_maxs = [getattr(c, 'recovery_max', 30.0) for c in self.disruption_configs]
            mean_rec_min = float(np.mean(recovery_mins)) if recovery_mins else 1.0
            mean_rec_max = float(np.mean(recovery_maxs)) if recovery_maxs else 30.0

            recovery_model = RecoveryModel(
                recovery_min=mean_rec_min,
                recovery_max=mean_rec_max,
                mean_redundancy=self._mean_node_redundancy(),
                primary_zone=self._primary_zone(),
                rng=self.rng,
            )

            max_severity_per_iter = severity_matrix.max(axis=1) if severity_matrix.shape[1] > 0 \
                else np.zeros(self.n_iterations)

            recovery_times = recovery_model.sample_recovery_times(
                severity_per_iteration=max_severity_per_iter,
                n_iterations=self.n_iterations,
            )

            # ── Phase 6: Build disruption summaries (sample, not all 10k) ───
            # Only summarise 500 worst-case iterations for JSONB storage
            worst_indices = np.argsort(cost_dict["total"])[-500:]
            disruption_summaries_partial = disruption_model.build_disruption_summary(
                occurrence_matrix, severity_matrix, duration_matrix,
                iteration_indices=worst_indices,
            )
            # Full list: empty for non-worst, summary for worst
            disruption_summaries = [[]] * self.n_iterations
            for local_idx, global_idx in enumerate(worst_indices):
                disruption_summaries[global_idx] = disruption_summaries_partial[local_idx]

            # ── Phase 7: Populate output arrays ─────────────────────────────
            output.total_cost_usd          = cost_dict["total"]
            output.total_delay_days        = duration_matrix.max(axis=1)
            output.production_loss_barrels = (
                (1.0 - flow_fractions)
                * self.cost_constants.baseline_daily_throughput_bpd
                * duration_matrix.max(axis=1)
            )
            output.nodes_affected          = self._count_nodes_affected(occurrence_matrix)
            output.links_disrupted         = self._count_links_disrupted(occurrence_matrix)
            output.supply_chain_flow_pct   = flow_fractions
            output.recovery_time_days      = recovery_times
            output.disruptions_triggered   = disruption_summaries

            # ── Phase 8: Compute aggregate statistics ────────────────────────
            logger.info("monte_carlo.phase8.aggregates", run_id=self.run_id)
            output.aggregates = self._compute_aggregates(output)
            output.probability_of_failure = float(
                (flow_fractions < FAILURE_FLOW_THRESHOLD).mean()
            )
            output.mean_flow_fraction = float(flow_fractions.mean())

            # ── Phase 9: Vulnerability assessment ────────────────────────────
            logger.info("monte_carlo.phase9.vulnerability", run_id=self.run_id)
            output.vulnerabilities = self._assess_vulnerabilities(
                occurrence_matrix=occurrence_matrix,
                cost_array=cost_dict["total"],
                delay_array=output.total_delay_days,
            )

        except Exception as exc:
            logger.error(
                "monte_carlo.failed",
                run_id=self.run_id,
                error=str(exc),
                traceback=traceback.format_exc(),
            )
            raise

        output.elapsed_seconds = time.perf_counter() - t_start
        logger.info(
            "monte_carlo.completed",
            run_id=self.run_id,
            elapsed_seconds=round(output.elapsed_seconds, 2),
            mean_cost_usd=float(output.total_cost_usd.mean()),
            p_failure=output.probability_of_failure,
        )

        return output

    # ── Private methods ───────────────────────────────────────────────────────

    def _build_flow_model(self) -> tuple[FlowModel, list[LinkCostData]]:
        """Construct the FlowModel and extract link cost data from network_data."""
        from app.or_engine.network_builder import NetworkBuilder

        nodes = self.network_data.get("nodes", [])
        links = self.network_data.get("links", [])

        builder = NetworkBuilder()
        graph = builder.build_graph(nodes, links)

        upstream_ids   = [n["node_id"] for n in nodes if n.get("stage") == "upstream"]
        downstream_ids = [n["node_id"] for n in nodes if n.get("stage") == "downstream"]
        node_cap_map   = {n["node_id"]: float(n.get("capacity_bpd", 0)) for n in nodes}

        flow_model = FlowModel(
            graph=graph,
            upstream_node_ids=upstream_ids,
            downstream_node_ids=downstream_ids,
            node_capacity_map=node_cap_map,
        )

        link_cost_data = [
            LinkCostData(
                link_id=lk["link_id"],
                link_type=lk.get("link_type", "pipeline"),
                transport_cost_per_barrel=float(lk.get("transport_cost_per_barrel", 1.0)),
                distance_km=float(lk.get("distance_km", 0)),
                max_capacity_bpd=float(lk.get("max_capacity_bpd", 0)),
                index=idx,
            )
            for idx, lk in enumerate(links)
        ]

        return flow_model, link_cost_data

    def _build_scope_matrices(
        self,
        disruption_model: DisruptionModel,
        flow_model: FlowModel,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Build binary scope matrices:
            node_disruption_map[d, n] = 1 if disruption d can affect node n
            link_disruption_map[d, l] = 1 if disruption d can affect link l

        Used to compute per-node and per-link severity from the
        iteration-level severity matrix via matrix multiplication.
        """
        nodes = self.network_data.get("nodes", [])
        links = self.network_data.get("links", [])
        n_disrupt = len(self.disruption_configs)
        n_nodes   = len(nodes)
        n_links   = len(links)

        node_map = np.zeros((n_disrupt, n_nodes), dtype=np.float64)
        link_map = np.zeros((n_disrupt, n_links), dtype=np.float64)

        node_id_to_idx = {n["node_id"]: i for i, n in enumerate(nodes)}
        link_id_to_idx = {lk["link_id"]: i for i, lk in enumerate(links)}

        for d_idx, cfg in enumerate(self.disruption_configs):
            # Explicit target nodes from scenario_disruptions
            for node_id in cfg.target_node_ids:
                if node_id in node_id_to_idx:
                    node_map[d_idx, node_id_to_idx[node_id]] = 1.0

            # Explicit target links
            for link_id in cfg.target_link_ids:
                if link_id in link_id_to_idx:
                    link_map[d_idx, link_id_to_idx[link_id]] = 1.0

            # If no explicit targets, affect all matching node/link types
            if not cfg.target_node_ids and cfg.affected_node_types:
                for n_idx, node in enumerate(nodes):
                    if node.get("node_type") in cfg.affected_node_types:
                        node_map[d_idx, n_idx] = 1.0

            if not cfg.target_link_ids and cfg.affected_link_types:
                for l_idx, link in enumerate(links):
                    if link.get("link_type") in cfg.affected_link_types:
                        link_map[d_idx, l_idx] = 1.0

        return node_map, link_map

    def _compute_aggregates(self, output: SimulationOutput) -> list[AggregateMetrics]:
        """Compute AggregateMetrics for all key metrics."""
        metrics_to_aggregate = {
            "total_cost_usd":          output.total_cost_usd,
            "total_delay_days":        output.total_delay_days,
            "production_loss_barrels": output.production_loss_barrels,
            "supply_chain_flow_pct":   output.supply_chain_flow_pct,
            "recovery_time_days":      output.recovery_time_days,
            "nodes_affected":          output.nodes_affected.astype(np.float64),
            "links_disrupted":         output.links_disrupted.astype(np.float64),
        }
        return [
            AggregateMetrics.from_array(name, arr)
            for name, arr in metrics_to_aggregate.items()
            if arr is not None and len(arr) > 0
        ]

    def _assess_vulnerabilities(
        self,
        occurrence_matrix: np.ndarray,
        cost_array: np.ndarray,
        delay_array: np.ndarray,
    ) -> list[VulnerabilityScore]:
        """
        Compute per-disruption vulnerability scores from simulation results.

        For each disruption d:
            failure_frequency   = mean(occurrence_matrix[:, d])
            avg_impact_cost     = mean(cost_array[occurrence_matrix[:, d]])
            avg_impact_delay    = mean(delay_array[occurrence_matrix[:, d]])
            vulnerability_score = 0.5 × failure_frequency + 0.5 × (avg_cost / max_cost)
        """
        from app.or_engine.vulnerability import VulnerabilityScorer

        nodes = self.network_data.get("nodes", [])
        max_cost = float(cost_array.max()) if cost_array.max() > 0 else 1.0

        scores = []
        for d_idx, cfg in enumerate(self.disruption_configs):
            fired_mask = occurrence_matrix[:, d_idx]
            freq = float(fired_mask.mean())
            if freq == 0:
                continue

            avg_cost  = float(cost_array[fired_mask].mean())
            avg_delay = float(delay_array[fired_mask].mean())

            vuln_score = 0.50 * freq + 0.50 * (avg_cost / max_cost)

            # Map disruption to its primary target node(s)
            for node_id in cfg.target_node_ids:
                scores.append(VulnerabilityScore(
                    entity_id=node_id,
                    entity_type="node",
                    vulnerability_score=min(1.0, vuln_score),
                    criticality_rank=0,           # ranked after all computed
                    failure_frequency=freq,
                    avg_impact_cost_usd=avg_cost,
                    avg_impact_delay_days=avg_delay,
                    bottleneck_score=freq,
                ))

            for link_id in cfg.target_link_ids:
                scores.append(VulnerabilityScore(
                    entity_id=link_id,
                    entity_type="link",
                    vulnerability_score=min(1.0, vuln_score),
                    criticality_rank=0,
                    failure_frequency=freq,
                    avg_impact_cost_usd=avg_cost,
                    avg_impact_delay_days=avg_delay,
                    bottleneck_score=freq,
                ))

        # Rank by vulnerability_score descending
        scores.sort(key=lambda s: s.vulnerability_score, reverse=True)
        for rank, score in enumerate(scores, start=1):
            score.criticality_rank = rank

        return scores

    def _count_nodes_affected(self, occurrence_matrix: np.ndarray) -> np.ndarray:
        """Count unique nodes affected per iteration (approximation via disruption count)."""
        nodes = self.network_data.get("nodes", [])
        n_nodes = len(nodes)
        # Conservative estimate: each disruption affects ~15% of nodes
        affected_fraction = np.clip(occurrence_matrix.sum(axis=1) * 0.15, 0, 1)
        return np.round(affected_fraction * n_nodes).astype(np.int32)

    def _count_links_disrupted(self, occurrence_matrix: np.ndarray) -> np.ndarray:
        """Count links disrupted per iteration."""
        links = self.network_data.get("links", [])
        n_links = len(links)
        disrupted_fraction = np.clip(occurrence_matrix.sum(axis=1) * 0.20, 0, 1)
        return np.round(disrupted_fraction * n_links).astype(np.int32)

    def _mean_node_redundancy(self) -> float:
        """Extract mean redundancy score from network nodes."""
        nodes = self.network_data.get("nodes", [])
        if not nodes:
            return 0.4
        return float(np.mean([n.get("redundancy_score", 0.4) for n in nodes]))

    def _primary_zone(self) -> str:
        """Identify the most common geopolitical zone in the network."""
        nodes = self.network_data.get("nodes", [])
        if not nodes:
            return "SS"
        zones = [n.get("geopolitical_zone", "SS") for n in nodes]
        return max(set(zones), key=zones.count)
