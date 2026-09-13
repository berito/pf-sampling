"""Best-fit 2D rigid alignment (rotation + translation), used by the ATE and aligned map error."""
import numpy as np


def fit_rigid_2d(source, target):
    """Rotation R and translation t minimizing ||R·source + t − target|| (Kabsch, no scaling). Points (N, 2)."""
    source_mean, target_mean = source.mean(axis=0), target.mean(axis=0)
    H = (source - source_mean).T @ (target - target_mean)
    U, _, Vt = np.linalg.svd(H)
    D = np.diag([1.0, np.sign(np.linalg.det(Vt.T @ U.T))])
    R = Vt.T @ D @ U.T
    return R, target_mean - R @ source_mean


def apply(R, t, points):
    return points @ R.T + t
