"""Auxiliary particle filter proposal for localization (Pitt & Shephard 1999).

Borrowed from particle_filter_tutorial/core/particle_filters/auxiliary_particle_filter.py@e6014b7
(Elfring et al.; MIT licence).

First picks which particles to continue from, using how well a trial propagation of each explains
the measurement; then propagates the picked ones again and corrects the weight by the trial
likelihood. Changes: vectorized; log weights; the first-stage selection uses the experiment's
resampler instead of hardcoded multinomial (set `first_stage` to pin it).
"""
import numpy as np

from pfexp import registry
from pfexp.registry import register
from pfexp.techniques.base import Proposal

LOG_MIN_LIKELIHOOD = np.log(1e-10)  # upstream floors the trial likelihood at 1e-10


@register("proposal", "auxiliary")
class Auxiliary(Proposal):
    filter = "mcl"

    def __init__(self, first_stage=None):
        self.first_stage = first_stage

    def describe(self):
        return {"name": self.name, "first_stage": self.first_stage}

    def propose(self, particles, control, measurement, model, resampler):
        trial = model.propagate(particles.poses, control)
        trial_log_likelihood = model.log_likelihood(trial, measurement)
        with np.errstate(divide="ignore"):
            first_stage_log_weights = np.log(particles.weights) + trial_log_likelihood
        first_stage_weights = np.exp(first_stage_log_weights - first_stage_log_weights.max())
        first_stage_weights /= first_stage_weights.sum()

        selector = registry.create("resampler", self.first_stage) if self.first_stage else resampler
        indices = selector.resample(first_stage_weights)
        picked = particles.select(indices)

        poses = model.propagate(picked.poses, control)
        log_weights = (model.log_likelihood(poses, measurement)
                       - np.maximum(trial_log_likelihood[indices], LOG_MIN_LIKELIHOOD))
        return picked.with_poses(poses), log_weights
