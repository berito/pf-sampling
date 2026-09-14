# Tools: build, download and run scripts

```
tools/
  fetch_vendors.py         download the upstream code at the pinned commits (--check: verify only)
  fetch_datasets.py        download the datasets and verify checksums (--check: verify only)
  run_vendor_baseline.py   rerun the upstream demos unchanged, into results/baseline/
  build_gmapping.sh        copy vendor gmapping to .build/, patch, build
  background.sh            run experiments in the background (make start / running / log / stop)
  patches/                 fixes applied to the .build/ copy of gmapping (never to vendor/)
```

Everything runs inside the devcontainer, so nothing is installed on the host.
Open the **project folder** in VS Code and choose *Reopen in Container*, or without VS Code:

```bash
docker run -d --init --restart unless-stopped --name pf-sampling-dev --user $(id -u):$(id -g) -e PFEXP_HOST=$(hostname) \
  -v "$PWD":/workspaces/pf-sampling \
  -w /workspaces/pf-sampling pf-sampling:dev sleep infinity
docker exec pf-sampling-dev <command>
```

The project works from any folder and any mount path; gmapping finds its libraries relative to its binaries.

## gmapping

```bash
bash tools/build_gmapping.sh
```

Then run SLAM headlessly and pull out the effective-sample-size trace:

```bash
BIN=.build/openslam_gmapping/bin
$BIN/gfs_nogui -filename datasets/carmen/aces_publicb.log \
               -particles 20 -resampleThreshold 0.5 -outfilename results/aces.gfs
$BIN/gfs2neff results/aces.gfs results/aces_neff.txt
```

The two experiment knobs are on the command line: `-particles` (N) and `-resampleThreshold`
(the ESS trigger, as a fraction of N; gmapping's default is 0.5). `-randseed` makes a run repeatable.

The sweep over both is an ordinary experiment, `experiments/E06_gmapping_resampling.yaml` (`make run E=E06`).
It calls `gfs_nogui` through `pfexp/filters/gmapping.py`, in a temporary folder under `.build/`.

`patches/0001-gmapping-modern-toolchain-fixes.patch` makes 2004-era C++ build with GCC 12 and
GNU make 4.3:

1. `Makefile`: drop the `gui` subdirectory, which needs Qt3. `gfs_nogui` does not need Qt and is
   built separately by the script.
2. `gridfastslam/gfs2rec.cpp`: a loop variable was redeclared inside its own loop body.
3. `gui/gsp_thread.cpp`: a stray `<< cout` in the middle of a stream chain.
