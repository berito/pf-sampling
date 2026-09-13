"""Wall-clock time spent in filter steps (excluding world simulation and logging)."""
from pfexp.registry import register
from pfexp.techniques.base import Metric


@register("metric", "runtime")
class Runtime(Metric):
    def compute(self, log):
        return {"runtime_total_s": log.total_time, "runtime_per_step_ms": 1000 * log.total_time / log.n_steps}
