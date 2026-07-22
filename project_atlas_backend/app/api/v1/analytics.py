"""
app/api/v1/analytics.py
========================
Aggregated analytics endpoints — OR engine results, network analysis,
mitigation optimisation.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.db.models import MitigationStrategy, SupplyChainNode, SupplyChainLink
from app.dependencies import AnalystRequired, CurrentUser, DbSession, NodeRepo, LinkRepo
from app.core.exceptions import SimulationRunNotFoundError, NetworkGraphError

router = APIRouter(prefix="/analytics", tags=["Analytics & OR Engine"])


@router.get(
    "/network/graph",
    response_model=dict,
    summary="Get the full network graph for visualisation",
)
async def get_network_graph(
    _user: CurrentUser,
    node_repo: NodeRepo,
    link_repo: LinkRepo,
) -> dict:
    """
    Return the complete supply chain network as a JSON graph
    (nodes + edges with all attributes) suitable for D3.js or Recharts.
    """
    from app.or_engine.network_builder import NetworkBuilder

    node_data = await node_repo.get_network_graph_data()
    link_data = await link_repo.get_links_for_graph()

    builder = NetworkBuilder()
    graph   = builder.build_graph(node_data["nodes"], link_data)
    return builder.export_for_frontend(graph)


@router.get(
    "/network/validate",
    response_model=dict,
    summary="Validate network graph connectivity",
)
async def validate_network(
    _user: CurrentUser,
    node_repo: NodeRepo,
    link_repo: LinkRepo,
) -> dict:
    """
    Run the network connectivity validation checks:
    - Weak connectivity (are all nodes reachable?)
    - Isolated nodes (no edges)
    - Upstream → downstream path existence
    """
    from app.or_engine.network_builder import NetworkBuilder
    import dataclasses

    node_data = await node_repo.get_network_graph_data()
    link_data = await link_repo.get_links_for_graph()

    builder = NetworkBuilder()
    graph   = builder.build_graph(node_data["nodes"], link_data)
    report  = builder.validate_graph_connectivity(graph)
    return dataclasses.asdict(report)


@router.get(
    "/network/critical-path",
    response_model=dict,
    summary="Compute the critical path through the supply chain network",
)
async def get_critical_path(
    _user: CurrentUser,
    node_repo: NodeRepo,
    link_repo: LinkRepo,
) -> dict:
    """
    Runs CPM (Critical Path Method) on the supply chain DAG.

    Returns the longest lead-time path from upstream sources to
    downstream consumers and identifies bottleneck links.
    """
    from app.or_engine.network_builder import NetworkBuilder
    from app.or_engine.critical_path import CriticalPathAnalyzer
    import dataclasses

    nodes     = (await node_repo.get_network_graph_data())["nodes"]
    links     = await link_repo.get_links_for_graph()
    builder   = NetworkBuilder()
    graph     = builder.build_graph(nodes, links)

    upstream_ids   = [n["node_id"] for n in nodes if n.get("stage") == "upstream"]
    downstream_ids = [n["node_id"] for n in nodes if n.get("stage") == "downstream"]

    if not upstream_ids or not downstream_ids:
        raise NetworkGraphError(
            message="Network must contain upstream and downstream nodes."
        )

    analyzer = CriticalPathAnalyzer(graph, upstream_ids, downstream_ids)
    cp_result  = analyzer.find_critical_path()
    mc_result  = analyzer.find_min_cut()
    spofs      = analyzer.find_single_points_of_failure()
    importance = analyzer.compute_node_importance()

    return {
        "critical_path":        cp_result.critical_path,
        "critical_link_ids":    list(cp_result.critical_link_ids),
        "total_lead_time_days": cp_result.total_lead_time,
        "min_cut_bpd":          mc_result.max_flow_bpd,
        "bottleneck_edges":     mc_result.cut_edges,
        "single_points_of_failure": spofs,
        "node_importance":      {k: round(v, 4) for k, v in importance.items()},
    }


@router.get(
    "/run/{run_id}/vulnerability-report",
    response_model=dict,
    summary="Generate full composite vulnerability report for a run",
)
async def get_vulnerability_report(
    run_id: uuid.UUID,
    _user: CurrentUser,
    db: DbSession,
    node_repo: NodeRepo,
    link_repo: LinkRepo,
    weights_structural:  float = Query(default=0.25, ge=0.0, le=1.0),
    weights_stochastic:  float = Query(default=0.35, ge=0.0, le=1.0),
    weights_economic:    float = Query(default=0.25, ge=0.0, le=1.0),
    weights_temporal:    float = Query(default=0.15, ge=0.0, le=1.0),
) -> dict:
    """
    Generate a composite vulnerability report combining:
    - Structural (graph topology)
    - Stochastic (simulation failure frequency)
    - Economic (cost impact)
    - Temporal (recovery time)

    Weights must sum to 1.0 (validated before execution).
    """
    from app.or_engine.network_builder import NetworkBuilder
    from app.or_engine.vulnerability import VulnerabilityScorer
    from app.db.models import VulnerabilityAssessment

    total_weight = weights_structural + weights_stochastic + weights_economic + weights_temporal
    if abs(total_weight - 1.0) > 0.01:
        from app.core.exceptions import ValidationError
        raise ValidationError(
            message=f"Vulnerability weights must sum to 1.0, got {total_weight:.3f}."
        )

    nodes     = (await node_repo.get_network_graph_data())["nodes"]
    links     = await link_repo.get_links_for_graph()
    builder   = NetworkBuilder()
    graph     = builder.build_graph(nodes, links)

    # Pull simulation results for this run
    va_rows = (await db.execute(
        select(VulnerabilityAssessment)
        .where(VulnerabilityAssessment.run_id == run_id)
    )).scalars().all()

    sim_results: dict = {}
    for va in va_rows:
        eid = str(va.node_id or va.link_id)
        sim_results[eid] = {
            "failure_frequency":    float(va.failure_frequency),
            "avg_impact_cost_usd":  float(va.avg_impact_cost_usd),
            "avg_recovery_days":    float(va.avg_impact_delay_days),
        }

    scorer = VulnerabilityScorer(
        graph=graph,
        weights={
            "structural": weights_structural,
            "stochastic": weights_stochastic,
            "economic":   weights_economic,
            "temporal":   weights_temporal,
        },
    )
    import dataclasses
    report = scorer.generate_vulnerability_report(
        run_id=str(run_id),
        simulation_results=sim_results,
    )
    return dataclasses.asdict(report)


@router.post(
    "/optimise/mitigations",
    response_model=dict,
    dependencies=[AnalystRequired],
    summary="Run ILP optimisation to select the best mitigation strategies",
)
async def optimise_mitigations(
    db: DbSession,
    _user: CurrentUser,
    mode: str = Query(
        default="min_cost",
        pattern="^(min_cost|max_effect)$",
        description="'min_cost': minimise cost subject to effectiveness; "
                    "'max_effect': maximise effectiveness subject to budget",
    ),
    target_effectiveness: float = Query(
        default=0.60,
        ge=0.01,
        le=1.0,
        description="[min_cost mode] Required minimum aggregate effectiveness score",
    ),
    budget_usd: Optional[float] = Query(
        default=None,
        gt=0,
        description="[max_effect mode] Maximum total implementation budget in USD",
    ),
) -> dict:
    """
    Run the Integer Linear Programme to select the optimal set of
    mitigation strategies from the database catalogue.

    Solver: CBC (COIN Branch-and-Cut) via PuLP — open source, no licence.

    Returns: selected strategy IDs, total cost, effectiveness, and
    expected probability/severity reductions.
    """
    from app.or_engine.optimizer import MitigationOptimizer, MitigationStrategyInput
    import dataclasses

    rows = (await db.execute(select(MitigationStrategy))).scalars().all()
    if not rows:
        return {"status": "No strategies", "selected_strategies": []}

    strategies = [
        MitigationStrategyInput(
            strategy_id=str(r.strategy_id),
            strategy_name=r.strategy_name,
            implementation_cost_usd=float(r.implementation_cost_usd),
            annual_maintenance_cost_usd=float(r.annual_maintenance_cost_usd),
            effectiveness_score=float(r.effectiveness_score),
            reduces_probability_by=float(r.reduces_probability_by),
            reduces_severity_by=float(r.reduces_severity_by),
            reduces_recovery_time_by_pct=float(r.reduces_recovery_time_by_pct),
            feasibility_score=float(r.feasibility_score),
        )
        for r in rows
    ]

    optimizer = MitigationOptimizer(strategies)

    if mode == "min_cost":
        result = optimizer.optimise_min_cost(
            target_effectiveness=target_effectiveness,
            budget_usd=budget_usd,
        )
    else:
        if budget_usd is None:
            from app.core.exceptions import ValidationError
            raise ValidationError(
                message="budget_usd is required for max_effect mode."
            )
        result = optimizer.optimise_max_effectiveness(budget_usd=budget_usd)

    return dataclasses.asdict(result)
