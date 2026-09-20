"""The interfaces a sampling technique implements.

Particles are always handled as a numpy array of normalized weights (shape N) plus filter-specific
states, so the same resampler or trigger works for every filter. Randomness comes from the global
numpy generator, which the runner seeds per run, as the upstream code works the same way.
"""
import numpy as np


class Technique:
    """Common base: parameters come from the experiment config as keyword arguments."""

    kind = None
    name = None

    def __init__(self, **params):
        if params:
            raise TypeError(f"{type(self).__name__} takes no parameters, got {sorted(params)}")

    def describe(self):
        """Settings recorded with every run (name plus parameters)."""
        return {"name": self.name}


class Resampler(Technique):
    """Draw N particle indices according to the weights."""

    def resample(self, weights: np.ndarray) -> np.ndarray:
        raise NotImplementedError


class Trigger(Technique):
    """Decide whether to resample at this step."""

    def should_resample(self, weights: np.ndarray) -> bool:
        raise NotImplementedError


class Proposal(Technique):
    """Draw new particle states given the control and the measurement.

    Which filter a proposal belongs to is set by `filter`; the filter defines the exact call.
    It returns the new particles and their unnormalized log weights.

    `gives_marginal_likelihood` says whether those weights sum to p(z_t | z_1:t-1), which holds for a
    bootstrap proposal but not for one that weights in two stages.
    """

    filter = None
    gives_marginal_likelihood = False

    def initialize(self, particles, model):
        """Add any per-particle state the proposal needs (optional)."""

    def propose(self, particles, control, measurement, model, resampler):
        raise NotImplementedError


class Move(Technique):
    """Change particle states after resampling (e.g. MCMC moves), keeping the target distribution."""

    def move(self, particles, context):
        raise NotImplementedError


class Metric(Technique):
    """Compute one or more numbers from a finished run log."""

    def applies_to(self, log) -> bool:
        """Whether this metric makes sense for the run (e.g. map error only for SLAM)."""
        return True

    def compute(self, log) -> dict:
        raise NotImplementedError
