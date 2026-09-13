"""Landmark map error at the end of a SLAM run: mean distance to the true landmarks, raw and after alignment."""
import numpy as np

from pfexp.metrics.alignment import apply, fit_rigid_2d
from pfexp.registry import register
from pfexp.techniques.base import Metric


@register("metric", "map_error")
class MapError(Metric):
    def applies_to(self, log):
        return log.landmarks_true is not None and len(log.landmarks_est) > 0

    def compute(self, log):
        estimated, true = log.landmarks_est[-1], log.landmarks_true
        mapped = ~np.isnan(estimated).any(axis=1)
        if mapped.sum() == 0:
            return {"map_error": float("nan"), "map_error_aligned": float("nan"), "landmarks_mapped": 0}
        raw = np.hypot(*(estimated[mapped] - true[mapped]).T)
        aligned = raw
        if mapped.sum() >= 2:
            R, t = fit_rigid_2d(estimated[mapped], true[mapped])
            aligned = np.hypot(*(apply(R, t, estimated[mapped]) - true[mapped]).T)
        return {"map_error": float(raw.mean()), "map_error_aligned": float(aligned.mean()),
                "landmarks_mapped": int(mapped.sum())}
