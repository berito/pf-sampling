# Particle-Filter PGM Project — Working Plan

*My personal plan for this project: why it is worth doing for me, and the step-by-step of how to execute it and run the experiments. Separate from the TA-facing `PROPOSAL.md` and the `README.md` brief.*

> ## ⚠ Decision & guardrail — re-read before each session
> - **Scope: CORE only, time-boxed.** The project is required for the course, so do C1–C4 (PF/RBPF + sampling experiments + report) efficiently, building on existing code. Don't over-engineer.
> - **Thesis is primary (due 2026-09-30).** This project must not compete with it. The moment it starts eating thesis time, stop and ship the core.
> - **Stretch deferred.** Gazebo/camera/real demos and the differentiable / learned PF are deferred until after the thesis ships — if at all this term.
> - **Where the value is:** thesis-completion (the filter side of SLAM-as-inference) + coding practice + the required grade — not a standout portfolio piece.

---

## 1. Why this matters (for me)

This project is **required** for the PGM course, not optional. Since I have to do it anyway, the goal is to make that mandatory work pay off for several of my other goals at once, rather than spending the effort on just a grade:

- **Completes my command of SLAM as probabilistic inference.** My thesis is the optimization / MAP side (factor graphs, robust PGO); this is the filtering / particle side (RBPF, FastSLAM). Together they are the two halves of the same picture, so my SLAM expertise becomes complete rather than one-sided — and it strengthens the thesis's own "SLAM as inference" framing.
- **A portfolio piece.** A PF/RBPF SLAM testbed + experiments + a clean writeup is concrete, showable work: particle filters, FastSLAM/gmapping, sampling methods, and rigorous experiments with real metrics (ATE/RMSE, degeneracy). It reads well to SLAM/robotics employers and clients, and the visual runs make an easy demo.
- **Builds the saleable-SLAM skills I'm targeting.** The stretch stages (Gazebo + LiDAR → Gazebo + camera → real camera + IMU) are exactly the frontend / visual-SLAM + ROS2/Gazebo skills I need for paid work. The "bonus" doubles as career skill-building.
- **Closes my theory-strong / code-new gap.** I know the theory; implementing and adapting the testbed turns it into *done* (implemented) rather than *read*. Fast, concrete coding practice on something I already understand.
- **A writing + credibility artifact.** The report (DBN framing + Rao-Blackwellization + results) is a technical-writing sample, and practice for writing the thesis.
- **(Stretch) a frontier angle.** The differentiable / learned-PF extension touches ML + SLAM — distinctive if I get that far.

**One-liner:** thesis-deepening + portfolio demo + saleable-skill building + coding practice + writing sample, in one project.

---

## 2. Step-by-step plan — how to handle the project

> Rule: build on existing code (don't write from scratch); finish the CORE before any stretch. Steps are being detailed one at a time.

### Step 0 — Setup
*Goal: an existing PF-SLAM running on synthetic 2D data, visualized and committed — the baseline everything else builds on.*

- [ ] **0.1 Pick an existing PF/RBPF implementation to build on** — readable and runnable (e.g. the `jelfring` FastSLAM code named in the README, or another simple Python PF-SLAM repo). Not from scratch.
- [ ] **0.2 Reproducible Python environment** — a venv or conda env with numpy, scipy, matplotlib, plus whatever the chosen repo needs; pin the versions.
- [ ] **0.3 Data / simulator** — a synthetic 2D world: a moving robot and landmarks producing odometry + range-bearing observations. Usually the repo includes one; if not, a small generator.
- [ ] **0.4 Run it end to end once and visualize** — confirm the PF runs and you can see the particles, the estimated trajectory, and the map. This is the working baseline.
- [ ] **0.5 Project layout + git** — create `src/`, `data/`, `experiments/` (README §8) and put it under version control so experiments stay reproducible.

*Output: a known PF-SLAM running on synthetic data, visualized and committed.*

### Steps 1–6 (to detail next)
1. **Minimal particle filter (localization / MCL)** — sampling → weighting → resampling, visualized.
2. **RBPF SLAM (FastSLAM)** — add the map (the Rao-Blackwellized factorization).
3. **Make the sampling parts swappable** — proposal (motion-model vs measurement-informed) and resampling (fixed vs adaptive).
4. **Run the experiments** — vary one axis at a time; collect the metrics.
5. **Analyze** — plots + tables comparing the axes.
6. **Report** — DBN framing + Rao-Blackwellization + results (the graded deliverable).

*Stretch (only after the core ships):* Gazebo + LiDAR → Gazebo + camera → real camera + IMU; differentiable / learned PF.

---

## 3. How to run an experiment (method)

> *Proposed template — to refine together.*

- **Question** — state it (e.g. "does the measurement-informed proposal need fewer particles for the same accuracy?").
- **Vary one axis** — fix everything else, change only the proposal, or only the resampling.
- **Measure** — trajectory error (ATE / RMSE), effective sample size, particle degeneracy, number of particles, runtime.
- **Repeat** over several random seeds; plot; write down what it shows.

---

*Next: we detail Section 2 and Section 3 step by step.*
