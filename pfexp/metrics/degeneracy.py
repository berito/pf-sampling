"""How often the filter resampled, how often all weights collapsed, and how many distinct particles survive."""
import numpy as np

from pfexp.registry import register
from pfexp.techniques.base import Metric


@register("metric", "degeneracy")
class Degeneracy(Metric):
    def compute(self, log):
        resampled = log.array("resampled")
        unique = log.array("unique_after")[resampled] / log.n_particles
        return {
            "resample_rate": float(resampled.mean()),
            "collapses": int(log.array("collapsed").sum()),
            "unique_after_resampling": float(unique.mean()) if len(unique) else 1.0,
            "max_weight_mean": float(log.array("max_weight").mean()),
        }
