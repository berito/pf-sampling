"""Systematic resampling — Elfring's implementation, imported unchanged.

A single uniform draw, then N evenly spaced points along the cumulative weights (lowest variance).
"""
from pfexp.registry import register
from pfexp.techniques.resamplers._elfring import ElfringResampler


@register("resampler", "systematic")
class Systematic(ElfringResampler):
    algorithm = "SYSTEMATIC"
