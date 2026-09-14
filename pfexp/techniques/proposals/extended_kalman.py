"""Extended Kalman particle filter proposal for localization: a measurement-informed proposal.

Borrowed from particle_filter_tutorial/core/particle_filters/extended_kalman_particle_filter.py@e6014b7
(Elfring et al.; MIT licence).

Each particle carries an EKF covariance. The EKF prediction and a sequential update over the landmark
measurements give a Gaussian per particle; the new pose is sampled from it and weighted by
likelihood * prior / proposal.

Differences from upstream: vectorized over particles; log weights; previous weights are carried over (upstream
resamples every step, so its weights are always uniform); resampling is left to the experiment's trigger and
resampler.

Corrections (all on by default; `upstream_bugs=True` reproduces the upstream behaviour):
1. Covariance prediction uses the matrix product F P F^T (upstream: element-wise `F * P * F.T`).
2. Q and R are built from variances (upstream: standard deviations).
3. Angle innovation and angle differences in the prior are wrapped to [-pi, pi).
4. The prior is centred on the prediction (upstream aliases the predicted state list and updates it in
   place, so its prior is centred on the EKF-updated state).
5. The measurement Jacobian of the angle uses -dy/r^2, dx/r^2 (upstream: dy/dx forms that divide by zero
   at dx = 0).
6. Position differences in the prior and proposal densities are wrapped to the cyclic world. A pose sampled
   just across the world's edge is moved to the other side by `validate`; unwrapped, it looks a world-width
   away from its prediction and gets an arbitrarily large weight (upstream compares the raw differences).
"""
import numpy as np

from pfexp.particles import log_gaussian, sample_gaussian, wrap_angle
from pfexp.registry import register
from pfexp.techniques.base import Proposal


@register("proposal", "extended_kalman")
class ExtendedKalman(Proposal):
    filter = "mcl"

    def __init__(self, upstream_bugs=False):
        self.upstream_bugs = upstream_bugs

    def describe(self):
        return {"name": self.name, "upstream_bugs": self.upstream_bugs}

    def initialize(self, particles, model):
        particles.extras["cov"] = np.tile(np.eye(3), (len(particles), 1, 1))  # upstream: np.eye(3)

    def sample(self, mean, cov):
        """Draw one pose per particle from N(mean, cov)."""
        return sample_gaussian(mean, cov)

    def propose(self, particles, control, measurement, model, resampler):
        bugs = self.upstream_bugs
        forward, turn = control
        process_std, measurement_std = np.asarray(model.process_std), np.asarray(model.measurement_std)
        Q = np.diag(np.array([process_std[0], process_std[0], process_std[1]]) ** (1 if bugs else 2))
        R = np.diag(measurement_std ** (1 if bugs else 2))

        # EKF prediction with the noise-free motion model
        predicted = particles.poses.copy()
        predicted[:, 2] += turn
        predicted[:, 0] += forward * np.cos(predicted[:, 2])
        predicted[:, 1] += forward * np.sin(predicted[:, 2])
        predicted = model.validate(predicted)

        F = np.tile(np.eye(3), (len(predicted), 1, 1))
        F[:, 0, 2] = -forward * np.sin(predicted[:, 2])
        F[:, 1, 2] = forward * np.cos(predicted[:, 2])
        cov = particles.extras["cov"]
        Ft = F.transpose(0, 2, 1)
        cov = (F * cov * Ft if bugs else F @ cov @ Ft) + Q

        # EKF update, one landmark at a time
        state = predicted.copy()
        identity = np.eye(3)
        for landmark, z in zip(model.landmarks, np.asarray(measurement)):
            dx = state[:, 0] - landmark[0]
            dy = state[:, 1] - landmark[1]
            r2 = dx * dx + dy * dy
            r = np.sqrt(r2)
            H = np.zeros((len(state), 2, 3))
            H[:, 0, 0], H[:, 0, 1] = dx / r, dy / r
            if bugs:
                H[:, 1, 0] = 1 / (1 + (dy / dx) ** 2) * -dy / dx ** 2
                H[:, 1, 1] = 1 / (1 + (dy / dx) ** 2) * 1 / dx
            else:
                H[:, 1, 0], H[:, 1, 1] = -dy / r2, dx / r2
            innovation = np.column_stack([z[0] - r, z[1] - np.arctan2(dy, dx)])
            if not bugs:
                innovation[:, 1] = wrap_angle(innovation[:, 1])
            Ht = H.transpose(0, 2, 1)
            S = H @ cov @ Ht + R
            K = cov @ Ht @ np.linalg.pinv(S)
            state = model.validate(state + (K @ innovation[:, :, None])[:, :, 0])
            cov = (identity - K @ H) @ cov

        # Sample from the per-particle Gaussian and weight
        poses = model.validate(self.sample(state, cov))
        prior_diff = poses - (state if bugs else predicted)
        proposal_diff = poses - state
        if not bugs:
            size = np.asarray(model.size, dtype=float)
            for diff in (prior_diff, proposal_diff):
                diff[:, :2] = (diff[:, :2] + size / 2) % size - size / 2
                diff[:, 2] = wrap_angle(diff[:, 2])
        with np.errstate(divide="ignore"):
            log_weights = (np.log(particles.weights)
                           + model.log_likelihood(poses, measurement)
                           + log_gaussian(prior_diff, Q)
                           - log_gaussian(proposal_diff, cov))
        return particles.with_poses(poses, cov=cov), log_weights
