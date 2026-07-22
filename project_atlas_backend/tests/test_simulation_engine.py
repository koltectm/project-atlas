"""
tests/test_simulation_engine.py
================================
Unit tests for the Monte Carlo simulation engine and its sub-models.

Run with: pytest tests/test_simulation_engine.py -v

All tests are deterministic (fixed random seed) and require only
numpy, scipy, and networkx — no database or network access.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.simulation.disruption_model import DisruptionConfig, DisruptionModel
from app.simulation.cost_model import CostModel, LinkCostData, NetworkCostConstants
from app.simulation.recovery_model import RecoveryModel
from app.simulation.engine import AggregateMetrics, MonteCarloEngine

# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _make_rng(seed: int = 42) -> np.random.Generator:
    return np.random.default_rng(seed)


def _make_disruption_configs() -> list[DisruptionConfig]:
    """Three representative disruption types mirroring the seed data."""
    return [
        DisruptionConfig(
            disruption_type_id="d1",
            name="Pipeline Vandalism",
            category="infrastructure",
            annual_probability=0.85,
            severity_min=0.20, severity_mode=0.65, severity_max=1.00,
            duration_min=1.0, duration_mode=14.0, duration_max=90.0,
            cascade_targets={"d3": 0.45},
            target_node_ids=[],
            target_link_ids=["l1", "l2"],
            affected_node_types=["pipeline", "export_terminal"],
            affected_link_types=["pipeline"],
        ),
        DisruptionConfig(
            disruption_type_id="d2",
            name="Apapa Port Congestion",
            category="logistics",
            annual_probability=0.80,
            severity_min=0.15, severity_mode=0.40, severity_max=0.75,
            duration_min=7.0, duration_mode=21.0, duration_max=70.0,
            cascade_targets={},
            target_node_ids=["n_port"],
            target_link_ids=[],
            affected_node_types=["port"],
            affected_link_types=["sea_route"],
        ),
        DisruptionConfig(
            disruption_type_id="d3",
            name="Niger Delta Militant Attack",
            category="geopolitical",
            annual_probability=0.40,
            severity_min=0.30, severity_mode=0.70, severity_max=1.00,
            duration_min=7.0, duration_mode=30.0, duration_max=120.0,
            cascade_targets={},
            target_node_ids=["n1", "n2"],
            target_link_ids=[],
            affected_node_types=["wellhead", "pipeline"],
            affected_link_types=["pipeline"],
        ),
    ]


def _make_cost_constants() -> NetworkCostConstants:
    return NetworkCostConstants(
        baseline_daily_throughput_bpd=1_300_000.0,
        crude_price_usd_per_barrel=82.50,
        holding_cost_usd_per_barrel_day=0.50,
        sla_tolerance_days=7.0,
        penalty_per_day_usd=50_000.0,
        avg_inventory_barrels=15_000_000.0,
    )


def _make_link_cost_data() -> list[LinkCostData]:
    return [
        LinkCostData(
            link_id="l1", link_type="pipeline",
            transport_cost_per_barrel=0.85, distance_km=160.0,
            max_capacity_bpd=450_000.0, index=0,
        ),
        LinkCostData(
            link_id="l2", link_type="pipeline",
            transport_cost_per_barrel=0.75, distance_km=97.0,
            max_capacity_bpd=500_000.0, index=1,
        ),
        LinkCostData(
            link_id="l3", link_type="sea_route",
            transport_cost_per_barrel=1.20, distance_km=520.0,
            max_capacity_bpd=400_000.0, index=2,
        ),
    ]


# ─── DisruptionModel Tests ────────────────────────────────────────────────────

class TestDisruptionModel:

    def test_effective_probability_annual_to_horizon(self):
        """Annual probability correctly scaled to 180-day horizon."""
        cfg = _make_disruption_configs()[0]  # p_annual = 0.85
        p_180 = cfg.effective_probability(180)
        expected = 1.0 - (1.0 - 0.85) ** (180 / 365)
        assert abs(p_180 - expected) < 1e-10

    def test_effective_probability_zero(self):
        cfg = DisruptionConfig(
            disruption_type_id="x", name="test", category="test",
            annual_probability=0.0,
            severity_min=0, severity_mode=0.5, severity_max=1,
            duration_min=1, duration_mode=5, duration_max=10,
        )
        assert cfg.effective_probability(365) == 0.0

    def test_effective_probability_one(self):
        cfg = DisruptionConfig(
            disruption_type_id="x", name="test", category="test",
            annual_probability=1.0,
            severity_min=0, severity_mode=0.5, severity_max=1,
            duration_min=1, duration_mode=5, duration_max=10,
        )
        assert cfg.effective_probability(365) == 1.0

    def test_sample_all_shapes(self):
        """sample_all() returns matrices of the correct shape."""
        configs = _make_disruption_configs()
        model = DisruptionModel(configs, time_horizon_days=365, rng=_make_rng(42))
        n_iter = 500

        occ, sev, dur = model.sample_all(n_iter)

        assert occ.shape == (n_iter, 3)
        assert sev.shape == (n_iter, 3)
        assert dur.shape == (n_iter, 3)

    def test_severity_zero_when_not_occurred(self):
        """Severity must be 0.0 wherever disruption did not occur."""
        configs = _make_disruption_configs()
        model = DisruptionModel(configs, time_horizon_days=365, rng=_make_rng(7))
        occ, sev, dur = model.sample_all(1000)

        # Where occurrence is False, severity must be 0
        not_occurred = ~occ
        assert np.all(sev[not_occurred] == 0.0), \
            "Non-zero severity found where disruption did not occur"

    def test_duration_zero_when_not_occurred(self):
        """Duration must be 0.0 wherever disruption did not occur."""
        configs = _make_disruption_configs()
        model = DisruptionModel(configs, time_horizon_days=365, rng=_make_rng(7))
        occ, sev, dur = model.sample_all(1000)

        not_occurred = ~occ
        assert np.all(dur[not_occurred] == 0.0)

    def test_severity_within_bounds(self):
        """All sampled severities must be within [s_min, s_max]."""
        configs = _make_disruption_configs()
        model = DisruptionModel(configs, time_horizon_days=365, rng=_make_rng(99))
        occ, sev, _ = model.sample_all(2000)

        for i, cfg in enumerate(configs):
            active_sev = sev[occ[:, i], i]
            if len(active_sev) == 0:
                continue
            assert active_sev.min() >= cfg.severity_min - 1e-9, \
                f"Severity below minimum for disruption {cfg.name}"
            assert active_sev.max() <= cfg.severity_max + 1e-9, \
                f"Severity above maximum for disruption {cfg.name}"

    def test_duration_within_bounds(self):
        """All sampled durations must be within [d_min, d_max]."""
        configs = _make_disruption_configs()
        model = DisruptionModel(configs, time_horizon_days=365, rng=_make_rng(99))
        occ, _, dur = model.sample_all(2000)

        for i, cfg in enumerate(configs):
            active_dur = dur[occ[:, i], i]
            if len(active_dur) == 0:
                continue
            assert active_dur.min() >= cfg.duration_min - 1e-9
            assert active_dur.max() <= cfg.duration_max + 1e-9

    def test_cascade_increases_secondary_occurrence(self):
        """
        d1 has cascade_target d3 with probability 0.45.
        When d1 fires, d3 should fire more often than its base probability.
        """
        configs = _make_disruption_configs()
        # d1 has p=0.85 annual → very high; d3 base p=0.40
        model = DisruptionModel(configs, time_horizon_days=365, rng=_make_rng(42))
        occ, _, _ = model.sample_all(5000)

        d3_given_d1   = occ[occ[:, 0], 2].mean()   # P(d3 fires | d1 fired)
        d3_given_no_d1 = occ[~occ[:, 0], 2].mean() if (~occ[:, 0]).any() else 0.0

        assert d3_given_d1 > d3_given_no_d1, \
            (f"Cascade effect not detected: P(d3|d1)={d3_given_d1:.3f} "
             f"≤ P(d3|¬d1)={d3_given_no_d1:.3f}")

    def test_reproducibility_with_seed(self):
        """Same seed must produce identical results across two runs."""
        configs = _make_disruption_configs()
        occ1, sev1, dur1 = DisruptionModel(
            configs, 365, _make_rng(123)
        ).sample_all(1000)
        occ2, sev2, dur2 = DisruptionModel(
            configs, 365, _make_rng(123)
        ).sample_all(1000)

        np.testing.assert_array_equal(occ1, occ2)
        np.testing.assert_array_almost_equal(sev1, sev2)
        np.testing.assert_array_almost_equal(dur1, dur2)

    def test_occurrence_mean_close_to_expected_probability(self):
        """
        At 10,000 iterations, empirical occurrence rate should be
        within 3 percentage points of the theoretical probability.
        """
        configs = _make_disruption_configs()
        model = DisruptionModel(configs, time_horizon_days=365, rng=_make_rng(0))
        occ, _, _ = model.sample_all(10_000)

        for i, cfg in enumerate(configs):
            expected_p = cfg.effective_probability(365)
            empirical_p = occ[:, i].mean()
            assert abs(empirical_p - expected_p) < 0.03, (
                f"{cfg.name}: expected p={expected_p:.3f}, "
                f"empirical p={empirical_p:.3f} (diff={abs(empirical_p-expected_p):.3f})"
            )


# ─── AggregateMetrics Tests ───────────────────────────────────────────────────

class TestAggregateMetrics:

    def test_from_array_basic_statistics(self):
        """Verify that AggregateMetrics computes correct statistical moments."""
        rng  = np.random.default_rng(42)
        data = rng.exponential(scale=1_000_000, size=10_000)

        agg = AggregateMetrics.from_array("total_cost_usd", data)

        assert abs(agg.mean_value    - float(data.mean()))         < 1.0
        assert abs(agg.std_deviation - float(data.std()))          < 1.0
        assert abs(agg.median_value  - float(np.median(data)))     < 1.0
        assert abs(agg.percentile_5  - float(np.percentile(data, 5)))  < 1.0
        assert abs(agg.percentile_95 - float(np.percentile(data, 95))) < 1.0

    def test_cvar_exceeds_var(self):
        """CVaR must always be ≥ VaR (by definition)."""
        rng  = np.random.default_rng(7)
        data = rng.lognormal(mean=14, sigma=1.5, size=10_000)
        agg  = AggregateMetrics.from_array("test", data)
        assert agg.cvar_95 >= agg.var_95, \
            f"CVaR ({agg.cvar_95:.0f}) < VaR ({agg.var_95:.0f})"

    def test_var95_is_95th_percentile(self):
        rng  = np.random.default_rng(1)
        data = rng.uniform(0, 1_000_000, size=10_000)
        agg  = AggregateMetrics.from_array("test", data)
        expected_var = float(np.percentile(data, 95))
        assert abs(agg.var_95 - expected_var) < 1.0

    def test_positive_skewness_for_exponential(self):
        """Exponential distribution has positive skewness ≈ 2.0."""
        rng  = np.random.default_rng(42)
        data = rng.exponential(scale=1.0, size=50_000)
        agg  = AggregateMetrics.from_array("test", data)
        assert agg.skewness > 1.5, f"Expected skewness > 1.5, got {agg.skewness:.3f}"

    def test_kurtosis_near_zero_for_normal(self):
        """Normal distribution has excess kurtosis ≈ 0.0."""
        rng  = np.random.default_rng(42)
        data = rng.normal(0, 1, size=100_000)
        agg  = AggregateMetrics.from_array("test", data)
        assert abs(agg.kurtosis) < 0.15, \
            f"Normal kurtosis should be ~0, got {agg.kurtosis:.3f}"

    def test_constant_array_std_zero(self):
        """Constant array should have std=0, skewness=0, kurtosis=0."""
        data = np.ones(1000) * 5_000_000.0
        agg  = AggregateMetrics.from_array("test", data)
        assert agg.std_deviation == 0.0
        assert agg.skewness      == 0.0
        assert agg.kurtosis      == 0.0

    def test_empty_array_raises(self):
        with pytest.raises(ValueError, match="empty array"):
            AggregateMetrics.from_array("test", np.array([]))


# ─── CostModel Tests ─────────────────────────────────────────────────────────

class TestCostModel:

    def _make_model(self) -> CostModel:
        return CostModel(
            link_cost_data=_make_link_cost_data(),
            constants=_make_cost_constants(),
        )

    def _make_inputs(self, n_iter: int = 100):
        rng = np.random.default_rng(42)
        flow_fractions       = rng.uniform(0.3, 1.0, n_iter)
        duration_matrix      = rng.uniform(0, 30, (n_iter, 3))
        occurrence_matrix    = rng.random((n_iter, 3)) < 0.5
        link_severity_matrix = rng.uniform(0, 0.8, (n_iter, 3))
        cost_mult_matrix     = rng.uniform(1.0, 3.0, (n_iter, 3))
        return flow_fractions, duration_matrix, occurrence_matrix, link_severity_matrix, cost_mult_matrix

    def test_output_shapes(self):
        model = self._make_model()
        n_iter = 200
        inputs = self._make_inputs(n_iter)
        result = model.compute_all_costs(*inputs)

        for key in ("transport", "delay", "production_loss", "penalty", "total"):
            assert key in result
            assert result[key].shape == (n_iter,), \
                f"Key '{key}' has wrong shape {result[key].shape}"

    def test_all_costs_non_negative(self):
        model = self._make_model()
        result = model.compute_all_costs(*self._make_inputs(500))
        for key, arr in result.items():
            assert np.all(arr >= 0), \
                f"Negative values in '{key}': min={arr.min():.2f}"

    def test_total_equals_sum_of_components(self):
        model = self._make_model()
        result = model.compute_all_costs(*self._make_inputs(500))
        computed_total = (
            result["transport"]
            + result["delay"]
            + result["production_loss"]
            + result["penalty"]
        )
        np.testing.assert_allclose(result["total"], computed_total, rtol=1e-6)

    def test_zero_flow_loss_maximises_production_loss(self):
        """When flow_fraction = 0 (total failure), production_loss is maximised."""
        model = self._make_model()
        n_iter = 50
        flow_fractions       = np.zeros(n_iter)
        duration_matrix      = np.full((n_iter, 3), 30.0)  # 30-day disruption
        occurrence_matrix    = np.ones((n_iter, 3), dtype=bool)
        link_severity_matrix = np.ones((n_iter, 3))
        cost_mult_matrix     = np.ones((n_iter, 3))

        result = model.compute_all_costs(
            flow_fractions, duration_matrix, occurrence_matrix,
            link_severity_matrix, cost_mult_matrix,
        )
        consts = _make_cost_constants()
        expected_loss = (
            1.0 * consts.baseline_daily_throughput_bpd
            * 30.0
            * consts.crude_price_usd_per_barrel
        )
        np.testing.assert_allclose(
            result["production_loss"], expected_loss, rtol=0.01,
            err_msg="Production loss does not match expected value for total flow failure"
        )

    def test_no_disruption_no_penalty(self):
        """Zero duration → zero penalty."""
        model = self._make_model()
        n_iter = 100
        flow_fractions       = np.ones(n_iter)
        duration_matrix      = np.zeros((n_iter, 3))
        occurrence_matrix    = np.zeros((n_iter, 3), dtype=bool)
        link_severity_matrix = np.zeros((n_iter, 3))
        cost_mult_matrix     = np.ones((n_iter, 3))

        result = model.compute_all_costs(
            flow_fractions, duration_matrix, occurrence_matrix,
            link_severity_matrix, cost_mult_matrix,
        )
        np.testing.assert_array_equal(result["penalty"], 0.0)
        np.testing.assert_array_equal(result["production_loss"], 0.0)


# ─── RecoveryModel Tests ──────────────────────────────────────────────────────

class TestRecoveryModel:

    def _make_model(self, zone: str = "SS") -> RecoveryModel:
        return RecoveryModel(
            recovery_min=3.0,
            recovery_max=45.0,
            mean_redundancy=0.4,
            primary_zone=zone,
            rng=_make_rng(42),
        )

    def test_recovery_zero_when_no_disruption(self):
        model = self._make_model()
        severity = np.zeros(1000)
        times = model.sample_recovery_times(severity, 1000)
        np.testing.assert_array_equal(times, 0.0)

    def test_recovery_positive_when_disrupted(self):
        model = self._make_model()
        severity = np.ones(1000) * 0.6
        times = model.sample_recovery_times(severity, 1000)
        assert np.all(times > 0), "All disrupted iterations should have positive recovery time"

    def test_recovery_floor_at_minimum(self):
        """Recovery time must never fall below recovery_min for disrupted iterations."""
        model = self._make_model()
        severity = np.ones(500) * 0.5
        times = model.sample_recovery_times(severity, 500)
        assert np.all(times[times > 0] >= 3.0 - 1e-9), \
            f"Recovery time below minimum: {times[times > 0].min():.3f}"

    def test_ss_zone_slower_than_sw(self):
        """Niger Delta (SS) should have higher recovery times than South-West (SW)."""
        sev = np.ones(5000) * 0.6
        times_ss = RecoveryModel(3, 45, 0.4, "SS", _make_rng(42)).sample_recovery_times(sev, 5000)
        times_sw = RecoveryModel(3, 45, 0.4, "SW", _make_rng(42)).sample_recovery_times(sev, 5000)
        assert times_ss.mean() > times_sw.mean(), \
            f"SS mean ({times_ss.mean():.1f}) should exceed SW mean ({times_sw.mean():.1f})"

    def test_mitigation_reduces_recovery(self):
        model = self._make_model()
        sev   = np.ones(1000) * 0.7
        base  = model.sample_recovery_times(sev, 1000)
        mitigated = model.apply_mitigation_effect(base, mitigation_reduction_pct=0.40)
        np.testing.assert_allclose(mitigated, base * 0.60, rtol=1e-9)

    def test_mitigation_capped_at_90_pct(self):
        model = self._make_model()
        sev   = np.ones(100) * 0.7
        base  = model.sample_recovery_times(sev, 100)
        mitigated = model.apply_mitigation_effect(base, mitigation_reduction_pct=0.99)
        # Cap is 0.90, so minimum factor = 0.10
        np.testing.assert_allclose(mitigated, base * 0.10, rtol=1e-9)

    def test_resilience_score_bounds(self):
        model = self._make_model()
        sev   = np.random.default_rng(0).uniform(0, 1, 1000)
        times = model.sample_recovery_times(sev, 1000)
        scores = model.compute_resilience_scores(times, time_horizon_days=365)
        assert np.all(scores >= 0.0) and np.all(scores <= 1.0)

    def test_resilience_one_when_no_disruption(self):
        model = self._make_model()
        times = np.zeros(100)
        scores = model.compute_resilience_scores(times, 365)
        np.testing.assert_array_equal(scores, 1.0)


# ─── Integration Test: End-to-End Engine Smoke Test ──────────────────────────

class TestMonteCarloEngineIntegration:
    """
    Smoke test: run the full engine on a tiny synthetic network.
    Does NOT require a database — all data is passed in-memory.
    """

    def _make_network_data(self) -> dict:
        nodes = [
            {"node_id": "n_wh1",  "node_type": "wellhead",      "stage": "upstream",
             "capacity_bpd": 200_000, "current_utilization_pct": 0.7,
             "criticality_score": 0.82, "redundancy_score": 0.45,
             "status": "operational", "geopolitical_zone": "SS",
             "latitude": 4.44, "longitude": 7.16},
            {"node_id": "n_et1",  "node_type": "export_terminal","stage": "midstream",
             "capacity_bpd": 800_000, "current_utilization_pct": 0.62,
             "criticality_score": 0.90, "redundancy_score": 0.55,
             "status": "operational", "geopolitical_zone": "SS",
             "latitude": 4.45, "longitude": 7.15},
            {"node_id": "n_ref1", "node_type": "refinery",       "stage": "midstream",
             "capacity_bpd": 650_000, "current_utilization_pct": 0.45,
             "criticality_score": 0.95, "redundancy_score": 0.70,
             "status": "operational", "geopolitical_zone": "SW",
             "latitude": 6.41, "longitude": 3.38},
            {"node_id": "n_con1", "node_type": "consumer",       "stage": "downstream",
             "capacity_bpd": 0, "current_utilization_pct": 0.85,
             "criticality_score": 0.65, "redundancy_score": 0.60,
             "status": "operational", "geopolitical_zone": "SW",
             "latitude": 6.52, "longitude": 3.37},
        ]
        links = [
            {"link_id": "l1", "source_node_id": "n_wh1",  "target_node_id": "n_et1",
             "link_type": "pipeline", "max_capacity_bpd": 450_000,
             "transport_cost_per_barrel": 0.85, "distance_km": 160.0,
             "normal_lead_time_days": 1.5, "reliability_score": 0.62,
             "vandalism_risk_score": 0.78, "is_critical_path": True, "status": "operational"},
            {"link_id": "l2", "source_node_id": "n_et1",  "target_node_id": "n_ref1",
             "link_type": "sea_route", "max_capacity_bpd": 400_000,
             "transport_cost_per_barrel": 1.20, "distance_km": 520.0,
             "normal_lead_time_days": 2.5, "reliability_score": 0.88,
             "vandalism_risk_score": 0.02, "is_critical_path": True, "status": "operational"},
            {"link_id": "l3", "source_node_id": "n_ref1", "target_node_id": "n_con1",
             "link_type": "road", "max_capacity_bpd": 100_000,
             "transport_cost_per_barrel": 0.90, "distance_km": 30.0,
             "normal_lead_time_days": 0.4, "reliability_score": 0.90,
             "vandalism_risk_score": 0.05, "is_critical_path": False, "status": "operational"},
        ]
        return {"nodes": nodes, "links": links}

    def test_engine_runs_without_error(self):
        """Engine completes a 200-iteration run without raising."""
        from app.simulation.engine import MonteCarloEngine
        from app.simulation.cost_model import NetworkCostConstants

        engine = MonteCarloEngine(
            run_id="test-run-001",
            n_iterations=200,
            time_horizon_days=365,
            random_seed=42,
            disruption_configs=_make_disruption_configs(),
            network_data=self._make_network_data(),
            cost_constants=_make_cost_constants(),
        )
        output = engine.run()

        assert output.n_iterations == 200
        assert output.total_cost_usd is not None
        assert output.total_cost_usd.shape == (200,)
        assert output.supply_chain_flow_pct is not None
        assert output.supply_chain_flow_pct.shape == (200,)

    def test_output_arrays_have_no_nan_or_inf(self):
        """All output arrays must be finite (no NaN or Inf)."""
        from app.simulation.engine import MonteCarloEngine

        engine = MonteCarloEngine(
            run_id="test-run-002",
            n_iterations=200,
            time_horizon_days=180,
            random_seed=99,
            disruption_configs=_make_disruption_configs(),
            network_data=self._make_network_data(),
            cost_constants=_make_cost_constants(),
        )
        output = engine.run()

        for arr_name in ("total_cost_usd", "total_delay_days",
                         "supply_chain_flow_pct", "recovery_time_days"):
            arr = getattr(output, arr_name)
            assert arr is not None
            assert np.all(np.isfinite(arr)), \
                f"{arr_name} contains NaN or Inf: {arr[~np.isfinite(arr)]}"

    def test_flow_fraction_in_zero_one(self):
        """supply_chain_flow_pct must be in [0, 1] for all iterations."""
        from app.simulation.engine import MonteCarloEngine

        engine = MonteCarloEngine(
            run_id="test-run-003",
            n_iterations=300,
            time_horizon_days=365,
            random_seed=7,
            disruption_configs=_make_disruption_configs(),
            network_data=self._make_network_data(),
            cost_constants=_make_cost_constants(),
        )
        output = engine.run()
        f = output.supply_chain_flow_pct
        assert np.all(f >= 0.0) and np.all(f <= 1.0), \
            f"Flow fractions out of [0,1]: min={f.min():.4f}, max={f.max():.4f}"

    def test_aggregates_computed(self):
        """Engine produces aggregates for all key metrics."""
        from app.simulation.engine import MonteCarloEngine

        engine = MonteCarloEngine(
            run_id="test-run-004",
            n_iterations=200,
            time_horizon_days=365,
            random_seed=42,
            disruption_configs=_make_disruption_configs(),
            network_data=self._make_network_data(),
            cost_constants=_make_cost_constants(),
        )
        output = engine.run()

        assert len(output.aggregates) > 0
        metric_names = {a.metric_name for a in output.aggregates}
        for expected in ("total_cost_usd", "supply_chain_flow_pct", "recovery_time_days"):
            assert expected in metric_names, f"Missing aggregate: {expected}"

    def test_reproducibility_with_fixed_seed(self):
        """Two engine runs with the same seed produce identical results."""
        from app.simulation.engine import MonteCarloEngine

        kwargs = dict(
            run_id="test-run-005",
            n_iterations=100,
            time_horizon_days=180,
            random_seed=1234,
            disruption_configs=_make_disruption_configs(),
            network_data=self._make_network_data(),
            cost_constants=_make_cost_constants(),
        )
        out1 = MonteCarloEngine(**kwargs).run()
        out2 = MonteCarloEngine(**kwargs).run()

        np.testing.assert_array_almost_equal(
            out1.total_cost_usd, out2.total_cost_usd, decimal=2
        )
        np.testing.assert_array_almost_equal(
            out1.supply_chain_flow_pct, out2.supply_chain_flow_pct, decimal=6
        )

    def test_to_result_rows_length_and_keys(self):
        """to_result_rows() returns exactly n_iterations rows with required keys."""
        from app.simulation.engine import MonteCarloEngine

        n = 50
        engine = MonteCarloEngine(
            run_id="test-run-006",
            n_iterations=n,
            time_horizon_days=90,
            random_seed=0,
            disruption_configs=_make_disruption_configs(),
            network_data=self._make_network_data(),
            cost_constants=_make_cost_constants(),
        )
        output = engine.run()
        rows = output.to_result_rows()

        assert len(rows) == n
        required_keys = {
            "run_id", "iteration_number", "total_cost_usd",
            "total_delay_days", "production_loss_barrels",
            "nodes_affected", "links_disrupted",
            "supply_chain_flow_pct", "recovery_time_days",
            "disruptions_triggered",
        }
        for row in rows:
            missing = required_keys - set(row.keys())
            assert not missing, f"Missing keys in result row: {missing}"

    def test_iteration_numbers_are_sequential(self):
        """Iteration numbers in result rows must be 1, 2, …, N."""
        from app.simulation.engine import MonteCarloEngine

        n = 75
        engine = MonteCarloEngine(
            run_id="test-run-007",
            n_iterations=n,
            time_horizon_days=90,
            random_seed=0,
            disruption_configs=_make_disruption_configs(),
            network_data=self._make_network_data(),
            cost_constants=_make_cost_constants(),
        )
        output = engine.run()
        rows = output.to_result_rows()
        iter_nums = [r["iteration_number"] for r in rows]
        assert iter_nums == list(range(1, n + 1)), \
            "Iteration numbers are not sequential from 1"
