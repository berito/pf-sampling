"""Residual resampling: Elfring's implementation, imported unchanged.

Keeps floor(N*w) copies of each particle deterministically, draws the rest multinomially.
"""
from pfexp.registry import register
from pfexp.techniques.resamplers._elfring import ElfringResampler


@register("resampler", "residual")
class Residual(ElfringResampler):
    algorithm = "RESIDUAL"
