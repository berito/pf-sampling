# How we work vs. what we produce

Everything Claude uses to work lives in `.claude/` (untrack it with the one `.gitignore` line `.claude/`).
Your own planning notes and study material live in `docs/`. The project has two separate parts:

- **The product:** the code, experiments, results and report. It is written and documented for people, runs with
  ordinary commands (`make`, `python -m ...`, pytest), and never refers to the working material below.
- **The working material:** how the project is planned, tracked and checked while working with Claude. It lives
  only in the places listed here. The product must keep working, and read naturally, when all of it is deleted.

Every tool or working file that Claude creates must be listed in this file.

## Working material: what exists and where

| Where | What | Who uses it |
|---|---|---|
| `.claude/CLAUDE.md` | Rules and useful commands for Claude sessions, loaded automatically | Claude |
| `.claude/tools/README.md` | This file | Claude and you |
| `.claude/tools/check_milestones.py` | Checks each phase's steps in TASKS.md (by default only the current phase) and prints the next command. Also checks that no product file mentions the working material or uses typographic characters. | Claude (you can run it too) |
| `.claude/tools/test_check_milestones.py` | Tests for the checker | Claude |
| `docs/project/TASKS.md` | Phases, tasks with status, checkpoints, the Later list, decision log | Claude and you |
| `docs/project/ACTIONS.md` | One plain line per major action taken | You (a record), Claude |
| `docs/project/BRIEF.md`, `PLAN.md`, `PROPOSAL.md`, proposal PDF | Project brief, plan and course proposal | You, Claude |
| `docs/study/`, `docs/papers/` | Your study notes, the upstream code review (`VENDOR_REVIEW.md`), paper PDFs | You (learning), Claude (background) |
| `~/.claude/projects/…/memory/` (outside the repo) | Claude's memory across sessions, if any | Claude |

Run the tools inside the container:

```bash
docker exec pf-sampling-dev python .claude/tools/check_milestones.py            # the current phase
docker exec pf-sampling-dev python .claude/tools/check_milestones.py all --fast  # every phase, quick
docker exec pf-sampling-dev python -m pytest -q .claude/tools                     # the checker's tests
```

## The product: what a person gets

Everything else in the repository: `README.md`, `THIRD_PARTY.md`, `Makefile`, `show_results.py`, `vendors.yaml`,
`datasets.yaml`, `pyproject.toml`, `.devcontainer/`, `pfexp/`, `experiments/`, `tests/`, `tools/`, `report/`,
`results/`. It is documented in `README.md`, `experiments/README.md`, `report/README.md`, `pfexp/README.md` and
`tools/README.md`.

## Stages

- **Development (now):** `.claude/` and `docs/` are tracked, so they travel with the repo to other computers and
  servers. They stay separate from the product, and the product never uses them.
- **Release (after the experiments and the report):** untrack or remove them (uncomment `docs/` and `.claude/` in
  `.gitignore`), and share the product following the steps below.

## Sharing the product without the working material

1. Check that nothing in the product refers to the working material:
   `docker exec pf-sampling-dev python .claude/tools/check_milestones.py P1` ("shared files do not refer to …").
2. Make a copy without it (working files, generated and downloaded folders left out):
   ```bash
   rsync -a --exclude docs --exclude .claude --exclude .vscode --exclude datasets --exclude vendor \
         --exclude .build --exclude .git ./ ../pf-sampling-share/
   ```
   `vendor/` and `datasets/` are downloaded again by `make setup`; `.vscode/` holds one computer's editor settings.
3. In the copy, with its own container (the name `pf-sampling-dev` is already used by the original folder):
   `make CONTAINER=pf-share container setup test quick`. It must work without the deleted folders.
   Afterwards: `docker rm -f pf-share`.
4. To publish the repository itself, the working material must also leave the git history: the first commit
   contains `docs/` and `CLAUDE.md`. Use a fresh repository from the copy, or `git filter-repo --path docs
   --path .claude --path CLAUDE.md --invert-paths`.

## Rules for Claude

- New scripts, checks or notes that exist for planning, tracking or checking the work go in `.claude/tools/`
  and are added to the table above. Plans and logs for the user stay in `docs/project/`.
- Product files never mention milestones, task IDs, checkpoints, Claude, `docs/`, `.claude/` or the private notes.
  If a product file needs an explanation that lives in a private note (e.g. why an upstream bug was fixed), write
  the explanation itself in the product file or in `THIRD_PARTY.md`.
- No signatures and no conversation in files: product code, comments and documents say what the code is and
  does, never how it got that way ("now uses", "no longer", "moved", "earlier runs showed", "verified on <date>").
  That history belongs in the commit message. Anything no longer needed is deleted, not kept with a note.
  Use plain ASCII punctuation in product files (no em dashes, arrows, middle dots or Unicode maths); the checker
  flags them. Names with accents and the `±` in result tables are fine.
