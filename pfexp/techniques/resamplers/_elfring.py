"""Shared adapter around the Elfring resampler (imported unchanged from vendor/).

Elfring's `Resampler.resample` takes `[[weight, state], ...]` and returns `[[1/N, copy_of_state], ...]`.
Passing the particle index as the "state" turns it into an index resampler that works for any filter.
"""
import numpy as np

from pfexp import vendor
from pfexp.techniques.base import Resampler

vendor.use("particle_filter_tutorial")
from core.resampling import Resampler as _VendorResampler  # noqa: E402
from core.resampling import ResamplingAlgorithms  # noqa: E402


class ElfringResampler(Resampler):
    algorithm = None  # name of a core.resampling.ResamplingAlgorithms member

    def resample(self, weights):
        weights = np.asarray(weights, dtype=float)
        weights = weights / weights.sum()
        # The vendor search loops `while Q[m] < u` can step past the end if rounding leaves the
        # cumulative sum just below 1; lifting the last weight by that shortfall prevents it.
        weights[-1] += max(0.0, 1.0 - np.cumsum(weights)[-1]) + 1e-12
        samples = [[w, i] for i, w in enumerate(weights)]
        resampled = _VendorResampler().resample(samples, len(weights), ResamplingAlgorithms[self.algorithm])
        return np.array([index for _, index in resampled], dtype=int)
