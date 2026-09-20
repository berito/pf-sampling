"""The marginal likelihood estimator against a case where the answer is known exactly.

For a linear model with Gaussian noise the Kalman filter gives log p(z_1:T) in closed form, so the
particle estimate can be checked rather than only inspected: it should approach that value as the
number of particles grows, with a spread that shrinks, and it should not depend on whether the run
resamples.
"""
import numpy as np

from pfexp import particles as P
from pfexp.metrics.log_likelihood import LogLikelihood
from pfexp.runlog import RunLog

A, H = 0.9, 1.0          # state transition and observation
Q, R = 0.5, 0.3          # process and measurement variance
M0, P0 = 0.0, 1.0        # prior mean and variance
STEPS = 20


def simulate(seed, steps=STEPS):
    rng = np.random.default_rng(seed)
    x = rng.normal(M0, np.sqrt(P0))
    measurements = []
    for _ in range(steps):
        x = A * x + rng.normal(0, np.sqrt(Q))
        measurements.append(H * x + rng.normal(0, np.sqrt(R)))
    return np.array(measurements)


def kalman_log_likelihood(measurements):
    """log p(z_1:T), exactly."""
    mean, variance, total = M0, P0, 0.0
    for z in measurements:
        mean, variance = A * mean, A * A * variance + Q
        innovation, s = z - H * mean, H * H * variance + R
        total += -0.5 * (np.log(2 * np.pi * s) + innovation ** 2 / s)
        gain = H * variance / s
        mean, variance = mean + gain * innovation, (1 - gain * H) * variance
    return total


def particle_log_likelihood(measurements, n_particles, seed, resample):
    """The same estimator the filters use: the log of the summed unnormalized weights, per step."""
    rng = np.random.default_rng(seed + 10_000)
    states = rng.normal(M0, np.sqrt(P0), n_particles)
    weights = np.full(n_particles, 1.0 / n_particles)
    total = 0.0
    for z in measurements:
        states = A * states + rng.normal(0, np.sqrt(Q), n_particles)
        with np.errstate(divide="ignore"):
            log_weights = np.log(weights) - 0.5 * (np.log(2 * np.pi * R) + (z - H * states) ** 2 / R)
        total += P.log_evidence_increment(log_weights)
        weights, _ = P.normalize_log(log_weights)
        if resample:
            states = rng.choice(states, size=n_particles, p=weights)
            weights = np.full(n_particles, 1.0 / n_particles)
    return total


def spread_and_error(n_particles, resample=True, seeds=range(8), steps=STEPS):
    exact = [kalman_log_likelihood(simulate(seed, steps)) for seed in seeds]
    estimated = [particle_log_likelihood(simulate(seed, steps), n_particles, seed, resample)
                 for seed in seeds]
    errors = np.array(estimated) - np.array(exact)
    return float(np.abs(errors.mean())), float(errors.std())


def test_estimate_approaches_the_exact_log_likelihood():
    few_bias, few_spread = spread_and_error(50)
    many_bias, many_spread = spread_and_error(4000)
    assert many_bias < few_bias
    assert many_spread < few_spread
    assert many_bias < 0.1, f"still {many_bias:.3f} away from the exact value with 4000 particles"


def test_estimate_does_not_depend_on_resampling():
    """Over a few steps, before the weights degenerate, resampling or not gives the same value."""
    resampling, _ = spread_and_error(4000, resample=True, steps=4)
    plain, _ = spread_and_error(4000, resample=False, steps=4)
    assert resampling < 0.1 and plain < 0.1


def test_degenerate_weights_need_far_more_particles():
    """Without resampling the estimator is still right but converges slowly: the gap only narrows."""
    few, _ = spread_and_error(200, resample=False)
    many, _ = spread_and_error(8000, resample=False)
    assert many < few


def test_collapsed_weights_give_no_evidence():
    assert P.log_evidence_increment(np.full(5, -np.inf)) == -np.inf


def test_metric_absent_when_the_proposal_does_not_support_it():
    log = RunLog(settings={"n_particles": 2})
    poses, weights = np.zeros((2, 3)), np.full(2, 0.5)
    for _ in range(3):
        log.record(true_pose=[0.0, 0.0, 0.0], poses=poses, weights=weights, ess_before=2.0,
                   resampled=False, unique_after=2, collapsed=False, step_time=0.0)
    assert not LogLikelihood().applies_to(log)

    log.record(true_pose=[0.0, 0.0, 0.0], poses=poses, weights=weights, ess_before=2.0,
               resampled=False, unique_after=2, collapsed=False, step_time=0.0, log_evidence=-1.5)
    assert LogLikelihood().applies_to(log)
