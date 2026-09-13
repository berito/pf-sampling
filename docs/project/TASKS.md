# Tasks — Particle-Filter PGM Project

Status: [ ] todo · [~] in progress · [x] done · [-] dropped

This file lives in `docs/project/`; all paths below are relative to the project root.
A plain one-line-per-step record of what was done is in `ACTIONS.md` next to this file.

Rules:
- `vendor/` is never edited. Anything we need is imported from `vendor/` unchanged, or copied into `pfexp/`
  with a `Borrowed from <repo>/<file>@<commit>; licence; changes: ...` header. Copy only from MIT repos.
- Vendor code is never shipped: it is fetched by `tools/fetch_vendors.py` at pinned commits.
- Our code never imports from `docs/` — deleting `docs/` must not break anything.
- Sampling techniques are plug-ins: adding one = one new file, no edits elsewhere.
- Commits are made by the user, not by Claude.
- `results/` is tracked in git: experiments resume on any computer — finished runs are skipped, only missing runs execute.

## Milestones

| # | Milestone | Done when | Status |
|---|---|---|---|
| M0 | **Setup complete** | vendor code clean in `vendor/`, our tools separate, gmapping builds in the container | [x] |
| M1 | **Shareable project structure** | private material in `docs/`; vendors + datasets fetched by script; a copy without `docs/`, `vendor/`, `datasets/` rebuilds and runs | [x] |
| M2 | **Existing code experiment-ready (plug-ins)** | localization + borrowed FastSLAM run headless, seeded, with techniques and metrics as registered plug-ins | [x] |
| M3 | **Experiment pipeline + analysis ready** | an experiment YAML produces runs.csv, traces, tables, figures and summary.md; `python3 show_results.py` shows everything with no install | [~] |
| M4 | **Core experiments done** | E01–E04: resampling scheme, when to resample, proposal, particle count | [ ] |
| M5 | **New sampler added** | resample-move implemented as a plug-in and compared against M4 | [ ] |
| M6 | *(optional)* **Real-data check** | gmapping ESS sweep on the CARMEN logs | [ ] |

## Open decisions
- *(none)*

## Working environment
All code runs inside the devcontainer (image `pf-sampling:dev`); nothing is installed on the host.
- Start:  `docker run -d --name pf-sampling-dev --user $(id -u):$(id -g) -e PFEXP_HOST=$(hostname) -v "$PWD":/workspaces/pf-sampling -w /workspaces/pf-sampling pf-sampling:dev sleep infinity`
- Run:    `docker exec pf-sampling-dev <command>`
- `PYTHONDONTWRITEBYTECODE=1` is set in the Dockerfile, so Python never writes `__pycache__` into `vendor/`.
- Vendor demos and gmapping write files into their working directory — run them from `results/`, never from the root or `vendor/`.
- New Python dependency → add it to `.devcontainer/requirements.txt` (light, rebuilds in seconds); heavy stable ones live in
  `requirements-base.txt`. New system tool → a separate RUN line after the base apt layer. Never `pip install` on the host.

## Target layout
```
pf-sampling/
│  ── SHAREABLE ──
├─ README.md            public: what it is, quickstart, how to add a technique
├─ THIRD_PARTY.md       vendor repos, licences, borrowed functions
├─ vendors.yaml         name, URL, pinned commit, sparse paths, licence
├─ datasets.yaml        name, URL, checksum
├─ .devcontainer/
├─ tools/               fetch_vendors.py · fetch_datasets.py · build_gmapping.sh · patches/
├─ pfexp/           registry · techniques/ · filters/ · worlds · metrics/ · runner · analysis/
├─ experiments/         E01…E04 YAML configs
├─ tests/
│  ── FETCHED / GENERATED (delete freely, recreatable) ──
├─ vendor/              ← tools/fetch_vendors.py     (gitignore entry commented out until sharing)
├─ datasets/            ← tools/fetch_datasets.py    (gitignore entry commented out until sharing)
├─ .build/              ← tools/build_gmapping.sh    (gitignored)
├─ results/             ← experiment runs            (TRACKED — resumable across computers)
│  ── PRIVATE (tracked for now, removed before sharing) ──
└─ docs/
   ├─ project/          BRIEF.md · PLAN.md · PROPOSAL.md · proposal PDF · TASKS.md
   ├─ study/            MECHANISM · SAMPLING · PAPERS · CODE · notes/
   ├─ papers/           PDFs + technique↔paper map
   └─ report/           the write-up (later)
```

---

## M0 — Setup complete
- [x] 0.0 Start the pf-sampling-dev container; confirm python/numpy/scipy versions and that the project is mounted
- [x] 0.1 Move the four upstream repos from `code/` to `vendor/` (flattened: `vendor/particle_filter_tutorial`,
      `vendor/pythonrobotics`, `vendor/openslam_gmapping`, `vendor/grid_rbpf_python`)
- [x] 0.2 Restore all four vendor repos to their clean upstream commit (gmapping patch reverted — it matched
      `patches/0001-*.patch` exactly; build artifacts, `__pycache__` and a demo output image removed)
- [x] 0.3 Move our own files out of `code/`: `patches/` and `tools/` → `tools/` at project root; then remove `code/`
- [x] 0.4 Change `build_gmapping.sh` to copy gmapping into `.build/`, apply the patch there, and build there —
      inside the container (library path is relative, so the build works from any folder)
- [x] 0.5 Update path references (`.devcontainer/postcreate.sh`, READMEs)
- [x] 0.6 Add `vendor/README.md`: one line per repo — upstream URL, commit, licence, what we borrow from it
- [x] 0.7 `.gitignore`: generated only (`.build/`, caches); `results/` tracked; `vendor/`, `datasets/`, `docs/` present but commented out until sharing
- [x] 0.8 Check: `git -C vendor/<repo> status` clean for all four, and gmapping builds + runs inside the container
- [x] 0.9 Build artifacts → `.build/`; `data/` → `datasets/`; stray gmapping `.dat` outputs removed from the root

## M1 — Shareable project structure
- [x] S1 Move private material into `docs/` (`project/`, `study/`, `papers/`); today's README → `docs/project/BRIEF.md`; update all links
      (all relative links checked; shareable files no longer point into `docs/`)
- [x] S2 `vendors.yaml` + `tools/fetch_vendors.py` — pinned commit, shallow, sparse for PythonRobotics; `--check` reports status only
- [x] S3 Verify: fetch into a scratch folder → same commits and contents as current `vendor/`
      (0 differences for all four; exact-path sparse mode needed for PythonRobotics)
- [x] S4 `datasets.yaml` + `tools/fetch_datasets.py` — find the CARMEN source URL, record checksums, verify
      (source: Stachniss datasets page, linked from ipb.uni-bonn.de/datasets; downloads byte-identical to ours)
- [x] S5 `pfexp/vendor.py` — single access point to vendor code, with a "run tools/fetch_vendors.py" error if missing
- [x] S6 Public `README.md` (quickstart) + `THIRD_PARTY.md` — move `vendor/README.md` content there (vendor/ is fetched, so our notes can't live inside it)
      (also: postcreate.sh now fetches vendors + datasets before building; dataset credits checked against the source page)
- [x] S7 Share test: copy the repo without `docs/`, `vendor/`, `datasets/`, `.build/` → fetch → build → gmapping + grid runner run
      (96 KB copy, no docs/ references; fresh container: fetch + build OK, gmapping intel.log 910-step ESS trace, grid runner OK)
- [x] S8 ⏸ CHECKPOINT — reviewed and approved by user

## M2 — Existing code experiment-ready, as plug-ins (`pfexp/`)
- [x] A1 Baseline: run each vendor demo headless once (from `results/baseline/`, not `vendor/`)
      (`tools/run_vendor_baseline.py`: SIR, EKPF, resampling stats, FastSLAM 1/2; seeded, reproducible byte-for-byte;
      upstream bugs found → `docs/study/VENDOR_REVIEW.md`)
- [x] A2 Package skeleton + registry (register / look up by name) + the four technique interfaces
      (resampler · when to resample · proposal · move)
- [x] A3 Common run log format (per step + per run), shared by every filter
- [x] A4 Resamplers + resampling triggers: wrap Elfring's implementations as registered plug-ins
- [x] A5 Localization filter: built on Elfring classes; techniques come from the registry
- [x] A6 FastSLAM filter: borrow FS1/FS2 functions; proposal = plug-in (`motion_model` / `measurement_informed`)
- [x] A7 Shared seeded worlds (same trajectory + landmarks for every technique)
- [x] A8 Metrics as plug-ins: rmse, ate, map_error, ess, degeneracy, nees, runtime
- [x] A9 Tests: every registered plug-in runs; same seed → same result; borrowed FastSLAM matches the vendor script
- [x] A10 `pfexp/README.md` — "How to add a sampling technique" (verified by adding a dummy one)
- [x] A11 Test: nothing in `pfexp/`, `tools/`, `tests/` references `docs/`
- [x] A12 ⏸ CHECKPOINT — reviewed and approved by user

## M3 — Experiment pipeline + analysis ready
- [x] B1 Resumable runner: experiment YAML → expand the varied setting × seeds → each run gets a stable ID from its settings + seed
      → skip runs already in `results/<exp>/runs/` → run only missing ones → `--rerun` to force
- [x] B2 Outputs, one small file per run so git syncs cleanly across computers: `runs/<run_id>.json` (settings, metrics, host, date,
      vendor commits, versions) + `traces/<run_id>.csv.gz`; `runs.csv` rebuilt from them; runs whose settings changed are reported as stale
- [x] B3 Consistent style: fixed colour + display name per technique across all figures
- [x] B4 Analysis: tables (`.md` + `.tex`, mean ± std), figures (`.pdf` + `.png`), auto `summary.md`
- [x] B5 `compare.py`: combine `runs.csv` across experiments
- [x] B6 Dry run with E01 at 2 seeds end to end; then interrupt halfway, rerun, and confirm only the missing runs execute
- [x] B8 `show_results.py` — standard library only: terminal summary + self-contained `results/report.html`
- [x] B9 `--quick` mode — small rerun of every experiment into `results/quick/`, then shown the same way
- [x] B10 Test on a clean copy without the container: plain `python3 show_results.py` shows the report
- [~] B7 ⏸ CHECKPOINT — review with user

## M4 — Core experiments done (one YAML each)
- [ ] C1 `E01_resampling_scheme` — 4 schemes, localization + FastSLAM1
- [ ] C2 `E02_when_to_resample` — every step vs ESS threshold (swept) vs max-weight
- [ ] C3 `E03_proposal` — FS1 vs FS2 (SLAM); SIR vs extended Kalman PF vs auxiliary PF (localization)
- [ ] C4 `E04_particle_count` — sweep N, RMSE + runtime
- [ ] C5 ⏸ CHECKPOINT — results review

## M5 — New sampler added (the only new filter code)
- [ ] D1 `techniques/moves/resample_move_mh.py` — Metropolis-Hastings moves after resampling
- [ ] D2 Add it to E01/E04 configs; compare against the M4 results with `compare.py`
- [ ] D3 (optional) HMC move · unscented proposal

## M6 — (optional) Real-data check with gmapping
- [ ] E1 Sweep the resampling threshold and N on the CARMEN logs; ESS only (no ground truth)

---

## Log
<!-- date — what was done / decided -->
- 2026-09-13 — Plan approved. Vendor code stays untouched in `vendor/`; all work inside the devcontainer.
- 2026-09-13 — Tasks grouped under milestones at the user's request.
- 2026-09-13 — 0.0–0.2 done: container up; vendor repos moved and restored to clean upstream commits.
- 2026-09-13 — **M0 done.** code/ split into vendor/ (clean upstream) + tools/ (our scripts). gmapping now builds from a patched copy in build/ (later renamed .build/). Verified: gmapping on intel.log (910-step ESS trace), grid RBPF headless run, all 4 vendor repos clean. Container recreated with PYTHONDONTWRITEBYTECODE=1.
- 2026-09-13 — Build artifacts moved to `.build/`, `data/` renamed `datasets/`. Removed stray gmapping `.dat` outputs from the project root. Commits are done by the user only.
- 2026-09-13 — Plan revised: new M1 "shareable project structure" (docs/ private, vendors + datasets fetched by script), plug-in design for sampling techniques, report-ready results layout. `.gitignore` keeps `vendor/`, `datasets/`, `docs/` commented out until sharing.
- 2026-09-13 — `results/` tracked in git (user runs on several computers). Runner must resume: stable run IDs, skip finished runs, one file per run.
- 2026-09-13 — S1 done: study/, papers/, README (→ BRIEF.md), PLAN, PROPOSAL, TASKS and the proposal PDF moved to docs/. Links fixed (12 md files, 0 broken); tools/, .devcontainer/ and vendor/README no longer reference docs/.
- 2026-09-13 — S2–S3 done: vendors.yaml + tools/fetch_vendors.py; fresh fetch identical to current vendor/; --check reports wrong commit / local changes / missing.
- 2026-09-13 — S4 done: datasets.yaml + tools/fetch_datasets.py (sha256 for .gz and unpacked .log); source verified byte-identical.
- 2026-09-13 — S5–S6 done: src/pfexp/vendor.py (paths, use, commit, dataset; clear not-fetched errors), grid runner uses it. Public README.md + THIRD_PARTY.md; vendor/README.md removed (content moved). postcreate.sh fetches vendors + datasets.
- 2026-09-13 — S7 done: share test passed in a separate container on a copy without docs/, vendor/, datasets/, .build/. M1 waiting for checkpoint review.
- 2026-09-13 — Root README.md rewritten as a short, plain project README (objective, how to run, credits). CLAUDE.md added with project rules for future sessions. PYTHONDONTWRITEBYTECODE moved into the Dockerfile (image rebuilt).
- 2026-09-13 — **M1 done** (approved). Decision: pytest 9.1.1 added to the image. M2 started.
- 2026-09-13 — A1 done: vendor baselines recorded and reproducible. Image rebuilt with pytest 9.1.1 + pyyaml 6.0.3 pinned. Upstream code review found bugs that would bias FS1-vs-FS2 and EKPF comparisons (docs/study/VENDOR_REVIEW.md).
- 2026-09-13 — Decision: **borrow and fix** upstream bugs. Affected functions are copied into src/, a test first checks the unfixed copy matches the vendor baseline, then each fix is applied separately and listed in the file header + THIRD_PARTY.md.
- 2026-09-13 — A2 done: registry (register/get/create/names, auto-discovery of technique files), technique base classes, pyproject.toml with pytest config, PYTHONPATH=src in the image. 6 tests pass.
- 2026-09-13 — A3–A4 done: `runlog.py` + `particles.py` (circular heading mean, log-weight normalization, collapse flag); 4 resamplers and 3 triggers as one-file plug-ins calling Elfring's code unchanged (index trick for resamplers, stand-in object for triggers). Guard against cumulative-sum rounding in the vendor search loops. 35 tests pass.
- 2026-09-13 — A5 done: `filters/mcl.py` + `mcl_model.py` (borrowed, vectorized), proposals `motion_model`, `auxiliary`, `extended_kalman` (5 upstream bugs fixed, switchable), trigger `never`, `worlds.localization_world` (Elfring simulator, seeded, same world for every technique). Borrowed code verified against vendor functions with fixes off (likelihood, motion, full EKPF step). Finding: fixed EKPF is more accurate but needs ~300 particles from a uniform start. 48 tests pass.
- 2026-09-13 — A6–A7 done: `filters/fastslam.py` + `fastslam_model.py` (borrowed, vectorized), proposals `fastslam1`, `fastslam2` (rewritten per Montemerlo 2003; upstream kept behind `upstream_bugs`), `worlds.slam_world` (PythonRobotics scenario, its own functions, seeded). Verified vs vendor: prediction byte-identical, FS1/FS2 observation updates identical with bugs on. Fixed FS2 beats FS1 on map and pose error averaged over seeds. ParticleSet + Gaussian helpers moved to particles.py. 60 tests pass.
- 2026-09-13 — A8–A11 done: metrics rmse, ate (rigid alignment), map_error (raw + aligned), ess, degeneracy, nees, runtime; generic plug-in test runs every registered technique; how-to guide verified by adding a dummy resampler (picked up and tested automatically, then removed); docs/ dependency test. 86 tests pass. M2 waiting for checkpoint review.
- 2026-09-13 — Dockerfile reordered for caching (system → heavy Python → light Python → ENV) with pip/apt cache mounts; requirements split into requirements-base.txt + requirements.txt; tabulate added (rebuild 4.8 s). ACTIONS.md started (one line per major action).
- 2026-09-13 — **M2 done** (approved). M3 extended with show_results.py for the lecturer/TA: stdlib-only viewer of tracked results + `--quick` small rerun. M3 started.
- 2026-09-13 — B1–B4 done: `experiment.py` (YAML → runs, stable run IDs), `results.py` (one json + trace per run, atomic writes, provenance, code fingerprint of result-producing code only), `run.py` (parallel, resumable, --quick/--rerun/--dry-run), `style.py` (validated colour-blind-safe palette, fixed colour per technique), `analysis.py` (runs.csv, tables md/tex/csv, metrics + trace figures pdf/png, automatic findings with 95% intervals, summary.md/json). E01 config drafted. results/quick/ gitignored; PFEXP_HOST records the real machine name.
- 2026-09-13 — B5–B10 done: `compare.py`; interrupt test (killed mid-run: 14/16 stored, no partial files, rerun did only the 2 missing); `show_results.py` (stdlib only, terminal summary + self-contained report.html, `--quick` with friendly fallback); verified with `python3 -S` on a clean copy outside the container. Pipeline tests on a temp results folder. README gets "See the results" at the top. 93 tests pass. M3 waiting for checkpoint review.
- 2026-09-13 — Found `__pycache__` (cpython-310, i.e. host Python, likely VS Code test discovery after pyproject.toml added pytest config) in vendor/particle_filter_tutorial and vendor/pythonrobotics. Fix: `pfexp/__init__.py` and `tests/conftest.py` set `sys.dont_write_bytecode = True`; verified with host Python; cleaned; new test `test_vendor_code_is_untouched`. 94 tests pass.
- 2026-09-13 — Project renamed `pf-sampling` and moved out of the pgm_course repo to `~/Documents/code_base/learning/pf-sampling` (to become its own GitHub repo). Container path, image and container renamed; image + gmapping rebuilt; 94 tests, vendor and dataset checks, gmapping run and show_results --quick all pass.
- 2026-09-13 — Made the project independent of where it lives: package moved from `src/pfexp/` to `pfexp/` at the root (no PYTHONPATH needed; removed from the Dockerfile and `workspaceFolder` from devcontainer.json); gmapping linked with `$ORIGIN/../lib` instead of an absolute path (three-level escaping through make/sh/eval). Verified: copied project mounted at `/some/other/place/my-project` without rebuild — gmapping, runner, vendor check, 94 tests, show_results --quick all pass.
- 2026-09-13 — User ran `git init` + `git add .` in pf-sampling: embedded-repo warnings for vendor/. `vendor/` now ignored in .gitignore and its gitlinks removed from the index (`git rm -r --cached -f vendor`, files untouched). Commit left to the user.
