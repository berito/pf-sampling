"""Private project-management check for Claude (not part of the shared project; .claude/ can be untracked as a whole).

    docker exec pf-sampling-dev python .claude/tools/check_milestones.py            the current phase (the first not done)
    docker exec pf-sampling-dev python .claude/tools/check_milestones.py P1 P2      these phases
    docker exec pf-sampling-dev python .claude/tools/check_milestones.py all        every phase
    docker exec pf-sampling-dev python .claude/tools/check_milestones.py --fast     skip test suite, pipeline run, report build

For each phase in docs/project/TASKS.md it checks every step's "done when" condition automatically and prints what is
missing and the shareable command that fixes it. A phase ends with a complete report covering its experiments.
Reviews by the user are listed as "review" and don't count; a phase is closed when its row in the table in TASKS.md
is ticked, and the default skips closed phases. Exit code 0 when every checked phase is done.

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

REPORT_VERSION = "v2"   # the version of the report the current phase delivers

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

    folder = R.current_dir(R.experiment_dir(name))
    if folder is None:
        return Check(TODO, name, f"0 of {len(list(experiment.runs()))} runs stored (no result set yet)",
                     f"make start E={name}   (runs in the background)")
    changes = R.parameter_changes(folder, experiment)
    if changes:
        return Check(TODO, name, f"parameters changed since {folder.name}: " + "; ".join(changes),
                     f"make redo E={name}  (set {folder.name} was wrong)   or   make new E={name} NOTE=\"...\"  (on purpose)")
    expected = {spec.run_id for spec in experiment.runs()}
    stored = {p.stem for p in (folder / "runs").glob("*.json")} & expected
    if len(stored) < len(expected):
        started = f"{len(stored)} of {len(expected)} runs stored in {folder.name}"
        return Check(TODO, name, started, f"make start E={name}   (continues where it stopped)")

    current = R.code_fingerprint()
    stale = sum(json.loads(R.run_path(folder, run_id).read_text())["code"] != current for run_id in stored)
    if stale:
        return Check(TODO, name, f"{stale} of {len(expected)} runs in {folder.name} were made with older code",
                     f"make redo E={name}   (or keep them if the change cannot affect the numbers)")

    summary = folder / "summary.json"
    if not summary.exists() or json.loads(summary.read_text()).get("runs") != len(expected):
        return Check(TODO, name, "all runs stored, but tables and figures are not up to date",
                     f"make analyse E={name}")
    return Check(OK, name, f"{len(expected)} runs, report in results/{name}/{folder.name}/")


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
        folder = temporary / "results" / "M3_check" / "001"

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
    checks.append(Check(REVIEW, "compare with the E01 results",
                        fix="make compare DIRS=\"results/E01_resampling_scheme_localization results/E05_resample_move\""))
    return checks


def learning(fast):
    checks = []
    has_metric = "log_likelihood" in registry.names("metric")
    checks.append(Check(OK, "metric log_likelihood") if has_metric else
                  Check(TODO, "metric log_likelihood", "no log_likelihood metric is registered",
                        "add pfexp/metrics/log_likelihood.py; the run log needs the per-step log of the summed "
                        "unnormalized weights, then: make test"))
    tested = (PROJECT / "tests" / "test_log_likelihood.py").exists()
    checks.append(Check(OK, "the metric is checked against an exact log-likelihood") if tested else
                  Check(TODO, "the metric is checked against an exact log-likelihood",
                        "tests/test_log_likelihood.py does not exist",
                        "add a linear-Gaussian case whose Kalman log-likelihood is known in closed form, "
                        "then: make test"))
    checks += experiments_done("E11")
    checks.append(Check(REVIEW, "checkpoint: review E11 (the maximum-likelihood noise against the true noise)",
                        fix="make results"))
    return checks


def gmapping_experiment(fast):
    return experiments_done("E06")


TODO_MARK = "\\todo{"


def coverage(fast):
    checks = experiments_done("E07") + experiments_done("E08")
    checks.append(Check(REVIEW, "decide: measurement-aware proposals for FastSLAM (run E09 or state as a limitation)"))
    checks.append(Check(REVIEW, "decide: crossed combinations (run E10 or state as a limitation)"))
    checks.append(Check(REVIEW, "checkpoint: review the coverage experiments", fix="make results"))
    return checks


def report_check(prefixes, fast, version=REPORT_VERSION):
    """The report covers these experiments (by config prefix), has no TODO left, and builds."""
    sections = sorted((PROJECT / "report" / version).glob("**/*.tex"))
    text = {path: path.read_text() for path in sections}
    checks = []

    # an experiment counts as shown when a float names it, or when the text says it is reported in words
    included = {m for path, body in text.items() if path.name != "macros.tex"
                for m in re.findall(r"\\experiment(?:table|figure|best)(?:\[[^\]]*\])?\{([^}]+)\}", body)}
    included |= {m for body in text.values()
                 for m in re.findall(r"% reported in the text: (\S+)", body)}
    configs = {p.stem for prefix in prefixes for p in experiment_configs(prefix)}
    all_configs = {p.stem for p in (PROJECT / "experiments").glob("*.yaml")}
    not_in_report = sorted(configs - included)
    no_config = sorted(included - all_configs)
    later = sorted(included & (all_configs - configs))
    no_results = sorted(i for i in included & configs
                        if not (R.current_dir(R.RESULTS / i) or R.RESULTS / i / "none").joinpath("tables", "summary.tex").exists())
    detail = "; ".join(filter(None, [
        f"not in the report: {', '.join(not_in_report)}" if not_in_report else "",
        f"in the report but no config: {', '.join(no_config)}" if no_config else "",
        f"no results yet: {', '.join(no_results)}" if no_results else "",
        f"from a later phase (leave out until then): {', '.join(later)}" if later else "",
    ]))
    checks.append(Check(TODO if detail else OK, f"the report has the tables and figures of {', '.join(prefixes)}", detail,
                        f"add \\experimenttable / \\experimentfigure in report/{version}/sections/, "
                        "or run the missing experiments" if detail else ""))

    todos = [f"{path.relative_to(PROJECT)}: {body.count(TODO_MARK)}"
             for path, body in text.items() if path.name != "macros.tex" and TODO_MARK in body]
    checks.append(Check(TODO if todos else OK, "no TODO left in the text", "; ".join(todos),
                        "write those parts (see report/README.md)" if todos else ""))

    if fast:
        checks.append(Check(SKIPPED, "report builds", "--fast"))
    else:
        checks.append(command_succeeds(f"report builds (report/{version}/report.pdf)",
                                       ["make", "-C", "report", f"V={version}"],
                                       f"make report V={version}   (log: .build/report/{version}/main.log)"))
    checks.append(Check(REVIEW, "checkpoint: read the PDF together; the phase ends here", fix="open report/v2/report.pdf"))
    return checks


def step(title, checks):
    """Prefix a step's checks with its title, so a phase reads as a list of steps."""
    for check in checks:
        check.what = f"{title}: {check.what}"
    return checks


PHASE1 = ("E01", "E02", "E03", "E04")     # report v1 presents all four
PHASE2 = ("E01", "E02", "E11")            # report v2 studies two sampling choices, plus the learning experiments
PHASE3 = PHASE2 + ("E05",)
PHASE4 = PHASE3 + ("E07", "E08")
PHASE5 = PHASE4 + ("E06",)


def phase1(fast):
    return (step("setup", m0(fast)) + step("sharing", m1(fast)) + step("plug-ins", m2(fast))
            + step("pipeline", m3(fast)) + step("experiments", m4(fast))
            + step("report v1", report_check(PHASE1, fast, version="v1")))


def phase2(fast):
    return step("learning", learning(fast)) + step("report v2", report_check(PHASE2, fast))


def phase3(fast):
    return step("resample-move", m5(fast)) + step("report v3", report_check(PHASE3, fast))


def phase4(fast):
    return step("coverage", coverage(fast)) + step("report v4", report_check(PHASE4, fast))


def phase5(fast):
    return step("gmapping", gmapping_experiment(fast)) + step("report v5", report_check(PHASE5, fast))


PHASES = {
    "P1": ("Core study: E01-E04 and report v1", phase1),
    "P2": ("Parameter learning: E11 and report v2", phase2),
    "P3": ("Resample-move: E05 and report v3 (if time)", phase3),
    "P4": ("Wider coverage: E07-E10 and report v4 (if time)", phase4),
    "P5": ("Real data: gmapping E06 and report v5 (if time)", phase5),
}


def closed_phases():
    """The phases ticked in the table at the top of TASKS.md. Only a person closes a phase."""
    table = (PROJECT / "docs" / "project" / "TASKS.md").read_text()
    rows = re.findall(r"^\|\s*\*\*(\d+)[^|]*\|[^|]*\|[^|]*\|\s*\[([ x])\]\s*\|\s*$", table, re.M)
    return {f"P{number}" for number, status in rows if status == "x"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phases", nargs="*", help="e.g. P1 P2, or all (default: the current phase)")
    ap.add_argument("--fast", action="store_true", help="skip the test suite, the pipeline run and the report build")
    args = ap.parse_args(argv)

    selected = [p.upper() for p in args.phases]
    if selected == ["ALL"]:
        selected = list(PHASES)
    unknown = [p for p in selected if p not in PHASES]
    if unknown:
        ap.error(f"unknown phase {unknown}; choose from {', '.join(PHASES)} or all")
    current_only = not selected
    closed = closed_phases() if current_only else set()

    next_steps, all_done = [], True
    for key in (selected or list(PHASES)):
        title, checker = PHASES[key]
        if key in closed:
            print(f"\n{key}  {title}  —  closed in TASKS.md")
            continue
        started = time.perf_counter()
        checks = checker(args.fast)
        automatic = [c for c in checks if c.status != REVIEW]
        done = all(c.status == OK for c in automatic)
        skipped = any(c.status == SKIPPED for c in automatic)
        waiting = [c for c in checks if c.status == REVIEW]
        all_done &= done
        state = ("DONE, waiting for review" if waiting else "DONE") if done else (
            "NOT CHECKED FULLY" if skipped and all(c.status in (OK, SKIPPED) for c in automatic)
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
        if current_only and not (done and not waiting):
            print("\n(later phases start only when this one is closed; see them with: all)")
            break

    print()
    if next_steps:
        print(f"Next step  →  {next_steps[0]}")
    elif all_done:
        print("Everything checked is done. Items marked ⏸ still need a person to review them.")
    return 0 if all_done else 1


if __name__ == "__main__":
    sys.exit(main())
