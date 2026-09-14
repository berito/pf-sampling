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
- Noticed the public repo included the private `docs/` folder; the repo was made private, and cleaning `docs/` out of the history is noted before it goes public.

### Report
- Added milestone M7 for the LaTeX report, to be written at the end.
- Created the report structure: main file, one file per section, references, and a `make` build.
- Added LaTeX to the container image, placed so adding Python libraries stays fast.
- Made the report read experiment tables and figures directly from `results/`, with a red placeholder until they exist.
- Built the empty report, and a test version with the quick E01 results to confirm the table and figure appear.
- Switched figures to a white background so they print cleanly in the report.

### Teach and share
- Added milestone M8: a personal blog article explaining particle filters and sampling techniques, to follow the report.

### Running the rest without Claude
- Added a milestone checker: for each milestone it shows what is done, what is missing, and the next command.
- Added a Makefile with short commands that work on the host and inside the container.
- Wrote the experiment configs E01–E06; E01 and E03 now have a localization part and a SLAM part.
- Made the runner skip experiments that cannot run yet (like E05 before its plug-in exists), with the reason.
- Added gmapping as a filter so the real-data sweep (E06) runs, resumes and reports like the other experiments.
- Fixed the sweep figures (particle counts were plotted as text) and a crash with more than eight variants.
- Made the report always rebuild, list missing results, and preview with the quick results.
- Stopped the automatic findings from judging noise when there is only one seed.
- Wrote the guides experiments/README.md and report/README.md; pointed README.md at them.
- Added tests for the configs, the skipping, the sweeps, the gmapping output and the checker (110 tests pass).

### Keeping agent tooling out of the shared code
- Moved the milestone checker and its tests to a private folder, `docs/project/agent/`, since only Claude uses them.
- Moved `CLAUDE.md` to `.claude/`, to be left out when the code is shared.
- Removed milestone wording from the experiment configs, guides, Makefile and tests.
- Replaced `make check` with `make status`, which shows the runs done and to do for each experiment.
- Made the private checker also confirm that no shared file mentions private material.
- Checked every product file for traces of how we work; removed a reference to a private note and a mention of Claude.
- Wrote a private list of every working file and tool, with where it lives and how to share the product without them.
- Moved all of Claude's tools into `.claude/tools/`, so one folder can be untracked; `docs/` keeps only your notes.
- Deleted the early grid-SLAM exploration script, its upstream repo and OpenCV, since nothing uses them.
- Replaced typographic characters (long dashes, arrows, maths symbols) with plain text in the project files.
- Removed wording that tells the history of the work from project files; that belongs in commit messages.
- Tested a clean copy without the private folders in a new container: setup, tests, quick run and report all worked. M3 done.
- Tested the project on the shared server: image built without buildx from a temporary Dockerfile copy; setup, 108 tests, quick run of every experiment and the report all worked.
- Added background runs (make start / running / log / stop) that keep going after VS Code or the terminal is closed; VS Code no longer stops the container when closed; tested on the shared server.
- Added numbered result sets per experiment (redo replaces a wrong set, new keeps the earlier one, use picks the one the report shows); tests, guides and the report macros updated.
- Ran E01–E04 in the background on the shared server (1,120 runs, result set 001); all reports built; waiting for the results review.
- Fixed the extended Kalman proposal at the world's edge, made findings compare like with like, switched reports to median NEES, explained resampler runtimes in the report, and redid E01–E04.
- Added milestone M9 (wider coverage: when to resample in FastSLAM, resamplers with FastSLAM 2.0, SLAM proposals, crossed combinations) to the plan and the milestone checker.
- Renumbered the milestones by importance: resample-move, wider coverage, report, optional gmapping check, blog.
- Restructured the plan into phases that each end in a complete report; saved the rule; the milestone checker reports by phase; later-phase experiments removed from the report until their phase.
- Wrote the full report (v1) for E01-E04, removed conversational text from the stored results, and made the report tables and figures readable; Phase 1 is waiting for the user's review.
- Added a clickable DOI, arXiv or URL link to every reference in the report (each checked against its paper) and cited PythonRobotics.
- Phase 1 closed after the user's review; report v1 is the deliverable.
