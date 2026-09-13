# Sampling in the Particle Filter — taxonomy + experiment map
### (the likely experimental focus of the project)

> **Two different "sampling" mechanisms — don't conflate them:**
> **(A) the proposal distribution** = *where new particles are drawn* · **(B) resampling** = *how particles are redrawn ∝ weight*.
> Both are experiment knobs. The [`jelfring`](CODE.md) code already implements the four classic **(B)** schemes → it's the ready-made experiment base.

---

## (A) Proposal distribution — where particles are drawn
The PF is importance sampling over time; particles get weight `w ∝ p/q`. The spectrum is *how much of the current measurement you fold into the proposal `q`*:

| Proposal | `q` | Notes | Papers |
|---|---|---|---|
| **Prior / motion-model** (bootstrap) | `p(xₜ\|xₜ₋₁,uₜ)` | simplest; ignores the measurement when proposing → needs many particles | Gordon 1993 · FastSLAM 1.0 |
| **Optimal / measurement-informed** | `p(xₜ\|xₜ₋₁,zₜ)` | minimizes weight variance → far fewer particles; approximated by a Gaussian: | FastSLAM 2.0 · gmapping |
| ↳ EKF proposal | linearize | FastSLAM 2.0 | |
| ↳ scan-match proposal | Gaussian around likelihood peak | gmapping | |
| ↳ UKF/unscented proposal | sigma points, no Jacobians | Unscented PF / UFastSLAM | |
| **IMU-informed proposal** ⭐ | motion from IMU integration | **our mono+IMU setup** — the IMU gives a strong proposal → fewer particles | (visual-inertial PF-SLAM refs) |
| **Learned / neural proposal** | trained network / normalizing flow / diffusion | the modern frontier | §E papers (Chen NormFlow, Wan DiffPF…) |

## (B) Resampling — how particles are redrawn ∝ weight
Fights **degeneracy** (weight collapse). The four classic schemes (**all implemented in the jelfring repo**), lowest-variance last:

| Scheme | Idea | Variance |
|---|---|---|
| **Multinomial** | draw N indices independently ∝ weight | highest |
| **Residual** | deterministically keep ⌊N·wᵢ⌋ copies, sample the remainder | lower |
| **Stratified** | partition [0,1) into N strata, one draw per stratum | low |
| **Systematic** | one random offset, evenly spaced picks — O(N) | **lowest** (robotics default) |

**Adaptive resampling** — *not a scheme but a trigger*: only resample when **effective sample size** `ESS = 1/Σwᵢ²` drops below a threshold (e.g. N/2). Prevents needless diversity loss → the gmapping trick.

---

## The experiment plan (the "shift the sampling part" idea)
Baseline is free — jelfring gives the 4 resampling schemes. Build experiments on top:

**Tier 1 — characterize what exists (uses jelfring as-is):**
- Compare **multinomial vs residual vs stratified vs systematic** → measure **ESS over time · particle degeneracy · RMSE · #particles for a target accuracy · runtime**.
- Add **adaptive (ESS-triggered) resampling** → show it beats resample-every-step.

**Tier 2 — new sampling techniques (the "test new techniques" goal):**
- **Better proposals:** motion-only → **IMU-informed** (our setup) → measurement-informed (EKF/UKF). Show the particle-count reduction.
- **Auxiliary Particle Filter (APF)** — look one step ahead before resampling.
- **Regularized / kernel PF** — resample from a smoothed density to fight impoverishment.
- **Resample-move / MCMC-within-SMC** (Gilks–Berzuini) — MCMC moves after resampling to restore diversity.
- **HMC-informed proposals** (Neal) — gradient-based moves (needs a differentiable measurement model).
- **Learned / differentiable** proposals & **differentiable resampling** (Corenflos OT; NormFlow; DiffPF) — the modern angle.

**Metrics (define once, reuse):** ESS · degeneracy/impoverishment · trajectory RMSE/ATE · consistency (NEES) · #particles needed · wall-clock.

**Stress cases where sampling choice matters most:** loop closure (particle depletion — cf. Stachniss 2005) · high-outlier / aliased measurements · fast motion (weak proposal).

---

## Paper → technique map
Full mapping lives in [`PAPERS.md`](PAPERS.md) (§A–§G). Quick index:
- Resampling schemes + proposals explained: **Arulampalam tutorial**, **Doucet–Johansen tutorial**, **Elfring hands-on tutorial**.
- Measurement-informed proposal: **FastSLAM 2.0**, **gmapping**.
- Adaptive resampling: **gmapping**.
- Diversity recovery: **Stachniss 2005**.
- Modern learned/differentiable sampling: **§E** (Corenflos OT-resampling, Chen NormFlow, Wan DiffPF, …).

> **Code base:** [`jelfring/particle-filter-tutorial`](CODE.md) — the 4 resampling schemes live here; extend it for Tier-1/Tier-2 experiments. Cross-check against `rlabbe`/`filterpy`.
