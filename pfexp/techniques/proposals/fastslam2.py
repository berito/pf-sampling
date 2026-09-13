"""FastSLAM 2.0 proposal: sample the pose from a Gaussian that also uses the landmark observations.

Borrowed from PythonRobotics SLAM/FastSLAM2/fast_slam2.py@1fe4fb9 (proposal_sampling and
update_with_observation; MIT licence). The models are in `pfexp.filters.fastslam_model`.

FIX (on by default; `upstream_bugs=True` reproduces upstream exactly). Upstream samples the pose from the
motion model, then for each observation moves it to a proposal mean, but never draws from the proposal,
never corrects the weight for it, and keeps the proposal covariance P across steps. That is not FastSLAM
2.0. The fixed version follows Montemerlo et al. (IJCAI 2003) with known data association:

  1. predict the pose mean with the noise-free motion model; its covariance is B R B^T from the control noise
  2. for each observed, already-mapped landmark: weight by the predictive likelihood
     N(z; z_hat, Hv S Hv^T + Hf Pf Hf^T + Q), then update the pose Gaussian (mean mu, covariance S):
     S = inv(Hv^T inv(Sf) Hv + inv(S)),  mu = mu + S Hv^T inv(Sf) (z - z_hat)
  3. sample the pose from N(mu, S)
  4. update the landmark EKFs (or add new landmarks) using the sampled pose
"""
import numpy as np

from pfexp.particles import ParticleSet, log_gaussian, sample_gaussian, wrap_angle
from pfexp.registry import register
from pfexp.techniques.base import Proposal
from pfexp.techniques.proposals.fastslam1 import copy_map

POSE_JITTER = 1e-6  # B R B^T has no sideways component; a tiny diagonal keeps S invertible


@register("proposal", "fastslam2")
class FastSlam2(Proposal):
    filter = "fastslam"

    def __init__(self, upstream_bugs=False):
        self.upstream_bugs = upstream_bugs

    def describe(self):
        return {"name": self.name, "upstream_bugs": self.upstream_bugs}

    def initialize(self, particles, model):
        if self.upstream_bugs:
            particles.extras["P"] = np.tile(np.eye(3), (len(particles), 1, 1))  # upstream Particle.P

    def propose(self, particles, control, observations, model, resampler):
        if self.upstream_bugs:
            return self._propose_upstream(particles, control, observations, model)

        extras = copy_map(particles.extras)
        with np.errstate(divide="ignore"):
            log_weights = np.log(particles.weights)
        B = model.control_jacobian(particles.poses)
        sigma = B @ model.R @ B.transpose(0, 2, 1) + POSE_JITTER * np.eye(3)
        mu = model.motion(particles.poses, control)

        for z in observations.T:
            known = ~model.is_new(extras, int(z[2]))
            if not known.any():
                continue
            landmark_id = int(z[2])
            xf, Pf = extras["lm"][known, landmark_id], extras["lmP"][known, landmark_id]
            zp, Hv, Hf, Sf = model.jacobians(mu[known], xf, Pf)
            dz = model.innovation(z, zp)
            Hvt = Hv.transpose(0, 2, 1)
            log_weights[known] += log_gaussian(dz, Hv @ sigma[known] @ Hvt + Sf)
            Sf_inv = np.linalg.inv(Sf)
            sigma_known = np.linalg.inv(Hvt @ Sf_inv @ Hv + np.linalg.inv(sigma[known]))
            mu[known] += (sigma_known @ Hvt @ Sf_inv @ dz[:, :, None])[:, :, 0]
            mu[known, 2] = wrap_angle(mu[known, 2])
            sigma[known] = sigma_known

        poses = sample_gaussian(mu, sigma)
        poses[:, 2] = wrap_angle(poses[:, 2])

        for z in observations.T:
            new = model.is_new(extras, int(z[2]))
            if new.any():
                model.add_landmark(poses, extras, z, new)
            if (~new).any():
                model.update_landmark(poses, extras, z, ~new)
        return ParticleSet(poses, particles.weights, extras), log_weights

    def _propose_upstream(self, particles, control, observations, model):
        """Upstream order: motion sample, then per observation weight, landmark update, move to proposal mean."""
        poses = model.predict_noisy(particles.poses, control)
        extras = copy_map(particles.extras)
        with np.errstate(divide="ignore"):
            log_weights = np.log(particles.weights)
        for z in observations.T:
            new = model.is_new(extras, int(z[2]))
            if new.any():
                model.add_landmark(poses, extras, z, new)
            known = ~new
            if not known.any():
                continue
            landmark_id = int(z[2])
            log_weights[known] += model.landmark_log_weight(poses, extras, z, known)
            model.update_landmark(poses, extras, z, known)
            xf, Pf = extras["lm"][known, landmark_id], extras["lmP"][known, landmark_id]
            zp, Hv, _, Sf = model.jacobians(poses[known], xf, Pf)
            dz = model.innovation(z, zp)
            Hvt = Hv.transpose(0, 2, 1)
            Sf_inv = np.linalg.inv(Sf)
            P = np.linalg.inv(Hvt @ Sf_inv @ Hv + np.linalg.inv(extras["P"][known]))
            extras["P"][known] = P
            poses[known] += (P @ Hvt @ Sf_inv @ dz[:, :, None])[:, :, 0]
        return ParticleSet(poses, particles.weights, extras), log_weights
