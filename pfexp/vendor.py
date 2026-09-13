"""The single place our code reaches upstream code in vendor/ and data in datasets/.

Nothing else in the project hardcodes a vendor or dataset path. If something has not been
fetched yet, the error says which script to run instead of failing on an import.
"""
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parents[1]
VENDOR_DIR = PROJECT / "vendor"
DATASETS_DIR = PROJECT / "datasets"


class NotFetchedError(RuntimeError):
    pass


def manifest():
    """The vendors.yaml entries, keyed by name."""
    entries = yaml.safe_load((PROJECT / "vendors.yaml").read_text())["vendors"]
    return {entry["name"]: entry for entry in entries}


def path(name):
    """Folder of a fetched vendor repo."""
    if name not in manifest():
        raise KeyError(f"'{name}' is not listed in vendors.yaml")
    repo = VENDOR_DIR / name
    if not repo.is_dir():
        raise NotFetchedError(f"vendor/{name} is missing, run: python tools/fetch_vendors.py --only {name}")
    return repo


def use(name, subdir=""):
    """Make a vendor repo (or a folder inside it) importable, and return that folder."""
    folder = path(name) / subdir
    if not folder.is_dir():
        raise NotFetchedError(f"vendor/{name}/{subdir} not found, check the sparse paths in vendors.yaml")
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
    return folder


def commit(name):
    """Commit a vendor repo is actually at, for recording in experiment results."""
    return subprocess.run(
        ["git", "-C", str(path(name)), "rev-parse", "HEAD"],
        check=True, text=True, capture_output=True,
    ).stdout.strip()


def dataset(relative):
    """Path of a fetched dataset file, e.g. dataset('carmen/intel.log')."""
    file = DATASETS_DIR / relative
    if not file.exists():
        raise NotFetchedError(f"datasets/{relative} is missing, run: python tools/fetch_datasets.py")
    return file
