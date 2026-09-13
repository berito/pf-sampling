# SLAM-PF Paper Radar
### (the survey index — find → triage → read → note)

> **Status:** corpus downloaded & verified 2026-08-09 — **36 PDFs**, all now in [`../papers/`](../papers/) (see [`../papers/README.md`](../papers/README.md) for the layout); the 9 §H papers are in [`../papers/visual_pf_slam/`](../papers/visual_pf_slam/). Titles/authors/years verified during search. **Read** = ☐/✅ · **Note** = link to `notes/…` once written. Read the ⭐ ones deeply first.
>
> **Filename convention:** method paper → `<year>_<author>_<title>.pdf` · **survey** → `survey_<year>_…` · **tutorial** → `tutorial_<year>_…` (survey ≠ tutorial: a survey reviews the field, a tutorial teaches the method).
>
> **PF-SLAM limitations map (why section C exists):** FastSLAM's known problems are ① **particle depletion / impoverishment** (resampling kills diversity → over-confident, breaks loop closure), ② **needs many particles** (poor motion-only proposal), ③ **map representation** (landmark vs grid), ④ **curse of dimensionality**. Each section-C paper attacks one of these.

## A. PF / SMC foundations (the mechanism)
| Pri | Read | Paper | Authors | Year | What it adds | File |
|---|---|---|---|---|---|---|
| ⭐ | ☐ | Novel approach to nonlinear/non-Gaussian Bayesian state estimation (**bootstrap PF**) | Gordon, Salmond, Smith | 1993 | the original SIR particle filter | ✅ `1993_Gordon_BootstrapFilter.pdf` |
| ⭐ | ☐ | A Tutorial on Particle Filters for Online Nonlinear/Non-Gaussian Bayesian Tracking | Arulampalam, Maskell, Gordon, Clapp | 2002 | the standard PF tutorial | ✅ `tutorial_2002_Arulampalam_PF.pdf` |
| ⭐ | ☐ | A Tutorial on Particle Filtering and Smoothing: Fifteen Years Later | Doucet, Johansen | 2011 | the SMC reference (41 pp) | ✅ `tutorial_2011_Doucet_Johansen_PF.pdf` |
|  | ☐ | Rao-Blackwellised Particle Filtering for Dynamic Bayesian Networks | Doucet, de Freitas, Murphy, Russell | 2000 | **RBPF theory — the PGM root of FastSLAM** | ✅ `2000_Doucet_RBPF_DBN.pdf` |

## B. Particle-filter SLAM — the core line (the project's spine)
| Pri | Read | Paper | Authors | Year | What it adds | File |
|---|---|---|---|---|---|---|
| ⭐ | ☐ | **FastSLAM 1.0** — A Factored Solution to the SLAM Problem | Montemerlo, Thrun, Koller, Wegbreit | 2002 | RBPF SLAM; motion-model proposal | ✅ `2002_Montemerlo_FastSLAM1.pdf` |
| ⭐ | ☐ | **FastSLAM 2.0** — improved proposal, provably converges | Montemerlo, Thrun, Koller, Wegbreit | 2003 | measurement-informed proposal → far fewer particles | ✅ `2003_Montemerlo_FastSLAM2.pdf` |
| ⭐ | ☐ | **gmapping** — Improved Techniques for Grid Mapping with RBPF | Grisetti, Stachniss, Burgard | 2007 | improved proposal + adaptive resampling; grid maps | ✅ `2007_Grisetti_gmapping.pdf` |
|  | ☐ | Improving Grid-based SLAM with RBPF by Adaptive Proposals & Selective Resampling | Grisetti, Stachniss, Burgard | 2005 | the ICRA precursor to gmapping | ✅ `2005_Grisetti_AdaptiveProposals.pdf` |
|  | ☐ | Fast and Accurate SLAM with Rao-Blackwellized Particle Filters | Grisetti, Tipaldi, Stachniss, Burgard, Nardi | 2007 | consolidated journal treatment (method paper, not a survey) | ✅ `2007_Grisetti_FastAccurate_RBPF_SLAM.pdf` |

## C. Limitation-mitigation papers (PF-SLAM problems + fixes — the key set)
| Pri | Read | Paper | Authors | Year | Limitation it attacks | File |
|---|---|---|---|---|---|---|
| ⭐ | ☐ | **FastSLAM 2.0** (also in B) | Montemerlo et al. | 2003 | ② poor proposal → needs many particles | ✅ (see B) |
| ⭐ | ☐ | **Recovering Particle Diversity** in a RBPF for SLAM After Actively Closing Loops | Stachniss, Grisetti, Burgard | 2005 | ① **particle depletion** after loop closure | ✅ `2005_Stachniss_RecoveringParticleDiversity.pdf` |
|  | ☐ | gmapping — adaptive resampling (also in B) | Grisetti et al. | 2007 | ① depletion (ESS-triggered resampling) + ② proposal | ✅ (see B) |
|  | ☐ | **DP-SLAM** — Fast, Robust SLAM Without Predetermined Landmarks | Eliazar, Parr | 2003 | ③ **map representation** (dense occupancy, no landmarks; particle-ancestry tree) | ✅ `2003_Eliazar_DP-SLAM.pdf` |
|  | ☐ | **DP-SLAM 2.0** | Eliazar, Parr | 2004 | ③ + efficiency (hierarchical map, better data structures) | ✅ `2004_Eliazar_DP-SLAM2.pdf` |
|  | ☐ | **Unscented FastSLAM** — A Robust and Efficient Solution | Kim, Sakthivel, Chung | 2008 | ② proposal quality (UKF proposal, no Jacobians) | ⚠ **manual — IEEE-gated** (DOI 10.1109/TRO.2008.924946) |
|  | ☐ | **PF-Net** — Particle Filter Networks for Visual Localization | Karkus, Hsu, Lee | 2018 | learned, differentiable PF (modern mitigation) | ✅ `2018_Karkus_PF-Net.pdf` |
|  | ☐ | **Differentiable Particle Filters** — End-to-End Learning with Algorithmic Priors | Jonschkowski, Rastogi, Brock | 2018 | learned proposals/models; bridge to optimization side | ✅ `2018_Jonschkowski_Differentiable_Particle_Filters.pdf` |

## D. Sampling techniques (for the LATER sampling phase — not yet downloaded)
| Pri | Read | Paper | Authors | Year | What it adds | File |
|---|---|---|---|---|---|---|
|  | ☐ | The Unscented Particle Filter | van der Merwe, Doucet, de Freitas, Wan | 2000 | UKF-based proposal (general) | ☐ get when needed |
|  | ☐ | Resample-move / MCMC-within-SMC | Gilks, Berzuini | 2001 | MCMC moves to fight impoverishment | ☐ |
|  | ☐ | MCMC using Hamiltonian dynamics | Neal | 2011 | **HMC** — gradient-informed sampling | ☐ |
|  | ☐ | A Conceptual Introduction to Hamiltonian Monte Carlo | Betancourt | 2017 | HMC intuition | ☐ |

## E. Modern approaches (2018–2025) — the active frontier: learned / differentiable PF
> Classic PF-SLAM matured ~2010 (field moved to optimization); PF research shifted to **learned / differentiable particle filters** — end-to-end trainable proposals, models, and *differentiable resampling*. This is the "where it still exists today" section, and the **bridge to the optimization/thesis side** (differentiable optimization).

| Pri | Read | Paper | Authors | Year | What it adds | File |
|---|---|---|---|---|---|---|
| ⭐ | ☐ | Differentiable Particle Filters — End-to-End Learning with Algorithmic Priors | Jonschkowski, Rastogi, Brock | 2018 | the founding differentiable PF | ✅ `2018_Jonschkowski_Differentiable_Particle_Filters.pdf` |
| ⭐ | ☐ | PF-Net — Particle Filter Networks for Visual Localization | Karkus, Hsu, Lee | 2018 | learned PF for localization | ✅ `2018_Karkus_PF-Net.pdf` |
|  | ☐ | PFRNN — Particle Filter Recurrent Neural Networks | Ma, Karkus, Hsu, Lee | 2020 | particles inside an RNN latent state | ✅ `2020_Ma_PFRNN.pdf` |
| ⭐ | ☐ | **Differentiable Particle Filtering via Entropy-Regularized Optimal Transport** | Corenflos, Thornton, Deligiannidis, Doucet | 2021 | **differentiable resampling** (the hard part) via OT | ✅ `2021_Corenflos_OT_Resampling.pdf` |
|  | ☐ | How to Train Your Differentiable Filter | Kloss, Martius, Bohg | 2021 | practical training recipes for diff. filters | ✅ `2021_Kloss_TrainDifferentiableFilter.pdf` |
|  | ☐ | Differentiable Particle Filtering without Modifying the Forward Pass | Ścibior, Wood | 2021 | gradient estimator, unchanged forward pass | ✅ `2021_Scibior_DPF_NoForwardMod.pdf` |
|  | ☐ | Differentiable PF through Conditional Normalizing Flow | Chen, Wen, Li | 2021 | learned proposal via normalizing flows | ✅ `2021_Chen_CondNormFlow_DPF.pdf` |
|  | ☐ | Normalizing Flow-based Differentiable Particle Filters | Chen, Li | 2024 | flow-based diff. PF (journal) | ✅ `2024_Chen_NormFlow_DPF.pdf` |
|  | ☐ | Adversarial Transform Particle Filters | Gong, Lin, Zhang | 2025 | adversarially-learned transforms | ✅ `2025_Gong_AdversarialTransformPF.pdf` |
|  | ☐ | **DiffPF — Differentiable PF with Generative Sampling via Conditional Diffusion** | Wan, Zhao | 2026 | diffusion-model proposal (RA-L, newest) | ✅ `2026_Wan_DiffPF_Diffusion.pdf` |

## F. Recent PF-SLAM / MCL / manifold PF (2016–2024)
| Pri | Read | Paper | Authors | Year | What it adds | File |
|---|---|---|---|---|---|---|
|  | ☐ | **MegaParticles** — Range-based 6-DoF MCL with GPU Stein Particle Filter | Koide, Oishi, Yokozuka, Banno | 2024 | modern GPU MCL; Stein PF (recent SOTA localization) | ✅ `2024_Koide_MegaParticles_MCL.pdf` |
|  | ☐ | The Manifold Particle Filter (state estimation on implicit manifolds) | Klingensmith, Koval, Srinivasa, Pollard, Kaess | 2016 | **PF on manifolds** (rotation/SE(3) handling) — canonical | ✅ `2016_Klingensmith_ManifoldParticleFilter.pdf` |
|  | ☐ | Particle Filter SLAM for Vehicle Localization | Liu, Xu, Qiao, Jiang, Yu | 2024 | recent applied PF-SLAM *(⚠ low-tier venue)* | ✅ `2024_Liu_PF-SLAM_VehicleLocalization.pdf` |

## G. Surveys / tutorials / context
| Pri | Read | Paper | Authors | Year | What it adds | File |
|---|---|---|---|---|---|---|
| ⭐ | ☐ | **Particle Filters: A Hands-On Tutorial** | Elfring, Torta, van de Molengraft | 2021 | modern, practical PF tutorial (great starting read) | ✅ `tutorial_2021_Elfring_PF_HandsOn.pdf` |
|  | ☐ | An Overview of Differentiable Particle Filters (data-adaptive Bayesian inference) | Chen, Li | 2023 | **the survey of the modern diff-PF line** | ✅ `survey_2023_Chen_DiffPF_Overview.pdf` |

## H. Visual / Visual-Inertial PF-SLAM — 📁 `../papers/visual_pf_slam/` (the committed direction: mono camera + IMU)
> **RBPF-visual** = the particle-filter line with a *camera* as the sensor (visual features = landmarks). **Inverse-depth** papers are how bearing-only monocular landmarks get initialized — the key enabler for a plain phone camera. **EKF** papers are flagged: kept as *foundational context* (their inverse-depth init transfers directly to the PF version).

| Pri | Read | Paper | Authors | Year | Type | What it adds | File (`visual_pf_slam/`) |
|---|---|---|---|---|---|---|---|
| ⭐ | ☐ | **Scalable Monocular SLAM** | Eade, Drummond | 2006 | **PF** | **FastSLAM-style *monocular* SLAM — closest to the committed direction** | `2006_Eade_ScalableMonocularSLAM.pdf` |
| ⭐ | ☐ | **Higher-Order RBPF for Monocular vSLAM** | Farrokhsiar, Najjaran | 2010 | **PF** | monocular RBPF **+ inverse-depth init** — very on-target | `2010_Farrokhsiar_HigherOrderRBPF_vSLAM.pdf` |
| ⭐ | ☐ | **Stratified Particle Filter Monocular SLAM** | Słowak, Kaniewski | 2021 | **PF** | **recent** monocular PF with **stratified resampling** — direct sampling-experiment tie-in (§`SAMPLING.md`) | `2021_StratifiedPF_MonocularSLAM.pdf` |
| ⭐ | ☐ | Vision-based SLAM using the Rao-Blackwellised Particle Filter | Sim, Elinas, Griffin, Little | 2005 | **PF** | canonical RBPF-visual SLAM | `2005_Sim_VisionRBPF_SLAM.pdf` |
|  | ☐ | σSLAM: Stereo RBPF SLAM **with a novel mixture proposal** | Elinas, Sim, Little | 2006 | **PF** | RBPF + **novel proposal distribution** (→ sampling-experiment relevance) | `2006_Elinas_SigmaSLAM.pdf` |
|  | ☐ | Multi-robot Visual SLAM using a RBPF | Gil, Reinoso, Ballesta, Juliá | 2009 | **PF** | RBPF-visual, multi-robot | `2009_Gil_MultiRobotVisualRBPF.pdf` |
|  | ☐ | **Inverse Depth Parametrization for Monocular SLAM** | Civera, Davison, Montiel | 2008 | ⚠ EKF | **the inverse-depth landmark-init reference** (transfers to PF) | `2008_Civera_InverseDepth.pdf` |
|  | ☐ | Unified Inverse Depth Parametrization for Monocular SLAM | Montiel, Civera, Davison | 2006 | ⚠ EKF | the RSS precursor of inverse-depth init | `2006_Montiel_UnifiedInverseDepth.pdf` |
|  | ☐ | MonoSLAM: Real-Time Single Camera SLAM | Davison, Reid, Molton, Stasse | 2007 | ⚠ EKF | foundational monocular SLAM context | `2007_Davison_MonoSLAM.pdf` |

> **MDPI download tip** (for future MDPI papers): the `www.mdpi.com/…/pdf` endpoint is Cloudflare-blocked to `curl`, but the CDN serves the file directly — pattern: `https://res.mdpi.com/d_attachment/<journal>/<id>/article_deploy/<id>.pdf`.

---

### Reading order (suggested)
1. **Mechanism:** **Elfring hands-on tutorial (§G)** or Arulampalam → Doucet-Johansen (skim) → Gordon (the origin). Fill [`MECHANISM.md`](MECHANISM.md).
2. **RBPF theory:** Doucet RBPF-DBN (the factorization / PGM root).
3. **Core SLAM:** FastSLAM 1.0 → 2.0 (the proposal upgrade) → gmapping (adaptive resampling).
4. **Limitations:** Stachniss (depletion) → DP-SLAM 1/2 (map rep).
5. **Committed direction (§H — visual, mono+IMU):** Eade *Scalable Monocular SLAM* + Farrokhsiar *Higher-Order RBPF monocular* (the RBPF-visual core) → Civera *Inverse Depth* (how a plain camera initializes bearing-only landmarks) → Elinas *σSLAM* for the **mixture-proposal** idea (feeds [`SAMPLING.md`](SAMPLING.md)).
6. **Modern frontier (§E):** read the **Chen–Li overview (2023)** first for the map of the differentiable-PF line, then Jonschkowski/PF-Net (founding) → Corenflos (differentiable resampling) → the newest (NormFlow 2024, DiffPF 2026). This is the "still-active today" material + the bridge to the optimization/thesis side.
7. Defer **§D sampling techniques** (HMC/UPF/resample-move) to the sampling-experiment phase.

> **Notes:** all files (now in [`../papers/`](../papers/)) verified as real PDFs (2026-08-09). Doucet RBPF-DBN = author-posted arXiv version (1301.3853) of the UAI'00 paper. **Manifold PF (§F)** is 2016 but the canonical PF-on-manifolds reference (rotation handling). Liu 2024 PF-SLAM = low-tier venue (use with judgment). **Still manual:** Unscented FastSLAM (IEEE T-RO 2008, gated).
