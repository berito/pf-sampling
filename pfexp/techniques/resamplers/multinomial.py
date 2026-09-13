"""Multinomial resampling — Elfring's implementation, imported unchanged.

Draws every particle independently in proportion to its weight (highest variance).
"""
from pfexp.registry import register
from pfexp.techniques.resamplers._elfring import ElfringResampler


@register("resampler", "multinomial")
class Multinomial(ElfringResampler):
    algorithm = "MULTINOMIAL"
