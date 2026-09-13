"""Resample when 1/max(w) drops below threshold * N.

Elfring's ParticleFilterMWR rule, imported unchanged.
"""
from pfexp.registry import register
from pfexp.techniques.triggers._elfring import FractionThresholdTrigger


@register("trigger", "max_weight")
class MaxWeight(FractionThresholdTrigger):
    vendor_class = "ParticleFilterMWR"
