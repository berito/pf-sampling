"""gmapping (grid-based Rao-Blackwellized particle filter SLAM) on a real CARMEN log.

gmapping is C++, so a run calls its headless program `gfs_nogui` (built by tools/build_gmapping.sh) in a
temporary folder and reads the effective sample size and the resampling steps from its output file.
Real logs have no ground truth, so only sampling metrics are recorded: ESS, resampling rate and runtime.

The two settings studied are gmapping's own command-line options: the number of particles and the
resampling threshold (resample when ESS < threshold * N; gmapping's default is 0.5).
"""
import shutil
import subprocess
import tempfile
import time

import numpy as np
import pandas as pd

from pfexp import vendor

BINARY = vendor.PROJECT / ".build" / "openslam_gmapping" / "bin" / "gfs_nogui"
LOGS = {"intel": "carmen/intel.log", "aces": "carmen/aces_publicb.log"}


def problems(world):
    """Why a gmapping run cannot start yet, as a list of messages (empty when ready)."""
    found = []
    if not BINARY.exists():
        found.append("gmapping is not built, run: bash tools/build_gmapping.sh")
    name = world.get("dataset", "intel")
    if name not in LOGS:
        found.append(f"unknown dataset '{name}', expected one of {sorted(LOGS)}")
    elif not (vendor.DATASETS_DIR / LOGS[name]).exists():
        found.append(f"datasets/{LOGS[name]} is missing, run: python tools/fetch_datasets.py")
    return found


def read_output(path):
    """ESS per laser scan and whether gmapping resampled after it, from a .gfs output file."""
    ess, resampled = [], []
    with open(path, errors="ignore") as lines:
        for line in lines:
            if line.startswith("NEFF "):
                ess.append(float(line.split()[1]))
                resampled.append(False)
            elif line.startswith("RESAMPLE ") and resampled:
                resampled[-1] = True
    return np.array(ess), np.array(resampled, dtype=bool)


def run_gmapping(world, *, n_particles=30, resample_threshold=0.5, filter_seed=0):
    """Run gmapping on `world['dataset']`. Returns (metrics, traces), like a filter run after its metrics."""
    reasons = problems(world)
    if reasons:
        raise RuntimeError("; ".join(reasons))
    log = vendor.dataset(LOGS[world.get("dataset", "intel")])
    workdir = vendor.PROJECT / ".build" / "gmapping_runs"
    workdir.mkdir(parents=True, exist_ok=True)
    folder = tempfile.mkdtemp(dir=workdir)  # gmapping writes several files into its working directory
    try:
        command = [str(BINARY), "-filename", str(log), "-outfilename", "run.gfs",
                   "-particles", str(n_particles), "-resampleThreshold", str(resample_threshold),
                   "-randseed", str(filter_seed + 1)]  # randseed 0 would mean "not seeded"
        started = time.perf_counter()
        result = subprocess.run(command, cwd=folder, capture_output=True, text=True)
        seconds = time.perf_counter() - started
        if result.returncode != 0:
            raise RuntimeError(f"gfs_nogui failed ({result.returncode}): {result.stdout[-500:]}{result.stderr[-500:]}")
        ess, resampled = read_output(f"{folder}/run.gfs")
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    if len(ess) == 0:
        raise RuntimeError("gfs_nogui produced no ESS values")

    metrics = {
        "ess_mean": float(ess.mean() / n_particles), "ess_min": float(ess.min() / n_particles),
        "resample_rate": float(resampled.mean()), "resample_count": int(resampled.sum()),
        "runtime_total_s": seconds, "runtime_per_step_ms": 1000 * seconds / len(ess),
    }
    traces = pd.DataFrame({"step": np.arange(len(ess)), "ess": ess, "resampled": resampled})
    return metrics, traces
