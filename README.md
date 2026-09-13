# Particle Filters for Inference in Continuous State Space

A course project for Probabilistic Graphical Models.

Particle filters estimate things like a robot's position and map, where the variables are
continuous and exact inference isn't possible. This project treats the particle filter as
approximate inference on a graphical model, and uses robot localization and SLAM (FastSLAM,
gmapping) as examples.

## See the results

```bash
python3 show_results.py
```

This needs only Python 3 — nothing to install. It prints a summary of each experiment and opens
`results/report.html` with all tables and figures.

To check the code really produces them, rerun a small version of every experiment (a few minutes,
needs the container from "How to run" below):

```bash
docker exec pf-sampling-dev python show_results.py --quick
```

## Objective

Test how the sampling choices inside a particle filter affect its results:

- the resampling scheme (multinomial, residual, stratified, systematic)
- when to resample (every step, or only when the particles start to collapse)
- the proposal distribution (FastSLAM 1.0 vs 2.0)
- the number of particles
- MCMC moves after resampling

Each choice is compared on accuracy, particle degeneracy and runtime.

The filters come from existing open-source code (see Credits). This project adds what is needed
to run and compare the experiments.

## Status

Work in progress. The filters (localization and FastSLAM), the sampling techniques, the metrics and the
experiment pipeline are ready. The experiments themselves are being run.

## How to run

You only need Docker.

1. Build and start the container:

   ```bash
   docker build -t pf-sampling:dev .devcontainer
   docker run -d --name pf-sampling-dev --user $(id -u):$(id -g) -e PFEXP_HOST=$(hostname) \
     -v "$PWD":/workspaces/pf-sampling \
     -w /workspaces/pf-sampling \
     pf-sampling:dev sleep infinity
   ```

   Or, in VS Code, open the folder and choose **Reopen in Container**.

2. Download the upstream code and datasets, and build gmapping:

   ```bash
   docker exec pf-sampling-dev bash .devcontainer/postcreate.sh
   ```

   (VS Code does this automatically on the first start.)

3. Run an experiment:

   ```bash
   docker exec pf-sampling-dev python -m pfexp.run experiments/E01_resampling_scheme.yaml
   ```

   Results go to `results/E01_resampling_scheme/` (tables, figures and `summary.md`). If it is
   stopped, run the same command again: finished runs are kept and skipped.

To check that everything is downloaded correctly, run `python tools/fetch_vendors.py --check`
and `python tools/fetch_datasets.py --check` inside the container. To run the tests:
`docker exec pf-sampling-dev python -m pytest`.

How the code is organised and how to add a sampling technique: [pfexp/README.md](pfexp/README.md).

## Folders

```
show_results.py  shows the results (plain Python 3)
experiments/   one config file per experiment
pfexp/     project code (filters, sampling techniques, metrics, runner)
tests/         tests
tools/         download, build and run scripts
vendor/        upstream code (downloaded, never edited)
datasets/      datasets (downloaded)
results/       experiment results
.build/        build files (safe to delete)
```

## Credits

- **Particle filter tutorial** by Joris Elfring, Elena Torta and René van de Molengraft —
  [github.com/jelfring/particle-filter-tutorial](https://github.com/jelfring/particle-filter-tutorial) (MIT)
- **PythonRobotics** (FastSLAM) by Atsushi Sakai and contributors —
  [github.com/AtsushiSakai/PythonRobotics](https://github.com/AtsushiSakai/PythonRobotics) (MIT)
- **GMapping** by Giorgio Grisetti, Cyrill Stachniss and Wolfram Burgard —
  [github.com/OpenSLAM-org/openslam_gmapping](https://github.com/OpenSLAM-org/openslam_gmapping) (CC BY-NC-SA 2.0, non-commercial)
- **2D-Grid-SLAM** by toolbuddy —
  [github.com/toolbuddy/2D-Grid-SLAM](https://github.com/toolbuddy/2D-Grid-SLAM) (GPL-3.0)
- **Intel Research Lab** dataset by Dirk Hähnel and **ACES3** dataset by Patrick Beeson, from
  [Cyrill Stachniss's datasets page](http://www2.informatik.uni-freiburg.de/~stachnis/datasets.html)

Licence details: [THIRD_PARTY.md](THIRD_PARTY.md).
