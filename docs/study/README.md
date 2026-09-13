# Study & Survey — Particle Filters (the understand-first phase)

> **Phase 0 of the project — before any coding.** Goal: *really* understand the particle
> filter this time (mechanism + what it provides), and survey the papers written on the
> **SLAM side** of it — so the later sampling-experiments + code rest on real understanding,
> not a rough pass.
>
> **Order:** ① understand the mechanism → ② survey the SLAM-PF papers → ③ *(later)* sampling
> techniques → ④ *(later)* experiments + coding. This folder covers ① and ②.

## What's here
| File | Purpose |
|---|---|
| [`MECHANISM.md`](MECHANISM.md) | **Your understanding** of how the PF works + what it provides. A scaffold of guiding questions — fill it from your reading (this is *your* content, not generated). |
| [`PAPERS.md`](PAPERS.md) | The **SLAM-PF paper radar** — index of papers to find, read, and place. Seeded with canonical anchors (⚠ verify); expand via search. |
| [`CODE.md`](CODE.md) | **Reference code bases** to learn from (won't build from scratch) — Elfring PF-tutorial code, rlabbe/`filterpy`, Orocos BFL. |
| [`SAMPLING.md`](SAMPLING.md) | **The sampling axis** (likely experiment focus) — proposal + resampling taxonomy, the 4 schemes in the jelfring code, and the Tier-1/Tier-2 experiment plan. |
| [`../papers/`](../papers/) | the paper corpus — all PDFs live there, indexed by [`../papers/README.md`](../papers/README.md) |
| `notes/` | one short note per paper as you read it (create when you start reading) |

## How to work this phase
1. **Mechanism first** ([`MECHANISM.md`](MECHANISM.md)) — answer the guiding questions in your own words. Don't move on until sample → weight → resample and *why resampling exists* are solid. Pairs with the filter ladder in `learning/slam_engineer/slam_theory/estimation_filters/STUDY_GUIDE.md` (Rung 5–6).
2. **Then the papers** ([`PAPERS.md`](PAPERS.md)) — populate the radar (search), triage by relevance, read the core few deeply, one short note each in `notes/`.
3. **Capture the PGM lens throughout** — PF = approximate inference (sampling) in a DBN; the course is discrete-first, SLAM is continuous. That contrast is the project's spine.

## Definition of done for this phase
- `MECHANISM.md` answers all its guiding questions unaided.
- `PAPERS.md` has the core SLAM-PF line mapped (FastSLAM 1→2→gmapping + the SMC foundations), with the 4–6 must-reads read + noted.
- You can state, in one paragraph, *what the particle filter provides that EKF/UKF cannot, and at what cost* — and how Rao-Blackwellization makes it work for SLAM.

> Then → sampling techniques (HMC / MCMC-move / UPF …) and the coding milestones in the project [`../project/BRIEF.md`](../project/BRIEF.md).
