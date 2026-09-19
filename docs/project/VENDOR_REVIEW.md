# Review of the upstream filter code

Read on 2026-09-13 before wrapping the filters for experiments (M2). `vendor/` stays untouched;
this lists what the upstream code actually does, and where it would bias a comparison.

## particle_filter_tutorial (Elfring) — `e6014b7`

**Works as expected**
- Four resamplers (`core/resampling/resampler.py`) take `[[weight, state], ...]` and return new
  `[[1/N, copy_of_state], ...]`. Whatever sits in the state slot is copied, so passing particle
  indices there turns them into index resamplers without changing anything.
- When to resample is a subclass hook: `ParticleFilterSIR.needs_resampling()` (always),
  `ParticleFilterNEPR` (ESS < threshold), `ParticleFilterMWR` (1/max weight < threshold).
- Resampling statistics reproduce the textbook ordering (baseline `elfring_resampling_algorithms`):
  offspring-count std multinomial > residual > stratified ≈ systematic.
- All randomness goes through the global `np.random`, so seeding it makes runs reproducible.

**Problems that matter for experiments**
1. **Angle residual not wrapped** — `ParticleFilter.compute_likelihood` uses `expected_angle - measured_angle`
   directly. Near ±π a small error looks like ~2π, and the particle gets almost zero weight.
2. **Extended Kalman particle filter** (`extended_kalman_particle_filter.py`):
   - `cov_ekf = F * cov_ekf * np.transpose(F) + self.Q` is element-wise, not a matrix product.
   - `Q` and `R` are built from standard deviations, not variances.
   - Angle innovation not wrapped.
   - Resampling is hardcoded (multinomial, every step), so it can't take part in resampling comparisons.
   - `updated_state_ekf = propagated_state` binds the same list, so the EKF update overwrites the prediction and
     the prior `N(x - propagated_state, Q)` ends up centred on the updated state instead of the prediction.
   - The angle Jacobian uses `dy/dx` forms that divide by zero when dx = 0.
3. **Auxiliary particle filter** hardcodes multinomial first-stage sampling.
4. `ParticleFilter.__init__` sets `y_min, y_max` from the x limits (harmless for the square demo worlds).
5. Systematic/stratified loops `while Q[m] < u` can run past the end if the cumulative sum ends slightly
   below 1 through rounding (weights are normalized first, so this is rare).

## PythonRobotics FastSLAM — `1fe4fb9`

**Problems that matter for experiments**
1. **Resampling corrupts particles.** `tmp_particles = particles[:]` copies the list, not the particles, and
   the loop then overwrites `particles[i]` while still reading `tmp_particles[indexes[i]]` — the same objects.
   `lm[:, :]` is a numpy view, so landmark arrays also end up shared between particles.
2. **FastSLAM 2.0 does not sample from its proposal.** `proposal_sampling` moves the particle to the proposal
   mean but never draws a sample from `N(mean, P)`, doesn't correct the weight for the proposal, and never
   resets `particle.P`. It is closer to a per-particle EKF update than to FastSLAM 2.0. The resampling step also
   doesn't copy `P`.
3. Heading average in `calc_final_state` is a plain weighted mean of angles (breaks near ±π).
4. A landmark counts as "new" when `abs(lm_x) <= 0.01`, so a landmark estimated at x ≈ 0 is re-initialised.
5. `update_landmark` in FS1 uses the global `Q` instead of its `Q_cov` argument (same value, harmless).
6. Resampling is hardcoded (systematic-style, ESS < N/1.5).

## Observations after borrowing (2026-09-13)

- All borrowed localization code was checked against the vendor functions with the fixes switched off:
  likelihood and noise-free motion match exactly, and one full extended Kalman PF update matches the vendor
  update (poses, covariances, weights) when both use the Gaussian mean instead of a random draw.
- **Extended Kalman PF, fixed vs upstream**, running-example world, uniform start, last-10-step position error
  over filter seeds 1–5: upstream bugs at 100 particles ≈ 0.14 m on every seed; fixed at 100 particles
  0.07–1.16 m (locks onto a wrong pose on some seeds, ESS stays at 1–5); fixed at 300 particles ≈ 0.06 m on
  every seed. The upstream bug (std used as variance) inflates the motion noise, which makes the filter robust
  but less accurate. Worth a sentence in the report: proposal quality and particle count trade off.

- **FastSLAM:** prediction matches the vendor byte for byte with the same seed (vectorized draws come out of the
  generator in the same order). FS1 and FS2 observation updates with `upstream_bugs=True` match the vendor
  `update_with_observation` over two steps: weights, landmark means and covariances, FS2 poses and P.
- **FS1 vs fixed FS2**, upstream scenario, 3 worlds × 4 filter seeds: landmark error 1.00 → 0.78 m (50
  particles) and 0.81 → 0.59 m (500); map shape error (offset removed) 0.63 → 0.50 and 0.50 → 0.34 m; pose RMSE
  0.84 → 0.66 and 0.77 → 0.52 m; ESS/N 0.75 → 0.79. Single runs vary a lot because map and path drift together
  (absolute frame only anchored at the start; upstream filter noise is large: range std 3 m, control std 1 m/s).

## Consequence

Comparing these implementations as they are would mostly measure the bugs: FS1 vs FS2 in particular would not
compare a motion proposal with a measurement-informed one. Both repos are MIT, so the affected functions can be
copied into `pfexp/` and corrected, with every change listed in the file header and in THIRD_PARTY.md.
