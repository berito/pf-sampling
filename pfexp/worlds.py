"""Simulated worlds. A world is generated once per seed, so every technique sees the same data.

The localization world uses Elfring's `World` and `Robot` classes unchanged: the robot drives with
noisy motion and measures range and angle to every landmark.
"""
import contextlib
import io
from dataclasses import dataclass

import numpy as np

from pfexp import vendor

vendor.use("particle_filter_tutorial")
from simulator import Robot, World  # noqa: E402

# The world and settings of Elfring's demo_running_example.py.
ELFRING_RUNNING_EXAMPLE = {
    "size": [10.0, 10.0],
    "landmarks": [[2.0, 2.0], [2.0, 8.0], [9.0, 2.0], [8.0, 9.0]],
    "n_steps": 30,
    "start": [7.5, 2.0, 3.14 / 2.0],
    "control": [0.25, 0.02],             # setpoint: forward (m), turn (rad) per step
    "true_motion_std": [0.005, 0.002],   # forward, turn
    "true_measurement_std": [0.2, 0.05],  # range, angle
}


@dataclass
class LocalizationWorld:
    size: np.ndarray            # (2,) world is cyclic in x and y
    landmarks: np.ndarray       # (L, 2)
    true_poses: np.ndarray      # (T, 3) after each move
    controls: np.ndarray        # (T, 2) the setpoint the filter is told
    measurements: np.ndarray    # (T, L, 2) range and angle to each landmark
    settings: dict


def localization_world(seed, **overrides):
    """Simulate a localization run with Elfring's robot. `overrides` replace ELFRING_RUNNING_EXAMPLE keys."""
    settings = {**ELFRING_RUNNING_EXAMPLE, **overrides}
    unknown = set(overrides) - set(ELFRING_RUNNING_EXAMPLE)
    if unknown:
        raise TypeError(f"unknown world settings: {sorted(unknown)}")

    state = np.random.get_state()
    np.random.seed(seed)
    try:
        with contextlib.redirect_stdout(io.StringIO()):  # World() prints its landmarks
            world = World(*settings["size"], [list(map(float, lm)) for lm in settings["landmarks"]])
        robot = Robot(*settings["start"], *settings["true_motion_std"], *settings["true_measurement_std"])
        forward, turn = settings["control"]
        poses, measurements = [], []
        for _ in range(settings["n_steps"]):
            robot.move(desired_distance=forward, desired_rotation=turn, world=world)
            poses.append([robot.x, robot.y, robot.theta])
            measurements.append(robot.measure(world))
    finally:
        np.random.set_state(state)

    n = settings["n_steps"]
    return LocalizationWorld(
        size=np.array(settings["size"], dtype=float),
        landmarks=np.array(settings["landmarks"], dtype=float),
        true_poses=np.array(poses),
        controls=np.tile([forward, turn], (n, 1)).astype(float),
        measurements=np.array(measurements),
        settings={**settings, "seed": seed},
    )


# --- SLAM world ------------------------------------------------------------------------------

_modules = {}


def vendor_fastslam_module(version=1):
    """The PythonRobotics FastSLAM script as a module, imported unchanged (its main() is never called)."""
    import importlib.util

    path = vendor.use("pythonrobotics") / "SLAM" / f"FastSLAM{version}" / f"fast_slam{version}.py"
    name = f"vendor_fast_slam{version}"
    if name not in _modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.show_animation = False
        _modules[name] = module
    return _modules[name]

# The world of PythonRobotics fast_slam1.py / fast_slam2.py main().
PYTHONROBOTICS_FASTSLAM = {
    "landmarks": [[10.0, -2.0], [15.0, 10.0], [15.0, 15.0], [10.0, 20.0],
                  [3.0, 15.0], [-5.0, 20.0], [-5.0, 5.0], [-10.0, 15.0]],
    "sim_time": 50.0,
}


@dataclass
class SlamWorld:
    landmarks: np.ndarray        # (L, 2) true landmark positions
    true_poses: np.ndarray       # (T, 3)
    dead_reckoning: np.ndarray   # (T, 3) integrated noisy controls
    controls: np.ndarray         # (T, 2) noisy velocity and yaw rate the filter receives
    observations: list           # T arrays of shape (3, k): range, bearing, landmark id
    dt: float
    settings: dict


def slam_world(seed, **overrides):
    """Simulate the PythonRobotics FastSLAM scenario with its own functions, unchanged."""
    settings = {**PYTHONROBOTICS_FASTSLAM, **overrides}
    unknown = set(overrides) - set(PYTHONROBOTICS_FASTSLAM)
    if unknown:
        raise TypeError(f"unknown world settings: {sorted(unknown)}")
    fs = vendor_fastslam_module(1)
    landmarks = np.array(settings["landmarks"], dtype=float)

    state = np.random.get_state()
    np.random.seed(seed)
    try:
        x_true = np.zeros((3, 1))
        x_dr = np.zeros((3, 1))
        time, poses, dr, controls, observations = 0.0, [], [], [], []
        while settings["sim_time"] >= time:  # same loop condition as the vendor main()
            time += fs.DT
            u = fs.calc_input(time)
            x_true, z, x_dr, ud = fs.observation(x_true, x_dr, u, landmarks)
            poses.append(x_true[:, 0].copy())
            dr.append(x_dr[:, 0].copy())
            controls.append(ud[:, 0].copy())
            observations.append(z.copy())
    finally:
        np.random.set_state(state)

    return SlamWorld(
        landmarks=landmarks, true_poses=np.array(poses), dead_reckoning=np.array(dr),
        controls=np.array(controls), observations=observations, dt=fs.DT,
        settings={**settings, "seed": seed},
    )
