"""Motion model, landmark EKF and weights for FastSLAM with known data association.

Borrowed from PythonRobotics SLAM/FastSLAM1/fast_slam1.py and SLAM/FastSLAM2/fast_slam2.py@1fe4fb9
(Atsushi Sakai and contributors; MIT licence): motion_model, predict_particles, add_new_landmark,
compute_jacobians, update_kf_with_cholesky, update_landmark, compute_weight.

Changes: vectorized over particles (one observation at a time, as upstream); log weights; particles are
arrays (poses, landmark means, landmark covariances) instead of objects. Random draws in
`predict_noisy` come out of the global generator in the same order as upstream, so with the same seed
the predicted poses are identical.

FIX (on by default; `upstream_bugs=True` reproduces upstream): a landmark was treated as new when its
x estimate was within 0.01 of zero, so a landmark estimated near x = 0 was re-initialised. A `seen` flag
per particle and landmark is used instead.
"""
from dataclasses import dataclass

import numpy as np

from pfexp.particles import wrap_angle


@dataclass
class SlamModel:
    Q: np.ndarray         # (2, 2) measurement covariance (range, bearing) the filter assumes
    R: np.ndarray         # (2, 2) control noise covariance (velocity, yaw rate) the filter assumes
    dt: float
    n_landmarks: int
    upstream_bugs: bool = False

    # --- motion ---------------------------------------------------------------------------
    def motion(self, poses, controls):
        """Upstream motion_model, for (N, 3) poses and (N, 2) or (2,) controls."""
        controls = np.broadcast_to(controls, (len(poses), 2))
        moved = poses.copy()
        moved[:, 0] += self.dt * np.cos(poses[:, 2]) * controls[:, 0]
        moved[:, 1] += self.dt * np.sin(poses[:, 2]) * controls[:, 0]
        moved[:, 2] = wrap_angle(poses[:, 2] + self.dt * controls[:, 1])
        return moved

    def control_jacobian(self, poses):
        """d motion / d control, (N, 3, 2)."""
        B = np.zeros((len(poses), 3, 2))
        B[:, 0, 0] = self.dt * np.cos(poses[:, 2])
        B[:, 1, 0] = self.dt * np.sin(poses[:, 2])
        B[:, 2, 1] = self.dt
        return B

    def predict_noisy(self, poses, control):
        """Upstream predict_particles: add control noise per particle, then move."""
        noise = np.random.randn(len(poses), 2) @ self.R ** 0.5
        return self.motion(poses, np.asarray(control)[None, :] + noise)

    # --- landmarks --------------------------------------------------------------------------
    def is_new(self, extras, landmark_id):
        if self.upstream_bugs:
            return np.abs(extras["lm"][:, landmark_id, 0]) <= 0.01
        return ~extras["seen"][:, landmark_id]

    def add_landmark(self, poses, extras, z, mask):
        """Upstream add_new_landmark for the particles in `mask`."""
        r, b, landmark_id = z[0], z[1], int(z[2])
        yaw = poses[mask, 2]
        s, c = np.sin(wrap_angle(yaw + b)), np.cos(wrap_angle(yaw + b))
        extras["lm"][mask, landmark_id, 0] = poses[mask, 0] + r * c
        extras["lm"][mask, landmark_id, 1] = poses[mask, 1] + r * s
        dx, dy = r * c, r * s
        d2 = dx ** 2 + dy ** 2
        d = np.sqrt(d2)
        Gz = np.zeros((mask.sum(), 2, 2))
        Gz[:, 0, 0], Gz[:, 0, 1] = dx / d, dy / d
        Gz[:, 1, 0], Gz[:, 1, 1] = -dy / d2, dx / d2
        Gz_inv = np.linalg.inv(Gz)
        extras["lmP"][mask, landmark_id] = Gz_inv @ self.Q @ np.linalg.inv(Gz.transpose(0, 2, 1))
        extras["seen"][mask, landmark_id] = True

    def jacobians(self, poses, xf, Pf):
        """Upstream compute_jacobians: predicted measurement zp (N, 2), Hv (N, 2, 3), Hf (N, 2, 2), Sf (N, 2, 2)."""
        dx = xf[:, 0] - poses[:, 0]
        dy = xf[:, 1] - poses[:, 1]
        d2 = dx ** 2 + dy ** 2
        d = np.sqrt(d2)
        zp = np.column_stack([d, wrap_angle(np.arctan2(dy, dx) - poses[:, 2])])
        Hv = np.zeros((len(poses), 2, 3))
        Hv[:, 0, 0], Hv[:, 0, 1] = -dx / d, -dy / d
        Hv[:, 1, 0], Hv[:, 1, 1], Hv[:, 1, 2] = dy / d2, -dx / d2, -1.0
        Hf = np.zeros((len(poses), 2, 2))
        Hf[:, 0, 0], Hf[:, 0, 1] = dx / d, dy / d
        Hf[:, 1, 0], Hf[:, 1, 1] = -dy / d2, dx / d2
        Sf = Hf @ Pf @ Hf.transpose(0, 2, 1) + self.Q
        return zp, Hv, Hf, Sf

    def innovation(self, z, zp):
        dz = z[None, 0:2] - zp
        dz[:, 1] = wrap_angle(dz[:, 1])
        return dz

    def landmark_log_weight(self, poses, extras, z, mask):
        """Upstream compute_weight (as a log) for the particles in `mask`."""
        landmark_id = int(z[2])
        xf, Pf = extras["lm"][mask, landmark_id], extras["lmP"][mask, landmark_id]
        zp, _, _, Sf = self.jacobians(poses[mask], xf, Pf)
        dz = self.innovation(z, zp)
        mahalanobis = np.einsum("ni,nij,nj->n", dz, np.linalg.inv(Sf), dz)
        return -0.5 * mahalanobis - np.log(2.0 * np.pi * np.sqrt(np.linalg.det(Sf)))

    def update_landmark(self, poses, extras, z, mask):
        """Upstream update_landmark + update_kf_with_cholesky for the particles in `mask`."""
        landmark_id = int(z[2])
        xf, Pf = extras["lm"][mask, landmark_id], extras["lmP"][mask, landmark_id]
        zp, _, Hf, _ = self.jacobians(poses[mask], xf, Pf)
        dz = self.innovation(z, zp)
        PHt = Pf @ Hf.transpose(0, 2, 1)
        S = Hf @ PHt + self.Q
        S = (S + S.transpose(0, 2, 1)) * 0.5
        s_chol = np.linalg.cholesky(S).transpose(0, 2, 1)
        s_chol_inv = np.linalg.inv(s_chol)
        W1 = PHt @ s_chol_inv
        W = W1 @ s_chol_inv.transpose(0, 2, 1)
        extras["lm"][mask, landmark_id] = xf + (W @ dz[:, :, None])[:, :, 0]
        extras["lmP"][mask, landmark_id] = Pf - W1 @ W1.transpose(0, 2, 1)


def empty_map(n_particles, n_landmarks):
    return {
        "lm": np.zeros((n_particles, n_landmarks, 2)),
        "lmP": np.zeros((n_particles, n_landmarks, 2, 2)),
        "seen": np.zeros((n_particles, n_landmarks), dtype=bool),
    }
