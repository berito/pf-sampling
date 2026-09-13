"""Never resample (plain sequential importance sampling; also used with the auxiliary proposal, which selects particles itself)."""
from pfexp.registry import register
from pfexp.techniques.base import Trigger


@register("trigger", "never")
class Never(Trigger):
    def should_resample(self, weights):
        return False
