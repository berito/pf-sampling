"""The run log: one format recorded by every filter, and read by every metric.

Per step it stores the true pose, the estimate, the particle spread, and what the sampling did
(ESS before resampling, whether it resampled, how many distinct particles survived, whether the
weights collapsed). SLAM filters also store landmark estimates. Metrics only ever read this, so a
metric works for every filter.
"""
import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from pfexp import particles as P


@dataclass
class RunLog:
    settings: dict = field(default_factory=dict)
    steps: list = field(default_factory=list)
    landmarks_true: np.ndarray | None = None
    landmarks_est: list = field(default_factory=list)

    def record(self, *, true_pose, poses, weights, ess_before, resampled, unique_after, collapsed,
               step_time, landmarks_est=None):
        """Record one filter step. `poses` and `weights` are the particles after the step."""
        mean = P.weighted_pose_mean(poses, weights)
        self.steps.append({
            "true_pose": np.asarray(true_pose, dtype=float),
            "est_pose": mean,
            "est_cov": P.weighted_pose_cov(poses, weights, mean),
            "ess": float(ess_before),
            "resampled": bool(resampled),
            "unique_after": int(unique_after),
            "collapsed": bool(collapsed),
            "max_weight": float(np.max(weights)),
            "step_time": float(step_time),
        })
        if landmarks_est is not None:
            self.landmarks_est.append(np.asarray(landmarks_est, dtype=float))

    # --- arrays for metrics -------------------------------------------------------------
    @property
    def n_steps(self):
        return len(self.steps)

    @property
    def n_particles(self):
        return self.settings.get("n_particles")

    def array(self, key):
        return np.array([step[key] for step in self.steps])

    @property
    def total_time(self):
        return float(self.array("step_time").sum()) if self.steps else 0.0

    # --- per-step table for saving and plotting -----------------------------------------
    def traces(self):
        true_pose, est_pose = self.array("true_pose"), self.array("est_pose")
        error = est_pose - true_pose
        error[:, 2] = P.wrap_angle(error[:, 2])
        return pd.DataFrame({
            "step": np.arange(self.n_steps),
            "true_x": true_pose[:, 0], "true_y": true_pose[:, 1], "true_heading": true_pose[:, 2],
            "est_x": est_pose[:, 0], "est_y": est_pose[:, 1], "est_heading": est_pose[:, 2],
            "position_error": np.hypot(error[:, 0], error[:, 1]),
            "heading_error": np.abs(error[:, 2]),
            "ess": self.array("ess"),
            "resampled": self.array("resampled"),
            "unique_after": self.array("unique_after"),
            "collapsed": self.array("collapsed"),
            "max_weight": self.array("max_weight"),
            "step_time": self.array("step_time"),
        })


class StepTimer:
    """Measure one filter step: `with StepTimer() as t: ...; t.elapsed`."""

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.elapsed = time.perf_counter() - self._start
