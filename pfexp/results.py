"""Where results live and how single runs are stored.

    results/<experiment>/runs/<run_id>.json      settings, metrics and provenance of one run
    results/<experiment>/traces/<run_id>.csv.gz  per-step values of that run
    results/<experiment>/runs.csv                all runs in one table (rebuilt from runs/)

One small file per run means different computers add different files, so git merges them without
conflicts, and a run that is already stored is simply skipped.
"""
import hashlib
import json
import os
import platform
import socket
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from pfexp import vendor

RESULTS = vendor.PROJECT / "results"
QUICK_RESULTS = RESULTS / "quick"
PACKAGE = Path(__file__).resolve().parent


def experiment_dir(experiment_id, quick=False):
    return (QUICK_RESULTS if quick else RESULTS) / experiment_id


def run_path(folder, run_id):
    return folder / "runs" / f"{run_id}.json"


def is_done(folder, run_id):
    return run_path(folder, run_id).exists()


# Code that can change the numbers a run produces (analysis, plotting and the runner itself cannot).
RESULT_CODE = ["filters", "techniques", "metrics", "worlds.py", "particles.py", "runlog.py", "registry.py",
               "vendor.py"]


def code_fingerprint():
    """Hash of the code that produces results, plus the pinned vendor commits."""
    digest = hashlib.sha1()
    files = []
    for entry in RESULT_CODE:
        path = PACKAGE / entry
        files += sorted(path.rglob("*.py")) if path.is_dir() else [path]
    for path in files:
        digest.update(path.relative_to(PACKAGE).as_posix().encode())
        digest.update(path.read_bytes())
    digest.update((vendor.PROJECT / "vendors.yaml").read_bytes())
    return digest.hexdigest()[:12]


def provenance():
    return {
        "host": os.environ.get("PFEXP_HOST") or socket.gethostname(),
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "code": code_fingerprint(),
        "vendor_commits": {name: entry["commit"][:7] for name, entry in vendor.manifest().items()},
    }


def _write_atomically(path, write):
    """Write to a temporary file and rename, so an interrupted run never leaves a partial file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    write(temporary)
    temporary.replace(path)


def save_run(folder, spec, metrics, traces, duration):
    record = {
        "run_id": spec.run_id, "experiment": spec.experiment, "filter": spec.filter, "seed": spec.seed,
        "world": spec.world, "settings": spec.settings, "variant": spec.variant,
        "metrics": metrics, "duration_s": round(duration, 3), **provenance(),
    }
    # traces first: a run counts as done only once its json exists
    _write_atomically(folder / "traces" / f"{spec.run_id}.csv.gz",
                      lambda p: traces.to_csv(p, index=False, float_format="%.6g", compression="gzip"))
    _write_atomically(run_path(folder, spec.run_id),
                      lambda p: p.write_text(json.dumps(record, indent=1, default=_json_default)))
    return record


def _json_default(value):
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"not JSON serializable: {type(value)}")


def load_runs(folder):
    """All stored runs of an experiment, as a list of records."""
    return [json.loads(p.read_text()) for p in sorted((folder / "runs").glob("*.json"))]


def load_traces(folder, run_id):
    return pd.read_csv(folder / "traces" / f"{run_id}.csv.gz")


def clean_partial_files(folder):
    """Remove temporary files left by an interrupted run."""
    for temporary in folder.rglob(".*.tmp"):
        temporary.unlink()
