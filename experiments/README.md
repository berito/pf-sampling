# Experiments

Each file here is one experiment: one question, the settings that stay fixed, the settings that change, and
how many seeds (repeats). Running it stores every run in a numbered result set, `results/<experiment>/001/`, and
builds tables, figures and a `summary.md` there.

All commands below are run from the project folder. `make ...` works on the host and inside the container.
The full command is shown under each one, if you prefer not to use make (run it inside the container,
or put `docker exec pf-sampling-dev` in front).

## Where things stand

```bash
make status         # every experiment: its result set, runs done and to do, changed parameters
make status E=E03   # only the experiments starting with E03
```
`python -m pfexp.run experiments/*.yaml --dry-run`

## The experiments

| Config | Question | Runs | Time* |
|---|---|---|---|
| `E01_resampling_scheme_localization` | Does the resampling scheme matter? (4 schemes, 3 particle counts) | 240 | < 1 min |
| `E01_resampling_scheme_slam` | The same in FastSLAM 1.0 | 160 | ~1 min |
| `E02_when_to_resample` | Every step, never, ESS threshold or max-weight rule? | 160 | < 1 min |
| `E03_proposal_localization` | Motion model vs auxiliary PF vs extended Kalman PF | 240 | ~1 min |
| `E03_proposal_slam` | FastSLAM 1.0 vs 2.0 | 160 | ~1 min |
| `E04_particle_count` | How many particles are enough? | 160 | ~1 min |
| `E11_learn_measurement_range` | Can the assumed range noise be learned from the run? | 180 | < 1 min |
| `E11_learn_measurement_bearing` | The same for the bearing noise | 180 | < 1 min |
| `E11_learn_motion_forward` | The same for the forward motion noise | 140 | < 1 min |
| `E11_learn_motion_turn` | The same for the turn noise, over 30 steps | 140 | < 1 min |
| `E11_learn_motion_turn_long` | The turn noise again, over 400 steps | 140 | < 1 min |
| `E11_start_regime` | The range sweep from a known start and from the uniform start | 360 | < 1 min |
| `E11_estimator_particles` | The range sweep with 25 to 2000 particles | 720 | < 1 min |
| `E11_estimator_resampler` | The range sweep under the four resampling schemes | 720 | < 1 min |
| `E05_resample_move` | Do MCMC moves after resampling help? *Needs the resample-move technique first (below).* | 120 | ~1 min |
| `E06_gmapping_resampling` | gmapping's resampling threshold and number of particles on the real Intel log | 36 | ~10 min |

\* Estimated from single-run timings on a 16-core computer; one run per core minus one. The runner prints the
real time of every run.

## Running them

1. Try a small version first. It is quick and shows that everything works:

   ```bash
   make quick
   ```
   `python show_results.py --quick --no-open`, then open `results/quick/report.html`.

2. Run the experiments in order. `E=E01` runs every experiment whose name starts with `E01`:

   ```bash
   make run E=E01
   make run E=E02
   make run E=E03
   make run E=E04
   make run E=E11          # or everything at once: make run-all
   ```
   `python -m pfexp.run experiments/E01_resampling_scheme_localization.yaml experiments/E01_resampling_scheme_slam.yaml`

   You can stop a run at any time (Ctrl+C). Run the same command again: finished runs are kept, only the
   missing ones run.

3. Look at the results:

   ```bash
   make results            # summary in the terminal, and results/report.html with every table and figure
   ```
   Each result set also has `results/<experiment>/<number>/summary.md` (question, setup, table, automatic
   findings, figures), `tables/` (`.md`, `.tex`, `.csv`) and `figures/` (`.pdf`, `.png`).

## Numbered result sets

Every experiment keeps its results in numbered sets, each with the parameters it was run with:

```
results/E04_particle_count/
  current.txt          the number the report and make results show (the newest, unless you choose one)
  001/                 parameters.yaml, info.json (date, computer, code version, note), runs/, tables/, figures/, ...
  002/
```

There are three situations:

| Situation | Do | What happens |
|---|---|---|
| A run was stopped, or you added seeds | `make run E=E04` (or `make start`) | Continues the current number; only missing runs run |
| The results are wrong: a bug, a wrong setting, a broken setup | fix it, then `make redo E=E04` | The current number is deleted and run again under the same number |
| The results are fine, and you change a parameter to see its effect | edit the YAML, then `make new E=E04 NOTE="stratified resampler"` | A new number (`002`) with its own data; `001` stays as it was |

`python -m pfexp.run experiments/E04_particle_count.yaml --redo` / `--new --note "..."`. In the background:
`make start E=E04 ARGS=--redo`, or `make start E=E04 ARGS=--new NOTE="..."`.

If the YAML's parameters differ from those of the current number, `make run` stops and asks which of the last two it
is, so results of different settings are never mixed. The same happens if runs are still to do and the stored
ones were made with a different version of the code; if that change cannot affect the numbers, continue with
`ARGS=--code-change-ok`.

Choose which number the report and `make results` show, and compare numbers:

```bash
make use E=E04 N=1
make compare DIRS="results/E04_particle_count/001 results/E04_particle_count/002"
```
`python -m pfexp.run experiments/E04_particle_count.yaml --use 1`

## Running in the background

`make run` stops when the terminal it runs in is closed, and so does a VS Code window. For long runs, start
them in the background instead. They keep running inside the container after VS Code, the terminal or an SSH
connection is closed:

```bash
make start E=E01        # like make run E=E01, in the background (make start-all: every experiment)
make running            # is it still going?
make log                # follow its output; Ctrl+C stops following, not the run
make stop               # stop it; finished runs are kept, make start E=E01 again continues
```
`bash tools/background.sh start E01 experiments/E01_*.yaml` (output in `.build/logs/E01.log`)

One background run at a time, so runs don't compete for the same cores. The container restarts by itself
after a reboot; a run cut off by a reboot does not, so start it again and it skips what is done.

## Resample-move (E05)

1. Write the move technique: one new file, `pfexp/techniques/moves/resample_move_mh.py`. How to write a
   technique: [pfexp/README.md](../pfexp/README.md), "Adding a sampling technique". A move gets the resampled
   particles and a `context` with `model`, `control` and `measurement` (localization) or `observations`
   (FastSLAM). For localization, `context["model"].log_likelihood(poses, measurement)` and `.propagate(...)`
   are what a Metropolis-Hastings step needs.
2. `make test`. The technique tests pick up the new file automatically.
3. `make run E=E05`. Until the file exists, the runner skips E05 and says why.
4. Compare against plain resampling:
   ```bash
   make compare DIRS="results/E01_resampling_scheme_localization results/E05_resample_move"
   ```
   `python -m pfexp.compare results/E01_resampling_scheme_localization results/E05_resample_move` (writes `results/comparisons/`)

## gmapping on real data (E06)

```bash
make run E=E06
```
This needs gmapping built (`make setup` does it) and the datasets downloaded. There is no ground truth on real
logs, so it records the effective sample size, how often gmapping resampled, and the runtime.

## Into the report

See [report/README.md](../report/README.md). In short: write the text in `report/v2/sections/`, then run
`make report`. It lists any experiment whose results are still missing.

## Running on several computers

`results/` is tracked in git, and each run is its own small file named by a hash of its settings and seed.
So you can continue a result set on another computer:

```bash
git pull                   # get runs made elsewhere
make run E=E03             # runs only what is still missing
git add results && git commit -m "E03 runs"   && git push
```

Give each computer different experiments. Start a new number (`make new`, `make redo`, or an experiment's first
run) on one computer and push it before another computer continues it, so both use the same set. If two
computers make the same run, git reports a conflict on that run's file. The numbers are the same (only the host,
date and runtime differ), so keep either copy.

## Changing an experiment

- **Changing a parameter in the YAML** (`filter`, `world`, `fixed`, `vary`): `make new` if it is a deliberate
  change, `make redo` if the earlier setting was a mistake (see "Numbered result sets").
- **Changing the code** that produces numbers (`pfexp/filters`, `techniques`, `metrics`, `worlds.py`, ...) marks
  the stored runs as made with older code. `make status` and the summary show this. `make redo E=<experiment>`
  if the change can affect the numbers.
- **More seeds**: raise `seeds:`. Only the new seeds run, into the same number.
- **Title, question, hypothesis or `report:`** do not change any run: `make analyse E=<experiment>`.

## Adding an experiment

Copy the config closest to what you want and edit it:

```yaml
title: Short question as a title
question: >
  The question in one or two sentences.
hypothesis: >
  What you expect, and why.
filter: mcl                 # mcl (localization), fastslam, or gmapping
world: {}                   # world settings to change, e.g. {n_steps: 100}
fixed:                      # the same for every run
  proposal: motion_model
  trigger: {name: ess_threshold, threshold: 0.5}
vary:                       # every combination is run
  resampler: [multinomial, systematic]
  n_particles: [50, 200]    # a numeric setting goes on the x axis of the figures
seeds: 20
quick:                      # the small version for make quick (seeds, fixed, world, vary)
  seeds: 3
  vary: {n_particles: [50]}
report:
  metrics: [position_rmse, ess_mean, runtime_per_step_ms]
  traces: [ess]             # per-step plots; best with at most ~8 variants
```

Technique names are the file names in `pfexp/techniques/<kind>/`. Metric names are the keys each file in
`pfexp/metrics/` returns (e.g. `position_rmse`, `ate`, `map_error_aligned`, `ess_mean`, `unique_after_resampling`,
`resample_rate`, `nees_mean`, `runtime_per_step_ms`). Then add the experiment's table and figure to
`report/v2/sections/03_experiments.tex`.

## When something goes wrong

| You see | Do |
|---|---|
| `Error: No such container: pf-sampling-dev` | `make container` (build and start it), then `make setup` once |
| `E05_resample_move: skipped, cannot run yet` | The reason is printed below it, e.g. the plug-in file does not exist yet |
| `cannot continue 001: parameters changed` | `make redo E=...` if 001 was wrong, `make new E=... NOTE="..."` if the change is on purpose |
| `N runs were made with an older version of the code` | `make redo E=...` if the code change affects the numbers |
| `Incomplete: 12 of 160 runs stored` | The run was stopped. Run the same command again |
| A run crashes | The error names the setting. Try a single run in Python (see pfexp/README.md, "Running a filter") |
