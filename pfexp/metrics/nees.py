"""Normalized estimation error squared of the pose: does the particle spread match the actual error?

NEES = e^T inv(S) e with e the pose error and S the weighted particle covariance. For a consistent filter its
average is about 3 (the pose dimension); much larger means the particles are overconfident.
"""
import numpy as np

from pfexp.particles import wrap_angle
from pfexp.registry import register
from pfexp.techniques.base import Metric

JITTER = 1e-9  # a fully collapsed particle cloud has zero covariance


@register("metric", "nees")
class Nees(Metric):
    def compute(self, log):
        error = log.array("est_pose") - log.array("true_pose")
        error[:, 2] = wrap_angle(error[:, 2])
        cov = log.array("est_cov") + JITTER * np.eye(3)
        nees = np.einsum("ni,ni->n", error, np.linalg.solve(cov, error[:, :, None])[:, :, 0])
        return {"nees_mean": float(np.mean(nees)), "nees_median": float(np.median(nees))}
