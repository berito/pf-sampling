# pfexp

The experiment package: particle filters with swappable sampling steps.

```
registry.py        looks up techniques and metrics by name
particles.py       particle set and small helpers (normalizing, ESS, pose mean, Gaussians)
runlog.py          what every run records, step by step
worlds.py          simulated worlds, the same for every technique with the same seed
vendor.py          the only way to reach vendor/ and datasets/
filters/           localization (mcl), FastSLAM, and gmapping (runs the C++ program), built on the upstream code
techniques/        resamplers/, triggers/, proposals/, moves/: one file per technique
metrics/           one file per metric
```

A filter step is: **proposal** (sample new poses, compute weights), then **trigger** (resample now?), then
**resampler** (which particles survive), then **move** (optional, after resampling).

## Running experiments

The guide is [experiments/README.md](../experiments/README.md) (with short `make` commands). The underlying commands:

```bash
python -m pfexp.run experiments/E01_resampling_scheme_localization.yaml     # runs what is missing, then builds the report
python -m pfexp.run experiments/*.yaml --quick                 # small version into results/quick/
python -m pfexp.analysis experiments/E01_resampling_scheme_localization.yaml  # rebuild tables and figures only
python -m pfexp.run experiments/E04_particle_count.yaml --new --note "what changed"   # next numbered result set
python -m pfexp.run experiments/E04_particle_count.yaml --redo   # the current result set was wrong: run it again
python -m pfexp.compare results/E01_resampling_scheme_localization results/E05_resample_move   # across experiments
```

An experiment is a YAML file: a question, the fixed settings, the settings to vary, and the number of
seeds (see `experiment.py`). Set `PFEXP_RESULTS=/some/folder` to store results somewhere other than `results/`. Each run is stored as one file named by a hash of its settings and seed, so
a run that already exists (from this computer or another one) is skipped.

## Running a filter

```python
from pfexp.worlds import localization_world
from pfexp.filters.mcl import run_mcl
from pfexp.metrics import compute_all

world = localization_world(seed=0)
log = run_mcl(world, n_particles=500, resampler="systematic",
              trigger={"name": "ess_threshold", "threshold": 0.5})
print(compute_all(log))
```

`run_fastslam(slam_world(seed=0), proposal="fastslam2")` works the same way.

## Adding a sampling technique

1. Create one file in the folder for its kind, e.g. `techniques/resamplers/my_resampler.py`.
2. Subclass the matching base class from `techniques/base.py` and register it with a name:

   ```python
   import numpy as np

   from pfexp.registry import register
   from pfexp.techniques.base import Resampler


   @register("resampler", "my_resampler")
   class MyResampler(Resampler):
       def resample(self, weights):
           return np.random.choice(len(weights), size=len(weights), p=weights)
   ```

3. Use the name in an experiment config or a `run_*` call: `resampler="my_resampler"`.

That's all. The file is found automatically, and `tests/test_plugins.py` runs every registered technique,
so `python -m pytest` tests the new one too.

What each kind implements:

| Kind | Folder | Method |
|---|---|---|
| resampler | `techniques/resamplers/` | `resample(weights)` returns indices |
| trigger | `techniques/triggers/` | `should_resample(weights)` returns a bool |
| proposal | `techniques/proposals/` | `propose(particles, control, measurement, model, resampler)` returns `(particles, log_weights)`; set `filter = "mcl"` or `"fastslam"` |
| move | `techniques/moves/` | `move(particles, context)` returns particles |
| metric | `metrics/` | `compute(log)` returns a dict |

If a technique takes parameters, accept them in `__init__` and return them from `describe()` so they are
recorded with every run. In a config: `trigger: {name: ess_threshold, threshold: 0.5}`.

Use `np.random` for randomness; each run seeds it, so results are reproducible.

## Code borrowed from upstream

Files that copy upstream code say so in their header: the source file and commit, the licence, and what was
changed. Bug fixes can be switched off (`upstream_bugs=True` or `wrap_angle_residual=False`), and the tests
check that the copies match the upstream functions when they are.
