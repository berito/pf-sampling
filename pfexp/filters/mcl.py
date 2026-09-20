"""Particle-filter localization (MCL) with swappable sampling steps.

The loop follows Elfring's particle filters (propose, weight, maybe resample), with each step
taken from the registry: a proposal, a trigger that decides whether to resample, a resampler, and an
optional move applied after resampling. Models come from `mcl_model.py`.
"""
import numpy as np

from pfexp import particles as P
from pfexp.particles import ParticleSet
from pfexp import registry
from pfexp.filters.mcl_model import LocalizationModel
from pfexp.runlog import RunLog, StepTimer


def run_mcl(world, *, n_particles, proposal="motion_model", resampler="multinomial", trigger="every_step",
            move="none", forward_std=0.1, turn_std=0.2, range_std=0.4, bearing_std=0.3,
            wrap_angle_residual=True, start="uniform", start_spread=0.2, filter_seed=0):
    """Run localization on a `worlds.LocalizationWorld`. Defaults are those of Elfring's running example.

    The four noise settings are what the filter assumes, which the world need not share: `forward_std` and
    `turn_std` for the motion, `range_std` and `bearing_std` for the measurements.

    `start` is "uniform" for particles spread over the whole world, which is global localization, or "known"
    for particles drawn around the world's start pose with standard deviation `start_spread`, which is
    tracking a robot whose initial pose is roughly known.
    """
    if start not in ("uniform", "known"):
        raise ValueError(f"start must be 'uniform' or 'known', not {start!r}")
    process_std, measurement_std = (forward_std, turn_std), (range_std, bearing_std)
    proposal = registry.create("proposal", proposal)
    if proposal.filter != "mcl":
        raise ValueError(f"proposal '{proposal.name}' is for the '{proposal.filter}' filter, not 'mcl'")
    resampler = registry.create("resampler", resampler)
    trigger = registry.create("trigger", trigger)
    move = registry.create("move", move)

    model = LocalizationModel(world.size, world.landmarks, tuple(process_std), tuple(measurement_std),
                              wrap_angle_residual)
    log = RunLog(settings={
        "filter": "mcl", "n_particles": n_particles, "filter_seed": filter_seed,
        "proposal": proposal.describe(), "resampler": resampler.describe(),
        "trigger": trigger.describe(), "move": move.describe(),
        "forward_std": forward_std, "turn_std": turn_std,
        "range_std": range_std, "bearing_std": bearing_std,
        "wrap_angle_residual": wrap_angle_residual, "start": start,
    })

    np.random.seed(filter_seed)
    poses = (model.initial_uniform(n_particles) if start == "uniform"
             else model.initial_gaussian(n_particles, world.settings["start"], [start_spread] * 3))
    particles = ParticleSet(poses, np.full(n_particles, 1.0 / n_particles))
    proposal.initialize(particles, model)

    for t in range(len(world.true_poses)):
        control, measurement = world.controls[t], world.measurements[t]
        with StepTimer() as timer:
            particles, log_weights = proposal.propose(particles, control, measurement, model, resampler)
            evidence = (P.log_evidence_increment(log_weights) if proposal.gives_marginal_likelihood
                        else float("nan"))
            weights, collapsed = P.normalize_log(log_weights)
            particles = particles.with_weights(weights)
            ess = P.effective_sample_size(weights)
            resampled = trigger.should_resample(weights)
            unique = n_particles
            if resampled:
                indices = resampler.resample(weights)
                unique = len(np.unique(indices))
                particles = particles.select(indices)
                particles = move.move(particles, {"model": model, "control": control, "measurement": measurement})
        log.record(true_pose=world.true_poses[t], poses=particles.poses, weights=particles.weights,
                   ess_before=ess, resampled=resampled, unique_after=unique, collapsed=collapsed,
                   step_time=timer.elapsed, log_evidence=evidence)
    return log
