"""Run experiments. Runs that are already stored are skipped, so this can be stopped and restarted anytime,
on any computer that has the same results/ folder.

    python -m pfexp.run experiments/E01_resampling_scheme_localization.yaml
    python -m pfexp.run experiments/*.yaml --jobs 8
    python -m pfexp.run experiments/*.yaml --quick          small version into results/quick/
    python -m pfexp.run experiments/E01_resampling_scheme_localization.yaml --rerun    run everything again
    python -m pfexp.run experiments/*.yaml --dry-run        only show what is done and what would run

An experiment that cannot run yet (a technique not written, gmapping not built) is skipped with the reason.
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


def pending_runs(experiment, folder, rerun=False):
    specs = list(experiment.runs())
    todo = specs if rerun else [s for s in specs if not R.is_done(folder, s.run_id)]
    return specs, todo


def run_experiment(experiment, quick=False, rerun=False, jobs=1, dry_run=False, report=True):
    folder = R.experiment_dir(experiment.id, quick)
    if folder.exists():
        R.clean_partial_files(folder)
    specs, todo = pending_runs(experiment, folder, rerun)
    older = R.count_older_runs(folder, [s.run_id for s in specs])
    print(f"{experiment.id}: {len(specs)} runs, {len(specs) - len(todo)} already done, {len(todo)} to run"
          + (" (quick)" if quick else "")
          + (f"; {older} made with older code (--rerun to redo them)" if older and not rerun else ""))
    if dry_run or not todo:
        if report and not dry_run and specs:
            _report(experiment, folder)
        return

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
    print(f"{experiment.id}: {done} runs in {time.perf_counter() - started:.0f}s")
    if report:
        _report(experiment, folder)


def _report(experiment, folder):
    from pfexp import analysis
    analysis.build(experiment, folder)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("configs", nargs="+", type=Path)
    ap.add_argument("--quick", action="store_true", help="small version of each experiment into results/quick/")
    ap.add_argument("--rerun", action="store_true", help="run again even if results exist")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--dry-run", action="store_true", help="only show what would run")
    ap.add_argument("--no-report", action="store_true", help="skip building tables and figures")
    args = ap.parse_args(argv)

    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ.setdefault(variable, "1")  # one thread per worker; the workers are the parallelism

    skipped = {}
    try:
        for config in args.configs:
            experiment = E.load(config, quick=args.quick)
            problems = experiment.problems()
            if problems:  # e.g. a technique that is planned but not written yet: run the other experiments
                skipped[experiment.id] = problems
                print(f"{experiment.id}: skipped, cannot run yet")
                continue
            run_experiment(experiment, quick=args.quick, rerun=args.rerun, jobs=args.jobs,
                           dry_run=args.dry_run, report=not args.no_report)
    except KeyboardInterrupt:
        print("\nInterrupted. Finished runs are kept; run the same command again to continue.", flush=True)
        return 130
    if skipped:
        print("\nSkipped experiments:")
        for experiment_id, problems in skipped.items():
            print(f"  {experiment_id}:")
            for problem in problems:
                print(f"    - {problem}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
