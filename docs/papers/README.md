# Sampling techniques — paper ↔ code ↔ experiment map

Which sampling technique can actually be experimented on, which paper defines it, and which
codebase in [`../../vendor/`](../../vendor/) already implements it. Everything in the "code" column was
verified to build and run inside the devcontainer.

All 43 PDFs for this project live here. `study/` keeps the written analysis
([`PAPERS.md`](../study/PAPERS.md) is still the annotated reading index) but no longer holds
any PDFs.

| Folder | Papers | Contents |
|---|---:|---|
| `foundations/` | 5 | Gordon 1993, the RBPF-for-DBNs result, and the three PF/SMC tutorials |
| `proposals/` | 5 | FastSLAM 1.0 and 2.0, gmapping, the two Grisetti improved-proposal papers |
| `resampling/` | 2 | the four schemes: comparison (Douc & Cappé) and implementation (Hol et al.) |
| `advanced_sampling/` | 7 | auxiliary PF, KLD-sampling, HMC, diversity recovery, PF on manifolds |
| `rbpf_slam/` | 4 | DP-SLAM 1 and 2, MegaParticles MCL, PF-SLAM for vehicle localisation |
| `differentiable_pf/` | 11 | the learned/differentiable-PF line, including Corenflos OT-resampling (stretch goal) |
| `visual_pf_slam/` | 9 | §H of `study/PAPERS.md` — monocular + IMU visual PF-SLAM (stretch goal) |

The sections below map the first four folders onto the code and the experiments. `rbpf_slam/`,
`differentiable_pf/` and `visual_pf_slam/` are background and stretch-goal reading; they are
indexed in [`../study/PAPERS.md`](../study/PAPERS.md).

---

## A. Proposal distribution — where particles are drawn

| Technique | Paper | Location | Code that implements it | Experiment |
|---|---|---|---|---|
| Prior / motion-model (bootstrap) | Gordon, Salmond & Smith 1993 | `foundations/1993_Gordon_BootstrapFilter.pdf` | `particle_filter_tutorial/core/particle_filters/particle_filter_sir.py`; `pythonrobotics/SLAM/FastSLAM1` | baseline for every proposal comparison |
| Measurement-informed, EKF linearisation | Montemerlo et al. 2003 (FastSLAM 2.0) | `proposals/2003_Montemerlo_FastSLAM2.pdf` | `pythonrobotics/SLAM/FastSLAM2`; `particle_filter_tutorial/.../extended_kalman_particle_filter.py` | particles needed for a target RMSE, FastSLAM 1 vs 2 |
| Scan-match proposal + adaptive resampling | Grisetti, Stachniss & Burgard 2007 | `proposals/2007_Grisetti_gmapping.pdf` | `openslam_gmapping` → `bin/gfs_nogui` | vary `-particles`, `-resampleThreshold` on the Intel/ACES logs |
| Adaptive proposal, selective resampling | Grisetti et al. 2005 | `proposals/2005_Grisetti_AdaptiveProposals.pdf` | same binary, different flags | selective vs every-step resampling |
| Same method, journal write-up (fuller derivation) | Grisetti, Stachniss & Burgard 2007 | `proposals/2007_Grisetti_FastAccurate_RBPF_SLAM.pdf` | same binary | background reading for the report |
| UKF / unscented proposal | van der Merwe, Doucet, de Freitas & Wan 2000 | **not obtained** (see below) | not implemented — would extend the EKF-proposal filter | sigma-point vs EKF proposal |
| Learned / neural proposal | Chen 2021/2024; Wan 2026 | `differentiable_pf/` (11 papers) | none (stretch goal) | bonus only |

## B. Resampling schemes — how particles are redrawn ∝ weight

| Scheme | Paper | Location | Code | Experiment |
|---|---|---|---|---|
| Multinomial · Residual · Stratified · Systematic | Douc & Cappé 2005 (comparison) | `resampling/2005_Douc_Cappe_ResamplingSchemes.pdf` | `particle_filter_tutorial/core/resampling/resampler.py` — all four | variance of the number of offspring; RMSE; runtime |
| Implementation and cost of the four schemes | Hol, Schön & Gustafsson 2006 | `resampling/2006_Hol_Schon_Gustafsson_ResamplingAlgorithms.pdf` | same | O(N) systematic vs O(N log N) multinomial |
| Grid RBPF resampling (multinomial, hardcoded) | — | — | `grid_rbpf_python/ParticleFilter.py::Resampling` | drop-in replacement target: swap in the four schemes |

`particle_filter_tutorial/challenge1_compare_resampling_algorithms.py` already prints the mean
and standard deviation of the offspring count per scheme, which is Douc & Cappé's central
comparison. Upstream repos and licences: [`../../THIRD_PARTY.md`](../../THIRD_PARTY.md).

## C. When to resample — adaptive triggers

| Trigger | Paper | Location | Code | Experiment |
|---|---|---|---|---|
| Effective sample size `ESS = 1/Σwᵢ²` | Liu & Chen 1998 | **not obtained** | `particle_filter_tutorial/.../particle_filter_nepr.py`; gmapping `-resampleThreshold` | ESS-triggered vs every-step resampling |
| Reciprocal of max weight | Elfring, Torta & van de Molengraft 2021 | `foundations/tutorial_2021_Elfring_PF_HandsOn.pdf` | `particle_filter_tutorial/.../particle_filter_max_weight_resampling.py` | alternative trigger vs ESS |
| KLD-sampling (adapt N on the fly) | Fox 2001 (NIPS) and 2003 (IJRR) | `advanced_sampling/2001_Fox_KLD_Sampling.pdf`, `2003_Fox_KLD_AdaptingSampleSize.pdf` | `particle_filter_tutorial/.../adaptive_particle_filter_kld.py` | particles used over time vs fixed N |
| Diversity loss / recovery | Stachniss et al. 2005 | `advanced_sampling/2005_Stachniss_RecoveringParticleDiversity.pdf` | gmapping | particle depletion at loop closure |

`.build/openslam_gmapping/bin/gfs2neff` extracts the ESS trace directly from a gmapping run,
so the ESS experiment needs no new instrumentation on the C++ side.

## D. Advanced samplers

| Technique | Paper | Location | Code | Experiment |
|---|---|---|---|---|
| Auxiliary particle filter | Pitt & Shephard 1999 | `advanced_sampling/1999_Pitt_Shephard_AuxiliaryPF.pdf` | `particle_filter_tutorial/.../auxiliary_particle_filter.py` | APF vs SIR under outlier-heavy measurements |
| Hamiltonian Monte Carlo moves | Neal 2011; Betancourt 2017 | `advanced_sampling/2011_Neal_HMC.pdf`, `2017_Betancourt_HMC_Conceptual.pdf` | none — needs a differentiable measurement model | gradient-informed moves |
| Resample-move (MCMC-within-SMC) | Gilks & Berzuini 2001 | **not obtained** | none — would extend the SIR filter | diversity restored after resampling |
| Regularised / kernel PF | Musso, Oudjane & Le Gland 2001 | **not obtained** | none | impoverishment (cf. `challenge2_impoverishment.py`) |

## E. Foundations and tutorials

| Paper | Location |
|---|---|
| Arulampalam et al. 2002 — PF tutorial | `foundations/tutorial_2002_Arulampalam_PF.pdf` |
| Doucet & Johansen 2011 — SMC tutorial | `foundations/tutorial_2011_Doucet_Johansen_PF.pdf` |
| Elfring et al. 2021 — hands-on tutorial (companion to the jelfring code) | `foundations/tutorial_2021_Elfring_PF_HandsOn.pdf` |
| Doucet et al. 2000 — RBPF for DBNs (the Rao-Blackwellisation result) | `foundations/2000_Doucet_RBPF_DBN.pdf` |
| Montemerlo et al. 2002 — FastSLAM 1.0 | `proposals/2002_Montemerlo_FastSLAM1.pdf` |

---

## Not obtained — paywalled, fetch through the university library

These have no open-access version. Each is listed with its DOI.

| Paper | Venue | DOI |
|---|---|---|
| Liu & Chen 1998, *Sequential Monte Carlo Methods for Dynamic Systems* | JASA 93(443) | 10.1080/01621459.1998.10473765 |
| Kitagawa 1996, *Monte Carlo Filter and Smoother for Non-Gaussian Nonlinear State Space Models* | J. Comp. Graph. Stat. 5(1) | 10.1080/10618600.1996.10474692 |
| Gilks & Berzuini 2001, *Following a Moving Target* | JRSS-B 63(1) | 10.1111/1467-9868.00280 |
| Musso, Oudjane & Le Gland 2001, *Improving Regularised Particle Filters* | in *SMC Methods in Practice*, Springer | 10.1007/978-1-4757-3437-9_12 |
| Li, Bolić & Djurić 2015, *Resampling Methods for Particle Filtering* | IEEE Signal Proc. Mag. 32(3) | 10.1109/MSP.2014.2330626 |
| Doucet, Godsill & Andrieu 2000, *On sequential MC sampling methods for Bayesian filtering* | Statistics and Computing 10(3) | 10.1023/A:1008935410038 |
| van der Merwe, Doucet, de Freitas & Wan 2000, *The Unscented Particle Filter* | Cambridge TR CUED/F-INFENG/TR 380 (also NIPS 13) | — |

Only the first two matter for the core experiments (ESS thresholding and systematic
resampling), and both techniques are already implemented in the code, so the papers are needed
for citation rather than for implementation.
