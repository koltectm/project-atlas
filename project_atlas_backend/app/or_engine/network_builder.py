"""
app/or_engine/network_builder.py
=================================
Constructs a weighted directed graph from Phase 1 supply chain data.

Graph G = (V, E) where:
    V = supply chain nodes (node_id as vertex label)
    E = supply chain links (directed source → target)

Edge weight attributes (all stored on each edge):
    capacity        : max_capacity_bpd
    cost            : transport_cost_per_barrel × distance_km  (total route cost)
    cost_per_barrel : transport_cost_per_barrel
    time            : normal_lead_time_days
    reliability     : reliability_score  (0–1; higher = more reliable)
    unreliability   : 1 − reliability_score  (used as weight in shortest-path)
    vandalism_risk  : vandalism_risk_score
    distance_km     : distance_km
    link_type       : link_type string
    link_id         : UUID string (for reverse-lookup)

Node attributes (stored on each vertex):
    node_type       : node_type string
    stage           : upstream | midstream | downstream
    capacity_bpd    : nameplate capacity
    utilization     : current_utilization_pct
    criticality     : criticality_score
    redundancy      : redundancy_score
    latitude        : float
    longitude       : float
    geopolitical_zone : str
    operator        : str
    status          : operational | degraded | offline
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import networkx as nx
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ValidationReport:
    """Result of graph connectivity and integrity validation."""
    is_valid:             bool
    is_weakly_connected:  bool
    n_weakly_connected_components: int
    n_nodes:              int
    n_edges:              int
    nodes_with_no_outgoing: list[str]   # terminal nodes (expected for consumers)
    nodes_with_no_incoming: list[str]   # source nodes (expected for wellheads)
    isolated_nodes:       list[str]     # nodes with neither in nor out edges
    warnings:             list[str]
    errors:               list[str]


class NetworkBuilder:
    """
    Constructs, annotates, and validates the supply chain network graph.

    The builder is stateless — call build_graph() to produce a new DiGraph
    from raw node/link data. Designed to be called once per simulation run.
    """

    # Stages used to identify production sources and demand sinks
    SOURCE_STAGES  = {"upstream"}
    SINK_STAGES    = {"downstream"}

    # Node types that never have outgoing or incoming links respectively
    TERMINAL_TYPES = {"consumer"}
    SOURCE_TYPES   = {"wellhead"}

    def build_graph(
        self,
        nodes: list[dict],
        links: list[dict],
    ) -> nx.DiGraph:
        """
        Build a weighted directed graph from node and link data.

        Parameters
        ----------
        nodes : list of dicts
            Each dict must contain at minimum:
            node_id, node_type, stage, capacity_bpd, status.
        links : list of dicts
            Each dict must contain at minimum:
            link_id, source_node_id, target_node_id,
            max_capacity_bpd, transport_cost_per_barrel,
            distance_km, normal_lead_time_days, reliability_score.

        Returns
        -------
        nx.DiGraph with all node and edge attributes populated.
        """
        G = nx.DiGraph()
        G = self.add_node_attributes(G, nodes)
        G = self.add_edge_attributes(G, links)

        logger.info(
            "network_builder.graph_built",
            n_nodes=G.number_of_nodes(),
            n_edges=G.number_of_edges(),
        )
        return G

    def add_node_attributes(
        self,
        graph: nx.DiGraph,
        nodes: list[dict],
    ) -> nx.DiGraph:
        """
        Add all supply chain nodes to the graph with their attributes.

        Offline nodes are still added (they may be referenced by links)
        but marked with status='offline' so the flow model zeroes their
        incident edge capacities.
        """
        for node in nodes:
            node_id = str(node["node_id"])
            graph.add_node(
                node_id,
                node_id=node_id,
                node_name=node.get("node_name", ""),
                node_code=node.get("node_code", ""),
                node_type=node.get("node_type", ""),
                stage=node.get("stage", ""),
                capacity_bpd=float(node.get("capacity_bpd", 0)),
                utilization=float(node.get("current_utilization_pct", 0)),
                criticality=float(node.get("criticality_score", 0)),
                redundancy=float(node.get("redundancy_score", 0)),
                latitude=float(node.get("latitude", 0)),
                longitude=float(node.get("longitude", 0)),
                geopolitical_zone=node.get("geopolitical_zone", ""),
                operator=node.get("operator", ""),
                status=node.get("status", "operational"),
                mtbf_days=float(node.get("mean_time_between_failures_days") or 365),
                mttr_days=float(node.get("mean_time_to_repair_days") or 14),
            )
        return graph

    def add_edge_attributes(
        self,
        graph: nx.DiGraph,
        links: list[dict],
    ) -> nx.DiGraph:
        """
        Add all supply chain links as directed edges with weight attributes.

        Skips links where either endpoint node is not in the graph
        (defensive — should not happen with FK-consistent data).
        """
        skipped = 0
        for link in links:
            src = str(link["source_node_id"])
            tgt = str(link["target_node_id"])
            lid = str(link["link_id"])

            if src not in graph or tgt not in graph:
                logger.warning(
                    "network_builder.edge_skipped",
                    link_id=lid,
                    reason="endpoint_node_missing",
                    source=src,
                    target=tgt,
                )
                skipped += 1
                continue

            dist_km   = float(link.get("distance_km", 1.0))
            cost_pb   = float(link.get("transport_cost_per_barrel", 1.0))
            cap_bpd   = float(link.get("max_capacity_bpd", 0.0))
            rel       = float(link.get("reliability_score", 0.9))
            lead_time = float(link.get("normal_lead_time_days", 1.0))
            van_risk  = float(link.get("vandalism_risk_score") or 0.0)

            # Status-aware capacity: degraded → 50% capacity, offline → 0
            status = link.get("status", "operational")
            if status == "offline":
                effective_cap = 0.0
            elif status == "degraded":
                effective_cap = cap_bpd * 0.50
            else:
                effective_cap = cap_bpd

            graph.add_edge(
                src, tgt,
                link_id=lid,
                link_code=link.get("link_code", ""),
                link_type=link.get("link_type", "pipeline"),
                capacity=effective_cap,         # used by max-flow algorithm
                max_capacity_bpd=cap_bpd,       # original nameplate
                cost_per_barrel=cost_pb,
                distance_km=dist_km,
                total_route_cost=cost_pb * dist_km,  # used as Dijkstra weight
                time=lead_time,
                reliability=rel,
                unreliability=1.0 - rel,        # inverse weight for shortest reliable path
                vandalism_risk=van_risk,
                is_critical_path=bool(link.get("is_critical_path", False)),
                status=status,
                alternative_routes=link.get("alternative_routes", []),
            )

        if skipped:
            logger.warning("network_builder.edges_skipped_total", count=skipped)

        return graph

    def export_for_frontend(self, graph: nx.DiGraph) -> dict:
        """
        Export graph as JSON-serialisable dict for D3/Recharts visualisation.

        Returns
        -------
        dict with keys:
            nodes : list of node dicts (id + attributes)
            edges : list of edge dicts (source, target + attributes)
            metadata : graph-level statistics
        """
        nodes_out = []
        for node_id, attrs in graph.nodes(data=True):
            if node_id.startswith("__"):
                continue  # Skip super-source/sink sentinels
            nodes_out.append({"id": node_id, **attrs})

        edges_out = []
        for src, tgt, attrs in graph.edges(data=True):
            if src.startswith("__") or tgt.startswith("__"):
                continue
            edges_out.append({"source": src, "target": tgt, **attrs})

        return {
            "nodes": nodes_out,
            "edges": edges_out,
            "metadata": {
                "n_nodes":       graph.number_of_nodes(),
                "n_edges":       graph.number_of_edges(),
                "total_capacity_bpd": sum(
                    d.get("max_capacity_bpd", 0)
                    for _, _, d in graph.edges(data=True)
                ),
            },
        }

    def validate_graph_connectivity(self, graph: nx.DiGraph) -> ValidationReport:
        """
        Validate the graph structure for simulation correctness.

        Checks:
        1. Weak connectivity (is the graph connected at all?)
        2. Isolated nodes (no edges at all — likely a data error)
        3. Reachability from upstream → downstream
        4. Presence of source and sink nodes
        """
        warnings: list[str] = []
        errors:   list[str] = []

        # Filter out sentinel nodes
        real_nodes = [n for n in graph.nodes if not str(n).startswith("__")]
        real_graph = graph.subgraph(real_nodes)

        # Check weak connectivity
        undirected = real_graph.to_undirected()
        components = list(nx.connected_components(undirected))
        n_components = len(components)
        is_weakly = nx.is_weakly_connected(real_graph) if real_graph.number_of_nodes() > 0 else False

        if not is_weakly:
            errors.append(
                f"Graph is not weakly connected: {n_components} components found. "
                "Some nodes are unreachable from the rest of the network."
            )

        # Isolated nodes
        isolated = [n for n in real_graph.nodes
                    if real_graph.in_degree(n) == 0 and real_graph.out_degree(n) == 0]
        if isolated:
            warnings.append(f"Isolated nodes (no edges): {isolated}")

        # Source nodes (no incoming)
        no_incoming = [
            n for n in real_graph.nodes
            if real_graph.in_degree(n) == 0 and n not in isolated
        ]
        # Sink nodes (no outgoing)
        no_outgoing = [
            n for n in real_graph.nodes
            if real_graph.out_degree(n) == 0 and n not in isolated
        ]

        # Validate source and sink nodes exist
        upstream_nodes = [
            n for n, d in real_graph.nodes(data=True)
            if d.get("stage") == "upstream"
        ]
        downstream_nodes = [
            n for n, d in real_graph.nodes(data=True)
            if d.get("stage") == "downstream"
        ]

        if not upstream_nodes:
            errors.append("No upstream nodes found. At least one wellhead/source node is required.")
        if not downstream_nodes:
            errors.append("No downstream nodes found. At least one consumer/sink node is required.")

        # Check that at least one path exists from upstream to downstream
        if upstream_nodes and downstream_nodes:
            path_found = False
            for src in upstream_nodes[:3]:  # Check first 3 sources (performance)
                for tgt in downstream_nodes[:3]:
                    try:
                        if nx.has_path(real_graph, src, tgt):
                            path_found = True
                            break
                    except nx.NetworkXError:
                        pass
                if path_found:
                    break

            if not path_found:
                errors.append(
                    "No path found from any upstream node to any downstream node. "
                    "The network cannot model supply chain flow."
                )
            else:
                logger.debug("network_builder.path_check.passed")

        is_valid = len(errors) == 0

        report = ValidationReport(
            is_valid=is_valid,
            is_weakly_connected=is_weakly,
            n_weakly_connected_components=n_components,
            n_nodes=real_graph.number_of_nodes(),
            n_edges=real_graph.number_of_edges(),
            nodes_with_no_outgoing=no_outgoing,
            nodes_with_no_incoming=no_incoming,
            isolated_nodes=isolated,
            warnings=warnings,
            errors=errors,
        )

        log_fn = logger.error if not is_valid else logger.info
        log_fn(
            "network_builder.validation",
            is_valid=is_valid,
            n_nodes=report.n_nodes,
            n_edges=report.n_edges,
            n_components=n_components,
            errors=errors,
            warnings=warnings,
        )

        return report
