"""Weighted particle sets and small helpers, shared by all filters, techniques and metrics."""
from dataclasses import dataclass, field, replace

import numpy as np


@dataclass
class ParticleSet:
    poses: np.ndarray                              # (N, 3)
    weights: np.ndarray                            # (N,) normalized
    extras: dict = field(default_factory=dict)     # other per-particle arrays, e.g. landmark maps

    def __len__(self):
        return len(self.poses)

    def select(self, indices):
        """Copies of the particles at the given indices, with uniform weights (the result of resampling)."""
        return ParticleSet(
            poses=self.poses[indices].copy(),
            weights=np.full(len(indices), 1.0 / len(indices)),
            extras={key: value[indices].copy() for key, value in self.extras.items()},
        )

    def with_poses(self, poses, **extras):
        return replace(self, poses=poses, extras={**self.extras, **extras})

    def with_weights(self, weights):
        return replace(self, weights=weights)


def wrap_angle(angle):
    """Wrap angles to [-pi, pi)."""
    return (np.asarray(angle) + np.pi) % (2 * np.pi) - np.pi


def normalize(weights):
    """Normalize weights. If they all underflow to zero, return uniform weights and collapsed=True."""
    weights = np.asarray(weights, dtype=float)
    total = weights.sum()
    if not np.isfinite(total) or total <= 0.0:
        return np.full(len(weights), 1.0 / len(weights)), True
    return weights / total, False


def normalize_log(log_weights):
    """Normalize log weights without underflow. Returns weights and collapsed flag."""
    log_weights = np.asarray(log_weights, dtype=float)
    finite = np.isfinite(log_weights)
    if not finite.any():
        return np.full(len(log_weights), 1.0 / len(log_weights)), True
    shifted = np.where(finite, log_weights - log_weights[finite].max(), -np.inf)
    return normalize(np.exp(shifted))


def log_evidence_increment(log_weights):
    """log of the sum of the unnormalized weights: the incremental marginal likelihood p(z_t | z_1:t-1).

    It holds when a particle's unnormalized weight is its previous normalized weight times the likelihood
    of the new measurement, which is what a bootstrap proposal produces. Proposals that weight in two
    stages need a different estimator, so they report no evidence (see `Proposal.gives_marginal_likelihood`).
    """
    log_weights = np.asarray(log_weights, dtype=float)
    finite = np.isfinite(log_weights)
    if not finite.any():
        return -np.inf
    largest = log_weights[finite].max()
    return float(largest + np.log(np.exp(log_weights[finite] - largest).sum()))


def effective_sample_size(weights):
    """ESS = 1 / sum(w_i^2) for normalized weights."""
    weights = np.asarray(weights, dtype=float)
    return 1.0 / np.sum(weights ** 2)


def weighted_pose_mean(poses, weights):
    """Weighted mean of (x, y, heading) poses; heading uses the circular mean."""
    poses = np.asarray(poses, dtype=float)
    x = weights @ poses[:, 0]
    y = weights @ poses[:, 1]
    heading = np.arctan2(weights @ np.sin(poses[:, 2]), weights @ np.cos(poses[:, 2]))
    return np.array([x, y, heading])


def weighted_pose_cov(poses, weights, mean=None):
    """Weighted covariance of (x, y, heading) poses, with heading differences wrapped."""
    poses = np.asarray(poses, dtype=float)
    if mean is None:
        mean = weighted_pose_mean(poses, weights)
    diff = poses - mean
    diff[:, 2] = wrap_angle(diff[:, 2])
    return (weights[:, None] * diff).T @ diff


def sample_gaussian(mean, cov):
    """One draw per row from N(mean, cov): mean (N, d), cov (N, d, d). Tolerates singular covariances."""
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    root = eigenvectors * np.sqrt(np.clip(eigenvalues, 0, None))[:, None, :]
    return mean + (root @ np.random.randn(*mean.shape, 1))[:, :, 0]


def log_gaussian(diff, cov):
    """log N(diff; 0, cov) per row: diff (N, d), cov (d, d) or (N, d, d)."""
    cov = np.broadcast_to(cov, (len(diff),) + np.shape(cov)[-2:])
    solved = np.linalg.solve(cov, diff[:, :, None])[:, :, 0]
    _, logdet = np.linalg.slogdet(cov)
    return -0.5 * (np.sum(diff * solved, axis=1) + logdet + diff.shape[1] * np.log(2 * np.pi))
