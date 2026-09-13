"""Stratified resampling: Elfring's implementation, imported unchanged.

One uniform draw inside each of N equal strata of the cumulative weights.
"""
from pfexp.registry import register
from pfexp.techniques.resamplers._elfring import ElfringResampler


@register("resampler", "stratified")
class Stratified(ElfringResampler):
    algorithm = "STRATIFIED"
