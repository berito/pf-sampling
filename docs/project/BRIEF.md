# PGM Course Project — Particle Filters as Continuous-Space PGM Inference
### (with particle-filter SLAM — FastSLAM / gmapping — as the testbed)

> **Type:** course project, treated as a **mini-thesis** (understand an area properly → real implementation + experiments as the output).
> **Created:** 2026-08-09.
> **One-liner:** *Koller & Friedman treat inference in **discrete** space; the particle filter is the PGM tool for **continuous, non-Gaussian** inference. This project understands the PF from the PGM perspective in continuous space, uses particle-filter SLAM as the concrete testbed, and experiments with proposals / samplers / sparsity.*

---

## 1. Objective & priorities
**Intellectual goal:** understand the **particle filter as approximate PGM inference in continuous state space** — bridging the PGM course's **discrete-first** treatment (Bayes nets → variable elimination → junction tree, Gaussian nets as a special case) to the **continuous, non-Gaussian** setting where SLAM lives — and **experiment with sampling techniques**, reporting the results.

> ### ⭐ HIGHEST PRIORITY & SCOPE GUARDRAIL — re-read before every work session
> **The one required goal: showcase understanding of PGM concepts**, delivered as **sampling-technique experiments + results + a well-written report.** The grade lives here — nothing else does.
>
> **The rule:** *achieve the required goal FULLY first, then extend.* Every extension below (differentiable PF · Gazebo/camera/real demos) is **bonus, time-boxed, and abandonable.** The failure mode to avoid — the whole reason this box exists — is *starting an unbounded extension, running out of time, and missing even the basic course requirement.* **If any extension threatens the core deliverable, stop it and ship the core.**
>
> **Definition of done for the required goal (hit this BEFORE any extension):** C1–C4 done — PF/RBPF runs · the resampling schemes + proposals compared with metrics · and the report clearly derives **SLAM-as-a-DBN + Rao-Blackwellization** (the actual PGM content being showcased).

**Personal stretch (only if time remains — progressive realism, in order):** increasingly realistic SLAM demos — **Gazebo + LiDAR → Gazebo + camera → real mobile camera + IMU**. See §7 Roadmap.

**Success = I can:** (a) frame SLAM as a graphical model and derive the PF as approximate inference on it; (b) explain *why* the PF fits continuous, non-Gaussian/multi-modal beliefs; (c) **show experimentally how sampling choices (proposal / resampling / advanced samplers) change accuracy, degeneracy, and cost** — and write it up clearly.

## 2. Why this is a PGM project (the graphical-model content — foreground this)
1. **SLAM as a Dynamic Bayesian Network (DBN)** — states over time + controls + observations + map. → KF **Ch.6** (template/temporal models) + **Ch.15** (inference in temporal models).
2. **Rao-Blackwellization = exploiting conditional independence** — given the full trajectory, map features are conditionally independent:
   `p(x₁:ₜ, m | z, u) = p(x₁:ₜ | z, u) · ∏ₖ p(mₖ | x₁:ₜ, z)`.
   → sample the trajectory (particles), solve the rest analytically (a small Gaussian per feature). *This factorization is the whole reason FastSLAM scales — and it is a pure graphical-model statement.*
3. **Sampling = approximate inference** — importance sampling, MCMC, proposal distributions → KF **Ch.12** (particle-based approximate inference) + **Ch.11** (inference as optimization / variational, for contrast).
4. **Discrete → continuous** — the explicit bridge this project is *about*: how the discrete-PGM inference machinery re-expresses itself in continuous space.

## 3. The testbed (application)
Particle-filter SLAM / localization families — all **Rao-Blackwellized particle filters (RBPF)**:
- **MCL / AMCL** — particle-filter *localization* in a known map (the minimal starting point).
- **FastSLAM 1.0** — RBPF SLAM, **motion-model proposal**.
- **FastSLAM 2.0** — RBPF SLAM, **measurement-informed proposal** (the key upgrade).
- **gmapping** — grid-map RBPF with an **improved proposal + adaptive resampling**.

## 4. Experimental axes (the "mini-thesis" investigations — each = hypothesis + metric)
| Axis | What to vary | PGM angle |
|---|---|---|
| **Proposal distribution** | motion-only (FastSLAM1) → measurement-informed (FastSLAM2) → UKF-proposal (Unscented PF) | the proposal *is* the approximate-inference design choice |
| **Advanced sampling** | resample-move / **MCMC-within-SMC**, **Hamiltonian Monte Carlo (HMC)** gradient-informed moves, auxiliary PF, SMC samplers | connects continuous sampling theory to the filter |
| **Sparsity** | sparse information form (SEIF), sparse/factorized proposals, exploiting the RBPF factorization | the information matrix = the graph structure (bridge to the optimization side) |
| **Resampling & degeneracy** | ESS-triggered adaptive resampling, stratified vs systematic | particle degeneracy / weight collapse |
| **Learned / differentiable** *(extension — bonus, not core)* | learned proposals · **differentiable resampling** (Corenflos OT · NormFlow · DiffPF, §H/§E) | learned approximate inference — the modern frontier; still PGM-grounded, but heavier (needs training) |

## 5. Metrics (what the experiments measure)
Trajectory error (**ATE / RMSE**) · **effective sample size (ESS)** & degeneracy · consistency (**NEES**) · **runtime / particles needed** for a target accuracy.

## 6. Deliverables (the output)
1. **Writeup** — the DBN framing + Rao-Blackwellization derivation + discrete→continuous bridge + experiment results/plots. *(This is the "understanding" half — the graded PGM content.)*
2. **Code** — a small continuous-space PF/RBPF **testbed** where proposal / sampler / resampling are swappable modules.
3. **Results** — plots + tables comparing the axes above.

## 7. Roadmap — how far we go (priority-ordered)

### 🟢 CORE — graded, MUST complete (the whole grade lives here)
A lightweight PF/RBPF testbed + **sampling-technique experiments** + report. **No Gazebo or real robot needed** — a synthetic/simple 2D sim (à la the `jelfring` code) is enough. Build on existing code, don't write from scratch.
- **C1 — Minimal continuous-space PF** (MCL) on synthetic 2D range-bearing data. Sampling → weighting → resampling, visualized.
- **C2 — RBPF SLAM (FastSLAM 1.0)** — add the map (the Rao-Blackwellized factorization).
- **C3 — Sampling experiments** ⭐ *(the graded heart — see [`../study/SAMPLING.md`](../study/SAMPLING.md)):* compare the 4 resampling schemes + adaptive (ESS); proposal upgrades (motion → measurement-informed); ≥1 advanced sampler. Measure **ESS · degeneracy · RMSE · #particles · runtime**.
- **C4 — Report** ⭐ — DBN framing + Rao-Blackwellization derivation + discrete→continuous bridge + experiment results/plots. **This is the graded deliverable.**

### 🟡 STRETCH — experiment extensions (only after 🟢 CORE is shipped)
- **E1 — Differentiable / learned PF** *(the "new direction")*: learned proposals + **differentiable resampling** (§E papers — Corenflos OT · NormFlow · DiffPF). A natural continuation of the sampling story — *"can a learned proposal beat the hand-designed schemes from C3?"* Still PGM-grounded (learned approximate inference), but **heavier** (needs a differentiable framework + training) → strictly bonus, time-boxed.

### 🟡 STRETCH — demo stages (progressive realism, in order)
- **S1 — Gazebo + LiDAR:** build a **campus-like Gazebo world**, a **wheeled robot with a LiDAR**, run **FastSLAM / gmapping and variants** in sim.
- **S2 — Gazebo + camera:** *same world*, **swap LiDAR → camera**, do the **same SLAM** (visual PF-SLAM — see [`../study/PAPERS.md`](../study/PAPERS.md) §H).
- **S3 — Real demo (final stage):** **real mobile camera + IMU** (phone) — monocular-inertial PF-SLAM of the actual indoor square.

> **Discipline:** finish 🟢 **CORE (experiments + report) before touching 🟡 STRETCH.** The stretch stages are impressive but **ungraded** — they must not eat the core. Each stretch stage (S1→S2→S3) is independently shippable; stop whenever time runs out. S1–S3 also feed the `simulation_ros2_engineer` skill track (Gazebo/ROS2) — double duty.

## 8. Layout
The full layout (shareable code · fetched/generated · private `docs/`) is kept in
[`TASKS.md`](TASKS.md) → *Target layout*. Private material lives under `docs/`:
```
docs/
  project/   ← this brief · PLAN · PROPOSAL · proposal PDF · TASKS (milestones + task tracker)
  study/     ← ✅ literature + understanding (MECHANISM · PAPERS · SAMPLING · CODE)
  papers/    ← ✅ the paper corpus (43 PDFs) + the technique↔code↔experiment map
  report/    ← 🟢 CORE: the report (the graded deliverable)
```
*(🟡 STRETCH: a `sim/` folder for the Gazebo world + robot, if it happens.)*

## 9. Resources (⚠ seeded from model knowledge — verify author/year/venue before citing)
**PGM side (already have):** Koller & Friedman — **Ch.12** particle-based approximate inference · **Ch.15** temporal models · **Ch.6** template models · **Ch.7** Gaussian networks. Extracts in `../../books/KollerFriedman_extracts/`.
**Filter / SLAM side:**
- Thrun, Burgard, Fox — *Probabilistic Robotics* — Ch.4 (particle filters), Ch.8 (MCL), Ch.13 (FastSLAM). The primary. *(in `learning/BOOKS.md`.)*
- Montemerlo et al. — **FastSLAM 1.0** (AAAI 2002) · **FastSLAM 2.0** (IJCAI 2003).
- Grisetti, Stachniss, Burgard — **improved gmapping** (grid RBPF, improved proposal + adaptive resampling; IEEE T-RO 2007).
- Doucet & Johansen — *A Tutorial on Particle Filtering and Smoothing* (2009) — the SMC reference.
- Doucet, de Freitas, Gordon (eds.) — *Sequential Monte Carlo Methods in Practice* (2001).
**Sampling side:**
- Neal — *MCMC using Hamiltonian dynamics* (2011) — the HMC reference · Betancourt — *A Conceptual Introduction to HMC* (2017).
- Gilks & Berzuini — resample-move (MCMC-within-SMC).
- van der Merwe et al. — **the Unscented Particle Filter** (2000).

## 10. How it fits the rest of the system
- **Complements the thesis (no overlap):** thesis = the **optimization / MAP** side of SLAM-as-PGM-inference (factor graphs, robust PGO); this project = the **filter / particle** side. Same PGM lens, two halves.
- **`learning/slam_engineer/slam_theory/PGM_INFERENCE_SLAM_BRIDGE.md`** already maps the *optimization* side to KF chapters — this project is the *filter*-side counterpart.
- **`learning/slam_engineer/slam_theory/estimation_filters/STUDY_GUIDE.md`** — the filter-family ladder (Rung 5 PF, Rung 6 FastSLAM/MCL) this project builds on; **the "state on a manifold" card there** applies (rotations in the PF: sample in the tangent space, compose, Karcher mean).
- **`learning/foundations/maths/RESOURCES.md`** §4 (sampling/optimization) + §5 (SE(2)/SE(3) for the pose particles).
