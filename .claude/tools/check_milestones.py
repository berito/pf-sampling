"""Private project-management check for Claude (not part of the shared project; .claude/ can be untracked as a whole).

    docker exec pf-sampling-dev python .claude/tools/check_milestones.py            all milestones
    docker exec pf-sampling-dev python .claude/tools/check_milestones.py M3 M4      only these
    docker exec pf-sampling-dev python .claude/tools/check_milestones.py --fast     skip test suite, pipeline run, report build

For each milestone in docs/project/TASKS.md it checks the "done when" condition automatically and prints what is
missing and the shareable command that fixes it. Reviews by the user are listed as "review" and don't count.
Exit code 0 when every checked milestone is done.

It may use the project code; the project code must never refer to this file.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT))

try:
    import yaml  # noqa: F401  (a project library: its absence means we are outside the container)

    from pfexp import experiment as E
    from pfexp import registry
    from pfexp import results as R
    from pfexp.filters import gmapping
except ImportError as missing:
    sys.exit(f"The checks need the project's Python libraries ({missing.name} is missing).\n"
             "Run it inside the container:  docker exec pf-sampling-dev python .claude/tools/check_milestones.py")

OK, TODO, REVIEW, SKIPPED = "ok", "todo", "review", "skipped"
SYMBOLS = {OK: "✔", TODO: "✘", REVIEW: "⏸", SKIPPED: "–"}


@dataclass
class Check:
    status: str
    what: str
    detail: str = ""
    fix: str = ""        # the command (or action) that completes this item


def run(command, **kwargs):
    return subprocess.run(command, cwd=PROJECT, capture_output=True, text=True, **kwargs)


def last_lines(text, n=6):
    return "\n".join(text.strip().splitlines()[-n:])


# --- building blocks ------------------------------------------------------------------------

def command_succeeds(what, command, fix):
    result = run(command)
    if result.returncode == 0:
        return Check(OK, what)
    return Check(TODO, what, last_lines(result.stdout + result.stderr), fix)


def experiment_configs(prefix):
    return sorted((PROJECT / "experiments").glob(f"{prefix}_*.yaml"))


def experiment_check(path):
    """Are all runs of this experiment stored, made with the current code, and is its report built?"""
    experiment = E.load(path)
    name = experiment.id
    problems = experiment.problems()
    if problems:
        return Check(TODO, name, "cannot run yet: " + "; ".join(problems), f"make run E={name}   (after fixing the above)")

    folder = R.experiment_dir(name)
    expected = {spec.run_id for spec in experiment.runs()}
    stored = {p.stem for p in (folder / "runs").glob("*.json")} & expected
    if len(stored) < len(expected):
        started = f"{len(stored)} of {len(expected)} runs stored"
        return Check(TODO, name, started, f"make run E={name}   (continues where it stopped)")

    current = R.code_fingerprint()
    stale = sum(json.loads(R.run_path(folder, run_id).read_text())["code"] != current for run_id in stored)
    if stale:
        return Check(TODO, name, f"{stale} of {len(expected)} runs were made with older code",
                     f"make run E={name} ARGS=--rerun   (or keep them if the change cannot affect the numbers)")

    summary = folder / "summary.json"
    if not summary.exists() or json.loads(summary.read_text()).get("runs") != len(expected):
        return Check(TODO, name, "all runs stored, but tables and figures are not up to date",
                     f"make analyse E={name}")
    return Check(OK, name, f"{len(expected)} runs, report in results/{name}/")


def experiments_done(prefix):
    configs = experiment_configs(prefix)
    if not configs:
        return [Check(TODO, f"{prefix} config", f"no experiments/{prefix}_*.yaml",
                      "write the config (see experiments/README.md)")]
    return [experiment_check(path) for path in configs]


# --- milestones -----------------------------------------------------------------------------

def m0(fast):
    return [
        command_succeeds("upstream code fetched, at the pinned commits, unmodified",
                         [sys.executable, "tools/fetch_vendors.py", "--check"], "python tools/fetch_vendors.py"),
        Check(OK, "gmapping built") if gmapping.BINARY.exists()
        else Check(TODO, "gmapping built", f"{gmapping.BINARY.relative_to(PROJECT)} missing", "bash tools/build_gmapping.sh"),
    ]


def m1(fast):
    shareable = ["README.md", "THIRD_PARTY.md", "vendors.yaml", "datasets.yaml", ".devcontainer/Dockerfile",
                 "tools/fetch_vendors.py", "tools/fetch_datasets.py", "show_results.py"]
    missing = [name for name in shareable if not (PROJECT / name).exists()]
    return [
        command_succeeds("datasets downloaded, checksums match",
                         [sys.executable, "tools/fetch_datasets.py", "--check"], "python tools/fetch_datasets.py"),
        Check(OK, "shareable files present") if not missing
        else Check(TODO, "shareable files present", "missing: " + ", ".join(missing)),
        private_references(),
    ]


# Private folders, the private notes by name, and words that only belong to how we work (not to the product).
PRIVATE_PATHS = ("docs/", ".claude/", "CLAUDE.md", "check_milestones", "VENDOR_REVIEW", "TASKS.md", "ACTIONS.md",
                 "BRIEF.md", "PLAN.md", "PROPOSAL.md")
PROCESS_WORDS = ("Claude", "milestone", "Milestone", "checkpoint", "Checkpoint", "agent tooling")
SHARED_FOLDERS = ("pfexp", "tools", "tests", ".devcontainer", "report", "experiments")
SHARED_FILES = ("README.md", "THIRD_PARTY.md", "vendors.yaml", "datasets.yaml", "pyproject.toml", "Makefile",
                "show_results.py", ".gitignore")
TYPOGRAPHIC = "\u2014\u2013\u2192\u2190\u00b7\u2022\u2026\u2248\u2212\u1d40\u207b\u00b9\u00b2\u03a3\u03bc\u1e91\u00d7\u2713\u2714\u2718"
# Change-log voice: history of the work, which belongs in commit messages, not in files.
HISTORY = re.compile(r"(?i)(; now |\bno longer\b|\bearlier runs\b|\bat first\b|\bverified\b.*\bon 20\d\d|"
                     r"\bwas (moved|renamed|removed|replaced|changed)\b|\bused to be\b|\bpreviously\b)")
TEXT = {".py", ".sh", ".json", ".yaml", ".toml", ".md", ".tex", ".bib", ".txt", ""}


def private_references():
    """Shared files must not mention private folders or notes, the agent tooling, or how we work (milestones, ...)."""
    offenders = []
    paths = [p for folder in SHARED_FOLDERS for p in (PROJECT / folder).rglob("*") if p.is_file() and p.suffix in TEXT]
    paths += [PROJECT / name for name in SHARED_FILES]
    for path in paths:
        text = path.read_text(errors="ignore")
        words = PROCESS_WORDS if path.name == ".gitignore" else PRIVATE_PATHS + PROCESS_WORDS  # it may list docs/
        found = [word for word in words if word in text]
        found += sorted({ch for ch in text if ch in TYPOGRAPHIC})  # characters people rarely type in code and notes
        found += sorted({f"history: '{m.group(0).strip()}'" for m in HISTORY.finditer(text)})
        if found:
            offenders.append(f"{path.relative_to(PROJECT)} ({', '.join(found)})")
    what = "shared files do not refer to private folders or agent tooling"
    return Check(OK, what) if not offenders else Check(TODO, what, "\n".join(offenders), "remove those references")


def m2(fast):
    counts = {kind: len(registry.names(kind)) for kind in registry.KINDS}
    wanted = {"resampler": 4, "trigger": 3, "proposal": 5, "move": 1, "metric": 7}
    short = [f"{kind}: {counts[kind]} (want ≥ {n})" for kind, n in wanted.items() if counts[kind] < n]
    checks = [Check(OK, "plug-ins registered", ", ".join(f"{counts[k]} {k}s" for k in wanted)) if not short
              else Check(TODO, "plug-ins registered", "; ".join(short))]
    if fast:
        checks.append(Check(SKIPPED, "test suite passes", "--fast"))
    else:
        checks.append(command_succeeds("test suite passes (every plug-in, reproducibility, borrowed code vs upstream)",
                                       [sys.executable, "-m", "pytest", "-q"], "make test   (read the failures above)"))
    return checks


PIPELINE_CONFIG = """
title: Milestone check
question: Does the pipeline work end to end?
filter: mcl
world: {n_steps: 6}
fixed: {n_particles: 30, proposal: motion_model}
vary:
  resampler: [multinomial, systematic]
seeds: 3
report:
  metrics: [position_rmse, ess_mean]
  traces: [ess]
"""


def pipeline_check():
    """A tiny experiment in a temporary folder: run, lose two runs, resume, analyse, show the results."""
    what = "pipeline end to end: run → resume → tables, figures, summary → show_results.py"
    (PROJECT / ".build").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=PROJECT / ".build") as temporary:
        temporary = Path(temporary)
        config = temporary / "M3_check.yaml"
        config.write_text(PIPELINE_CONFIG)
        env = {**os.environ, "PFEXP_RESULTS": str(temporary / "results")}
        folder = temporary / "results" / "M3_check"

        first = run([sys.executable, "-m", "pfexp.run", str(config), "--jobs", "2"], env=env)
        if first.returncode != 0:
            return Check(TODO, what, "run failed:\n" + last_lines(first.stdout + first.stderr))
        runs = sorted((folder / "runs").glob("*.json"))
        if len(runs) != 6:
            return Check(TODO, what, f"expected 6 stored runs, found {len(runs)}")
        for path in runs[:2]:
            path.unlink()
        second = run([sys.executable, "-m", "pfexp.run", str(config), "--jobs", "2"], env=env)
        if "4 already done, 2 to run" not in second.stdout:
            return Check(TODO, what, "resume did not rerun only the 2 missing runs:\n" + last_lines(second.stdout))

        expected = ["runs.csv", "summary.md", "summary.json", "tables/summary.md", "tables/summary.tex",
                    "figures/metrics.pdf", "figures/metrics.png", "figures/trace_ess.png"]
        missing = [name for name in expected if not (folder / name).exists()]
        if missing:
            return Check(TODO, what, "missing outputs: " + ", ".join(missing))

        # the lecturer's view: plain Python, no site packages
        shown = run(["python3", "-S", "show_results.py", "--no-open"], env=env)
        if shown.returncode != 0 or not (temporary / "results" / "report.html").exists():
            return Check(TODO, what, "show_results.py failed:\n" + last_lines(shown.stdout + shown.stderr))
    return Check(OK, what)


def m3(fast):
    checks = []
    broken = []
    for path in sorted((PROJECT / "experiments").glob("*.yaml")):
        try:
            E.load(path), E.load(path, quick=True)
        except Exception as error:  # noqa: BLE001  (report any config error to the reader)
            broken.append(f"{path.name}: {error}")
    checks.append(Check(OK, "every experiment config loads (full and --quick)") if not broken
                  else Check(TODO, "every experiment config loads", "\n".join(broken), "fix the config"))
    checks.append(Check(SKIPPED, "pipeline end to end", "--fast") if fast else pipeline_check())
    checks.append(Check(REVIEW, "checkpoint: review the pipeline and a quick run",
                        fix="make quick   then open results/quick/report.html"))
    return checks


def m4(fast):
    checks = []
    for prefix in ("E01", "E02", "E03", "E04"):  # resampling scheme, when to resample, proposal, particle count
        checks += experiments_done(prefix)
    checks.append(Check(REVIEW, "checkpoint: review the results of E01–E04", fix="make results"))
    return checks


def m5(fast):
    has_move = "resample_move_mh" in registry.names("move")
    checks = [
        Check(OK, "move plug-in resample_move_mh") if has_move else
        Check(TODO, "move plug-in resample_move_mh", "pfexp/techniques/moves/resample_move_mh.py does not exist",
              "write it (see pfexp/README.md, 'Adding a sampling technique'), then: make test"),
    ]
    checks += experiments_done("E05")
    checks.append(Check(REVIEW, "compare with the M4 results",
                        fix="make compare DIRS=\"results/E01_resampling_scheme_localization results/E05_resample_move\""))
    return checks


def m6(fast):
    return experiments_done("E06")


TODO_MARK = "\\todo{"


def m7(fast):
    sections = sorted((PROJECT / "report").glob("**/*.tex"))
    text = {path: path.read_text() for path in sections}
    checks = []

    included = {m for body in text.values() for m in re.findall(r"\\experiment(?:table|figure)\{([^}]+)\}", body)}
    configs = {p.stem for p in (PROJECT / "experiments").glob("*.yaml")}
    not_in_report = sorted(configs - included)
    no_config = sorted(included - configs)
    no_results = sorted(i for i in included & configs if not (R.RESULTS / i / "tables" / "summary.tex").exists())
    detail = "; ".join(filter(None, [
        f"not in the report: {', '.join(not_in_report)}" if not_in_report else "",
        f"in the report but no config: {', '.join(no_config)}" if no_config else "",
        f"no results yet: {', '.join(no_results)}" if no_results else "",
    ]))
    checks.append(Check(TODO if detail else OK, "every experiment's table and figure are in the report", detail,
                        "add \\experimenttable / \\experimentfigure in report/sections/05_experiments.tex, "
                        "or run the missing experiments" if detail else ""))

    todos = [f"{path.relative_to(PROJECT)}: {body.count(TODO_MARK)}"
             for path, body in text.items() if path.name != "macros.tex" and TODO_MARK in body]
    checks.append(Check(TODO if todos else OK, "no TODO left in the text", "; ".join(todos),
                        "write those parts (see report/README.md)" if todos else ""))

    if fast:
        checks.append(Check(SKIPPED, "report builds", "--fast"))
    else:
        checks.append(command_succeeds("report builds (report/report.pdf)", ["make", "-C", "report"],
                                       "make report   (the LaTeX log is in .build/report/main.log)"))
    checks.append(Check(REVIEW, "checkpoint: read the PDF with your supervisor or teammates", fix="open report/report.pdf"))
    return checks


MILESTONES = {
    "M0": ("Setup complete", m0),
    "M1": ("Shareable project structure", m1),
    "M2": ("Existing code experiment-ready (plug-ins)", m2),
    "M3": ("Experiment pipeline + analysis ready", m3),
    "M4": ("Core experiments done (E01–E04)", m4),
    "M5": ("New sampler added: resample-move (E05)", m5),
    "M6": ("(optional) Real-data check with gmapping (E06)", m6),
    "M7": ("Report (LaTeX)", m7),
}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("milestones", nargs="*", help="e.g. M3 M4 (default: all)")
    ap.add_argument("--fast", action="store_true", help="skip the test suite, the pipeline run and the report build")
    args = ap.parse_args(argv)

    selected = [m.upper() for m in args.milestones] or list(MILESTONES)
    unknown = [m for m in selected if m not in MILESTONES]
    if unknown:
        ap.error(f"unknown milestone {unknown}; choose from {', '.join(MILESTONES)}")

    next_steps, all_done = [], True
    for key in selected:
        title, checker = MILESTONES[key]
        started = time.perf_counter()
        checks = checker(args.fast)
        automatic = [c for c in checks if c.status != REVIEW]
        done = all(c.status == OK for c in automatic)
        skipped = any(c.status == SKIPPED for c in automatic)
        all_done &= done
        waiting = any(c.status == REVIEW for c in checks)
        state = ("DONE, waiting for review" if waiting else "DONE") if done else ("NOT CHECKED FULLY" if skipped and all(c.status in (OK, SKIPPED) for c in automatic)
                                     else f"{sum(c.status == OK for c in automatic)}/{len(automatic)} done")
        print(f"\n{key}  {title}  —  {state}  ({time.perf_counter() - started:.0f}s)")
        for check in checks:
            print(f"   {SYMBOLS[check.status]} {check.what}" + (f"  ({check.detail})" if check.detail and "\n" not in check.detail else ""))
            if check.detail and "\n" in check.detail:
                print("       " + check.detail.replace("\n", "\n       "))
            if check.fix and check.status in (TODO, REVIEW):
                print(f"       → {check.fix}")
                if check.status == TODO:
                    next_steps.append(f"{key}: {check.fix}")

    print()
    if next_steps:
        print(f"Next step  →  {next_steps[0]}")
    elif all_done:
        print("Everything checked is done. Items marked ⏸ still need a person to review them.")
    return 0 if all_done else 1


if __name__ == "__main__":
    sys.exit(main())
