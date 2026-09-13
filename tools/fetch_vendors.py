"""Fetch the upstream repositories listed in vendors.yaml into vendor/.

Each repo is cloned shallowly at its pinned commit (and sparsely, if the manifest says so).
An existing clone is never modified: if it is at the wrong commit or has local changes, this
script reports it and leaves it alone.

    python tools/fetch_vendors.py            fetch whatever is missing, check the rest
    python tools/fetch_vendors.py --check    only report status, change nothing
    python tools/fetch_vendors.py --only pythonrobotics
    python tools/fetch_vendors.py --dest /tmp/vendor_copy
"""
import argparse
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent.parent


def git(repo, *args, capture=True):
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def status(repo, commit):
    """Return (ok, message) for an existing clone."""
    if not (repo / ".git").exists():
        return False, "exists but is not a git clone"
    head = git(repo, "rev-parse", "HEAD")
    if head != commit:
        return False, f"at {head[:7]}, expected {commit[:7]}"
    changes = git(repo, "status", "--porcelain", "--ignored")
    if changes:
        n = len(changes.splitlines())
        return False, f"at {commit[:7]} but has {n} local change(s), see `git -C {repo} status --ignored`"
    return True, f"ok at {commit[:7]}"


def fetch(repo, url, commit, sparse):
    repo.mkdir(parents=True)
    git(repo, "init", "--quiet")
    git(repo, "remote", "add", "origin", url)
    if sparse:
        # Exact paths only (no cone mode, which would also pull in every top-level file).
        git(repo, "sparse-checkout", "set", "--no-cone", *("/" + path for path in sparse))
    git(repo, "fetch", "--quiet", "--depth", "1", "origin", commit)
    git(repo, "checkout", "--quiet", "--detach", "FETCH_HEAD")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report status only, change nothing")
    ap.add_argument("--only", nargs="+", metavar="NAME", help="restrict to these vendor names")
    ap.add_argument("--dest", type=Path, default=PROJECT / "vendor", help="target folder (default: vendor/)")
    args = ap.parse_args()

    vendors = yaml.safe_load((PROJECT / "vendors.yaml").read_text())["vendors"]
    if args.only:
        unknown = set(args.only) - {v["name"] for v in vendors}
        if unknown:
            sys.exit(f"unknown vendor(s): {', '.join(sorted(unknown))}")
        vendors = [v for v in vendors if v["name"] in args.only]

    problems = 0
    for v in vendors:
        repo = args.dest / v["name"]
        if repo.exists():
            ok, message = status(repo, v["commit"])
        elif args.check:
            ok, message = False, "missing, run without --check to fetch"
        else:
            print(f"{v['name']:26s} fetching {v['url']} @ {v['commit'][:7]} ...", flush=True)
            fetch(repo, v["url"], v["commit"], v.get("sparse"))
            ok, message = status(repo, v["commit"])
        problems += not ok
        print(f"{v['name']:26s} {'OK ' if ok else '!! '} {message}")

    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
