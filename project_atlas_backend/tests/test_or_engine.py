"""
tests/test_or_engine.py
========================
Unit tests for the Operations Research engine:
  - NetworkBuilder: graph construction and validation
  - CriticalPathAnalyzer: CPM, min-cut, SPOF detection
  - VulnerabilityScorer: composite scoring
  - MitigationOptimizer: ILP solver (skipped if PuLP unavailable)

Run with: pytest tests/test_or_engine.py -v
"""

from __future__ import annotations

import pytest
import networkx as nx
import numpy as np

from app.or_engine.network_builder import NetworkBuilder
from app.or_engine.critical_path import CriticalPathAnalyzer
from app.or_engine.vulnerability import VulnerabilityScorer


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _make_nodes() -> list[dict]:
    return [
        {"node_id": "wh1",  "node_code": "WH-001",  "node_type": "wellhead",
         "stage": "upstream",   "capacity_bpd": 200_000, "current_utilization_pct": 0.72,
         "criticality_score": 0.82, "redundancy_score": 0.45, "status": "operational",
         "geopolitical_zone": "SS", "latitude": 4.44, "longitude": 7.16,
         "operator": "SPDC", "mean_time_between_failures_days": 210, "mean_time_to_repair_days": 14},
        {"node_id": "et1",  "node_code": "ET-001",  "node_type": "export_terminal",
         "stage": "midstream",  "capacity_bpd": 800_000, "current_utilization_pct": 0.62,
         "criticality_score": 0.90, "redundancy_score": 0.55, "status": "operational",
         "geopolitical_zone": "SS", "latitude": 4.45, "longitude": 7.15, "operator": "SPDC",
         "mean_time_between_failures_days": 365, "mean_time_to_repair_days": 7},
        {"node_id": "ref1", "node_code": "REF-001", "node_type": "refinery",
         "stage": "midstream",  "capacity_bpd": 650_000, "current_utilization_pct": 0.45,
         "criticality_score": 0.95, "redundancy_score": 0.70, "status": "operational",
         "geopolitical_zone": "SW", "latitude": 6.41, "longitude": 3.38, "operator": "Dangote",
         "mean_time_between_failures_days": 200, "mean_time_to_repair_days": 14},
        {"node_id": "dep1", "node_code": "DEP-001", "node_type": "storage_depot",
         "stage": "midstream",  "capacity_bpd": 0, "current_utilization_pct": 0.80,
         "criticality_score": 0.88, "redundancy_score": 0.50, "status": "operational",
         "geopolitical_zone": "SW", "latitude": 6.39, "longitude": 3.35, "operator": "NNPC",
         "mean_time_between_failures_days": 120, "mean_time_to_repair_days": 5},
        {"node_id": "con1", "node_code": "CON-001", "node_type": "consumer",
         "stage": "downstream", "capacity_bpd": 0, "current_utilization_pct": 0.85,
         "criticality_score": 0.65, "redundancy_score": 0.60, "status": "operational",
         "geopolitical_zone": "SW", "latitude": 6.52, "longitude": 3.37, "operator": "Various",
         "mean_time_between_failures_days": 30, "mean_time_to_repair_days": 2},
    ]


def _make_links() -> list[dict]:
    return [
        {"link_id": "l1", "link_code": "L-001", "link_type": "pipeline",
         "source_node_id": "wh1", "target_node_id": "et1",
         "distance_km": 160, "normal_lead_time_days": 1.5,
         "transport_cost_per_barrel": 0.85, "max_capacity_bpd": 450_000,
         "current_utilization_pct": 0.72, "reliability_score": 0.62,
         "vandalism_risk_score": 0.78, "is_critical_path": True, "status": "operational"},
        {"link_id": "l2", "link_code": "L-002", "link_type": "sea_route",
         "source_node_id": "et1", "target_node_id": "ref1",
         "distance_km": 520, "normal_lead_time_days": 2.5,
         "transport_cost_per_barrel": 1.20, "max_capacity_bpd": 400_000,
         "current_utilization_pct": 0.45, "reliability_score": 0.88,
         "vandalism_risk_score": 0.02, "is_critical_path": True, "status": "operational"},
        {"link_id": "l3", "link_code": "L-003", "link_type": "road",
         "source_node_id": "ref1", "target_node_id": "dep1",
         "distance_km": 18, "normal_lead_time_days": 0.2,
         "transport_cost_per_barrel": 0.28, "max_capacity_bpd": 600_000,
         "current_utilization_pct": 0.45, "reliability_score": 0.95,
         "vandalism_risk_score": 0.05, "is_critical_path": True, "status": "operational"},
        {"link_id": "l4", "link_code": "L-004", "link_type": "road",
         "source_node_id": "dep1", "target_node_id": "con1",
         "distance_km": 30, "normal_lead_time_days": 0.4,
         "transport_cost_per_barrel": 0.90, "max_capacity_bpd": 150_000,
         "current_utilization_pct": 0.85, "reliability_score": 0.90,
         "vandalism_risk_score": 0.05, "is_critical_path": False, "status": "operational"},
    ]


@pytest.fixture
def graph() -> nx.DiGraph:
    builder = NetworkBuilder()
    return builder.build_graph(_make_nodes(), _make_links())


@pytest.fixture
def analyzer(graph) -> CriticalPathAnalyzer:
    return CriticalPathAnalyzer(
        graph=graph,
        upstream_node_ids=["wh1"],
        downstream_node_ids=["con1"],
    )


# ─── NetworkBuilder Tests ─────────────────────────────────────────────────────

class TestNetworkBuilder:

    def test_graph_node_count(self, graph):
        assert graph.number_of_nodes() == 5

    def test_graph_edge_count(self, graph):
        assert graph.number_of_edges() == 4

    def test_edge_capacity_attribute(self, graph):
        """Every edge must have a capacity attribute."""
        for u, v, data in graph.edges(data=True):
            assert "capacity" in data, f"Edge ({u},{v}) missing 'capacity'"
            assert data["capacity"] >= 0

    def test_edge_cost_attributes(self, graph):
        """Every edge must have cost_per_barrel and total_route_cost."""
        for u, v, data in graph.edges(data=True):
            assert "cost_per_barrel" in data
            assert "total_route_cost" in data
            assert data["total_route_cost"] > 0

    def test_node_attributes(self, graph):
        """Nodes must have stage, node_type, criticality, redundancy."""
        for node_id, data in graph.nodes(data=True):
            assert "stage"       in data, f"Node {node_id} missing 'stage'"
            assert "node_type"   in data
            assert "criticality" in data
            assert "redundancy"  in data

    def test_offline_node_edge_capacity_zero(self):
        """Links to/from an offline node must have capacity=0."""
        nodes = _make_nodes()
        links = _make_links()
        # Mark l2 as offline
        links[1]["status"] = "offline"

        builder = NetworkBuilder()
        g = builder.build_graph(nodes, links)
        cap = g.edges["et1", "ref1"]["capacity"]
        assert cap == 0.0, f"Offline link should have capacity=0, got {cap}"

    def test_degraded_link_half_capacity(self):
        """Degraded links should have 50% of their nameplate capacity."""
        nodes = _make_nodes()
        links = _make_links()
        links[0]["status"] = "degraded"
        original_cap = links[0]["max_capacity_bpd"]

        builder = NetworkBuilder()
        g = builder.build_graph(nodes, links)
        cap = g.edges["wh1", "et1"]["capacity"]
        assert abs(cap - original_cap * 0.5) < 1.0, \
            f"Degraded capacity: expected {original_cap*0.5}, got {cap}"

    def test_unreliability_is_one_minus_reliability(self, graph):
        for u, v, data in graph.edges(data=True):
            assert abs(data["unreliability"] - (1.0 - data["reliability"])) < 1e-10

    def test_validation_report_is_valid(self, graph):
        builder = NetworkBuilder()
        report = builder.validate_graph_connectivity(graph)
        assert report.is_valid, f"Graph validation failed: {report.errors}"
        assert report.is_weakly_connected
        assert report.n_nodes == 5
        assert report.n_edges == 4

    def test_validation_detects_isolated_nodes(self):
        """A graph with an isolated node should report a warning."""
        nodes = _make_nodes() + [{
            "node_id": "isolated", "node_code": "ISO-001",
            "node_type": "wellhead", "stage": "upstream",
            "capacity_bpd": 0, "current_utilization_pct": 0,
            "criticality_score": 0, "redundancy_score": 0,
            "status": "operational", "geopolitical_zone": "NC",
            "latitude": 9.0, "longitude": 7.0, "operator": "Test",
        }]
        builder = NetworkBuilder()
        g = builder.build_graph(nodes, _make_links())
        report = builder.validate_graph_connectivity(g)
        assert "isolated" in report.isolated_nodes

    def test_export_for_frontend_structure(self, graph):
        builder = NetworkBuilder()
        exported = builder.export_for_frontend(graph)
        assert "nodes" in exported
        assert "edges" in exported
        assert "metadata" in exported
        assert exported["metadata"]["n_nodes"] == 5
        assert exported["metadata"]["n_edges"] == 4

    def test_missing_endpoint_node_skips_edge(self):
        """An edge referencing a non-existent node should be silently skipped."""
        links = _make_links() + [{
            "link_id": "l_bad", "link_code": "BAD",
            "link_type": "road", "source_node_id": "NONEXISTENT",
            "target_node_id": "con1", "distance_km": 10,
            "normal_lead_time_days": 1, "transport_cost_per_barrel": 1,
            "max_capacity_bpd": 10_000, "current_utilization_pct": 0.5,
            "reliability_score": 0.9, "vandalism_risk_score": 0,
            "is_critical_path": False, "status": "operational",
        }]
        builder = NetworkBuilder()
        g = builder.build_graph(_make_nodes(), links)
        # Should have only 4 valid edges (bad edge skipped)
        assert g.number_of_edges() == 4


# ─── CriticalPathAnalyzer Tests ───────────────────────────────────────────────

class TestCriticalPathAnalyzer:

    def test_find_critical_path_returns_path(self, analyzer):
        result = analyzer.find_critical_path()
        assert len(result.critical_path) >= 2, "Critical path should contain at least 2 nodes"

    def test_critical_path_starts_upstream_ends_downstream(self, analyzer):
        result = analyzer.find_critical_path()
        assert result.critical_path[0]  == "wh1",  "Path should start at upstream wellhead"
        assert result.critical_path[-1] == "con1", "Path should end at downstream consumer"

    def test_critical_path_total_lead_time_positive(self, analyzer):
        result = analyzer.find_critical_path()
        assert result.total_lead_time > 0

    def test_find_min_cut_flow_positive(self, analyzer):
        result = analyzer.find_min_cut()
        assert result.max_flow_bpd > 0, "Min-cut max flow should be positive"

    def test_min_cut_identifies_bottleneck_edges(self, analyzer):
        result = analyzer.find_min_cut()
        # The bottleneck should be the DEP→CON link (150,000 bpd — smallest capacity)
        assert len(result.cut_edges) >= 1
        cut_caps = [e["capacity_bpd"] for e in result.cut_edges]
        assert min(cut_caps) <= 150_000, \
            f"Min-cut capacity unexpectedly high: {min(cut_caps)}"

    def test_betweenness_centrality_all_nodes(self, analyzer):
        bc = analyzer.compute_betweenness_centrality()
        nodes = _make_nodes()
        node_ids = {n["node_id"] for n in nodes}
        for nid in node_ids:
            assert nid in bc, f"Node {nid} missing from betweenness centrality"
            assert 0.0 <= bc[nid] <= 1.0, f"BC out of [0,1]: {bc[nid]}"

    def test_closeness_centrality_non_negative(self, analyzer):
        cc = analyzer.compute_closeness_centrality()
        for nid, score in cc.items():
            assert score >= 0.0

    def test_find_spof_detects_intermediary(self, analyzer):
        """et1 and ref1 are intermediary nodes — removing either disconnects wh1 from con1."""
        spofs = analyzer.find_single_points_of_failure()
        # At minimum et1 should be a SPOF (only path from wh1 goes through it)
        assert "et1" in spofs or "ref1" in spofs, \
            f"Expected et1 or ref1 to be SPOF, got: {spofs}"

    def test_compute_node_importance_bounds(self, analyzer):
        importance = analyzer.compute_node_importance()
        for nid, score in importance.items():
            assert 0.0 <= score <= 1.0, \
                f"Importance score out of [0,1]: {nid}={score}"

    def test_rank_vulnerabilities_ordered(self, analyzer):
        rankings = analyzer.rank_vulnerabilities()
        scores = [r.composite_score for r in rankings]
        assert scores == sorted(scores, reverse=True), \
            "Vulnerability rankings should be sorted descending by composite_score"

    def test_rank_assignments_sequential(self, analyzer):
        rankings = analyzer.rank_vulnerabilities()
        ranks = [r.rank for r in rankings]
        assert ranks == list(range(1, len(rankings) + 1)), \
            "Ranks should be sequential integers starting at 1"


# ─── VulnerabilityScorer Tests ────────────────────────────────────────────────

class TestVulnerabilityScorer:

    def test_weights_must_sum_to_one(self, graph):
        with pytest.raises(ValueError, match="must sum to 1.0"):
            VulnerabilityScorer(graph, weights={
                "structural": 0.5, "stochastic": 0.5,
                "economic": 0.5, "temporal": 0.5,
            })

    def test_structural_scores_in_bounds(self, graph):
        scorer = VulnerabilityScorer(graph)
        scores = scorer.compute_structural_vulnerability()
        for nid, score in scores.items():
            assert 0.0 <= score <= 1.0, f"{nid} structural score out of [0,1]: {score}"

    def test_composite_with_no_simulation_data(self, graph):
        """Composite should gracefully handle empty simulation_results."""
        scorer = VulnerabilityScorer(graph)
        struct = scorer.compute_structural_vulnerability()
        stoch  = scorer.compute_stochastic_vulnerability({})
        econ   = scorer.compute_economic_vulnerability({})
        temp   = scorer.compute_temporal_vulnerability({})
        composite = scorer.compute_composite_score(struct, stoch, econ, temp)

        for nid, score in composite.items():
            assert 0.0 <= score <= 1.0

    def test_high_frequency_entity_gets_high_stochastic_score(self, graph):
        scorer = VulnerabilityScorer(graph)
        sim_data = {
            "wh1":  {"failure_frequency": 0.9, "avg_impact_cost_usd": 50_000_000},
            "et1":  {"failure_frequency": 0.1, "avg_impact_cost_usd":  5_000_000},
            "con1": {"failure_frequency": 0.0, "avg_impact_cost_usd":          0},
        }
        stoch = scorer.compute_stochastic_vulnerability(sim_data)
        assert stoch.get("wh1", 0) > stoch.get("et1", 0), \
            "High-frequency entity should have higher stochastic vulnerability"
        assert stoch.get("et1", 0) > stoch.get("con1", 0)

    def test_generate_report_returns_ranked_entities(self, graph):
        scorer = VulnerabilityScorer(graph)
        report = scorer.generate_vulnerability_report(
            run_id="test-run",
            simulation_results={
                "wh1": {"failure_frequency": 0.7, "avg_impact_cost_usd": 20_000_000, "avg_recovery_days": 25},
                "et1": {"failure_frequency": 0.5, "avg_impact_cost_usd": 10_000_000, "avg_recovery_days": 10},
            },
        )
        assert len(report.ranked_entities) > 0
        scores = [e["composite_score"] for e in report.ranked_entities]
        assert scores == sorted(scores, reverse=True)

    def test_custom_weights_applied(self, graph):
        """Setting structural weight to 1.0 should dominate the composite score."""
        scorer = VulnerabilityScorer(graph, weights={
            "structural": 1.0,
            "stochastic": 0.0,
            "economic":   0.0,
            "temporal":   0.0,
        })
        struct    = scorer.compute_structural_vulnerability()
        stoch     = scorer.compute_stochastic_vulnerability({})
        econ      = scorer.compute_economic_vulnerability({})
        temp      = scorer.compute_temporal_vulnerability({})
        composite = scorer.compute_composite_score(struct, stoch, econ, temp)

        for nid in struct:
            assert abs(composite.get(nid, 0) - struct[nid]) < 1e-9, \
                f"Composite should equal structural when w_structural=1.0 for {nid}"


# ─── MitigationOptimizer Tests ────────────────────────────────────────────────

try:
    import pulp as _pulp
    PULP_AVAILABLE = True
except ImportError:
    PULP_AVAILABLE = False


@pytest.mark.skipif(not PULP_AVAILABLE, reason="PuLP not installed")
class TestMitigationOptimizer:

    def _make_strategies(self):
        from app.or_engine.optimizer import MitigationStrategyInput
        return [
            MitigationStrategyInput(
                strategy_id="s1", strategy_name="Aerial Surveillance",
                implementation_cost_usd=85_000_000, annual_maintenance_cost_usd=12_000_000,
                effectiveness_score=0.55, reduces_probability_by=0.40,
                reduces_severity_by=0.30, reduces_recovery_time_by_pct=0.35,
                feasibility_score=0.70,
            ),
            MitigationStrategyInput(
                strategy_id="s2", strategy_name="Strategic Petroleum Reserve",
                implementation_cost_usd=2_500_000_000, annual_maintenance_cost_usd=45_000_000,
                effectiveness_score=0.80, reduces_probability_by=0.00,
                reduces_severity_by=0.70, reduces_recovery_time_by_pct=0.50,
                feasibility_score=0.55,
            ),
            MitigationStrategyInput(
                strategy_id="s3", strategy_name="Community Engagement Fund",
                implementation_cost_usd=200_000_000, annual_maintenance_cost_usd=50_000_000,
                effectiveness_score=0.65, reduces_probability_by=0.55,
                reduces_severity_by=0.40, reduces_recovery_time_by_pct=0.20,
                feasibility_score=0.75,
            ),
            MitigationStrategyInput(
                strategy_id="s4", strategy_name="Generator Backup",
                implementation_cost_usd=180_000_000, annual_maintenance_cost_usd=15_000_000,
                effectiveness_score=0.85, reduces_probability_by=0.80,
                reduces_severity_by=0.90, reduces_recovery_time_by_pct=0.95,
                feasibility_score=0.90,
            ),
        ]

    def test_min_cost_returns_optimal_status(self):
        from app.or_engine.optimizer import MitigationOptimizer
        opt    = MitigationOptimizer(self._make_strategies())
        result = opt.optimise_min_cost(target_effectiveness=0.50)
        assert result.status == "Optimal"

    def test_min_cost_meets_effectiveness_target(self):
        from app.or_engine.optimizer import MitigationOptimizer
        target = 0.60
        opt    = MitigationOptimizer(self._make_strategies())
        result = opt.optimise_min_cost(target_effectiveness=target)
        assert result.total_effectiveness >= target - 0.001, \
            f"Effectiveness {result.total_effectiveness:.3f} < target {target}"

    def test_max_effect_returns_optimal_status(self):
        from app.or_engine.optimizer import MitigationOptimizer
        opt    = MitigationOptimizer(self._make_strategies())
        result = opt.optimise_max_effectiveness(budget_usd=500_000_000)
        assert result.status == "Optimal"

    def test_max_effect_respects_budget(self):
        from app.or_engine.optimizer import MitigationOptimizer
        budget = 500_000_000
        opt    = MitigationOptimizer(self._make_strategies())
        result = opt.optimise_max_effectiveness(budget_usd=budget)
        assert result.total_cost_usd <= budget + 1.0, \
            f"Total cost {result.total_cost_usd:,.0f} exceeds budget {budget:,.0f}"

    def test_selected_strategies_are_subset(self):
        from app.or_engine.optimizer import MitigationOptimizer
        strats = self._make_strategies()
        opt    = MitigationOptimizer(strats)
        result = opt.optimise_min_cost(target_effectiveness=0.50)
        valid_ids = {s.strategy_id for s in strats}
        for sid in result.selected_strategies:
            assert sid in valid_ids, f"Unknown strategy selected: {sid}"

    def test_infeasible_target_returns_non_optimal(self):
        """Requesting effectiveness > 1.0 worth of strategies should be infeasible."""
        from app.or_engine.optimizer import MitigationOptimizer
        opt = MitigationOptimizer(self._make_strategies())
        # Requesting effectiveness of 10.0 (impossible — all strategies sum to < 3.0)
        result = opt.optimise_min_cost(target_effectiveness=10.0)
        assert result.status != "Optimal"

    def test_zero_budget_selects_nothing(self):
        from app.or_engine.optimizer import MitigationOptimizer
        opt    = MitigationOptimizer(self._make_strategies())
        result = opt.optimise_max_effectiveness(budget_usd=1.0)  # $1 budget
        assert len(result.selected_strategies) == 0

    def test_cost_breakdown_matches_selected(self):
        from app.or_engine.optimizer import MitigationOptimizer
        opt    = MitigationOptimizer(self._make_strategies())
        result = opt.optimise_min_cost(target_effectiveness=0.50)
        bd_ids = {entry["strategy_id"] for entry in result.cost_breakdown}
        assert bd_ids == set(result.selected_strategies)

    def test_invalid_target_raises(self):
        from app.or_engine.optimizer import MitigationOptimizer
        opt = MitigationOptimizer(self._make_strategies())
        with pytest.raises(ValueError):
            opt.optimise_min_cost(target_effectiveness=0.0)
        with pytest.raises(ValueError):
            opt.optimise_min_cost(target_effectiveness=1.5)

    def test_empty_strategies_raises(self):
        from app.or_engine.optimizer import MitigationOptimizer
        with pytest.raises(ValueError, match="At least one"):
            MitigationOptimizer([])
