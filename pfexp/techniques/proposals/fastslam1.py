"""FastSLAM 1.0 proposal: sample the pose from the motion model, weight by each landmark observation.

Borrowed from PythonRobotics SLAM/FastSLAM1/fast_slam1.py@1fe4fb9 (predict_particles and
update_with_observation; MIT licence). The models are in `pfexp.filters.fastslam_model`.
`upstream_bugs=True` restores the upstream new-landmark test (see that module).
"""
import numpy as np

from pfexp.particles import ParticleSet
from pfexp.registry import register
from pfexp.techniques.base import Proposal


def copy_map(extras):
    return {key: value.copy() for key, value in extras.items()}


@register("proposal", "fastslam1")
class FastSlam1(Proposal):
    filter = "fastslam"

    def __init__(self, upstream_bugs=False):
        self.upstream_bugs = upstream_bugs

    def describe(self):
        return {"name": self.name, "upstream_bugs": self.upstream_bugs}

    def propose(self, particles, control, observations, model, resampler):
        poses = model.predict_noisy(particles.poses, control)
        extras = copy_map(particles.extras)
        with np.errstate(divide="ignore"):
            log_weights = np.log(particles.weights)
        for z in observations.T:
            new = model.is_new(extras, int(z[2]))
            if new.any():
                model.add_landmark(poses, extras, z, new)
            known = ~new
            if known.any():
                log_weights[known] += model.landmark_log_weight(poses, extras, z, known)
                model.update_landmark(poses, extras, z, known)
        return ParticleSet(poses, particles.weights, extras), log_weights
