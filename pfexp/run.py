"""Run experiments. Runs that are already stored are skipped, so this can be stopped and restarted anytime,
on any computer that has the same results/ folder.

Each experiment keeps numbered result sets (results/<experiment>/001/, 002/, ...), each with the parameters
it was run with:

    python -m pfexp.run experiments/E04_particle_count.yaml            run or continue the current number
    python -m pfexp.run experiments/E04_particle_count.yaml --redo     the current number was wrong (a bug, a wrong
                                                                        setup): delete it and run it again
    python -m pfexp.run experiments/E04_particle_count.yaml --new --note "stratified resampler"
                                                                        parameters changed on purpose: next number
    python -m pfexp.run experiments/E04_particle_count.yaml --use 1    show number 001 in the report
    python -m pfexp.run experiments/*.yaml --jobs 8
    python -m pfexp.run experiments/*.yaml --quick          small version into results/quick/
    python -m pfexp.run experiments/*.yaml --dry-run        only show what is done and what would run

A plain run refuses to continue a number whose parameters differ from the config, or whose runs were made with
other code, so results of different settings are never mixed. An experiment that cannot run yet (a technique not
written, gmapping not built) is skipped with the reason.
"""
import argparse
import multiprocessing
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from pfexp import experiment as E
from pfexp import results as R


def execute(spec_dict, folder):
    """Run one filter run and store it. Runs in a worker process."""
    import numpy as np  # noqa: F401  (imported after the thread limits are set)

    from pfexp.filters.fastslam import run_fastslam
    from pfexp.filters.gmapping import run_gmapping
    from pfexp.filters.mcl import run_mcl
    from pfexp.metrics import compute_all
    from pfexp.worlds import localization_world, slam_world

    spec = E.RunSpec(**spec_dict)
    started = time.perf_counter()
    if spec.filter == "gmapping":  # an external program: it returns metrics and traces directly
        metrics, traces = run_gmapping(spec.world, filter_seed=spec.seed, **spec.settings)
    else:
        if spec.filter == "mcl":
            log = run_mcl(localization_world(spec.seed, **spec.world), filter_seed=spec.seed, **spec.settings)
        else:
            log = run_fastslam(slam_world(spec.seed, **spec.world), filter_seed=spec.seed, **spec.settings)
        metrics, traces = compute_all(log), log.traces()
    R.save_run(Path(folder), spec, metrics, traces, time.perf_counter() - started)
    return spec.run_id, time.perf_counter() - started


def pending_runs(experiment, folder):
    specs = list(experiment.runs())
    todo = [s for s in specs if not R.is_done(folder, s.run_id)]
    return specs, todo


def blockers(experiment, folder):
    """Why the stored result set cannot be continued with this config: changed parameters, or runs still to do while
    the stored ones were made with other code (a finished set is never mixed, so a code change alone is fine)."""
    reasons = [f"parameters changed since {folder.name}: {change}" for change in R.parameter_changes(folder, experiment)]
    specs, todo = pending_runs(experiment, folder)
    older = R.count_older_runs(folder, [s.run_id for s in specs]) if todo else 0
    if older:
        reasons.append(f"{older} stored runs of {folder.name} were made with a different version of the code")
    return reasons


def choose_folder(experiment, quick=False, redo=False, new=False, note="", dry_run=False, code_change_ok=False):
    """The result set to run into, created unless this is a dry run.

    Returns (folder, message, state): state is "fresh" (a new or emptied number), "continue", or "blocked".
    """
    parent = R.experiment_dir(experiment.id, quick)
    current = R.current_number(parent)
    stored = R.numbers(parent)

    if new or current is None:
        number = (stored[-1] + 1) if stored else 1
        folder = R.number_dir(parent, number)
        if not dry_run:
            R.start_number(parent, experiment, number, note)
        return folder, f"new number {folder.name}", "fresh"

    folder = R.number_dir(parent, current)
    reasons = blockers(experiment, folder)
    if code_change_ok:
        reasons = [r for r in reasons if "version of the code" not in r]
    if redo or (reasons and quick):  # quick results are throwaway: start them again instead of asking
        why = "redo" if redo else "; ".join(reasons)
        if not dry_run:
            R.start_number(parent, experiment, current, note or R.read_info(folder).get("note", ""))
        return folder, f"{folder.name} deleted and started again ({why})", "fresh"
    if reasons:
        return folder, "\n".join(f"  - {r}" for r in reasons), "blocked"
    if not dry_run:
        R.write_parameters(folder, experiment)  # the seeds may have grown
    return folder, f"continuing {folder.name}", "continue"


BLOCKED_HELP = """  Choose what this is:
    the stored results are wrong (a bug, a wrong setup):   make redo E={id}      (--redo: deletes {number} and runs it again)
    you changed the parameters on purpose:                  make new E={id} NOTE="what changed"   (--new: next number)
    the code change cannot affect these numbers:            make run E={id} ARGS=--code-change-ok"""


def run_experiment(experiment, quick=False, redo=False, new=False, note="", jobs=1, dry_run=False, report=True,
                   code_change_ok=False):
    """Run the missing runs of one experiment. Returns False if it was blocked (see choose_folder)."""
    folder, message, state = choose_folder(experiment, quick, redo, new, note, dry_run, code_change_ok)
    if state == "blocked":
        print(f"{experiment.id}: cannot continue {folder.name}:\n{message}\n"
              + BLOCKED_HELP.format(id=experiment.id, number=folder.name))
        return False
    label = f"{experiment.id} {folder.name}" + (" (quick)" if quick else "")
    if dry_run and state == "fresh":
        print(f"{label}: {len(list(experiment.runs()))} runs to run ({'would be ' + message})")
        return True

    R.clean_partial_files(folder)
    specs, todo = pending_runs(experiment, folder)
    print(f"{label}: {len(specs)} runs, {len(specs) - len(todo)} already done, {len(todo)} to run"
          + ("" if dry_run else f"; {message}"))
    if dry_run or not todo:
        if report and not dry_run and specs:
            _report(experiment, folder)
        return True

    started = time.perf_counter()
    done = 0
    context = multiprocessing.get_context("spawn")  # fresh workers pick up the thread limits below
    with ProcessPoolExecutor(max_workers=jobs, mp_context=context) as pool:
        futures = {pool.submit(execute, vars(spec), str(folder)): spec for spec in todo}
        try:
            for future in as_completed(futures):
                spec = futures[future]
                run_id, seconds = future.result()
                done += 1
                variant = ", ".join(f"{k}={E.label(v)}" for k, v in spec.variant.items())
                print(f"  [{done}/{len(todo)}] {variant} seed={spec.seed} ({seconds:.1f}s)", flush=True)
        except KeyboardInterrupt:
            pool.shutdown(wait=False, cancel_futures=True)
            raise
    print(f"{experiment.id} {folder.name}: {done} runs in {time.perf_counter() - started:.0f}s")
    if report:
        _report(experiment, folder)
    return True


def _report(experiment, folder):
    from pfexp import analysis
    analysis.build(experiment, folder)


def use(experiment, number, quick=False):
    parent = R.experiment_dir(experiment.id, quick)
    R.set_current(parent, number)
    info = R.read_info(R.number_dir(parent, number))
    note = f" ({info['note']})" if info.get("note") else ""
    print(f"{experiment.id}: the report now uses {R.number_name(number)}{note}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("configs", nargs="+", type=Path)
    ap.add_argument("--quick", action="store_true", help="small version of each experiment into results/quick/")
    which = ap.add_mutually_exclusive_group()
    which.add_argument("--redo", action="store_true", help="delete the current number and run it again")
    which.add_argument("--new", action="store_true", help="start the next number (the parameters changed on purpose)")
    which.add_argument("--use", type=int, metavar="N", help="make number N the one the report shows; runs nothing")
    ap.add_argument("--note", default="", help="what is different about this number (with --new or --redo)")
    ap.add_argument("--code-change-ok", action="store_true",
                    help="continue although the code changed (only if the change cannot affect the numbers)")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--dry-run", action="store_true", help="only show what would run")
    ap.add_argument("--no-report", action="store_true", help="skip building tables and figures")
    args = ap.parse_args(argv)

    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ.setdefault(variable, "1")  # one thread per worker; the workers are the parallelism

    skipped, blocked = {}, []
    try:
        for config in args.configs:
            experiment = E.load(config, quick=args.quick)
            if args.use is not None:
                use(experiment, args.use, args.quick)
                continue
            problems = experiment.problems()
            if problems:  # e.g. a technique that is planned but not written yet: run the other experiments
                skipped[experiment.id] = problems
                print(f"{experiment.id}: skipped, cannot run yet")
                continue
            ok = run_experiment(experiment, quick=args.quick, redo=args.redo, new=args.new, note=args.note,
                                jobs=args.jobs, dry_run=args.dry_run, report=not args.no_report,
                                code_change_ok=args.code_change_ok)
            if not ok:
                blocked.append(experiment.id)
    except KeyboardInterrupt:
        print("\nInterrupted. Finished runs are kept; run the same command again to continue.", flush=True)
        return 130
    if skipped:
        print("\nSkipped experiments:")
        for experiment_id, problems in skipped.items():
            print(f"  {experiment_id}:")
            for problem in problems:
                print(f"    - {problem}")
    if blocked and not args.dry_run:
        print(f"\nNot run (see above): {', '.join(blocked)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
