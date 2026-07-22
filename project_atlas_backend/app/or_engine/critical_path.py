"""
app/or_engine/critical_path.py
===============================
Critical path analysis and single-point-of-failure detection.

Methods Implemented
-------------------
1. Longest Path (CPM — Critical Path Method)
   Applied to the DAG weighted by normal_lead_time_days.
   Critical path = path with maximum total lead time from source to sink.
   Float = LS − ES (Late Start − Early Start); zero float → critical activity.

2. Maximum Flow / Minimum Cut
   Uses NetworkX preflow_push to find the bottleneck edge set.
   min_cut_capacity = max_flow (max-flow min-cut theorem).

3. Betweenness Centrality
   BC(v) = Σ_{s≠v≠t} [σ_st(v) / σ_st]
   High BC → critical intermediary node.

4. Single Points of Failure (SPOF)
   Articulation points of the undirected projection.
   A node is SPOF if its removal disconnects source from any sink.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import networkx as nx
import numpy as np
import structlog

logger = structlog.get_logger(__name__)

_SUPER_SOURCE = "__CP_SOURCE__"
_SUPER_SINK   = "__CP_SINK__"


@dataclass
class CriticalPathResult:
    """Output of CPM critical path analysis."""
    critical_path:     list[str]       # Ordered list of node IDs
    critical_edges:    list[tuple[str, str]]
    total_lead_time:   float           # Days
    critical_node_ids: set[str]
    critical_link_ids: set[str]
    all_paths_count:   int


@dataclass
class MinCutResult:
    """Output of max-flow / min-cut analysis."""
    max_flow_bpd:    float
    cut_edges:       list[dict]        # [{source, target, capacity_bpd}]
    cut_capacity:    float             # Same as max_flow (max-flow min-cut theorem)
    reachable_nodes: set[str]


@dataclass
class VulnerabilityRanking:
    """Single entity ranked by combined structural + simulation vulnerability."""
    entity_id:   str
    entity_type: str          # "node" or "link"
    entity_name: str
    rank:        int
    composite_score:       float
    betweenness_centrality: float
    is_spof:               bool
    failure_frequency:     float
    avg_cost_impact_usd:   float


class CriticalPathAnalyzer:
    """
    Identifies critical paths and structural vulnerabilities in the supply
    chain network graph.

    Parameters
    ----------
    graph : nx.DiGraph
        Supply chain graph built by NetworkBuilder (without super-source/sink).
    upstream_node_ids : list[str]
        Production source node IDs.
    downstream_node_ids : list[str]
        Consumer/export sink node IDs.
    """

    def __init__(
        self,
        graph: nx.DiGraph,
        upstream_node_ids: list[str],
        downstream_node_ids: list[str],
    ) -> None:
        self.graph = graph
        self.upstream_ids   = upstream_node_ids
        self.downstream_ids = downstream_node_ids
        self._augmented: Optional[nx.DiGraph] = None

    # ── Public interface ──────────────────────────────────────────────────────

    def find_critical_path(self) -> CriticalPathResult:
        """
        Find the longest (time-critical) path using DAG longest-path algorithm.

        If the graph has cycles, falls back to betweenness-centrality-based
        identification of the most important path.

        Returns
        -------
        CriticalPathResult
        """
        # Add super-source/sink for single-source/single-sink longest path
        aug = self._build_augmented()

        try:
            # nx.dag_longest_path requires a DAG; use 'time' edge weight
            critical_path = nx.dag_longest_path(aug, weight="time")
        except nx.NetworkXUnfeasible:
            # Graph has cycles — fall back to betweenness centrality ordering
            logger.warning("critical_path.dag_has_cycles.fallback_to_betweenness")
            bc = nx.betweenness_centrality(self.graph, weight="unreliability")
            top_nodes = sorted(bc, key=bc.get, reverse=True)[:10]
            critical_path = top_nodes

        # Strip super-source/sink sentinels
        critical_path = [
            n for n in critical_path
            if not str(n).startswith("__CP_")
        ]

        # Compute total lead time along path
        total_lead_time = sum(
            self.graph.edges[critical_path[i], critical_path[i + 1]].get("time", 0)
            for i in range(len(critical_path) - 1)
            if self.graph.has_edge(critical_path[i], critical_path[i + 1])
        )

        critical_edges = [
            (critical_path[i], critical_path[i + 1])
            for i in range(len(critical_path) - 1)
            if self.graph.has_edge(critical_path[i], critical_path[i + 1])
        ]

        # Collect critical link_ids for DB update
        critical_link_ids: set[str] = set()
        for src, tgt in critical_edges:
            link_id = self.graph.edges[src, tgt].get("link_id", "")
            if link_id:
                critical_link_ids.add(link_id)

        result = CriticalPathResult(
            critical_path=critical_path,
            critical_edges=critical_edges,
            total_lead_time=total_lead_time,
            critical_node_ids=set(critical_path),
            critical_link_ids=critical_link_ids,
            all_paths_count=self._estimate_path_count(),
        )

        logger.info(
            "critical_path.found",
            path_length=len(critical_path),
            total_lead_time_days=total_lead_time,
            n_critical_links=len(critical_link_ids),
        )
        return result

    def find_min_cut(self) -> MinCutResult:
        """
        Find the minimum cut (bottleneck) of the network.

        Uses preflow_push (O(V²√E)) for performance on our graph sizes.

        Returns
        -------
        MinCutResult with max_flow, cut capacity, and bottleneck edges.
        """
        aug = self._build_augmented()

        try:
            cut_value, (reachable, non_reachable) = nx.minimum_cut(
                aug, _SUPER_SOURCE, _SUPER_SINK,
                flow_func=nx.algorithms.flow.preflow_push,
            )
        except (nx.NetworkXError, nx.NetworkXUnfeasible) as exc:
            logger.error("critical_path.min_cut_failed", error=str(exc))
            return MinCutResult(
                max_flow_bpd=0.0, cut_edges=[], cut_capacity=0.0, reachable_nodes=set()
            )

        # Identify the cut edges (cross the partition boundary)
        cut_edges = []
        for u in reachable:
            for v in aug.successors(u):
                if v in non_reachable and not str(u).startswith("__") and not str(v).startswith("__"):
                    data = aug.edges[u, v]
                    cut_edges.append({
                        "source":       u,
                        "target":       v,
                        "link_id":      data.get("link_id", ""),
                        "link_type":    data.get("link_type", ""),
                        "capacity_bpd": data.get("max_capacity_bpd", 0),
                    })

        real_reachable = {n for n in reachable if not str(n).startswith("__")}

        logger.info(
            "critical_path.min_cut",
            max_flow_bpd=cut_value,
            n_cut_edges=len(cut_edges),
        )

        return MinCutResult(
            max_flow_bpd=float(cut_value),
            cut_edges=cut_edges,
            cut_capacity=float(cut_value),
            reachable_nodes=real_reachable,
        )

    def compute_betweenness_centrality(self) -> dict[str, float]:
        """
        Compute betweenness centrality for all nodes.

        BC(v) = Σ_{s≠v≠t} σ_st(v) / σ_st

        Weight: unreliability (1 − reliability_score) so shortest-path
        represents the most reliable route.

        Returns
        -------
        dict mapping node_id → betweenness_centrality [0.0, 1.0]
        """
        bc = nx.betweenness_centrality(
            self.graph,
            weight="unreliability",
            normalized=True,
        )
        logger.debug(
            "critical_path.betweenness",
            top_5=sorted(bc.items(), key=lambda x: -x[1])[:5],
        )
        return bc

    def compute_closeness_centrality(self) -> dict[str, float]:
        """Closeness centrality weighted by transport cost."""
        return nx.closeness_centrality(self.graph, distance="total_route_cost")

    def compute_degree_centrality(self) -> dict[str, float]:
        """Degree centrality (normalised in-degree + out-degree)."""
        return nx.degree_centrality(self.graph)

    def find_single_points_of_failure(self) -> list[str]:
        """
        Identify articulation points — nodes whose removal disconnects
        some source from some sink.

        Uses the undirected projection of the graph for articulation point
        detection (standard graph theory definition).

        Returns
        -------
        List of node_id strings that are single points of failure.
        """
        # Work only on real nodes (exclude super-source/sink)
        real_nodes = [n for n in self.graph.nodes if not str(n).startswith("__")]
        subgraph = self.graph.subgraph(real_nodes)
        undirected = subgraph.to_undirected()

        # Articulation points on the undirected graph
        ap_all = set(nx.articulation_points(undirected))

        # Further filter: only count as SPOF if removing the node disconnects
        # at least one upstream node from at least one downstream node
        true_spofs = []
        for candidate in ap_all:
            remaining = [n for n in real_nodes if n != candidate]
            reduced = self.graph.subgraph(remaining)
            spof_confirmed = False
            for src in self.upstream_ids[:5]:
                if src == candidate:
                    spof_confirmed = True
                    break
                for tgt in self.downstream_ids[:5]:
                    if tgt == candidate:
                        spof_confirmed = True
                        break
                    if src in reduced and tgt in reduced:
                        if not nx.has_path(reduced, src, tgt):
                            spof_confirmed = True
                            break
                if spof_confirmed:
                    break
            if spof_confirmed:
                true_spofs.append(candidate)

        logger.info(
            "critical_path.spof_detected",
            n_articulation_points=len(ap_all),
            n_confirmed_spofs=len(true_spofs),
            spofs=true_spofs,
        )
        return true_spofs

    def compute_node_importance(self) -> dict[str, float]:
        """
        Composite node importance score combining:
            - Betweenness centrality (structural position)
            - Degree centrality (connectivity)
            - Closeness centrality (reachability)

        Weights: 0.50 betweenness + 0.30 degree + 0.20 closeness.

        Returns
        -------
        dict mapping node_id → importance_score [0.0, 1.0]
        """
        bc = self.compute_betweenness_centrality()
        dc = self.compute_degree_centrality()
        cc = self.compute_closeness_centrality()

        all_nodes = set(bc) | set(dc) | set(cc)
        importance = {}
        for node in all_nodes:
            score = (
                0.50 * bc.get(node, 0.0)
                + 0.30 * dc.get(node, 0.0)
                + 0.20 * cc.get(node, 0.0)
            )
            importance[node] = min(1.0, score)

        return importance

    def rank_vulnerabilities(
        self,
        simulation_results: Optional[dict] = None,
    ) -> list[VulnerabilityRanking]:
        """
        Rank all network entities by combined structural and simulation vulnerability.

        Parameters
        ----------
        simulation_results : optional dict
            Keys: node_id → {failure_frequency, avg_cost_impact_usd}.
            If None, ranking is structural only.

        Returns
        -------
        List of VulnerabilityRanking sorted by composite_score descending.
        """
        importance    = self.compute_node_importance()
        bc            = self.compute_betweenness_centrality()
        spofs         = set(self.find_single_points_of_failure())

        rankings = []
        sim_data = simulation_results or {}

        for node_id, attrs in self.graph.nodes(data=True):
            if str(node_id).startswith("__"):
                continue

            struct_score = importance.get(node_id, 0.0)
            sim_entry    = sim_data.get(node_id, {})
            freq         = float(sim_entry.get("failure_frequency", 0.0))
            cost_impact  = float(sim_entry.get("avg_cost_impact_usd", 0.0))

            # Normalise cost impact to [0,1] if max cost is known
            max_cost = max(
                (v.get("avg_cost_impact_usd", 0) for v in sim_data.values()),
                default=1.0,
            )
            norm_cost = cost_impact / max_cost if max_cost > 0 else 0.0

            # SPOF bonus: confirmed SPOFs get 0.20 score addition
            spof_bonus = 0.20 if node_id in spofs else 0.0

            composite = min(1.0,
                0.40 * struct_score
                + 0.35 * freq
                + 0.25 * norm_cost
                + spof_bonus
            )

            rankings.append(VulnerabilityRanking(
                entity_id=node_id,
                entity_type="node",
                entity_name=attrs.get("node_name", attrs.get("node_code", node_id)),
                rank=0,
                composite_score=composite,
                betweenness_centrality=bc.get(node_id, 0.0),
                is_spof=node_id in spofs,
                failure_frequency=freq,
                avg_cost_impact_usd=cost_impact,
            ))

        # Sort and assign ranks
        rankings.sort(key=lambda r: r.composite_score, reverse=True)
        for rank_idx, ranking in enumerate(rankings, start=1):
            ranking.rank = rank_idx

        logger.info("critical_path.rankings_computed", n_entities=len(rankings))
        return rankings

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_augmented(self) -> nx.DiGraph:
        """Build augmented graph with super-source/sink (cached)."""
        if self._augmented is not None:
            return self._augmented

        g = self.graph.copy()
        g.add_node(_SUPER_SOURCE)
        g.add_node(_SUPER_SINK)

        INF_CAP = float(
            sum(d.get("capacity", 0) for _, _, d in g.edges(data=True)) * 10
        )
        INF_TIME = 0.0  # Super edges have zero lead time

        for node_id in self.upstream_ids:
            if node_id in g:
                g.add_edge(_SUPER_SOURCE, node_id,
                           capacity=INF_CAP, time=INF_TIME, unreliability=0.0,
                           total_route_cost=0.0, max_capacity_bpd=INF_CAP)

        for node_id in self.downstream_ids:
            if node_id in g:
                g.add_edge(node_id, _SUPER_SINK,
                           capacity=INF_CAP, time=INF_TIME, unreliability=0.0,
                           total_route_cost=0.0, max_capacity_bpd=INF_CAP)

        self._augmented = g
        return g

    def _estimate_path_count(self) -> int:
        """Estimate total number of source-to-sink paths (capped for performance)."""
        try:
            count = 0
            for src in self.upstream_ids[:3]:
                for tgt in self.downstream_ids[:3]:
                    if nx.has_path(self.graph, src, tgt):
                        paths = nx.all_simple_paths(
                            self.graph, src, tgt, cutoff=20
                        )
                        for _ in paths:
                            count += 1
                            if count >= 10_000:
                                return count
            return count
        except Exception:
            return -1
