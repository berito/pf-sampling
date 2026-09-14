"""Where results live and how single runs are stored.

Each experiment keeps numbered result sets. A new number is an experiment run with different parameters;
a set made with wrong code or setup is replaced under its own number.

    results/<experiment>/current.txt                 the number the report and show_results.py use, e.g. 002
    results/<experiment>/<number>/parameters.yaml    the parameters this set was run with
    results/<experiment>/<number>/info.json          when it started, on which computer, code version, note
    results/<experiment>/<number>/runs/<run_id>.json      settings, metrics and provenance of one run
    results/<experiment>/<number>/traces/<run_id>.csv.gz  per-step values of that run
    results/<experiment>/<number>/runs.csv           all runs in one table (rebuilt from runs/)

One small file per run means different computers add different files, so git merges them without
conflicts, and a run that is already stored is simply skipped.
"""
import hashlib
import json
import os
import platform
import re
import shutil
import socket
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from pfexp import vendor

# PFEXP_RESULTS points everything at another folder, e.g. a temporary one for a test run.
RESULTS = Path(os.environ["PFEXP_RESULTS"]).resolve() if os.environ.get("PFEXP_RESULTS") else vendor.PROJECT / "results"
QUICK_RESULTS = RESULTS / "quick"
PACKAGE = Path(__file__).resolve().parent


def experiment_dir(experiment_id, quick=False):
    """The folder holding all numbered result sets of one experiment."""
    return (QUICK_RESULTS if quick else RESULTS) / experiment_id


# --- numbered result sets -------------------------------------------------------------------

def number_name(number):
    return f"{number:03d}"


def numbers(experiment_folder):
    """The numbers stored for an experiment, in order."""
    if not experiment_folder.is_dir():
        return []
    return sorted(int(p.name) for p in experiment_folder.iterdir() if p.is_dir() and re.fullmatch(r"\d{3}", p.name))


def number_dir(experiment_folder, number):
    return experiment_folder / number_name(number)


def current_number(experiment_folder):
    """The number in current.txt, else the highest stored number, else None."""
    stored = numbers(experiment_folder)
    pointer = experiment_folder / "current.txt"
    if pointer.exists():
        text = pointer.read_text().strip()
        if text.isdigit() and int(text) in stored:
            return int(text)
    return stored[-1] if stored else None


def set_current(experiment_folder, number):
    if number not in numbers(experiment_folder):
        raise ValueError(f"{experiment_folder.name} has no result set {number_name(number)}")
    (experiment_folder / "current.txt").write_text(number_name(number) + "\n")


def current_dir(experiment_folder):
    """The folder of the current number, or None if the experiment has not run yet."""
    number = current_number(experiment_folder)
    return None if number is None else number_dir(experiment_folder, number)


def start_number(experiment_folder, experiment, number, note=""):
    """Create (or recreate) a numbered result set, recording its parameters, and make it current."""
    folder = number_dir(experiment_folder, number)
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    write_parameters(folder, experiment)
    info = {"number": number_name(number), "note": note, **provenance()}
    (folder / "info.json").write_text(json.dumps(info, indent=1) + "\n")
    set_current(experiment_folder, number)
    return folder


def write_parameters(folder, experiment):
    stored = {**experiment.parameters(), "seeds": experiment.seeds}
    (folder / "parameters.yaml").write_text(yaml.safe_dump(stored, sort_keys=False, default_flow_style=None))


def read_parameters(folder):
    return yaml.safe_load((folder / "parameters.yaml").read_text())


def read_info(folder):
    path = folder / "info.json"
    return json.loads(path.read_text()) if path.exists() else {}


def parameter_changes(folder, experiment):
    """The parameters that differ between a stored result set and the experiment config, as readable lines."""
    stored = read_parameters(folder)
    wanted = json.loads(json.dumps(experiment.parameters()))  # same types as a YAML round trip
    changes = []
    for key, value in wanted.items():
        if stored.get(key) != value:
            changes.append(f"{key}: {stored.get(key)} -> {value}")
    return changes


def experiment_for(folder, experiment):
    """The experiment as it was run in this result set: stored parameters, config title and report settings."""
    stored = read_parameters(folder)
    return experiment.with_parameters(stored, seeds=stored.get("seeds"))


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


def count_older_runs(folder, run_ids):
    """How many of these stored runs were made with a different version of the result-producing code."""
    current = code_fingerprint()
    paths = [run_path(folder, run_id) for run_id in run_ids]
    return sum(json.loads(path.read_text())["code"] != current for path in paths if path.exists())


def load_runs(folder):
    """All stored runs of an experiment, as a list of records."""
    return [json.loads(p.read_text()) for p in sorted((folder / "runs").glob("*.json"))]


def load_traces(folder, run_id):
    return pd.read_csv(folder / "traces" / f"{run_id}.csv.gz")


def clean_partial_files(folder):
    """Remove temporary files left by an interrupted run."""
    for temporary in folder.rglob(".*.tmp"):
        temporary.unlink()
