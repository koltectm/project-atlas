"""
app/simulation/flow_model.py
============================
Supply chain flow computation under disrupted network conditions.

Mathematical Foundation
-----------------------
The supply chain is modelled as a directed flow network G = (V, E).

Max-flow / Min-cut theorem (Ford-Fulkerson):
    max_flow(source → sink) = min_cut_capacity

Under disruption with severity s on link l:
    effective_capacity_l = original_capacity_l × max(0, 1 − s)

Under node failure with severity s on node n:
    For all incident edges e of n:
        effective_capacity_e = original_capacity_e × max(0, 1 − s)

Flow fraction (per iteration):
    flow_fraction_i = max_flow_disrupted_i / max_flow_baseline

Vectorisation Strategy
-----------------------
Running NetworkX max_flow for all 10,000 iterations independently would take
~100–500 seconds. Instead we:

1. Cluster iterations by their unique disruption pattern (using a hash of
   which disruptions fired). Typical unique cluster count: 50–300.
2. Run max_flow only once per unique cluster.
3. Map results back to all iterations via cluster membership.

This reduces max_flow calls from 10,000 to ~50–300, achieving the 60s target.
"""

from __future__ import annotations

import hashlib
from typing import Any

import networkx as nx
import numpy as np
import structlog

logger = structlog.get_logger(__name__)

# Super-source and super-sink node IDs (sentinel strings)
_SUPER_SOURCE = "__SUPER_SOURCE__"
_SUPER_SINK   = "__SUPER_SINK__"


class FlowModel:
    """
    Computes supply chain throughput under disrupted conditions.

    Parameters
    ----------
    graph : nx.DiGraph
        Baseline supply chain graph built by NetworkBuilder.
        Each edge must have a 'capacity' attribute (max_capacity_bpd).
    upstream_node_ids : list[str]
        Node IDs that act as production sources (wellheads, FPSO terminals).
    downstream_node_ids : list[str]
        Node IDs that act as final demand sinks (consumers, export markets).
    node_capacity_map : dict[str, float]
        Maps node_id → capacity_bpd. Used to model node-level failures.
    """

    def __init__(
        self,
        graph: nx.DiGraph,
        upstream_node_ids: list[str],
        downstream_node_ids: list[str],
        node_capacity_map: dict[str, float],
    ) -> None:
        self.graph = graph
        self.upstream_node_ids = upstream_node_ids
        self.downstream_node_ids = downstream_node_ids
        self.node_capacity_map = node_capacity_map

        # Build augmented graph with super-source and super-sink
        self._augmented = self._build_augmented_graph(graph)

        # Compute baseline max flow (no disruptions)
        self.baseline_flow = self._compute_max_flow(self._augmented)
        if self.baseline_flow <= 0:
            raise ValueError(
                "Baseline max flow is zero or negative. "
                "Check that the network graph is connected and has positive capacities."
            )

        logger.info(
            "flow_model.initialised",
            baseline_flow_bpd=self.baseline_flow,
            upstream_nodes=len(upstream_node_ids),
            downstream_nodes=len(downstream_node_ids),
        )

    # ── Public interface ──────────────────────────────────────────────────────

    def compute_flow_fractions(
        self,
        occurrence_matrix: np.ndarray,
        severity_matrix: np.ndarray,
        node_disruption_map: np.ndarray,
        link_disruption_map: np.ndarray,
    ) -> np.ndarray:
        """
        Compute supply chain flow fraction for each Monte Carlo iteration.

        Uses cluster-based deduplication: iterations with identical disruption
        patterns share a single max-flow computation.

        Parameters
        ----------
        occurrence_matrix : ndarray (n_iter, n_disruptions)
        severity_matrix   : ndarray (n_iter, n_disruptions)
        node_disruption_map : ndarray (n_disruptions, n_nodes)
            Binary matrix: 1 if disruption d affects node n.
        link_disruption_map : ndarray (n_disruptions, n_links)
            Binary matrix: 1 if disruption d affects link l.

        Returns
        -------
        flow_fractions : ndarray (n_iter,), values in [0.0, 1.0]
        """
        n_iter = occurrence_matrix.shape[0]
        flow_fractions = np.ones(n_iter, dtype=np.float64)

        # Compute effective capacity reduction per node and link per iteration
        # Shape: (n_iter, n_nodes) and (n_iter, n_links)
        node_severity = severity_matrix @ node_disruption_map  # (n_iter, n_nodes)
        link_severity = severity_matrix @ link_disruption_map  # (n_iter, n_links)
        node_severity = np.clip(node_severity, 0.0, 1.0)
        link_severity = np.clip(link_severity, 0.0, 1.0)

        # --- Cluster by unique (node_severity, link_severity) pattern ---
        # Convert each iteration's pattern to a hash for clustering
        n_no_disruption = int((~occurrence_matrix.any(axis=1)).sum())
        no_disruption_mask = ~occurrence_matrix.any(axis=1)
        flow_fractions[no_disruption_mask] = 1.0  # baseline → no computation needed

        disrupted_mask = occurrence_matrix.any(axis=1)
        disrupted_indices = np.where(disrupted_mask)[0]

        if len(disrupted_indices) == 0:
            return flow_fractions

        # Round severity values to 2 decimal places for clustering
        # (prevents an explosion of unique states from floating point noise)
        node_sev_disrupted = np.round(node_severity[disrupted_indices], 2)
        link_sev_disrupted = np.round(link_severity[disrupted_indices], 2)

        # Cluster using a view of the combined array
        combined = np.concatenate([node_sev_disrupted, link_sev_disrupted], axis=1)
        cluster_ids, cluster_inverse = np.unique(
            combined, axis=0, return_inverse=True
        )

        logger.debug(
            "flow_model.clusters",
            n_disrupted_iterations=len(disrupted_indices),
            n_unique_clusters=len(cluster_ids),
        )

        node_ids   = self._get_ordered_node_ids()
        link_pairs = self._get_ordered_link_pairs()

        # Compute one max_flow per unique cluster
        cluster_flows = np.empty(len(cluster_ids), dtype=np.float64)
        for cluster_idx, cluster_row in enumerate(cluster_ids):
            node_sev_row = cluster_row[:len(node_ids)]
            link_sev_row = cluster_row[len(node_ids):]

            # Build capacity-modified graph for this cluster
            mod_graph = self._apply_capacity_reductions(
                node_ids, link_pairs, node_sev_row, link_sev_row
            )
            cluster_flows[cluster_idx] = self._compute_max_flow(mod_graph)

        # Map cluster flows back to iterations
        for local_idx, global_idx in enumerate(disrupted_indices):
            cluster_flow = cluster_flows[cluster_inverse[local_idx]]
            flow_fractions[global_idx] = min(
                1.0, cluster_flow / self.baseline_flow
            )

        return np.clip(flow_fractions, 0.0, 1.0)

    def identify_bottlenecks(self) -> list[dict]:
        """
        Identify network bottlenecks by finding the minimum cut.

        Returns a list of dicts describing the bottleneck edges (the min-cut set).
        """
        try:
            cut_value, (reachable, non_reachable) = nx.minimum_cut(
                self._augmented, _SUPER_SOURCE, _SUPER_SINK
            )
        except nx.NetworkXError as exc:
            logger.warning("flow_model.min_cut_failed", error=str(exc))
            return []

        # Identify cut edges: from reachable → non-reachable
        bottlenecks = []
        for u in reachable:
            for v in self._augmented.successors(u):
                if v in non_reachable:
                    data = self._augmented.edges[u, v]
                    bottlenecks.append({
                        "source": u,
                        "target": v,
                        "capacity_bpd": data.get("capacity", 0),
                        "cut_value_bpd": cut_value,
                    })

        return sorted(bottlenecks, key=lambda x: x["capacity_bpd"])

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_augmented_graph(self, graph: nx.DiGraph) -> nx.DiGraph:
        """
        Add a super-source connected to all upstream nodes and
        a super-sink connected from all downstream nodes.

        The super-source/sink edges have infinite capacity so they never
        become the bottleneck.
        """
        g = graph.copy()
        g.add_node(_SUPER_SOURCE)
        g.add_node(_SUPER_SINK)

        INF = float(sum(
            d.get("capacity", 0)
            for _, _, d in graph.edges(data=True)
        ) * 10)  # 10× total network capacity as ∞ proxy

        for node_id in self.upstream_node_ids:
            if node_id in g:
                g.add_edge(_SUPER_SOURCE, node_id, capacity=INF)

        for node_id in self.downstream_node_ids:
            if node_id in g:
                g.add_edge(node_id, _SUPER_SINK, capacity=INF)

        return g

    def _compute_max_flow(self, graph: nx.DiGraph) -> float:
        """
        Run NetworkX maximum flow using the Preflow-Push algorithm.

        Preflow-Push (highest-label variant) is O(V²√E) and significantly
        faster than Edmonds-Karp O(VE²) for dense supply chain graphs.
        """
        try:
            flow_value, _ = nx.maximum_flow(
                graph,
                _SUPER_SOURCE,
                _SUPER_SINK,
                flow_func=nx.algorithms.flow.preflow_push,
            )
            return float(flow_value)
        except (nx.NetworkXError, nx.NetworkXUnfeasible) as exc:
            logger.warning("flow_model.max_flow_failed", error=str(exc))
            return 0.0

    def _get_ordered_node_ids(self) -> list[str]:
        """Return node IDs in a stable order (excluding super-source/sink)."""
        return [
            n for n in self.graph.nodes
            if n not in (_SUPER_SOURCE, _SUPER_SINK)
        ]

    def _get_ordered_link_pairs(self) -> list[tuple[str, str]]:
        """Return (source, target) pairs for all edges in a stable order."""
        return list(self.graph.edges())

    def _apply_capacity_reductions(
        self,
        node_ids: list[str],
        link_pairs: list[tuple[str, str]],
        node_severity_row: np.ndarray,
        link_severity_row: np.ndarray,
    ) -> nx.DiGraph:
        """
        Return a modified copy of the augmented graph with capacities
        reduced according to the node and link severity vectors.

        Node failures propagate to all incident edges:
            new_edge_capacity = base_capacity × (1 - max(node_sev_src, node_sev_tgt))
        """
        g = self._augmented.copy()

        # Build node severity lookup
        node_sev = {nid: float(node_severity_row[i]) for i, nid in enumerate(node_ids)}

        # Build link severity lookup  {(src, tgt): severity}
        link_sev = {pair: float(link_severity_row[i]) for i, pair in enumerate(link_pairs)}

        for u, v, data in g.edges(data=True):
            if u in (_SUPER_SOURCE, _SUPER_SINK) or v in (_SUPER_SOURCE, _SUPER_SINK):
                continue  # Never reduce super-source/sink edges

            base_cap = data.get("capacity", 0.0)

            # Link-level severity
            edge_sev = link_sev.get((u, v), 0.0)

            # Node-level severity (propagated from incident node failures)
            max_node_sev = max(node_sev.get(u, 0.0), node_sev.get(v, 0.0))

            # Combined: use max of link and node severity (conservative)
            combined_sev = max(edge_sev, max_node_sev)

            # Effective capacity — floor at 0
            g.edges[u, v]["capacity"] = max(0.0, base_cap * (1.0 - combined_sev))

        return g
