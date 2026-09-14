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

This needs only Python 3, nothing to install. It prints a summary of each experiment and opens
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

You only need Docker (and `make`, which most systems have).

1. Build and start the container, then download the upstream code and datasets and build gmapping:

   ```bash
   make container
   make setup
   ```

   Or, in VS Code, open the folder and choose **Reopen in Container** (it runs the setup by itself).

2. Check that everything works, and see which experiment runs are done:

   ```bash
   make test
   make status
   ```

3. Run an experiment, and look at the results:

   ```bash
   make run E=E02
   make results
   ```

   Results go to a numbered set, `results/<experiment>/001/` (tables, figures and `summary.md`). If a run is
   stopped, run the same command again: finished runs are kept and skipped. For long runs, `make start E=E02`
   runs it in the background, so it keeps going after VS Code or the terminal is closed (`make log` to follow,
   `make stop`). After changing a parameter, `make new E=E02` keeps the earlier set; see the experiments guide.

`make` on its own lists every command. Each one is also written out in full in the guides, if you prefer
not to use make:

- [experiments/README.md](experiments/README.md): the experiments, the order to run them in, and adding one
- [report/README.md](report/README.md): building and writing the report
- [pfexp/README.md](pfexp/README.md): how the code is organised, and adding a sampling technique
- [tools/README.md](tools/README.md): download, build and gmapping scripts

Without make: `docker exec pf-sampling-dev <command>`, e.g. `docker exec pf-sampling-dev python -m pytest`.

## Folders

```
show_results.py  shows the results (plain Python 3)
Makefile       short commands (`make` lists them)
report/        the LaTeX report (`make report` builds report/report.pdf)
experiments/   one config file per experiment, and the guide to running them
pfexp/     project code (filters, sampling techniques, metrics, runner)
tests/         tests
tools/         download, build and check scripts
vendor/        upstream code (downloaded, never edited)
datasets/      datasets (downloaded)
results/       experiment results
.build/        build files (safe to delete)
```

## Credits

- **Particle filter tutorial** by Joris Elfring, Elena Torta and René van de Molengraft:
  [github.com/jelfring/particle-filter-tutorial](https://github.com/jelfring/particle-filter-tutorial) (MIT)
- **PythonRobotics** (FastSLAM) by Atsushi Sakai and contributors:
  [github.com/AtsushiSakai/PythonRobotics](https://github.com/AtsushiSakai/PythonRobotics) (MIT)
- **GMapping** by Giorgio Grisetti, Cyrill Stachniss and Wolfram Burgard:
  [github.com/OpenSLAM-org/openslam_gmapping](https://github.com/OpenSLAM-org/openslam_gmapping) (CC BY-NC-SA 2.0, non-commercial)
- **Intel Research Lab** dataset by Dirk Hähnel and **ACES3** dataset by Patrick Beeson, from
  [Cyrill Stachniss's datasets page](http://www2.informatik.uni-freiburg.de/~stachnis/datasets.html)

Licence details: [THIRD_PARTY.md](THIRD_PARTY.md).
