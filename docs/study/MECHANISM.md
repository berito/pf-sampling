# Particle Filter — Mechanism & What It Provides
### (your understanding — fill each section in your own words as you read)

> **This is a study note — the content is yours.** Below are only *guiding questions* +
> section headings to structure your understanding. Answer them from your reading (Thrun
> *Probabilistic Robotics* Ch.4, Doucet/Arulampalam tutorials, Koller & Friedman Ch.12).
> Aim: be able to explain each unaided, and code it later without looking it up.

---

## 1. What it is (one paragraph)
- What problem does the particle filter solve? What is a "particle"?
- *(fill in)*

## 2. The core loop — sample → weight → resample
For each step: *what happens*, *the equation*, *the intuition*, *why it's there*.
- **Predict / sample** (propagate each particle through the motion model / proposal). Equation? Why sample from the proposal and not the posterior directly?
- **Weight** (importance weights from the measurement likelihood). Where does the weight formula come from (importance sampling)?
- **Resample** (draw N new particles ∝ weight). *Why* is resampling needed (degeneracy / weight collapse)? What does it cost (sample impoverishment)?
- *(fill in each)*

## 3. What it provides that KF/EKF/UKF do not
- What class of beliefs can it represent that Gaussian filters can't? (multi-modal, non-Gaussian, nonlinear)
- Concrete SLAM/localization cases where this matters (global localization, kidnapped robot)?
- *(fill in)*

## 4. The proposal distribution — the crux
- Why is the choice of proposal the most important design decision?
- Motion-model proposal vs measurement-informed proposal — what changes, and why does the better proposal need fewer particles? (this is the FastSLAM 1 → 2 story)
- *(fill in)*

## 5. Resampling schemes & degeneracy
- Effective sample size (ESS) — what it measures, when to resample.
- Multinomial vs stratified vs systematic — differences.
- *(fill in)*

## 6. Rao-Blackwellization (the SLAM-critical trick)
- State the factorization `p(x₁:ₜ, m | z, u) = p(x₁:ₜ | z,u) · ∏ₖ p(mₖ | x₁:ₜ, z)` and explain *why it holds* (conditional independence of the map given the trajectory).
- What do you sample, what do you solve analytically? Why does this beat sampling the whole state?
- *(fill in)*

## 7. Assumptions & failure modes
- Curse of dimensionality — why you can't PF a full high-dim state directly (→ RBPF).
- Particle depletion, impoverishment, compute cost, tuning.
- *(fill in)*

## 8. The PGM view (the project's spine)
- The PF as **approximate inference in a Dynamic Bayesian Network**. Draw the DBN.
- Which Koller & Friedman machinery is this? (importance sampling / MCMC — Ch.12; temporal models — Ch.15). How does the **discrete-first** book map onto the **continuous** PF?
- *(fill in)*

## 9. Open questions to resolve (carry into the survey + sampling phase)
- *(list the things still fuzzy after the reading — these drive PAPERS.md and the experiments.)*

---

### Self-check (you understand the PF when you can, unaided)
1. Walk the sample → weight → resample loop and write the importance-weight expression.
2. Explain why resampling exists and what it costs.
3. Say what the PF provides over EKF/UKF and at what price.
4. Derive the Rao-Blackwellized factorization and explain the conditional independence.
5. Explain FastSLAM 1 vs 2 as a *proposal* difference.
6. Place the PF as approximate inference in a DBN (the PGM view).
