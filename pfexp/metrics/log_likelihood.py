"""Marginal likelihood of the observations, log p(z_1:T | theta), under the model the filter assumes.

The filter's own weights estimate it: summing the unnormalized weights at a step gives
p(z_t | z_1:t-1), and the run log stores the log of that sum per step. Maximizing this over the noise
parameters is maximum-likelihood parameter learning with the trajectory latent.

Only proposals that mark themselves with `gives_marginal_likelihood` record the per-step value, so the
metric is absent for the others rather than reporting a number the estimator does not support.
"""
import numpy as np

from pfexp.registry import register
from pfexp.techniques.base import Metric


@register("metric", "log_likelihood")
class LogLikelihood(Metric):
    def applies_to(self, log):
        return log.n_steps > 0 and not np.isnan(log.array("log_evidence")).all()

    def compute(self, log):
        increments = log.array("log_evidence")
        total = float(np.sum(increments))
        return {"log_likelihood": total, "log_likelihood_per_step": total / len(increments)}
