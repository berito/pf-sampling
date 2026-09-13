"""Root mean square error of the estimated position and heading against the true pose."""
import numpy as np

from pfexp.registry import register
from pfexp.techniques.base import Metric


@register("metric", "rmse")
class Rmse(Metric):
    def compute(self, log):
        traces = log.traces()
        return {
            "position_rmse": float(np.sqrt(np.mean(traces["position_error"] ** 2))),
            "heading_rmse": float(np.sqrt(np.mean(traces["heading_error"] ** 2))),
            "final_position_error": float(traces["position_error"].iloc[-1]),
        }
