import numpy as np
import pytest

from pfexp import particles as P
from pfexp import registry

RESAMPLERS = ["multinomial", "residual", "stratified", "systematic"]


@pytest.fixture(autouse=True)
def seed():
    np.random.seed(0)


def test_all_four_schemes_are_registered():
    assert set(RESAMPLERS) <= set(registry.names("resampler"))


@pytest.mark.parametrize("name", RESAMPLERS)
def test_returns_n_valid_indices(name):
    weights = np.random.dirichlet(np.ones(50))
    indices = registry.create("resampler", name).resample(weights)
    assert indices.shape == (50,) and indices.dtype.kind == "i"
    assert indices.min() >= 0 and indices.max() < 50


@pytest.mark.parametrize("name", RESAMPLERS)
def test_all_weight_on_one_particle(name):
    weights = np.zeros(20)
    weights[7] = 1.0
    assert (registry.create("resampler", name).resample(weights) == 7).all()


@pytest.mark.parametrize("name", RESAMPLERS)
def test_rounding_in_cumulative_sum_does_not_crash(name):
    weights = np.full(1000, 1.0 / 1000) * (1 - 1e-12)
    assert len(registry.create("resampler", name).resample(weights)) == 1000


@pytest.mark.parametrize("name", RESAMPLERS)
def test_same_seed_same_result(name):
    weights = np.random.dirichlet(np.ones(30))
    np.random.seed(5)
    first = registry.create("resampler", name).resample(weights)
    np.random.seed(5)
    assert (registry.create("resampler", name).resample(weights) == first).all()


def test_unbiased_and_variance_ordering():
    """Mean offspring count is N·w for every scheme; its spread follows the textbook ordering."""
    weights = np.array([0.1, 0.25, 0.2, 0.15, 0.3])
    stats = {}
    for name in RESAMPLERS:
        resampler = registry.create("resampler", name)
        counts = np.array([np.bincount(resampler.resample(weights), minlength=5) for _ in range(4000)])
        assert np.allclose(counts.mean(axis=0), 5 * weights, atol=0.05)
        stats[name] = counts.std(axis=0).mean()
    assert stats["multinomial"] > stats["residual"]
    assert stats["multinomial"] > stats["stratified"] >= stats["systematic"] - 0.02


def test_every_step_always_resamples():
    assert registry.create("trigger", "every_step").should_resample(np.full(10, 0.1))


@pytest.mark.parametrize("threshold", [0.3, 0.5, 0.9])
def test_ess_threshold_matches_definition(threshold):
    trigger = registry.create("trigger", {"name": "ess_threshold", "threshold": threshold})
    for _ in range(50):
        weights = np.random.dirichlet(np.full(40, 0.3))
        expected = P.effective_sample_size(weights) < threshold * 40
        assert trigger.should_resample(weights) == expected


def test_max_weight_matches_definition():
    trigger = registry.create("trigger", {"name": "max_weight", "threshold": 0.5})
    for _ in range(50):
        weights = np.random.dirichlet(np.full(40, 0.3))
        assert trigger.should_resample(weights) == (1.0 / weights.max() < 20)


def test_threshold_must_be_a_fraction():
    with pytest.raises(ValueError):
        registry.create("trigger", {"name": "ess_threshold", "threshold": 50})
