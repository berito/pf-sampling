# CLAUDE.md

Particle-filter experiments for a PGM course project. See README.md for what the project is.

## Before starting work
- If `docs/project/TASKS.md` exists, read it first: milestones, task status, and a log of decisions.
  Tick tasks and add a log line as you finish work. Stop at ⏸ checkpoints for the user's review.
- Also add one plain, single line per major action to `docs/project/ACTIONS.md` as you go (what you did, not how).
- Show a plan before starting larger changes, and wait for approval.

## Rules
- **Never edit `vendor/`.** Upstream code is fetched by `tools/fetch_vendors.py` at the commits in
  `vendors.yaml`. Import it unchanged via `pfexp/vendor.py`, or copy a function into `pfexp/` with a
  header: `Borrowed from <repo>/<file>@<commit>; licence; changes: ...`, and list it in THIRD_PARTY.md.
  Copy only from MIT repos (particle_filter_tutorial, pythonrobotics).
- **Run everything inside the dev container** (image `pf-sampling:dev`, container `pf-sampling-dev`,
  `docker exec pf-sampling-dev <cmd>`). Never install packages on the host. Add light libraries to
  `.devcontainer/requirements.txt` (rebuilds in seconds); keep heavy, stable ones in `requirements-base.txt`;
  add system tools as a new RUN line after the base apt layer. Keep the Dockerfile ordered rare → frequent.
- **Don't commit.** The user makes all commits.
- **Keep folders clean:** build artifacts only in `.build/`, datasets in `datasets/`, outputs in
  `results/`. Nothing generated in the project root. gmapping and the vendor demos write files into
  their working directory, so run them from an output folder.
- **Code must not depend on `docs/`.** `docs/` is private and gets removed before sharing.
- **`results/` is tracked in git**, so experiments can continue on another computer. The runner must
  skip runs that already exist.
- **Sampling techniques are plug-ins:** adding one should be one new file, no edits elsewhere.
- `.gitignore`: `vendor/` is ignored (recreated by `tools/fetch_vendors.py`); `datasets/`, `docs/` are listed but commented out until the code is shared.
  Don't uncomment them unless asked.
- README.md is for people: keep it short and plain.

## Useful commands
```bash
python tools/fetch_vendors.py --check     # upstream code present, pinned, unmodified
python tools/fetch_datasets.py --check    # datasets present, checksums match
bash tools/build_gmapping.sh              # patched copy of gmapping → .build/
python -m pytest                          # all tests (includes a check that code never references docs/)
python tools/run_vendor_baseline.py       # rerun the upstream demos → results/baseline/
python -m pfexp.run experiments/<E>.yaml  # run an experiment (resumable) → results/<E>/
python show_results.py [--quick]          # what the lecturer runs; must stay standard-library only
```

Borrowed upstream code keeps its bug fixes switchable (`upstream_bugs`, `wrap_angle_residual`); tests compare
the copies against the vendor functions with the fixes off. Adding a technique: see pfexp/README.md.
