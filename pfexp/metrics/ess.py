"""Effective sample size before resampling, as a fraction of the number of particles."""
import numpy as np

from pfexp.registry import register
from pfexp.techniques.base import Metric


@register("metric", "ess")
class Ess(Metric):
    def compute(self, log):
        ess = log.array("ess") / log.n_particles
        return {"ess_mean": float(ess.mean()), "ess_min": float(ess.min())}
