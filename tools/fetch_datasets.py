"""Download the datasets listed in datasets.yaml into datasets/.

Each file is checked against its sha256; .gz files are unpacked next to the download.
Files that already exist are only checked, never overwritten.

    python tools/fetch_datasets.py            download whatever is missing, check the rest
    python tools/fetch_datasets.py --check    only report status, change nothing
    python tools/fetch_datasets.py --only intel
    python tools/fetch_datasets.py --dest /tmp/datasets_copy
"""
import argparse
import gzip
import hashlib
import shutil
import sys
import urllib.request
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent.parent


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check(path, expected):
    if not path.exists():
        return False, "missing"
    if sha256(path) != expected:
        return False, "checksum mismatch"
    return True, "ok"


def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".part")
    with urllib.request.urlopen(url, timeout=120) as response, open(partial, "wb") as out:
        shutil.copyfileobj(response, out)
    partial.rename(path)


def unpack(path):
    target = path.with_suffix("")
    with gzip.open(path, "rb") as src, open(target, "wb") as out:
        shutil.copyfileobj(src, out)
    return target


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report status only, change nothing")
    ap.add_argument("--only", nargs="+", metavar="NAME", help="restrict to these dataset names")
    ap.add_argument("--dest", type=Path, default=PROJECT / "datasets", help="target folder (default: datasets/)")
    args = ap.parse_args()

    datasets = yaml.safe_load((PROJECT / "datasets.yaml").read_text())["datasets"]
    if args.only:
        unknown = set(args.only) - {d["name"] for d in datasets}
        if unknown:
            sys.exit(f"unknown dataset(s): {', '.join(sorted(unknown))}")
        datasets = [d for d in datasets if d["name"] in args.only]

    problems = 0
    for d in datasets:
        path = args.dest / d["path"]
        if not path.exists() and not args.check:
            print(f"{d['name']:10s} downloading {d['url']} ...", flush=True)
            download(d["url"], path)
        ok, message = check(path, d["sha256"])
        report = [f"{path.name} {message}"]

        if ok and "unpacked" in d:
            target = path.with_suffix("")
            if not target.exists() and not args.check:
                unpack(path)
            unpacked_ok, unpacked_message = check(target, d["unpacked"])
            ok = ok and unpacked_ok
            report.append(f"{target.name} {unpacked_message}")

        problems += not ok
        print(f"{d['name']:10s} {'OK ' if ok else '!! '} {' | '.join(report)}")

    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
