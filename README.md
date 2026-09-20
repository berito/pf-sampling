# Particle Filters for Inference in Continuous State Space

A course project for Probabilistic Graphical Models. It treats the particle filter as approximate
inference on a graphical model, with robot localization and SLAM (FastSLAM, gmapping) as examples.

## See the results

```bash
python3 show_results.py
```

Python 3 only, nothing to install. Prints a summary per experiment and opens `results/report.html`.

## What is compared

How the sampling choices inside a particle filter affect accuracy, particle degeneracy and runtime:

- resampling scheme (multinomial, residual, stratified, systematic)
- when to resample (every step, or when the particles collapse)
- proposal distribution (FastSLAM 1.0 vs 2.0)
- number of particles
- MCMC moves after resampling

The filters come from the open-source projects under Credits.

## How to run

Needs Docker and `make`.

```bash
make container   # build and start the container
make setup       # download upstream code and datasets, build gmapping
make test
make run E=E02   # run one experiment
make results
```

Results go to `results/<experiment>/001/` (tables, figures, `summary.md`). Rerunning skips finished
runs. `make status` shows which are done; `make start E=E02` runs in the background (`make log`,
`make stop`); `make` alone lists every command.

Without make: `docker exec pf-sampling-dev <command>`.

Guides: [experiments/](experiments/README.md) (running and adding experiments),
[pfexp/](pfexp/README.md) (code layout, adding a sampling technique),
[report/](report/README.md) (building the report), [tools/](tools/README.md) (scripts).

## Folders

```
pfexp/         filters, sampling techniques, metrics, runner
experiments/   one config file per experiment
results/       experiment results
report/        the LaTeX report
tools/         download, build and check scripts
tests/         tests
vendor/        upstream code (downloaded, never edited)
datasets/      datasets (downloaded)
.build/        build files (safe to delete)
```

## Credits

- **Particle filter tutorial** by Joris Elfring, Elena Torta and René van de Molengraft:
  [jelfring/particle-filter-tutorial](https://github.com/jelfring/particle-filter-tutorial) (MIT)
- **PythonRobotics** (FastSLAM) by Atsushi Sakai and contributors:
  [AtsushiSakai/PythonRobotics](https://github.com/AtsushiSakai/PythonRobotics) (MIT)
- **GMapping** by Giorgio Grisetti, Cyrill Stachniss and Wolfram Burgard:
  [OpenSLAM-org/openslam_gmapping](https://github.com/OpenSLAM-org/openslam_gmapping) (CC BY-NC-SA 2.0, non-commercial)
- **Intel Research Lab** dataset by Dirk Hähnel and **ACES3** dataset by Patrick Beeson, from
  [Cyrill Stachniss's datasets page](http://www2.informatik.uni-freiburg.de/~stachnis/datasets.html)

Licences: [THIRD_PARTY.md](THIRD_PARTY.md).
