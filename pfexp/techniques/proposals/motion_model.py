"""Motion-model (bootstrap) proposal for localization: sample from p(x_t | x_t-1, u), weight by p(z | x_t).

The standard particle filter — what Elfring's ParticleFilterSIR does.
"""
import numpy as np

from pfexp.registry import register
from pfexp.techniques.base import Proposal


@register("proposal", "motion_model")
class MotionModel(Proposal):
    filter = "mcl"

    def propose(self, particles, control, measurement, model, resampler):
        poses = model.propagate(particles.poses, control)
        with np.errstate(divide="ignore"):
            log_weights = np.log(particles.weights) + model.log_likelihood(poses, measurement)
        return particles.with_poses(poses), log_weights
