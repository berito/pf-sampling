"""Resample when the effective sample size 1/sum(w²) drops below threshold·N.

Elfring's ParticleFilterNEPR rule, imported unchanged.
"""
from pfexp.registry import register
from pfexp.techniques.triggers._elfring import FractionThresholdTrigger


@register("trigger", "ess_threshold")
class EssThreshold(FractionThresholdTrigger):
    vendor_class = "ParticleFilterNEPR"
