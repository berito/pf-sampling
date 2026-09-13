import numpy as np

from pfexp import particles as P
from pfexp.runlog import RunLog


def test_wrap_angle():
    assert np.allclose(P.wrap_angle([np.pi + 0.1, -np.pi - 0.1, 0.5]), [-np.pi + 0.1, np.pi - 0.1, 0.5])


def test_normalize_handles_collapse():
    weights, collapsed = P.normalize(np.zeros(4))
    assert collapsed and np.allclose(weights, 0.25)
    weights, collapsed = P.normalize_log(np.array([-1e6, -1e6 + 1]))
    assert not collapsed and np.isclose(weights.sum(), 1) and weights[1] > weights[0]


def test_ess_bounds():
    assert np.isclose(P.effective_sample_size(np.full(10, 0.1)), 10)
    assert np.isclose(P.effective_sample_size(np.eye(10)[3]), 1)


def test_heading_mean_across_pi():
    poses = np.array([[0, 0, np.pi - 0.1], [0, 0, -np.pi + 0.1]])
    mean = P.weighted_pose_mean(poses, np.array([0.5, 0.5]))
    assert np.isclose(abs(mean[2]), np.pi)
    cov = P.weighted_pose_cov(poses, np.array([0.5, 0.5]))
    assert np.isclose(cov[2, 2], 0.01)


def test_record_and_traces():
    log = RunLog(settings={"n_particles": 3})
    poses = np.array([[1.0, 2.0, 0.0], [1.2, 2.0, 0.1], [0.8, 2.0, -0.1]])
    weights = np.full(3, 1 / 3)
    for step in range(4):
        log.record(true_pose=[1.0, 2.1, 0.0], poses=poses, weights=weights, ess_before=2.5,
                   resampled=step % 2 == 0, unique_after=3, collapsed=False, step_time=0.01)
    traces = log.traces()
    assert len(traces) == 4 and log.n_steps == 4
    assert np.allclose(traces["position_error"], 0.1)
    assert traces["resampled"].tolist() == [True, False, True, False]
    assert np.isclose(log.total_time, 0.04)
