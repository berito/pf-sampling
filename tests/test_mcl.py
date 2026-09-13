"""Localization: borrowed models match the vendor code, and the filter works end to end."""
import numpy as np
import pytest

from pfexp import particles as P
from pfexp import registry, vendor
from pfexp.filters.mcl import run_mcl
from pfexp.particles import ParticleSet
from pfexp.filters.mcl_model import LocalizationModel
from pfexp.worlds import localization_world

vendor.use("particle_filter_tutorial")
from core.particle_filters import KalmanParticleFilter, ParticleFilterSIR  # noqa: E402
from core.resampling import ResamplingAlgorithms  # noqa: E402

LANDMARKS = [[2.0, 2.0], [2.0, 8.0], [9.0, 2.0], [8.0, 9.0]]


def vendor_filter(cls, process_noise, measurement_noise, **kwargs):
    return cls(number_of_particles=1, limits=[0, 10, 0, 10], process_noise=process_noise,
               measurement_noise=measurement_noise, **kwargs)


def model(**kwargs):
    return LocalizationModel(np.array([10.0, 10.0]), np.array(LANDMARKS), (0.1, 0.2), (0.4, 0.3), **kwargs)


@pytest.fixture
def poses():
    np.random.seed(1)
    return model().initial_uniform(200)


# --- borrowed copy matches upstream (fixes switched off) ---------------------------------

def test_log_likelihood_matches_vendor_without_fix(poses):
    vendor_pf = vendor_filter(ParticleFilterSIR, [0.1, 0.2], [0.4, 0.3],
                              resampling_algorithm=ResamplingAlgorithms.MULTINOMIAL)
    z = [[3.0, 1.0], [5.0, -2.0], [4.0, 0.5], [6.0, 2.5]]
    ours = model(wrap_angle_residual=False).log_likelihood(poses, z)
    theirs = np.array([vendor_pf.compute_likelihood(list(p), z, LANDMARKS) for p in poses])
    finite = theirs > 0
    assert finite.sum() > 100
    assert np.allclose(np.exp(ours[finite]), theirs[finite], rtol=1e-9, atol=1e-300)


def test_propagate_matches_vendor_without_noise(poses):
    vendor_pf = vendor_filter(ParticleFilterSIR, [0.0, 0.0], [0.4, 0.3],
                              resampling_algorithm=ResamplingAlgorithms.MULTINOMIAL)
    ours = model().propagate(poses, (0.25, 0.3), noise=False)
    theirs = np.array([vendor_pf.propagate_sample(list(p), 0.25, 0.3) for p in poses])
    diff = ours - theirs
    diff[:, 2] = P.wrap_angle(diff[:, 2])
    assert np.allclose(diff, 0, atol=1e-12)


def test_propagate_noise_has_the_vendor_spread(poses):
    np.random.seed(2)
    start = np.tile([5.0, 5.0, 0.0], (20000, 1))
    moved = model().propagate(start, (0.25, 0.0))
    assert np.isclose(np.std(moved[:, 2]), 0.2, rtol=0.03)


def test_extended_kalman_step_matches_vendor_with_upstream_bugs(monkeypatch):
    """Run one vendor EKPF update and our copy on the same particles, with sampling replaced by the mean."""
    np.random.seed(3)
    m = model(wrap_angle_residual=False)
    start = m.initial_uniform(25)
    z = [[3.0, 1.0], [5.0, -2.0], [4.0, 0.5], [6.0, 2.5]]

    vendor_pf = vendor_filter(KalmanParticleFilter, [0.1, 0.2], [0.4, 0.3])
    vendor_pf.n_particles = len(start)
    vendor_pf.particles = [[1.0 / len(start), list(p), np.eye(3)] for p in start]
    monkeypatch.setattr(np.random, "multivariate_normal", lambda mean, cov: np.array(mean, dtype=float))
    monkeypatch.setattr(KalmanParticleFilter, "multinomial_resampling", lambda self: None)
    vendor_pf.update(0.25, 0.02, z, LANDMARKS)

    proposal = registry.create("proposal", {"name": "extended_kalman", "upstream_bugs": True})
    proposal.sample = lambda mean, cov: mean
    ours = ParticleSet(start.copy(), np.full(len(start), 1.0 / len(start)))
    proposal.initialize(ours, m)
    ours, log_weights = proposal.propose(ours, (0.25, 0.02), z, m, None)
    weights, _ = P.normalize_log(log_weights)

    theirs_poses = np.array([p[1] for p in vendor_pf.particles])
    theirs_cov = np.array([p[2] for p in vendor_pf.particles])
    theirs_weights = np.array([p[0] for p in vendor_pf.particles])
    pose_diff = ours.poses - theirs_poses
    pose_diff[:, 2] = P.wrap_angle(pose_diff[:, 2])
    assert np.allclose(pose_diff, 0, atol=1e-9)
    assert np.allclose(ours.extras["cov"], theirs_cov, atol=1e-9)
    assert np.allclose(weights, theirs_weights, rtol=1e-6, atol=1e-12)


# --- the filter --------------------------------------------------------------------------

def test_world_is_the_same_for_the_same_seed():
    a, b = localization_world(seed=4), localization_world(seed=4)
    assert np.array_equal(a.true_poses, b.true_poses) and np.array_equal(a.measurements, b.measurements)
    assert not np.array_equal(a.measurements, localization_world(seed=5).measurements)


def test_world_does_not_disturb_the_global_random_state():
    np.random.seed(9)
    expected = np.random.rand()
    np.random.seed(9)
    localization_world(seed=1)
    assert np.random.rand() == expected


def test_same_seed_same_run():
    world = localization_world(seed=0)
    a = run_mcl(world, n_particles=300, filter_seed=7).traces()
    b = run_mcl(world, n_particles=300, filter_seed=7).traces()
    assert a.drop(columns="step_time").equals(b.drop(columns="step_time"))


PROPOSAL_SETUPS = [
    {"proposal": "motion_model"},
    {"proposal": "auxiliary", "trigger": "never"},
    {"proposal": "extended_kalman"},
    {"proposal": "extended_kalman", "trigger": {"name": "ess_threshold", "threshold": 0.5},
     "resampler": "systematic"},
]


@pytest.mark.parametrize("setup", PROPOSAL_SETUPS, ids=lambda s: s["proposal"])
def test_filter_localizes_the_robot(setup):
    """On Elfring's running-example world, the estimate ends up close to the true pose.

    The fixed extended Kalman PF needs ~300 particles from a uniform start; at 100 it can lock onto a
    wrong pose (its effective sample size stays at a few particles).
    """
    n = 300 if setup["proposal"] == "extended_kalman" else 1000
    errors = []
    for seed in range(3):
        traces = run_mcl(localization_world(seed=seed), n_particles=n, filter_seed=seed, **setup).traces()
        errors.append(traces["position_error"].iloc[-10:].mean())
    assert np.mean(errors) < 0.5, errors


def test_vendor_baseline_accuracy_is_comparable():
    """Our SIR filter (every step, multinomial) is about as accurate as the recorded vendor demo run."""
    import pandas as pd
    baseline = vendor.PROJECT / "results" / "baseline" / "elfring_sir" / "trajectory.csv"
    if not baseline.exists():
        pytest.skip("run tools/run_vendor_baseline.py first")
    vendor_run = pd.read_csv(baseline)
    vendor_error = np.hypot(vendor_run.est_x - vendor_run.true_x, vendor_run.est_y - vendor_run.true_y)
    ours = [run_mcl(localization_world(seed=s), n_particles=1000, filter_seed=s).traces()["position_error"]
            for s in range(3)]
    assert np.mean([o.iloc[-10:].mean() for o in ours]) < vendor_error.iloc[-10:].mean() + 0.3


def test_proposal_for_another_filter_is_rejected():
    registry._registry["proposal"]["_fake"] = type("Fake", (registry.get("proposal", "motion_model"),),
                                                   {"filter": "fastslam", "name": "_fake"})
    try:
        with pytest.raises(ValueError, match="not 'mcl'"):
            run_mcl(localization_world(seed=0), n_particles=10, proposal="_fake")
    finally:
        del registry._registry["proposal"]["_fake"]
