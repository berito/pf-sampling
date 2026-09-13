"""FastSLAM (Rao-Blackwellized particle filter SLAM) with swappable sampling steps.

Each particle samples a robot trajectory and keeps its own map: one small EKF per landmark. That split is
the Rao-Blackwellization: given the trajectory, the landmarks are independent. The proposal decides how
poses are sampled (FastSLAM 1.0 or 2.0); resampling and moves come from the registry as for localization.
Defaults follow the PythonRobotics scripts (100 particles, resample when ESS < N/1.5, low-variance resampling).
"""
import numpy as np

from pfexp import particles as P
from pfexp import registry
from pfexp.filters.fastslam_model import SlamModel, empty_map
from pfexp.particles import ParticleSet
from pfexp.runlog import RunLog, StepTimer

# Upstream filter settings (fast_slam1.py): Q measurement noise, R control noise, as standard deviations.
UPSTREAM_MEASUREMENT_STD = (3.0, np.deg2rad(10.0))
UPSTREAM_CONTROL_STD = (1.0, np.deg2rad(20.0))


def landmark_estimates(particles):
    """Weighted mean landmark positions over the particles that have seen each landmark (NaN if none)."""
    seen = particles.extras["seen"]
    weights = particles.weights[:, None] * seen
    total = weights.sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.einsum("nl,nlk->lk", weights, particles.extras["lm"]) / total[:, None]


def run_fastslam(world, *, n_particles=100, proposal="fastslam1", resampler="systematic",
                 trigger=None, move="none", measurement_std=UPSTREAM_MEASUREMENT_STD,
                 control_std=UPSTREAM_CONTROL_STD, filter_seed=0):
    """Run FastSLAM on a `worlds.SlamWorld`."""
    if trigger is None:
        trigger = {"name": "ess_threshold", "threshold": 1 / 1.5}
    proposal = registry.create("proposal", proposal)
    if proposal.filter != "fastslam":
        raise ValueError(f"proposal '{proposal.name}' is for the '{proposal.filter}' filter, not 'fastslam'")
    resampler = registry.create("resampler", resampler)
    trigger = registry.create("trigger", trigger)
    move = registry.create("move", move)

    n_landmarks = len(world.landmarks)
    model = SlamModel(Q=np.diag(measurement_std) ** 2, R=np.diag(control_std) ** 2, dt=world.dt,
                      n_landmarks=n_landmarks, upstream_bugs=getattr(proposal, "upstream_bugs", False))
    log = RunLog(settings={
        "filter": "fastslam", "n_particles": n_particles, "filter_seed": filter_seed,
        "proposal": proposal.describe(), "resampler": resampler.describe(),
        "trigger": trigger.describe(), "move": move.describe(),
        "measurement_std": list(map(float, measurement_std)), "control_std": list(map(float, control_std)),
    }, landmarks_true=world.landmarks.copy())

    np.random.seed(filter_seed)
    particles = ParticleSet(np.zeros((n_particles, 3)), np.full(n_particles, 1.0 / n_particles),
                            empty_map(n_particles, n_landmarks))  # upstream: every particle starts at the origin
    proposal.initialize(particles, model)

    for t in range(len(world.true_poses)):
        control, observations = world.controls[t], world.observations[t]
        with StepTimer() as timer:
            particles, log_weights = proposal.propose(particles, control, observations, model, resampler)
            weights, collapsed = P.normalize_log(log_weights)
            particles = particles.with_weights(weights)
            ess = P.effective_sample_size(weights)
            resampled = trigger.should_resample(weights)
            unique = n_particles
            if resampled:
                indices = resampler.resample(weights)
                unique = len(np.unique(indices))
                particles = particles.select(indices)
                particles = move.move(particles, {"model": model, "control": control,
                                                  "observations": observations})
        log.record(true_pose=world.true_poses[t], poses=particles.poses, weights=particles.weights,
                   ess_before=ess, resampled=resampled, unique_after=unique, collapsed=collapsed,
                   step_time=timer.elapsed, landmarks_est=landmark_estimates(particles))
    return log
