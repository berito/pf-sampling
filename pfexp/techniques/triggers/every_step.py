"""Resample at every step (the SIR filter) — Elfring's ParticleFilterSIR rule, imported unchanged."""
from pfexp.registry import register
from pfexp.techniques.triggers._elfring import call_vendor_rule
from pfexp.techniques.base import Trigger


@register("trigger", "every_step")
class EveryStep(Trigger):
    def should_resample(self, weights):
        return call_vendor_rule("ParticleFilterSIR", weights)
