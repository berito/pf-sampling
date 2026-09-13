# Third-party code and data

This project does not ship any upstream code or datasets. `tools/fetch_vendors.py` clones the
repositories below into `vendor/` at pinned commits, and `tools/fetch_datasets.py` downloads the
datasets into `datasets/`. The pins and checksums live in [`vendors.yaml`](vendors.yaml) and
[`datasets.yaml`](datasets.yaml).

Upstream code is never edited. Our code either imports it unchanged through `pfexp/vendor.py`,
or copies a function into `pfexp/` with a header naming the source file, commit, licence and what we
changed. We only copy from the MIT-licensed repositories.

## Code

| Folder in `vendor/` | Upstream | Commit | Licence | How we use it |
|---|---|---|---|---|
| `particle_filter_tutorial/` | [jelfring/particle-filter-tutorial](https://github.com/jelfring/particle-filter-tutorial) | `e6014b7` | MIT | localization filters and the four resampling schemes, imported unchanged |
| `pythonrobotics/` | [AtsushiSakai/PythonRobotics](https://github.com/AtsushiSakai/PythonRobotics) (only `SLAM/FastSLAM1`, `SLAM/FastSLAM2`, `utils`) | `1fe4fb9` | MIT | FastSLAM 1.0 / 2.0 functions, copied into `pfexp/` because the scripts rely on module globals |
| `openslam_gmapping/` | [OpenSLAM-org/openslam_gmapping](https://github.com/OpenSLAM-org/openslam_gmapping) | `79ef0b0` | CC BY-NC-SA 2.0 | grid RBPF on real logs; built from a patched copy in `.build/`, never copied |

**Licence notes**
- gmapping is **non-commercial** (CC BY-NC-SA 2.0). `tools/patches/0001-gmapping-modern-toolchain-fixes.patch`
  is a diff of that code, so it carries the same licence.

### Borrowed functions

| Our file | Source | Changes |
|---|---|---|
| `pfexp/filters/mcl_model.py` | particle_filter_tutorial `core/particle_filters/particle_filter_base.py` (motion model, likelihood, cyclic world) | vectorized; log likelihood; **fix:** angle residual wrapped (switchable) |
| `pfexp/techniques/proposals/auxiliary.py` | particle_filter_tutorial `core/particle_filters/auxiliary_particle_filter.py` | vectorized; log weights; first-stage selection uses the configured resampler |
| `pfexp/techniques/proposals/extended_kalman.py` | particle_filter_tutorial `core/particle_filters/extended_kalman_particle_filter.py` | vectorized; log weights; resampling left to the experiment; **fixes:** matrix product in covariance prediction, variances instead of std, wrapped angles, prior centred on the prediction, stable angle Jacobian (all switchable with `upstream_bugs`) |
| `pfexp/filters/fastslam_model.py` | PythonRobotics `SLAM/FastSLAM1/fast_slam1.py` (motion model, prediction, landmark EKF, weights) | vectorized; log weights; arrays instead of particle objects; **fix:** "new landmark" test uses a seen flag instead of `abs(x) <= 0.01` (switchable) |
| `pfexp/techniques/proposals/fastslam1.py` | PythonRobotics `SLAM/FastSLAM1/fast_slam1.py` (`update_with_observation`) | vectorized; resampling left to the experiment (upstream resampling shared particle state between copies) |
| `pfexp/techniques/proposals/fastslam2.py` | PythonRobotics `SLAM/FastSLAM2/fast_slam2.py` (`proposal_sampling`, `update_with_observation`) | **fix:** upstream never samples from the proposal or corrects the weight for it; rewritten to follow Montemerlo et al. 2003 (upstream behaviour kept with `upstream_bugs`) |

Imported unchanged (not copied): the four resamplers (`core/resampling/resampler.py`), the three resampling
rules (`needs_resampling` of `ParticleFilterSIR`, `ParticleFilterNEPR`, `ParticleFilterMWR`), and the simulator
(`simulator/robot.py`, `simulator/world.py`) from particle_filter_tutorial; the FastSLAM scenario
(`calc_input`, `observation`, `motion_model`) from PythonRobotics.

## Data

| File in `datasets/` | Source | Credit |
|---|---|---|
| `carmen/intel.log.gz` | [Stachniss datasets page](http://www2.informatik.uni-freiburg.de/~stachnis/datasets.html) | Intel Research Lab, raw log provided by Dirk Hähnel |
| `carmen/aces_publicb.log.gz` | [Stachniss datasets page](http://www2.informatik.uni-freiburg.de/~stachnis/datasets.html) | ACES3 building, Austin, raw log provided by Patrick Beeson |

The same files are linked from the [IPB Bonn datasets page](https://www.ipb.uni-bonn.de/datasets/).

## Notes on the upstream code

- **particle_filter_tutorial** is the companion to Elfring, Torta & van de Molengraft, *Particle
  Filters: A Hands-On Tutorial*, Sensors 21(2):438, 2021. Besides the four resampling schemes it has
  ESS-based and max-weight resampling triggers, KLD and sample-likelihood adaptive filters, an
  auxiliary particle filter and an extended Kalman particle filter. Its demos save figures into the
  working directory, so don't run them from inside `vendor/`.
- **PythonRobotics FastSLAM** scripts set `show_animation = True`, and particle count, noise and
  simulation time are module globals.
- **gmapping** does not build with a current toolchain as-is (see `tools/README.md`). It writes
  `rawpath.dat` and one `w-NNN.dat` per particle into its working directory, so run it from an
  output folder.
- None of the upstream code computes trajectory error against ground truth, and none implements
  resample-move or an unscented proposal.
