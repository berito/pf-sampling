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

## Phases

Each phase has a fixed scope and ends with a complete result: its experiments run and reviewed, and a report that
could be handed in as it is. Finish the current phase before starting the next. Ideas and gaps found along the way go
to **Later**, never into the current phase. Phases 1 and 2 are the course requirement: between them they cover representation, inference and learning.
Phases 3-5 only if time allows.

| Phase | Scope | Ends with | Status |
|---|---|---|---|
| **1 Core study** | setup, pipeline, E01-E04 (resampling scheme, when to resample, proposal, particle count), full report text | **Report v1**, ready to hand in | [x] |
| **2 Parameter learning** | marginal likelihood from the particle weights, E11 (learning the filter's noise parameters) | **Report v2**, covering learning as well | [ ] |
| **3 Resample-move** *(if time)* | MCMC move plug-in, E05 compared with E01 | Report v3 (adds a section) | [ ] |
| **4 Wider coverage** *(if time)* | E07 when to resample in FastSLAM, E08 resamplers with FastSLAM 2.0, decisions on SLAM proposals and crossed combinations | Report v4 | [ ] |
| **5 Real data** *(if time)* | gmapping on the Intel log (E06) | Report v5 | [ ] |
| **Later** | not scheduled; picked only when a phase is closed | | |

Progress check: `python .claude/tools/check_milestones.py` (the current phase) or `... all`.

## Open decisions
- **Before making the GitHub repo public again:** remove `docs/` from the whole git history (it holds 43 publisher paper PDFs, the proposal PDF and personal notes, all pushed in the first commit), e.g. with `git filter-repo --path docs --invert-paths` + force push, or a fresh repo; and ignore `docs/` in `.gitignore`. Repo made private on 2026-09-13 until the work is finished.

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
├─ report/              LaTeX report: main.tex · sections/ · references.bib · Makefile
├─ tests/
│  ── FETCHED / GENERATED (delete freely, recreatable) ──
├─ vendor/              ← tools/fetch_vendors.py     (gitignore entry commented out until sharing)
├─ datasets/            ← tools/fetch_datasets.py    (gitignore entry commented out until sharing)
├─ .build/              ← tools/build_gmapping.sh    (gitignored)
├─ results/             ← experiment runs            (TRACKED — resumable across computers)
│  ── PRIVATE (tracked for now, removed before sharing) ──
└─ docs/
   ├─ project/          BRIEF.md · PLAN.md · PROPOSAL.md · proposal PDF · TASKS.md
   ├─ papers/           technique↔paper map (PDFs in the research repo)
   └─ report/           the write-up (later)
```

---

# Phase 1 — Core study (ends with report v1, ready to hand in)

### M0 — Setup complete
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

### M1 — Shareable project structure
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

### M2 — Existing code experiment-ready, as plug-ins (`pfexp/`)
- [x] A1 Baseline: run each vendor demo headless once (from `results/baseline/`, not `vendor/`)
      (`tools/run_vendor_baseline.py`: SIR, EKPF, resampling stats, FastSLAM 1/2; seeded, reproducible byte-for-byte;
      upstream bugs found → `docs/project/VENDOR_REVIEW.md`)
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

### M3 — Experiment pipeline + analysis ready
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
- [x] B11 Run the rest without Claude: root `Makefile` with short commands (host or container; `make status` shows runs
      done / to do / made with older code); configs for E01–E06 ready (E01 and E03 split into localization + SLAM parts;
      E05 skipped with a reason until the technique exists; E06 runs gmapping through the runner); guides
      `experiments/README.md` + `report/README.md`; `make report-preview`
- [x] B12 Agent tooling separated from the shared project: milestone checker + its tests in `docs/project/agent/` (moved to `.claude/tools/` in B14)
      (also checks that no shared file mentions private material); `CLAUDE.md` → `.claude/CLAUDE.md`; milestone wording
      removed from configs, guides, Makefile and tests
- [x] B13 Audit: product files free of working material (removed a private-note reference in `mcl_model.py` and a Claude
      mention in `.gitignore`; checker now also flags private note names and process words); inventory of all working
      material + sharing checklist in `docs/project/agent/README.md` (now `.claude/tools/README.md`)
- [x] B14 All of Claude's tooling in `.claude/tools/` (one folder to untrack, next to `.claude/CLAUDE.md`); exploration
      script `grid_rbpf_headless.py`, its 2D-Grid-SLAM repo and OpenCV deleted (unused);
      typographic characters (em dashes, arrows, Unicode maths) replaced with plain text in all product files
- [x] B7 ⏸ CHECKPOINT — reviewed with user; next: user commits, pushes and tests on the server computer

### M4 — Core experiments E01-E04 (one YAML each)
Configs are ready; run them with `make run E=E01` … `E=E04` (guide: experiments/README.md). Progress: `make status`, or `python .claude/tools/check_milestones.py P1`.
- [x] C0 Numbered experiments: each experiment keeps numbered result sets `results/<E>/001/`, `002/`, ... with the
      parameters they ran with; `make redo` replaces a broken one, `make new` starts the next number after a deliberate
      parameter change, `make use` picks the one the report shows; the runner refuses to mix changed parameters or code
- [x] C1 `E01_resampling_scheme_localization` + `E01_resampling_scheme_slam` — 4 schemes × N, localization + FastSLAM1
- [x] C2 `E02_when_to_resample` — every step, never, ESS threshold (0.2/0.5/0.8), max-weight (0.1/0.2/0.5)
- [x] C3 `E03_proposal_localization` (motion model vs auxiliary PF vs extended Kalman PF × N) + `E03_proposal_slam` (FS1 vs FS2 × N)
- [x] C4 `E04_particle_count` — sweep N, RMSE + runtime
- [x] C5 ⏸ CHECKPOINT — results review (review points handled: EKPF edge bug fixed and E01-E04 redone, findings compare like with like, median NEES, resampler runtime explained in the report)

### Report v1
- [x] R1 Structure: `report/` (main.tex, macros.tex, sections/, references.bib, Makefile), LaTeX layer in the image,
      build files in `.build/report/`; experiment tables and figures read straight from `results/` (red placeholder
      until an experiment has run). Verified: skeleton builds; pointed at quick E01 results it includes table + figure
- [x] R2 Background: SLAM as a DBN, Rao-Blackwellization, discrete → continuous inference
- [x] R3 Particle filters: importance sampling, proposals, resampling, MCMC moves
- [x] R4 Method: filters, worlds, implementation and upstream corrections, metrics
- [x] R5 Results: one subsection per experiment E01-E04 (choose report columns so tables stay readable)
- [x] R6 Discussion, conclusion, abstract, appendix; check references against the papers
- [x] R7 Final check: `make -C report` builds from a clean copy; no TODO left
- [x] R8 ⏸ CHECKPOINT — review with user

# Phase 2 — Parameter learning (ends with report v2)
E01-E04 ask how well the filter infers the pose when the model is given. This phase asks where the model itself
comes from: the motion and measurement noise the filter assumes are currently fixed by hand, and the same particle
weights that drive the filter also estimate the marginal likelihood p(z_1:T | theta), which is what a maximum-
likelihood estimate of theta maximizes. The world's true noise (`true_motion_std`, `true_measurement_std`) and the
filter's assumed noise (`process_std`, `measurement_std`) are already separate settings, so the world stays fixed
while the assumed value is swept.

In the course's terms, this is **maximum-likelihood parameter learning in a dynamic Bayesian network with latent
state**: the structure is given and only the parameters of two CPDs are estimated (parameter learning, not structure
learning), and the trajectory is never observed (incomplete data, Koller ch. 19, on the template models of ch. 6).
Parameter tying in the template is what makes one noise value cover every time slice, and what makes each step,
not each run, evidence about the parameters. The report keeps these three apart: model parameters (learned: the
noise levels), latent variables (inferred per run: poses and landmarks), and algorithm settings (chosen, not
learned: particle count, resampler, when to resample). Use this vocabulary in the write-up.

The filter's defaults are far from the world's truth: motion (0.1, 0.2) against (0.005, 0.002) and measurement
(0.4, 0.3) against (0.2, 0.05). Overstating noise is a known way to keep a filter robust, so the question is not
only whether the maximum-likelihood values recover the truth but what the inflated defaults cost or buy.

- [x] L1 Marginal likelihood in the run log: per step, the log of the sum of the unnormalized weights
      (`logsumexp` of the log weights before they are normalized); a `log_likelihood` metric sums them over the run.
      With the bootstrap proposal the unnormalized weight is already the previous weight times p(z_t | x_t), so the
      per-step sum is p(z_t | z_1:t-1) and the estimator telescopes correctly whether or not the step resampled.
      The auxiliary and extended Kalman proposals weight in two stages and need a different estimator, so the metric
      is reported for `motion_model` only and refuses the others rather than returning a wrong number.
- [x] L2 Test L1 against an exact answer: a small linear-Gaussian model in the test, where a Kalman filter gives the
      log-likelihood in closed form; the particle estimate must approach it as N grows, and its spread over seeds
      must shrink.
- [x] L3 `E11_noise_parameter_learning`: the world keeps its true noise, the filter's assumed `measurement_std` and
      `process_std` are swept; report log-likelihood, position RMSE, mean ESS/N and median NEES per value. The
      maximum-likelihood estimate is the argmax of the mean log-likelihood; compare it with the true noise and with
      the hand-set default, and compare the value that maximizes the likelihood with the value that minimizes RMSE.
      One parameter is swept at a time with the others at their true values (a profile likelihood), over log-spaced
      values wide enough to cover both the truth and the current defaults. A single scale factor cannot serve,
      because the components sit at different multiples of the truth.
      Two regimes, since they give opposite answers and the contrast is the result:
        - tracking start (particles begin near the true first pose): the profile peaks at the true value.
        - uniform start (the global localization of E01-E04): with the true noise the filter never finds the robot,
          the likelihood estimate collapses, and the profile has no peak within any sensible range.
      The uniform start needs no new experiment, but the tracking start needs a way to start the particles near a
      known pose, which `run_mcl` does not have yet.
- [x] L4 Check the assumption the template makes: estimate the parameters from each seed's recording separately and
      report how the estimates scatter. Tying one CPD across all time slices asserts the noise is constant; tight
      agreement between independent recordings supports it, wide scatter would say the model needs noise that varies
      with conditions. The scatter should also narrow as the number of steps grows.
- [x] L5 Tie the learning back to the inference results: the same sweep run with different particle counts and with
      the four resampling schemes, reporting how far the estimate scatters between recordings. A degenerate particle
      set gives a poor likelihood estimate, so the sampling choices decide how well theta can be learned at all.
- [x] L6 Report v2: a background subsection placing the phase in the course's taxonomy (parameter learning with
      incomplete data, parameter tying, and where EM would come in), the E11 subsection, and a discussion paragraph
      on inference quality as the limit on learning; `make report` builds, no TODO. Appendix A gains the missing
      normalizing constant in the localization likelihood, with why it does not change E01-E04.
- [ ] L7 ⏸ CHECKPOINT — review with user; phase closed

# Phase 3 — Resample-move *(if time; ends with report v3)*
- [ ] D1 `techniques/moves/resample_move_mh.py` — Metropolis-Hastings moves after resampling
- [ ] D2 Run `E05_resample_move` (config ready, skipped until D1 exists); compare against E01 with `make compare`
- [ ] D3 Report v3: add the E05 subsection (question, setup, table, figure, findings); `make report` builds, no TODO
- [ ] D4 ⏸ CHECKPOINT — review with user; phase closed

# Phase 4 — Wider coverage *(if time; ends with report v4)*
E01–E04 vary one sampling choice at a time and leave some filter/technique pairs out. Each gap is either run as its
own experiment (one YAML, numbered result set) or recorded as a limitation in the report.
- [ ] W1 `E07_when_to_resample_slam`: every step, never, ESS threshold (0.2/0.5/0.8), max weight (0.1/0.2/0.5) in
      FastSLAM 1.0 (no new code; map error matters here since each particle carries a map)
- [ ] W2 `E08_resampling_scheme_fastslam2`: the four resampling schemes with the FastSLAM 2.0 proposal × N (no new code)
- [ ] W3 Measurement-aware proposals in SLAM: decide whether auxiliary / extended Kalman proposals for FastSLAM are
      worth new code (FastSLAM 2.0 already uses the observation); if yes, write them as `fastslam` proposals and run
      `E09_proposal_slam_extended`; if no, state it as a limitation in the report
- [ ] W4 Crossed combinations: decide which pairs are worth crossing (e.g. resampler × when-to-resample, proposal ×
      resampler) and keep the run count manageable; run as `E10_...` or state it as a limitation
- [ ] W5 Report v4: a subsection per new experiment, and the limitations for what was decided against
- [ ] W6 ⏸ CHECKPOINT — review with user; phase closed

# Phase 5 — Real data *(if time; ends with report v5)*
- [ ] E1 `E06_gmapping_resampling` — resampling threshold × N on the Intel log; ESS only (no ground truth). Config ready: `make run E=E06`
- [ ] E2 Report v5: add the E06 subsection
- [ ] E3 ⏸ CHECKPOINT — review with user; phase closed

# Later (not scheduled)
Picked only when a phase is closed. New ideas are added here, not to the phase in progress.
- SMC-EM: a particle smoother as the E step and a closed-form update of the noise covariances as the M step,
  iterated until theta converges (a full learning algorithm rather than a sweep)
- Learned and differentiable proposals
- HMC move · unscented proposal
- Extended Kalman proposal that resets each particle's covariance every step (linearised optimal proposal): 0.12 m
  and ESS/N 0.58 at N=1000 in a side test, against 0.25 m and 0.22 for the current version
- Blog article *(personal; after report v1)*:
  Goal: understand particle filters properly by explaining them, and have a public technical article for your profile.
  - [ ] T1 Decide where it lives: draft in this project (`blog/`) and publish to your GitHub Pages site; pick the format
        (Markdown for Jekyll/GitHub Pages, or a notebook-style post)
  - [ ] T2 The particle filter from scratch: Bayes filtering, importance sampling, weights, resampling — with small
        pictures of particles
  - [ ] T3 SLAM as a graphical model and Rao-Blackwellization: why FastSLAM samples the path and keeps a small EKF per landmark
  - [ ] T4 The filter families: MCL, FastSLAM 1.0, FastSLAM 2.0, gmapping, auxiliary PF, extended Kalman PF — what each changes
  - [ ] T5 Sampling techniques and their drawbacks: resampling schemes, when to resample, proposals, MCMC moves
        (degeneracy, impoverishment, cost)
  - [ ] T6 What the experiments showed: figures and tables from `results/`, in plain language
  - [ ] T7 Lessons from reusing upstream code: the bugs found and why checking borrowed code matters
  - [ ] T8 Review for readers outside the course: clear, correct, links to the repo and the papers
  - [ ] T9 Publish on your GitHub page; link it from README.md
  - [ ] T10 ⏸ CHECKPOINT — review with user before publishing

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
- 2026-09-13 — Project renamed `pf-sampling` and moved out of the pgm_course repo to `~/Documents/code_base/research/slam/pf-sampling` (to become its own GitHub repo). Container path, image and container renamed; image + gmapping rebuilt; 94 tests, vendor and dataset checks, gmapping run and show_results --quick all pass.
- 2026-09-13 — Made the project independent of where it lives: package moved from `src/pfexp/` to `pfexp/` at the root (no PYTHONPATH needed; removed from the Dockerfile and `workspaceFolder` from devcontainer.json); gmapping linked with `$ORIGIN/../lib` instead of an absolute path (three-level escaping through make/sh/eval). Verified: copied project mounted at `/some/other/place/my-project` without rebuild — gmapping, runner, vendor check, 94 tests, show_results --quick all pass.
- 2026-09-13 — User ran `git init` + `git add .` in pf-sampling: embedded-repo warnings for vendor/. `vendor/` now ignored in .gitignore and its gitlinks removed from the index (`git rm -r --cached -f vendor`, files untouched). Commit left to the user.
- 2026-09-13 — First commit pushed to github.com/berito/pf-sampling (public) including docs/ (paper PDFs, proposal, personal notes). User made the repo private until the work is finished; removing docs/ from history is an open item before it goes public.
- 2026-09-13 — M7 (LaTeX report) added; R1 structure created now, text written at the end. LaTeX layer added to the image after heavy Python (1m20s, plus lmodern 51s); skeleton builds; inclusion of results verified against quick E01. Figures now saved on a white background for print.
- 2026-09-13 — M8 added (personal): a blog article on the user's GitHub page explaining particle filters, SLAM, the filter families and sampling techniques with the experiment results. Not a course deliverable; starts after the report (M7).
- 2026-09-13 — B11 done (plan approved by user): the rest of the project can be run without Claude. A milestone checker checks every milestone and names the next command; M0–M3 pass automatically (110 tests, pipeline run + resume + show_results in a temp folder). Root Makefile; experiments/README.md and report/README.md guides. Configs E01–E06 written and verified with --dry-run and --quick only (full runs left to the user). Decisions: E01/E03 split per filter; gmapping is a filter in the runner (E06, reproducible with -randseed); experiments that cannot run yet are skipped with the reason. Fixed: numeric sweep plots (settings were plotted as text), crash with more than 8 variants, report not rebuilding when results appear, findings claiming significance from one seed. M3 waiting for checkpoint review.
- 2026-09-13 — B12 done (user's request): agent and project-management tooling must not be part of the shared code, which has to read and run as ordinary human-written code. Milestone checker moved to `docs/project/agent/` (run: `python docs/project/agent/check_milestones.py`), with a new check that no shared file mentions `docs/`, `.claude/`, `CLAUDE.md` or the checker; `CLAUDE.md` moved to `.claude/` (added to the "uncomment when sharing" block of .gitignore); `make check` replaced by `make status` (runner dry run, now also counting runs made with older code); milestone labels removed from configs and guides; the docs-reference pytest moved into the private checker. 108 project tests + 2 private tests pass; M0–M3 checks pass.
- 2026-09-13 — B13 done (user's request: how we work and what we produce must be separable). Audit of every product file: clean except a "(docs: VENDOR_REVIEW, Elfring #1)" reference in `pfexp/filters/mcl_model.py` and a Claude comment in `.gitignore`, both removed. `docs/project/agent/README.md` lists every working file/tool with its location, the product folders, and the steps to share the product without the working material. Open for the user: whether `.gitignore` should drop its "uncomment when sharing" block, and whether `.vscode/` (personal ROS settings) should stay tracked.
- 2026-09-13 — B14 done (user: anything Claude uses must sit where it can be untracked). Tooling moved from `docs/project/agent/` to `.claude/tools/`, so `.claude/` holds everything of Claude's and `docs/` only the user's notes; `# .claude/` added next to `# docs/` in .gitignore. `tools/grid_rbpf_headless.py` (setup-phase exploration, unused by the product) moved there; its upstream repo removed from vendors.yaml, THIRD_PARTY.md and README credits, and opencv-python-headless from requirements-base.txt (image rebuilt). Em dashes, arrows, middle dots and Unicode maths replaced with plain text in product files; the checker now flags them.
- 2026-09-13 — B14 follow-up (user): unused things are deleted, not moved with a note; files never narrate history or past reasons (that goes in commit messages). Deleted `grid_rbpf_headless.py` and the local 2D-Grid-SLAM clone; rewrote change-log wording in `extended_kalman.py` ("used ...; now ...") and removed history notes from E02, E03 and datasets.yaml. The private checker now also flags change-log wording. Rule added to `.claude/CLAUDE.md`.
- 2026-09-13 — **M3 done** (user asked to complete it). Final check: a copy with exactly the files git would push, without `docs/`, `.claude/` and `.vscode/`, in a new container: `make container setup test status quick report` all succeeded (vendors + datasets fetched, gmapping built, 108 tests, quick run of all experiments, report built with placeholders for the not-yet-run experiments). Next: user tests on the server, then M4 (`make run E=E01` ... `E=E04`).
- 2026-09-13 — Project tested on the shared server (ai-server-01): Docker there has no buildx, so `make container` fails on `RUN --mount`; image built with the old builder from a temporary copy of the Dockerfile without cache mounts. `make setup`, `make test` (108 passed), `make quick` (all experiments, E05 skipped as expected) and `make report` all worked. Harmless warnings: user id 1003 has no home in the container (matplotlib/fontconfig cache). Open: whether the Dockerfile should also build without BuildKit.
- 2026-09-13 — Background runs added (user: experiments must keep running after VS Code is closed). `tools/background.sh` + `make start/start-all/running/log/stop`: run in its own session (setsid -f), one at a time, output in `.build/logs/`. devcontainer.json: `shutdownAction: none`, `--init`, `--restart unless-stopped`; same in `make container`. Tested: run survives closing the starting terminal; stop lets the current run finish (forced after 30 s), nothing partial saved; start again skips finished runs; make log ends with the run. Bugs found while testing and fixed: runs started with `&` ignored Ctrl+C and so ignored stop; `tail --pid` hung on zombie processes (container without --init). 108 tests pass.
- 2026-09-14 — C0 done (user: the same experiment may run several times; a run broken by a bug or wrong setup is replaced, a deliberate parameter change is a new experiment with its own data and parameters; user chose numbers over "repeat"). Results now in `results/<E>/<NNN>/` with `parameters.yaml` + `info.json`; `current.txt` picks what the report and show_results use. `make redo` / `make new NOTE=...` / `make use N=...`; `--rerun` removed. A plain run refuses to continue when the YAML parameters differ from the current set, or when runs remain and stored runs used other code (`--code-change-ok` overrides); quick sets are redone automatically. Seeds are not a parameter (more seeds continue the same set). Analysis uses each set's stored parameters; compare accepts sets; report macros take an optional number (`\experimenttable[002]{...}`, catchfile). 116 project tests + 8 private tests pass; make quick, new/redo/use/compare and report preview checked by hand. Decisions: 3-digit folder names; redo deletes without asking.
- 2026-09-14 — C1–C4 done: E01–E04 run as result set 001 (note "first full run") on ai-server-01 in the background, 16 jobs, 1,120 runs, no errors; milestone checker passes for all six configs. Waiting at C5. Points for the review: (1) automatic findings compare best vs worst across different particle counts in two-factor experiments (e.g. Multinomial N=1000 vs Stratified N=50), not meaningful; (2) EKPF gets worse with more particles in E03 localization (RMSE 0.67 at N=50 -> 0.98 at N=1000, ESS/N ~0.19), against the hypothesis, to investigate before accepting; (3) mean NEES identical (1.68e7) for every resampling rule in E02, i.e. dominated by the steps before the first resample: decide median NEES or skip early steps; (4) multinomial/stratified runtime reflects the upstream Python loops, not the schemes.
- 2026-09-14 — C5 review, first part (user: do the recommendations). (1) EKPF worse with more particles was a bug: position differences in the prior/proposal densities were not wrapped to the cyclic world, so a sample moved across the edge by validate got an arbitrarily large weight (step-0 collapse onto a particle ~8 m away, more likely with more particles). Fixed as correction 6 (switchable with upstream_bugs), regression test via the importance-sampling identity from a uniform start (fails by >10^4 without the fix). EKPF now improves with N (RMSE 0.59 -> 0.25) but keeps ESS/N ~0.2; resetting the per-particle covariance each step (linearized optimal proposal) gave 0.12 m and ESS/N 0.58 in a side test, a different algorithm, not adopted. (2) Findings compare like with like: two-setting experiments compare the technique within each value of the other setting. (3) Reports use median NEES (nees_median) instead of the mean. (4) Report E01 text explains that resampler runtimes reflect the upstream O(N^2) multinomial/stratified code. All six E01-E04 sets redone as 001 with the fixed code (1,120 runs, no errors). 118 project tests + 8 private tests pass; report builds.
- 2026-09-14 — M9 "Wider coverage" added (user: the coverage gaps of E01–E04 get their own milestone). Tasks W1–W6: E07 when to resample in FastSLAM, E08 resamplers with FastSLAM 2.0, W3/W4 decisions on SLAM proposals and crossed combinations (run or state as limitations), report entries, checkpoint. Numbered M9 so the existing M6–M8 keep their numbers; to be done after M5 and before the report text. Checker has an m9 check.
- 2026-09-14 — Milestones renumbered by importance (user): M6 is now Wider coverage (was M9), M7 Report stays, M8 is the optional gmapping check (was M6), M9 the blog article (was M8). Earlier log lines use the old numbers.
- 2026-09-14 — Plan restructured into phases (user: every phase or sprint must end in a complete result and report, so the project does not get stuck adding milestones and miss the deadline). Phase 1 = M0-M4 + report v1; Phase 2 resample-move (E05); Phase 3 wider coverage (E07-E10); Phase 4 gmapping (E06); Later: HMC, unscented proposal, covariance-reset EKPF, blog. Rule saved in .claude/CLAUDE.md and memory. Checker reports by phase (P1-P4) and shows only the current phase by default; the report only includes the current phase's experiments (E05/E06 subsections removed until their phase).
- 2026-09-14 — Report v1 written (R2-R7): introduction, DBN background with Rao-Blackwellization and the d-separation argument, particle filter theory, method (worlds, implementation, metrics, statistics), results for E01-E04 with every number and clear/within verdict taken from the stored summaries, discussion with limitations, conclusion, appendix of upstream corrections; author Mohammed as in the proposal. 17 pages, no TODO, builds from a clean .build/report. Results cleaned of conversational text: the "first full run" note removed from info.json and summaries, analysis status notes rephrased as facts, baseline logs regenerated (old project path). Tables and figures made readable: one column per varied setting, wrapped LaTeX headers, tables scaled only when wider than the page, log axis for NEES, trace legends outside the plot, E02 drops the always-zero collapses metric. 118 project tests + 8 private tests pass; P1 checker automatic checks pass. Waiting at C5 and R8 (user review); Phase 1 closes after that.
- 2026-09-14 — **Phase 1 closed** (approved by user): E01-E04 results and report v1 (report/report.pdf, 18 pages, clickable references) are the deliverable if the deadline comes first. User commits and pushes. Next, only if time allows: Phase 2 (resample-move).
