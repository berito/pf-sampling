"""Motion and measurement models for localization.

Borrowed from particle_filter_tutorial/core/particle_filters/particle_filter_base.py@e6014b7
(Elfring, Torta, van de Molengraft; MIT licence).

Changes:
- Vectorized over all particles (the upstream functions handle one particle at a time).
  Noise is drawn per particle in the same distributions, but in array order, so random draws
  don't line up one-to-one with the upstream loop.
- Log likelihood instead of likelihood, to avoid underflow with many landmarks, including the
  normalizing constant of the Gaussian. Upstream leaves it out, which does not change the weights
  because they are normalized, but it makes likelihoods computed with different `measurement_std`
  incomparable, and the marginal likelihood then grows without bound as the assumed noise grows.
- FIX (optional, on by default): the angle residual is wrapped to [-pi, pi). Upstream compares raw
  angles, so a small error across ±pi looks like ~2pi.
  `wrap_angle_residual=False` reproduces the upstream behaviour exactly.
"""
from dataclasses import dataclass

import numpy as np

from pfexp.particles import wrap_angle


@dataclass
class LocalizationModel:
    size: np.ndarray                  # (2,) cyclic world size
    landmarks: np.ndarray             # (L, 2)
    process_std: tuple                # (forward, turn) the filter assumes
    measurement_std: tuple            # (range, angle) the filter assumes
    wrap_angle_residual: bool = True

    def validate(self, poses):
        """Cyclic world in x, y; heading in [-pi, pi). Upstream: ParticleFilter.validate_state."""
        poses = poses.copy()
        poses[:, 0] %= self.size[0]
        poses[:, 1] %= self.size[1]
        poses[:, 2] = wrap_angle(poses[:, 2])
        return poses

    def initial_uniform(self, n):
        """Upstream: ParticleFilter.initialize_particles_uniform."""
        poses = np.column_stack([
            np.random.uniform(0, self.size[0], n),
            np.random.uniform(0, self.size[1], n),
            np.random.uniform(0, 2 * np.pi, n),
        ])
        return self.validate(poses)

    def initial_gaussian(self, n, mean, spread):
        """Upstream: ParticleFilter.initialize_particles_gaussian, with one standard deviation per dimension."""
        return self.validate(np.asarray(mean, dtype=float) + np.random.randn(n, 3) * np.asarray(spread, dtype=float))

    def propagate(self, poses, control, noise=True):
        """Rotate, then move forward along the new heading. Upstream: ParticleFilter.propagate_sample."""
        forward, turn = control
        n = len(poses)
        poses = poses.copy()
        if noise:
            poses[:, 2] += np.random.normal(turn, self.process_std[1], n)
            distance = np.random.normal(forward, self.process_std[0], n)
        else:
            poses[:, 2] += turn
            distance = np.full(n, forward)
        poses[:, 0] += distance * np.cos(poses[:, 2])
        poses[:, 1] += distance * np.sin(poses[:, 2])
        return self.validate(poses)

    def expected_measurements(self, poses):
        """Range and angle of each landmark as seen from each pose: (N, L, 2)."""
        dx = poses[:, None, 0] - self.landmarks[None, :, 0]
        dy = poses[:, None, 1] - self.landmarks[None, :, 1]
        return np.stack([np.hypot(dx, dy), np.arctan2(dy, dx)], axis=-1)

    def log_likelihood(self, poses, measurement):
        """log p(z | pose) for each pose. Upstream: ParticleFilter.compute_likelihood (unnormalized)."""
        measurement = np.asarray(measurement)
        residual = self.expected_measurements(poses) - measurement[None]
        if self.wrap_angle_residual:
            residual[..., 1] = wrap_angle(residual[..., 1])
        std = np.asarray(self.measurement_std)
        normalizer = len(measurement) * (np.log(std).sum() + np.log(2 * np.pi))
        return -0.5 * np.sum((residual / std) ** 2, axis=(1, 2)) - normalizer
