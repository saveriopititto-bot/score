import pytest

from engine.core import RunMetrics, ScoreEngine
from config import Config


def make_metrics(
    avg_power=280,
    avg_hr=150,
    distance=10000,
    moving_time=3000,
    elevation=100,
    weight=70,
    hr_max=185,
    hr_rest=50,
    temp=20,
    humidity=50,
):
    return RunMetrics(
        avg_power, avg_hr, distance, moving_time, elevation, weight, hr_max, hr_rest, temp, humidity
    )


@pytest.fixture
def engine():
    return ScoreEngine()


# --- RunMetrics -------------------------------------------------------


class TestRunMetrics:
    def test_avg_speed_mps(self):
        m = make_metrics(distance=10000, moving_time=2500)
        assert m.avg_speed_mps == pytest.approx(4.0)

    def test_avg_speed_mps_zero_time_does_not_divide_by_zero(self):
        m = make_metrics(distance=10000, moving_time=0)
        assert m.avg_speed_mps == 0


# --- ScoreEngine.calculate_zones --------------------------------------


class TestCalculateZones:
    def test_empty_watts_stream_returns_empty_dict(self, engine):
        assert engine.calculate_zones([], 250) == {}

    def test_falsy_ftp_returns_empty_dict(self, engine):
        assert engine.calculate_zones([100, 200], 0) == {}

    def test_zone_boundaries_at_150_180_210_are_exclusive_on_the_lower_bound(self, engine):
        # ftp=200 -> 0.75*ftp=150.0, 0.90*ftp=180.0, 1.05*ftp=210.0 (exact floats)
        ftp = 200
        watts = [149, 150, 179, 180, 209, 210, 300]
        zones = engine.calculate_zones(watts, ftp)
        # 149 -> Z2, 150 -> Z3 (150 < 150.0 is False)
        # 179 -> Z3, 180 -> Z4 (180 < 180.0 is False)
        # 209 -> Z4, 210 -> Z5, 300 -> Z5 (210 < 210.0 is False)
        total = len(watts)
        assert zones["Z2"] == pytest.approx(round(1 / total * 100, 1))
        assert zones["Z3"] == pytest.approx(round(2 / total * 100, 1))
        assert zones["Z4"] == pytest.approx(round(2 / total * 100, 1))
        assert zones["Z5"] == pytest.approx(round(2 / total * 100, 1))

    def test_z1_boundary_is_affected_by_floating_point_imprecision(self, engine):
        # 0.55 * 200 == 110.00000000000001 in IEEE754, not 110.0 exactly, so a
        # watt value exactly at the "documented" Z1/Z2 boundary still lands in
        # Z1 here -- unlike the 150/180/210 boundaries above, which are exact
        # floats and behave as the inequality reads. This asymmetry is a real
        # quirk of the current implementation, not a test artifact.
        ftp = 200
        assert 0.55 * ftp != 110.0
        zones = engine.calculate_zones([109, 110, 111], ftp)
        assert zones["Z1"] == pytest.approx(round(2 / 3 * 100, 1))  # 109 and 110
        assert zones["Z2"] == pytest.approx(round(1 / 3 * 100, 1))  # 111

    def test_zone_percentages_sum_to_100(self, engine):
        zones = engine.calculate_zones([50, 100, 150, 200, 250, 300], 200)
        assert sum(zones.values()) == pytest.approx(100.0)


# --- ScoreEngine.calculate_decoupling ---------------------------------


class TestCalculateDecoupling:
    def test_mismatched_stream_lengths_returns_zero(self, engine):
        assert engine.calculate_decoupling([1, 2, 3], [1, 2]) == 0.0

    def test_empty_streams_returns_zero(self, engine):
        assert engine.calculate_decoupling([], []) == 0.0

    def test_known_drift_value(self, engine):
        power = [200, 200, 200, 200]
        hr = [140, 140, 160, 160]
        # ratio1 = 200/140, ratio2 = 200/160 -> (ratio1-ratio2)/ratio1 = 0.125
        assert engine.calculate_decoupling(power, hr) == pytest.approx(0.125, abs=1e-6)

    def test_no_drift_when_power_and_hr_are_stable(self, engine):
        power = [200] * 10
        hr = [150] * 10
        assert engine.calculate_decoupling(power, hr) == pytest.approx(0.0)

    def test_zero_first_half_power_returns_zero(self, engine):
        power = [0, 0, 200, 200]
        hr = [140, 140, 160, 160]
        assert engine.calculate_decoupling(power, hr) == 0.0


# --- ScoreEngine.age_adjusted_percentile -------------------------------


class TestAgeAdjustedPercentile:
    @pytest.mark.parametrize(
        "age,mu",
        [
            (25, 0.22),  # < 30
            (30, 0.20),  # boundary: falls into the 30-39 bracket
            (35, 0.20),  # < 40
            (40, 0.18),  # boundary: falls into the 40-49 bracket
            (45, 0.18),  # < 50
            (50, 0.16),  # boundary: falls into the 50+ bracket
            (65, 0.16),  # >= 50
        ],
    )
    def test_score_equal_to_bracket_mean_gives_50th_percentile(self, engine, age, mu):
        assert engine.age_adjusted_percentile(mu, age) == pytest.approx(50.0)

    def test_percentile_clamped_at_upper_bound(self, engine):
        assert engine.age_adjusted_percentile(10.0, 25) == 99.9

    def test_percentile_clamped_at_lower_bound(self, engine):
        assert engine.age_adjusted_percentile(-10.0, 25) == 1.0


# --- ScoreEngine.compute_score ------------------------------------------


class TestComputeScore:
    def test_baseline_below_decoupling_threshold(self, engine):
        m = make_metrics(avg_power=280, avg_hr=150, distance=10000, weight=70, hr_max=185, hr_rest=50)
        score, details, wcf, wr_pct = engine.compute_score(m, decoupling=0.03)

        assert score == pytest.approx(0.62)
        assert wcf == pytest.approx(0.625)
        assert wr_pct == pytest.approx(62.5)
        assert details["Malus Efficienza"] == pytest.approx(0.0)

    def test_decoupling_above_threshold_applies_penalty(self, engine):
        m = make_metrics(avg_power=280, avg_hr=150, distance=10000, weight=70, hr_max=185, hr_rest=50)
        score, details, _, _ = engine.compute_score(m, decoupling=0.10)

        assert score == pytest.approx(0.52)
        assert details["Malus Efficienza"] == pytest.approx(-10.0)

    def test_world_class_factor_is_clamped_to_one(self, engine):
        # avg_power/weight far above Config.WR_WKG (6.4)
        m = make_metrics(avg_power=500, avg_hr=150, distance=10000, weight=70, hr_max=185, hr_rest=50)
        score, details, wcf, wr_pct = engine.compute_score(m, decoupling=0.02)

        assert wcf == 1.0
        assert wr_pct == 100.0
        assert details["Potenza"] == pytest.approx(50.0)

    def test_final_score_floors_at_point_zero_one(self, engine):
        m = make_metrics(avg_power=50, avg_hr=60, distance=500, weight=90, hr_max=185, hr_rest=50)
        score, _, _, _ = engine.compute_score(m, decoupling=0.5)

        assert score == 0.01

    def test_hr_reserve_falls_back_when_hr_max_equals_hr_rest(self, engine):
        m = make_metrics(avg_power=280, avg_hr=150, distance=10000, weight=70, hr_max=100, hr_rest=100)
        score, details, _, _ = engine.compute_score(m, decoupling=0.03)

        # hr_res falls back to 0.7 -> Intensità contribution = 0.7 * 0.2 * 100 = 14.0
        assert details["Intensità"] == pytest.approx(14.0)
        assert score == pytest.approx(0.61)

    def test_zero_weight_raises_zero_division_error(self, engine):
        # Documents current unguarded behavior: avg_power / m.weight has no
        # zero-check, unlike the hr_max/hr_rest and moving_time guards elsewhere.
        m = make_metrics(weight=0)
        with pytest.raises(ZeroDivisionError):
            engine.compute_score(m, decoupling=0.03)


# --- ScoreEngine.get_rank ------------------------------------------------


class TestGetRank:
    def test_rank_thresholds_are_exclusive_lower_bounds(self, engine):
        t = Config.RANK_THRESHOLDS
        assert engine.get_rank(t["ELITE"] + 0.01)[0] == "🏆 Elite"
        # exactly at the ELITE threshold does NOT count as Elite (`>`, not `>=`)
        assert engine.get_rank(t["ELITE"])[0] == "🥇 Pro"
        assert engine.get_rank(t["PRO"])[0] == "🥈 Advanced"
        assert engine.get_rank(t["ADVANCED"])[0] == "🥉 Intermediate"
        assert engine.get_rank(t["INTERMEDIATE"])[0] == "👟 Amateur"
        assert engine.get_rank(0.0)[0] == "👟 Amateur"

    def test_rank_returns_label_and_color_tuple(self, engine):
        label, color = engine.get_rank(0.5)
        assert label == "🏆 Elite"
        assert color == "#FFD700"
