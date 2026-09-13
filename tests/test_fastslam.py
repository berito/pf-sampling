"""FastSLAM: borrowed code matches the PythonRobotics functions, and the filter works end to end."""
import numpy as np
import pytest

from pfexp import particles as P
from pfexp import registry
from pfexp.filters.fastslam import UPSTREAM_CONTROL_STD, UPSTREAM_MEASUREMENT_STD, run_fastslam
from pfexp.filters.fastslam_model import SlamModel, empty_map
from pfexp.particles import ParticleSet
from pfexp.worlds import slam_world, vendor_fastslam_module

N = 100  # the vendor functions loop over their global N_PARTICLE = 100


@pytest.fixture(scope="module")
def world():
    return slam_world(seed=0)


def make_model(upstream_bugs):
    return SlamModel(Q=np.diag(UPSTREAM_MEASUREMENT_STD) ** 2, R=np.diag(UPSTREAM_CONTROL_STD) ** 2,
                     dt=0.1, n_landmarks=8, upstream_bugs=upstream_bugs)


def vendor_particles(fs, poses):
    particles = [fs.Particle(8) for _ in range(N)]
    for p, pose in zip(particles, poses):
        p.x, p.y, p.yaw = pose
    return particles


def start_poses(seed=1):
    rng = np.random.RandomState(seed)
    return np.column_stack([rng.normal(0, 0.3, N), rng.normal(0, 0.3, N), rng.normal(0, 0.1, N)])


def observation_step(world, t):
    """An observation that sees several landmarks."""
    z = world.observations[t]
    assert z.shape[1] >= 3
    return z


# --- borrowed copy matches upstream (fixes switched on as upstream) -----------------------

def test_prediction_matches_vendor_with_same_seed(world):
    fs = vendor_fastslam_module(1)
    poses = start_poses()
    control = world.controls[50]
    theirs = vendor_particles(fs, poses)
    np.random.seed(11)
    fs.predict_particles(theirs, control.reshape(2, 1))
    np.random.seed(11)
    ours = make_model(True).predict_noisy(poses, control)
    theirs = np.array([[p.x, p.y, p.yaw] for p in theirs])
    assert np.allclose(ours, theirs, atol=1e-12)


@pytest.mark.parametrize("version", [1, 2])
def test_observation_update_matches_vendor(world, version):
    """Two observation steps (adds landmarks, then updates them) on identical particles, no prediction noise."""
    fs = vendor_fastslam_module(version)
    poses = start_poses()
    z1, z2 = observation_step(world, 40), observation_step(world, 41)

    theirs = vendor_particles(fs, poses)
    theirs = fs.update_with_observation(theirs, z1)
    theirs = fs.update_with_observation(theirs, z2)

    proposal = registry.create("proposal", {"name": f"fastslam{version}", "upstream_bugs": True})
    model = make_model(True)
    model.predict_noisy = lambda poses, control: poses.copy()  # isolate the observation update
    ours = ParticleSet(poses.copy(), np.full(N, 1.0 / N), empty_map(N, 8))
    proposal.initialize(ours, model)
    for z in (z1, z2):
        ours, log_weights = proposal.propose(ours, None, z, model, None)
        ours = ours.with_weights(P.normalize_log(log_weights)[0])

    their_weights = np.array([p.w for p in theirs])
    assert np.allclose(ours.weights, their_weights / their_weights.sum(), rtol=1e-8)
    assert np.allclose(ours.extras["lm"], np.array([p.lm for p in theirs]), atol=1e-9)
    assert np.allclose(ours.extras["lmP"], np.array([p.lmP.reshape(8, 2, 2) for p in theirs]), atol=1e-9)
    if version == 2:
        assert np.allclose(ours.poses, np.array([[p.x, p.y, p.yaw] for p in theirs]), atol=1e-9)
        assert np.allclose(ours.extras["P"], np.array([p.P for p in theirs]), atol=1e-9)


def test_new_landmark_fix():
    """Upstream re-initialises a landmark whose x estimate is near zero; the fix uses a seen flag."""
    extras = empty_map(1, 8)
    extras["seen"][0, 3] = True  # mapped, with its x estimate at 0.0
    assert make_model(True).is_new(extras, 3)[0]
    assert not make_model(False).is_new(extras, 3)[0]


# --- the filter --------------------------------------------------------------------------

def test_world_matches_vendor_simulation():
    fs = vendor_fastslam_module(1)
    world = slam_world(seed=2)
    np.random.seed(2)
    x_true, x_dr = np.zeros((3, 1)), np.zeros((3, 1))
    for t in range(5):
        x_true, z, x_dr, ud = fs.observation(x_true, x_dr, fs.calc_input((t + 1) * fs.DT), world.landmarks)
    assert np.allclose(world.true_poses[4], x_true[:, 0]) and np.allclose(world.controls[4], ud[:, 0])


def test_same_seed_same_run(world):
    a = run_fastslam(world, n_particles=30, filter_seed=3).traces().drop(columns="step_time")
    b = run_fastslam(world, n_particles=30, filter_seed=3).traces().drop(columns="step_time")
    assert a.equals(b)


@pytest.mark.parametrize("resampler", ["multinomial", "residual", "stratified", "systematic"])
def test_every_resampler_plugs_in(world, resampler):
    log = run_fastslam(world, n_particles=30, resampler=resampler, trigger="every_step", filter_seed=0)
    assert log.n_steps == len(world.true_poses) and log.array("resampled").all()
    assert log.landmarks_est[-1].shape == (8, 2)


def landmark_error(log, world):
    return np.nanmean(np.hypot(*(log.landmarks_est[-1] - world.landmarks).T))


def test_fastslam2_beats_fastslam1_on_average():
    """Averaged over worlds and filter seeds, the measurement-informed proposal gives a better map and path.

    Single runs vary a lot: the whole map and path can drift together by ~1 m, because the absolute frame is
    only anchored at the start and the upstream filter noise settings are large.
    """
    errors = {1: [], 2: []}
    for world_seed in range(3):
        world = slam_world(seed=world_seed)
        for filter_seed in range(2):
            for version in (1, 2):
                log = run_fastslam(world, proposal=f"fastslam{version}", filter_seed=filter_seed)
                pose_rmse = np.sqrt(np.mean(log.traces()["position_error"] ** 2))
                errors[version].append((landmark_error(log, world), pose_rmse))
    fs1, fs2 = np.mean(errors[1], axis=0), np.mean(errors[2], axis=0)
    assert (fs2 < fs1).all(), errors


def test_mcl_proposal_is_rejected(world):
    with pytest.raises(ValueError, match="not 'fastslam'"):
        run_fastslam(world, n_particles=5, proposal="motion_model")
