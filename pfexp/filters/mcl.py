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
            move="none", process_std=(0.1, 0.2), measurement_std=(0.4, 0.3), wrap_angle_residual=True,
            filter_seed=0):
    """Run localization on a `worlds.LocalizationWorld`. Defaults are those of Elfring's running example."""
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
        "process_std": list(process_std), "measurement_std": list(measurement_std),
        "wrap_angle_residual": wrap_angle_residual,
    })

    np.random.seed(filter_seed)
    particles = ParticleSet(model.initial_uniform(n_particles), np.full(n_particles, 1.0 / n_particles))
    proposal.initialize(particles, model)

    for t in range(len(world.true_poses)):
        control, measurement = world.controls[t], world.measurements[t]
        with StepTimer() as timer:
            particles, log_weights = proposal.propose(particles, control, measurement, model, resampler)
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
                   step_time=timer.elapsed)
    return log
