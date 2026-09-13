# CLAUDE.md

Particle-filter experiments for a PGM course project. See README.md for what the project is.

## Before starting work
- If `docs/project/TASKS.md` exists, read it first: milestones, task status, and a log of decisions.
  Tick tasks and add a log line as you finish work. Stop at ⏸ checkpoints for the user's review.
- Also add one plain, single line per major action to `docs/project/ACTIONS.md` as you go (what you did, not how).
- Show a plan before starting larger changes, and wait for approval.

## Rules
- **Stages:** development (now): `.claude/` and `docs/` are tracked but separate from the product. Release (after the
  experiments and report): they are untracked/removed and the product must work without them.
- **How we work and what we produce stay separate.** `.claude/tools/README.md` lists every tool and working file
  Claude uses, and where it lives. Add anything new you create for planning, tracking or checking to that list.
- **No conversation or history in files.** Code, comments and docs state what things are and do, the way a person
  writes them. Reasons for past choices and what changed ("now", "no longer", "moved", "earlier runs showed") go in
  the commit message the user writes, not in files. Anything unused is deleted, not kept with an explanation.
- **Keep agent and project-management tooling out of the shared project.** Scripts, tests and notes that exist for
  Claude or for the milestone plan (e.g. the milestone checker) live in `.claude/tools/`; shared code, configs,
  guides and the Makefile never mention milestones, checkpoints, `docs/`, `.claude/` or that tooling. Shared code
  must read as a person would write it and be runnable with ordinary commands (`make`, `python -m ...`, pytest).
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
  Don't uncomment them unless asked. Sharing steps: `.claude/tools/README.md`.
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
make -C report                            # build the LaTeX report → report/report.pdf (build files in .build/report)
```
`make` lists short forms of all of these (`make status` = which experiment runs are done); they work on the host and
inside the container. Human guides: experiments/README.md, report/README.md, pfexp/README.md.

Private, for Claude only (run inside the container; not part of the shared project):
```bash
python .claude/tools/check_milestones.py [M4] [--fast]   # each milestone in TASKS.md: done / missing / next command
python -m pytest -q .claude/tools                         # its tests, incl. "shared files don't mention private material"
```
Keep the checker in step with TASKS.md and the experiment configs.
