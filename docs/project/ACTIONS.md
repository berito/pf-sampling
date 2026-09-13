# Actions

Every major step taken on the project, one line each, oldest first. Details are in TASKS.md.

## 2026-09-13

### Setup
- Started a dev container from the existing `pf-slam:dev` image and checked the Python libraries work.
- Moved the four upstream code repos from `code/` into `vendor/`.
- Found gmapping had been edited in place, saved the edits as a patch, and restored the original code.
- Restored the other upstream repos to their original state (removed cache files and a stray image).
- Moved our own scripts and the gmapping patch into `tools/`.
- Changed the gmapping build to copy the code into a build folder and patch the copy, not the original.
- Built gmapping and ran it on the Intel dataset to confirm it still works.
- Stopped Python from writing cache files into the upstream code.
- Removed files gmapping had written into the project root, and made it run from its own output folder.
- Renamed `build/` to `.build/` (safe to delete) and `data/` to `datasets/`.
- Set up `.gitignore`: generated files ignored; `vendor/`, `datasets/`, `docs/` listed but commented out until sharing.
- Made `results/` tracked in git so experiments can continue on another computer.

### Shareable structure
- Moved private material (study notes, papers, plans, proposal) into `docs/` and fixed all links.
- Wrote `vendors.yaml` and a script that downloads the upstream code at the exact versions we use.
- Checked a fresh download is identical to the existing upstream code.
- Traced the CARMEN datasets to their original source and confirmed the files are byte-identical.
- Wrote `datasets.yaml` and a script that downloads the datasets and checks their checksums.
- Added `src/pfexp/vendor.py`, the single place our code reaches upstream code and datasets.
- Wrote `THIRD_PARTY.md` with upstream repos, licences and dataset credits.
- Made the container's first start download the upstream code and datasets, then build gmapping.
- Tested sharing: copied the project without private or downloaded files, rebuilt it from scratch, ran it.
- Wrote a short public `README.md` (objective, how to run, credits).
- Added `CLAUDE.md` with the project rules for future Claude sessions.

### Existing code made experiment-ready
- Added pytest and pyyaml to the container.
- Ran the upstream demos unchanged with a fixed seed and saved the results as a baseline.
- Checked the baseline runs give identical results when repeated.
- Read the upstream filter code and listed the bugs that would distort comparisons.
- Decided (with the user) to copy the affected code, fix the bugs, and keep each fix switchable.
- Built the plug-in registry, so techniques are looked up by name and found automatically.
- Defined the run log: what every filter records at every step.
- Wrapped the four upstream resampling schemes as plug-ins without changing them.
- Wrapped the three upstream "when to resample" rules as plug-ins without changing them.
- Built shared simulated worlds, so every technique sees the same data for the same seed.
- Copied the localization motion and measurement models, sped them up, and fixed the angle wrap bug.
- Checked the copied likelihood and motion model match the upstream functions exactly.
- Copied the auxiliary particle filter as a proposal plug-in.
- Copied the extended Kalman particle filter as a proposal plug-in and fixed five bugs in it.
- Checked a full extended Kalman PF step matches the upstream one when the bugs are switched back on.
- Found the fixed extended Kalman PF is more accurate but needs about 300 particles instead of 100.
- Built the FastSLAM world with the upstream simulation functions.
- Checked the Gaussian random draws come out in the same order as upstream, so predictions match exactly.
- Copied the FastSLAM models and fixed the "new landmark" bug.
- Added FastSLAM 1.0 as a proposal plug-in.
- Rewrote FastSLAM 2.0 so it actually samples from its proposal (upstream never did).
- Checked the FastSLAM 1.0 and 2.0 updates match upstream exactly with the bugs switched back on.
- Checked FastSLAM 2.0 beats 1.0 on map and path error, averaged over several seeds.
- Added the metrics as plug-ins: RMSE, ATE, map error, ESS, degeneracy, NEES, runtime.
- Added a test that runs every registered plug-in automatically.
- Added a test that no shared code refers to `docs/`.
- Wrote the guide for adding a sampling technique and tested it by adding a dummy one.
- Reordered the Docker image so adding a library rebuilds in seconds (tested: 4.8 s instead of minutes).
- Started this action log.

### Experiment pipeline
- Planned `show_results.py` so a lecturer can see the results with plain Python, and added it to M3.
- Wrote the experiment config format: one YAML file per question, expanded into individual runs.
- Gave every run a stable ID from its settings and seed, so the same run is recognised on any computer.
- Built the runner: runs in parallel, skips runs that are already stored, saves each run safely.
- Checked that rerunning an experiment skips everything already done.
- Checked the colour palette with the colour-blind validator and fixed a colour per technique.
- Built the analysis: tables, figures, automatic findings and a summary per experiment.
- Looked at the figures and fixed overlapping labels.
- Made each run record the real computer name instead of the container's ID.
- Limited "stale result" warnings to code that can actually change results.
- Stopped tracking the small quick reruns in git.
- Added `compare.py` to put results from different experiments side by side.
- Tested resuming for real: stopped an experiment halfway, reran it, and only the missing runs ran.
- Made an interrupted run exit with a short message instead of an error dump.
- Wrote `show_results.py`: prints each experiment's summary and writes one report page with all figures.
- Checked `show_results.py` works with plain Python 3 outside the container, with no libraries at all.
- Made `--quick` explain how to use the container instead of crashing on a machine without the setup.
- Added tests for the config, the runner, resuming, the analysis and `show_results.py`.
- Added "See the results" to the top of the README.
- Found cache files in the upstream code written by a local Python 3.10 (likely the editor's test discovery), not the container.
- Made the project package switch off cache writing itself, so any Python leaves the upstream code clean.
- Added a test that fails if any upstream repo has local changes.

### Own repository
- Renamed the project to `pf-sampling` and moved it to `~/Documents/code_base/learning/pf-sampling`.
- Renamed the container path, image and container to match (`/workspaces/pf-sampling`, `pf-sampling:dev`, `pf-sampling-dev`).
- Rebuilt the image and gmapping for the new path and reran every check: tests, upstream code, datasets, gmapping.
- Moved the Python package from `src/pfexp/` to `pfexp/` so it runs without any fixed path setting.
- Changed the gmapping build so its programs find their libraries relative to themselves, not by a fixed path.
- Tested a copy of the project in a different folder at a different container path, without rebuilding: everything worked.
- Stopped git from adding the upstream repos to the new repo (`vendor/` ignored; `fetch_vendors.py` recreates it).
