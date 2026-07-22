"""
app/simulation/cost_model.py
============================
Economic cost computation for each Monte Carlo iteration.

Total Cost per Iteration
-------------------------
C_total = C_transport + C_delay + C_production_loss + C_penalty

Where:
    C_transport    = Σ_links (volume_l × cost_per_barrel_l × disruption_multiplier)
    C_delay        = Σ_nodes (delay_days × daily_holding_cost × avg_inventory)
    C_production_loss = lost_barrels × brent_crude_price_usd
    C_penalty      = max(0, max_delay_days − SLA_days) × penalty_per_day

Reference values (Nigerian context, 2023-2024):
    Brent crude:           ~$82.50/bbl
    Holding cost:          ~$0.50/bbl/day
    Pipeline transport:    ~$0.40–$2.20/bbl/100km
    Road transport:        ~$2.60–$4.80/bbl/100km
    Sea route:             ~$0.75–$1.85/bbl/100km
    SLA (contract delivery): typically 7–14 days lead time tolerance
    Penalty rate:          ~$50,000/day per contract (parameterised)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class LinkCostData:
    """Cost parameters for one supply chain link."""
    link_id:                   str
    link_type:                 str   # 'pipeline', 'road', 'sea_route', etc.
    transport_cost_per_barrel: float
    distance_km:               float
    max_capacity_bpd:          float
    index:                     int = -1  # Position in link arrays


@dataclass
class NetworkCostConstants:
    """Network-wide cost constants (loaded from settings + scenario)."""
    baseline_daily_throughput_bpd: float  # e.g. 1_300_000 for Nigeria
    crude_price_usd_per_barrel:    float  # e.g. 82.50
    holding_cost_usd_per_barrel_day: float  # e.g. 0.50
    sla_tolerance_days:            float  # delay tolerance before penalty
    penalty_per_day_usd:           float  # per-day contract penalty
    avg_inventory_barrels:         float  # average inventory held (all depots)


class CostModel:
    """
    Vectorised economic cost calculator.

    All methods operate on NumPy arrays of shape (n_iterations,) or
    (n_iterations, n_links/n_disruptions) — never on individual scalars.

    Parameters
    ----------
    link_cost_data : list[LinkCostData]
        Ordered list of per-link cost parameters (same order as link columns
        in the disruption and flow matrices).
    constants : NetworkCostConstants
        Network-wide cost parameters.
    """

    def __init__(
        self,
        link_cost_data: list[LinkCostData],
        constants: NetworkCostConstants,
    ) -> None:
        self.constants = constants
        self.link_data = link_cost_data

        # Pre-extract arrays for vectorised ops
        self._cost_per_barrel = np.array(
            [ld.transport_cost_per_barrel for ld in link_cost_data], dtype=np.float64
        )
        self._max_capacity = np.array(
            [ld.max_capacity_bpd for ld in link_cost_data], dtype=np.float64
        )

        logger.debug(
            "cost_model.initialised",
            n_links=len(link_cost_data),
            crude_price=constants.crude_price_usd_per_barrel,
        )

    # ── Public interface ──────────────────────────────────────────────────────

    def compute_all_costs(
        self,
        flow_fractions: np.ndarray,       # (n_iter,)
        duration_matrix: np.ndarray,      # (n_iter, n_disruptions)
        occurrence_matrix: np.ndarray,    # (n_iter, n_disruptions) bool
        link_severity_matrix: np.ndarray, # (n_iter, n_links) — capacity reduction per link
        cost_multiplier_matrix: np.ndarray, # (n_iter, n_disruptions) — from disruption_types
    ) -> dict[str, np.ndarray]:
        """
        Compute all cost components for all iterations simultaneously.

        Returns
        -------
        dict with keys:
            'transport'       : (n_iter,) transport cost
            'delay'           : (n_iter,) delay/holding cost
            'production_loss' : (n_iter,) lost production value
            'penalty'         : (n_iter,) contract penalties
            'total'           : (n_iter,) sum of all components
        """
        n_iter = flow_fractions.shape[0]
        consts = self.constants

        # Max disruption duration per iteration (drives delay cost)
        max_duration = duration_matrix.max(axis=1)  # (n_iter,)

        # ── Production loss ───────────────────────────────────────────────────
        # lost_fraction = 1 - flow_fraction
        # lost_bpd      = baseline_throughput × lost_fraction
        # lost_barrels  = lost_bpd × max_duration
        lost_fraction   = 1.0 - flow_fractions
        lost_bpd        = consts.baseline_daily_throughput_bpd * lost_fraction
        lost_barrels    = lost_bpd * max_duration
        production_loss = lost_barrels * consts.crude_price_usd_per_barrel

        # ── Transport cost overrun ────────────────────────────────────────────
        # When link severity > 0, remaining flow uses higher-cost alternatives.
        # Overrun = baseline_transport × capacity_reduction × cost_multiplier × duration
        # Simplified: use max cost_multiplier across active disruptions per iteration.
        if cost_multiplier_matrix.shape[1] > 0:
            active_multipliers = np.where(
                occurrence_matrix, cost_multiplier_matrix, 1.0
            )
            max_multiplier = active_multipliers.max(axis=1)  # (n_iter,)
        else:
            max_multiplier = np.ones(n_iter, dtype=np.float64)

        # Baseline daily transport cost: Σ(capacity × cost_per_barrel) across all links
        baseline_daily_transport = float(
            (self._max_capacity * self._cost_per_barrel).sum()
        )
        # Overrun = (multiplier - 1) × baseline × disrupted_fraction × duration
        avg_link_severity = link_severity_matrix.mean(axis=1)  # (n_iter,)
        transport = (
            (max_multiplier - 1.0)
            * baseline_daily_transport
            * avg_link_severity
            * max_duration
        )

        # ── Delay / Holding cost ──────────────────────────────────────────────
        # Inventory held in transit / at depots during disruption
        delay_cost = (
            max_duration
            * consts.holding_cost_usd_per_barrel_day
            * consts.avg_inventory_barrels
            * lost_fraction
        )

        # ── Contract penalty ──────────────────────────────────────────────────
        # Penalty applies only when delay exceeds SLA tolerance
        excess_delay = np.maximum(0.0, max_duration - consts.sla_tolerance_days)
        penalty = excess_delay * consts.penalty_per_day_usd

        # ── Total cost ────────────────────────────────────────────────────────
        total = production_loss + transport + delay_cost + penalty

        return {
            "transport":       np.maximum(0.0, transport),
            "delay":           np.maximum(0.0, delay_cost),
            "production_loss": np.maximum(0.0, production_loss),
            "penalty":         np.maximum(0.0, penalty),
            "total":           np.maximum(0.0, total),
        }

    def compute_cost_breakdown_summary(self, cost_dict: dict[str, np.ndarray]) -> dict:
        """
        Compute mean cost breakdown for reporting.

        Returns a dict of {component: mean_usd} suitable for
        insertion into the simulation_aggregates table.
        """
        return {
            component: float(arr.mean())
            for component, arr in cost_dict.items()
        }
