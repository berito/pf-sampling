"""Absolute trajectory error: position RMSE after the best-fit rigid alignment of the estimated path.

For SLAM the map frame is only fixed at the start, so a constant rotation or offset of the whole solution is
not an estimation error of the shape; ATE removes it. For localization in a known map it is close to the RMSE.
"""
import numpy as np

from pfexp.metrics.alignment import apply, fit_rigid_2d
from pfexp.registry import register
from pfexp.techniques.base import Metric


@register("metric", "ate")
class Ate(Metric):
    def compute(self, log):
        true_xy = log.array("true_pose")[:, :2]
        est_xy = log.array("est_pose")[:, :2]
        R, t = fit_rigid_2d(est_xy, true_xy)
        residual = apply(R, t, est_xy) - true_xy
        return {"ate": float(np.sqrt(np.mean(np.sum(residual ** 2, axis=1))))}
