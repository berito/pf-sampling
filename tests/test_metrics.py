import numpy as np
import pytest

from pfexp import registry
from pfexp.filters.fastslam import run_fastslam
from pfexp.filters.mcl import run_mcl
from pfexp.metrics import compute_all
from pfexp.metrics.alignment import apply, fit_rigid_2d
from pfexp.runlog import RunLog
from pfexp.worlds import localization_world, slam_world

METRICS = ["ate", "degeneracy", "ess", "map_error", "nees", "rmse", "runtime"]


def synthetic_log(offset=(0.3, 0.4), spread=0.5, n=200, steps=10, resampled=True):
    """Particles scattered around a pose shifted by `offset` from the truth."""
    rng = np.random.RandomState(0)
    log = RunLog(settings={"n_particles": n})
    for t in range(steps):
        true_pose = np.array([t, 0.0, 0.0])
        poses = true_pose + np.array([*offset, 0.0]) + rng.normal(0, spread, (n, 3))
        log.record(true_pose=true_pose, poses=poses, weights=np.full(n, 1 / n), ess_before=n / 2,
                   resampled=resampled, unique_after=n // 4, collapsed=t == 0, step_time=0.002)
    return log


def test_all_metrics_registered():
    assert set(METRICS) <= set(registry.names("metric"))


def test_rmse_and_ate():
    log = synthetic_log(spread=0.01)
    values = compute_all(log, ["rmse", "ate"])
    assert values["position_rmse"] == pytest.approx(0.5, abs=0.01)
    assert values["ate"] < 0.01  # a constant offset is removed by the alignment


def test_alignment_recovers_rotation_and_translation():
    rng = np.random.RandomState(1)
    points = rng.normal(size=(20, 2))
    angle = 0.7
    R = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    moved = apply(R, np.array([2.0, -1.0]), points)
    R_fit, t_fit = fit_rigid_2d(points, moved)
    assert np.allclose(R_fit, R) and np.allclose(t_fit, [2.0, -1.0])


def test_ess_degeneracy_runtime():
    values = compute_all(synthetic_log(), ["ess", "degeneracy", "runtime"])
    assert values["ess_mean"] == pytest.approx(0.5)
    assert values["resample_rate"] == 1.0 and values["collapses"] == 1
    assert values["unique_after_resampling"] == pytest.approx(0.25)
    assert values["runtime_per_step_ms"] == pytest.approx(2.0)


def test_nees_is_about_the_dimension_when_consistent():
    """Particles drawn around the truth with the spread they claim give NEES ≈ 3 on average."""
    rng = np.random.RandomState(2)
    log = RunLog(settings={"n_particles": 2000})
    for t in range(300):
        true_pose = np.zeros(3)
        estimate_offset = rng.normal(0, 0.2, 3)
        poses = true_pose + estimate_offset + rng.normal(0, 0.2, (2000, 3))
        log.record(true_pose=true_pose, poses=poses, weights=np.full(2000, 1 / 2000), ess_before=2000,
                   resampled=False, unique_after=2000, collapsed=False, step_time=0.0)
    assert compute_all(log, ["nees"])["nees_mean"] == pytest.approx(3.0, rel=0.15)


def test_nees_grows_when_overconfident():
    assert compute_all(synthetic_log(spread=0.05), ["nees"])["nees_mean"] > 50


def test_map_error_only_for_slam():
    assert "map_error" not in compute_all(synthetic_log())


def test_metrics_on_real_runs():
    mcl = compute_all(run_mcl(localization_world(seed=0), n_particles=300, filter_seed=0))
    slam = compute_all(run_fastslam(slam_world(seed=0), n_particles=30, filter_seed=0))
    for values in (mcl, slam):
        assert all(np.isfinite(v) for v in values.values())
    assert "map_error" not in mcl
    assert slam["landmarks_mapped"] == 8 and slam["map_error_aligned"] <= slam["map_error"] + 1e-9
