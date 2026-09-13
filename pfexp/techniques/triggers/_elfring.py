"""Shared adapter around Elfring's resampling rules (imported unchanged from vendor/).

In the vendor code, the rule for when to resample is the `needs_resampling` method of a filter
subclass, reading `self.particles` and `self.resampling_threshold`. Calling that method on a small
stand-in object reuses it without the rest of the filter.
"""
from types import SimpleNamespace

import numpy as np

from pfexp import vendor
from pfexp.techniques.base import Trigger

vendor.use("particle_filter_tutorial")
import core.particle_filters as vendor_filters  # noqa: E402


def call_vendor_rule(filter_class_name, weights, threshold=None):
    stand_in = SimpleNamespace(
        particles=[[w, None] for w in np.asarray(weights, dtype=float)],
        resampling_threshold=threshold,
    )
    return bool(getattr(vendor_filters, filter_class_name).needs_resampling(stand_in))


class FractionThresholdTrigger(Trigger):
    """A vendor rule whose threshold is an absolute particle count, configured here as a fraction of N."""

    vendor_class = None

    def __init__(self, threshold=0.5):
        if not 0.0 < threshold <= 1.0:
            raise ValueError(f"threshold is a fraction of N and must be in (0, 1], got {threshold}")
        self.threshold = threshold

    def should_resample(self, weights):
        return call_vendor_rule(self.vendor_class, weights, self.threshold * len(weights))

    def describe(self):
        return {"name": self.name, "threshold": self.threshold}
