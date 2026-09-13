"""Run the upstream demos unchanged, with a fixed seed, and save what they produce.

The demos don't return results, so this wraps a few of their functions from the outside (no edits
to vendor/) to record the true pose and the filter estimate at every step. These recordings are the
reference that our wrapped versions of the same filters are checked against later.

    python tools/run_vendor_baseline.py                 all baselines, seed 0
    python tools/run_vendor_baseline.py --only fastslam1 --seed 3

Output: results/baseline/<name>/  trajectory.csv · stdout.log · figure_*.png
"""
import argparse
import contextlib
import csv
import importlib.util
import io
import os
import runpy
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pfexp import vendor  # noqa: E402

PROJECT = vendor.PROJECT


def save_open_figures(out):
    for number in plt.get_fignums():
        plt.figure(number).savefig(out / f"figure_{number}.png", dpi=80)
    plt.close("all")


def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def run_elfring(script, filter_class_name, out):
    """Run an Elfring demo script as-is, recording robot pose and filter estimate per step."""
    root = vendor.use("particle_filter_tutorial")
    import core.particle_filters as filters
    import simulator

    rows = []
    true_pose = {}

    original_move = simulator.Robot.move

    def move(self, *args, **kwargs):
        original_move(self, *args, **kwargs)
        true_pose.update(x=self.x, y=self.y, theta=self.theta)

    filter_class = getattr(filters, filter_class_name)
    original_update = filter_class.update

    def update(self, *args, **kwargs):
        result = original_update(self, *args, **kwargs)
        est = self.get_average_state()
        rows.append([len(rows), true_pose["x"], true_pose["y"], true_pose["theta"], *est])
        return result

    simulator.Robot.move, filter_class.update = move, update
    plt.show = lambda *a, **k: None
    plt.pause = lambda *a, **k: None
    try:
        runpy.run_path(str(root / script), run_name="__main__")
    finally:
        simulator.Robot.move, filter_class.update = original_move, original_update
    write_csv(out / "trajectory.csv", ["step", "true_x", "true_y", "true_theta", "est_x", "est_y", "est_theta"], rows)


def run_script(script, out):
    """Run a script that only prints results."""
    root = vendor.use("particle_filter_tutorial")
    runpy.run_path(str(root / script), run_name="__main__")


def run_fastslam(version, out):
    """Run a PythonRobotics FastSLAM script as-is (animation off), recording the trajectories."""
    root = vendor.use("pythonrobotics")
    path = root / "SLAM" / f"FastSLAM{version}" / f"fast_slam{version}.py"
    spec = importlib.util.spec_from_file_location(f"vendor_fast_slam{version}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.show_animation = False

    rows = []
    latest = {}
    original_observation, original_final_state = module.observation, module.calc_final_state

    def observation(*args, **kwargs):
        x_true, z, x_dr, ud = original_observation(*args, **kwargs)
        latest.update(true=x_true[:, 0].copy(), dr=x_dr[:, 0].copy())
        return x_true, z, x_dr, ud

    def calc_final_state(particles):
        x_est = original_final_state(particles)
        rows.append([len(rows), *latest["true"], *latest["dr"], *x_est[:, 0]])
        return x_est

    module.observation, module.calc_final_state = observation, calc_final_state
    module.main()
    write_csv(
        out / "trajectory.csv",
        ["step", "true_x", "true_y", "true_yaw", "dr_x", "dr_y", "dr_yaw", "est_x", "est_y", "est_yaw"],
        rows,
    )


BASELINES = {
    "elfring_sir": lambda out: run_elfring("demo_running_example.py", "ParticleFilterSIR", out),
    "elfring_ekpf": lambda out: run_elfring(
        "demo_running_example_extended_Kalman_particle_filter.py", "KalmanParticleFilter", out),
    "elfring_resampling_algorithms": lambda out: run_script("challenge1_compare_resampling_algorithms.py", out),
    "fastslam1": lambda out: run_fastslam(1, out),
    "fastslam2": lambda out: run_fastslam(2, out),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="+", choices=sorted(BASELINES), metavar="NAME")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    for name in args.only or BASELINES:
        out = PROJECT / "results" / "baseline" / name
        out.mkdir(parents=True, exist_ok=True)
        np.random.seed(args.seed)
        log = io.StringIO()
        cwd = os.getcwd()
        os.chdir(out)  # demos write files into the working directory
        try:
            with contextlib.redirect_stdout(log):
                BASELINES[name](out)
            save_open_figures(out)
        finally:
            os.chdir(cwd)
        (out / "stdout.log").write_text(f"seed={args.seed}\n" + log.getvalue())
        print(f"{name:32s} → {out.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
