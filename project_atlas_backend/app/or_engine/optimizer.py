"""
app/or_engine/optimizer.py
===========================
Integer Linear Programme to select the optimal set of mitigation strategies
subject to budget and effectiveness constraints.

Mathematical Formulation
-------------------------
Decision variables:
    x_s ∈ {0, 1}  for each strategy s ∈ S

Objective (default: minimise cost subject to effectiveness constraint):
    min  Σ_s  implementation_cost_s × x_s

Subject to:
    [Effectiveness]  Σ_s  effectiveness_s × x_s  ≥  target_effectiveness
    [Budget]         Σ_s  implementation_cost_s × x_s  ≤  budget
    [Binary]         x_s ∈ {0, 1}

Alternative objective: maximise effectiveness subject to budget:
    max  Σ_s  effectiveness_s × x_s
    s.t. Σ_s  cost_s × x_s  ≤  budget

Solver: CBC (COIN Branch and Cut) via PuLP — open source, no licence required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import structlog

try:
    import pulp
    PULP_AVAILABLE = True
except ImportError:
    PULP_AVAILABLE = False
    pulp = None  # type: ignore

logger = structlog.get_logger(__name__)


@dataclass
class MitigationStrategyInput:
    """Parameters for one mitigation strategy passed to the optimiser."""
    strategy_id:              str
    strategy_name:            str
    implementation_cost_usd:  float
    annual_maintenance_cost_usd: float
    effectiveness_score:      float   # 0.0–1.0 composite
    reduces_probability_by:   float   # 0.0–1.0
    reduces_severity_by:      float   # 0.0–1.0
    reduces_recovery_time_by_pct: float  # 0.0–1.0
    feasibility_score:        float   # 0.0–1.0


@dataclass
class OptimizationResult:
    """Output of the mitigation optimisation run."""
    status:             str           # "Optimal", "Infeasible", "Not Solved"
    objective_value:    float
    selected_strategies: list[str]   # strategy_ids of selected strategies
    total_cost_usd:     float
    total_effectiveness: float
    total_probability_reduction: float
    total_severity_reduction: float
    cost_breakdown:     list[dict]   # [{strategy_id, name, cost, effectiveness}]
    solver_log:         str = ""


class MitigationOptimizer:
    """
    Integer Linear Programme for mitigation strategy selection.

    Two modes:
        "min_cost"   — minimise cost, subject to ≥ target_effectiveness
        "max_effect" — maximise effectiveness, subject to ≤ budget

    Parameters
    ----------
    strategies : list[MitigationStrategyInput]
        Available mitigation strategies with costs and effectiveness values.
    """

    def __init__(self, strategies: list[MitigationStrategyInput]) -> None:
        if not PULP_AVAILABLE:
            raise RuntimeError(
                "PuLP is not installed. Install it with: pip install pulp"
            )
        if not strategies:
            raise ValueError("At least one mitigation strategy is required.")

        self.strategies = strategies
        logger.info(
            "optimizer.init",
            n_strategies=len(strategies),
        )

    # ── Public interface ──────────────────────────────────────────────────────

    def optimise_min_cost(
        self,
        target_effectiveness: float,
        budget_usd: Optional[float] = None,
    ) -> OptimizationResult:
        """
        Find the minimum-cost set of strategies that achieves
        at least `target_effectiveness`.

        Parameters
        ----------
        target_effectiveness : float [0.0, 1.0]
            Required minimum weighted-sum effectiveness score.
        budget_usd : float, optional
            Hard budget ceiling. If None, no budget constraint applied.

        Returns
        -------
        OptimizationResult
        """
        if not (0.0 < target_effectiveness <= 1.0):
            raise ValueError(
                f"target_effectiveness must be in (0, 1], got {target_effectiveness}"
            )

        problem = pulp.LpProblem("MitigationMinCost", pulp.LpMinimize)

        # Binary decision variables
        x = {
            s.strategy_id: pulp.LpVariable(
                f"x_{i}", cat="Binary"
            )
            for i, s in enumerate(self.strategies)
        }

        # Objective: minimise total implementation cost
        problem += pulp.lpSum(
            s.implementation_cost_usd * x[s.strategy_id]
            for s in self.strategies
        ), "TotalImplementationCost"

        # Constraint 1: minimum effectiveness
        problem += (
            pulp.lpSum(
                s.effectiveness_score * x[s.strategy_id]
                for s in self.strategies
            ) >= target_effectiveness,
            "MinEffectiveness",
        )

        # Constraint 2: budget ceiling (optional)
        if budget_usd is not None:
            problem += (
                pulp.lpSum(
                    s.implementation_cost_usd * x[s.strategy_id]
                    for s in self.strategies
                ) <= budget_usd,
                "BudgetCeiling",
            )

        # Constraint 3: feasibility filter — exclude strategies with
        # feasibility_score < 0.3 (pre-screen non-viable options)
        for s in self.strategies:
            if s.feasibility_score < 0.30:
                problem += (x[s.strategy_id] == 0, f"FeasibilityExclude_{s.strategy_id}")

        return self._solve_and_extract(problem, x, mode="min_cost")

    def optimise_max_effectiveness(
        self,
        budget_usd: float,
    ) -> OptimizationResult:
        """
        Find the set of strategies that maximises total effectiveness
        within the given budget.

        Parameters
        ----------
        budget_usd : float
            Maximum total implementation cost.

        Returns
        -------
        OptimizationResult
        """
        if budget_usd <= 0:
            raise ValueError(f"budget_usd must be positive, got {budget_usd}")

        problem = pulp.LpProblem("MitigationMaxEffect", pulp.LpMaximize)

        x = {
            s.strategy_id: pulp.LpVariable(f"x_{i}", cat="Binary")
            for i, s in enumerate(self.strategies)
        }

        # Objective: maximise effectiveness
        problem += pulp.lpSum(
            s.effectiveness_score * x[s.strategy_id]
            for s in self.strategies
        ), "TotalEffectiveness"

        # Constraint: budget
        problem += (
            pulp.lpSum(
                s.implementation_cost_usd * x[s.strategy_id]
                for s in self.strategies
            ) <= budget_usd,
            "Budget",
        )

        # Feasibility pre-screen
        for s in self.strategies:
            if s.feasibility_score < 0.30:
                problem += (x[s.strategy_id] == 0, f"FeasibilityExclude_{s.strategy_id}")

        return self._solve_and_extract(problem, x, mode="max_effect")

    # ── Private helpers ───────────────────────────────────────────────────────

    def _solve_and_extract(
        self,
        problem: "pulp.LpProblem",
        x: dict,
        mode: str,
    ) -> OptimizationResult:
        """Solve the LP and extract results."""
        # Use CBC solver with suppressed output
        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=30)
        problem.solve(solver)

        status = pulp.LpStatus[problem.status]
        logger.info(
            "optimizer.solved",
            mode=mode,
            status=status,
            objective=pulp.value(problem.objective),
        )

        if status != "Optimal":
            return OptimizationResult(
                status=status,
                objective_value=0.0,
                selected_strategies=[],
                total_cost_usd=0.0,
                total_effectiveness=0.0,
                total_probability_reduction=0.0,
                total_severity_reduction=0.0,
                cost_breakdown=[],
            )

        # Extract selected strategies
        selected_ids = [
            sid for sid, var in x.items()
            if pulp.value(var) is not None and pulp.value(var) > 0.5
        ]

        strategy_map = {s.strategy_id: s for s in self.strategies}
        selected = [strategy_map[sid] for sid in selected_ids if sid in strategy_map]

        total_cost   = sum(s.implementation_cost_usd for s in selected)
        total_effect = sum(s.effectiveness_score for s in selected)
        total_prob_reduction = 1.0 - np.prod(
            [1.0 - s.reduces_probability_by for s in selected]
        ) if selected else 0.0
        total_sev_reduction = 1.0 - np.prod(
            [1.0 - s.reduces_severity_by for s in selected]
        ) if selected else 0.0

        cost_breakdown = [
            {
                "strategy_id":           s.strategy_id,
                "strategy_name":         s.strategy_name,
                "implementation_cost_usd": s.implementation_cost_usd,
                "effectiveness_score":   s.effectiveness_score,
                "reduces_probability_by": s.reduces_probability_by,
                "reduces_severity_by":   s.reduces_severity_by,
            }
            for s in selected
        ]

        return OptimizationResult(
            status=status,
            objective_value=float(pulp.value(problem.objective) or 0.0),
            selected_strategies=selected_ids,
            total_cost_usd=total_cost,
            total_effectiveness=min(1.0, total_effect),
            total_probability_reduction=min(1.0, total_prob_reduction),
            total_severity_reduction=min(1.0, total_sev_reduction),
            cost_breakdown=cost_breakdown,
        )


# numpy needed for product computation in _solve_and_extract
try:
    import numpy as np
except ImportError:
    import math
    class _NpShim:
        @staticmethod
        def prod(lst):
            result = 1.0
            for v in lst:
                result *= v
            return result
    np = _NpShim()  # type: ignore
