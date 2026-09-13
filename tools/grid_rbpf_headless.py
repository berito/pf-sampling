"""Drive the grid-based RBPF headlessly.

The upstream `test.py` is an interactive OpenCV demo driven by the w/a/s/d keys, so it
cannot be used for batch experiments. This runs the same environment and filter from a
scripted action sequence and writes the resulting maps to disk instead of a window.

    python tools/grid_rbpf_headless.py --steps 120 --particles 20 --out results/
"""
import argparse
import copy
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pfexp import vendor  # noqa: E402

REPO = vendor.use("grid_rbpf_python")

import cv2  # noqa: E402
import utils  # noqa: E402
from GridMap import GridMap  # noqa: E402
from ParticleFilter import ParticleFilter  # noqa: E402
from SingleBotLaser2D import SingleBotLaser2Dgrid  # noqa: E402

FORWARD, BACKWARD, LEFT, RIGHT = 1, 2, 3, 4


def sensor_mapping(m, bot_pos, bot_param, sensor_data):
    inter = (bot_param[2] - bot_param[1]) / (bot_param[0] - 1)
    for i in range(bot_param[0]):
        if sensor_data[i] > bot_param[3] - 1 or sensor_data[i] < 1:
            continue
        theta = bot_pos[2] + bot_param[1] + i * inter
        m.GridMapLine(
            int(bot_pos[0]),
            int(bot_pos[0] + sensor_data[i] * np.cos(np.deg2rad(theta))),
            int(bot_pos[1]),
            int(bot_pos[1] + sensor_data[i] * np.sin(np.deg2rad(theta))),
        )


def adaptive_get_map(m):
    img = m.GetMapProb(
        m.boundary[0] - 20, m.boundary[1] + 20, m.boundary[2] - 20, m.boundary[3] + 20
    )
    img = (255 * img).astype(np.uint8)
    return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)


def effective_sample_size(weights):
    w = np.asarray(weights, dtype=float)
    return float(1.0 / np.sum(w ** 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=120)
    ap.add_argument("--particles", type=int, default=10)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=Path("results/grid_rbpf"))
    args = ap.parse_args()

    np.random.seed(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)

    # SensorSize, StartAngle, EndAngle, MaxDist, Velocity, Angular
    bot_param = [240, -30.0, 210.0, 150.0, 6.0, 6.0]
    bot_pos = np.array([150.0, 100.0, 0.0])
    env = SingleBotLaser2Dgrid(bot_pos, bot_param, str(REPO / "map_large.png"))

    map_param = [0.4, -0.4, 5.0, -5.0]  # lo_occ, lo_free, lo_max, lo_min
    m = GridMap(map_param, gsize=1.0)
    sensor_data = env.Sensor()
    sensor_mapping(m, env.bot_pos, env.bot_param, sensor_data)

    pf = ParticleFilter(bot_pos.copy(), bot_param, copy.deepcopy(m), args.particles)

    # Reactive drive: go forward while the path ahead is clear, otherwise turn away.
    # A fixed pattern walks the robot into walls, which collapses every particle weight.
    # Sensor index 30 looks straight ahead (the scan spans -30..210 deg over 240 rays).
    ahead = slice(20, 41)
    ess_trace = []
    collapses = 0
    turn = LEFT

    for step in range(args.steps):
        clearance = float(np.min(sensor_data[ahead]))
        if clearance < 12.0:
            action = turn
        else:
            action = FORWARD
            turn = LEFT if (step // 25) % 2 == 0 else RIGHT
        env.BotAction(action)
        sensor_data = env.Sensor()
        sensor_mapping(m, env.bot_pos, env.bot_param, sensor_data)

        pf.Feed(action, sensor_data)
        # Upstream Feed normalises by the summed likelihood, which produces NaN if every
        # particle scores zero. That is total weight collapse; fall back to uniform so the
        # run continues, and count how often it happens.
        if not np.all(np.isfinite(pf.weights)) or pf.weights.sum() <= 0:
            pf.weights = np.ones(pf.size, dtype=float) / pf.size
            collapses += 1
        ess_trace.append(effective_sample_size(pf.weights))
        pf.Resampling(sensor_data)

    best = int(np.argmax(pf.weights))
    cv2.imwrite(str(args.out / "ground_truth_map.png"), adaptive_get_map(m))
    cv2.imwrite(str(args.out / "slam_map.png"), adaptive_get_map(pf.particle_list[best].gmap))
    np.savetxt(args.out / "ess_trace.csv", np.asarray(ess_trace), delimiter=",")

    ess = np.asarray(ess_trace)
    print(f"steps={args.steps} particles={args.particles} seed={args.seed}")
    print(f"ESS mean={ess.mean():.2f} min={ess.min():.2f} max={ess.max():.2f} "
          f"(N={args.particles})")
    print(f"total weight collapses: {collapses}/{args.steps}")
    print(f"wrote {args.out}/slam_map.png, ground_truth_map.png, ess_trace.csv")


if __name__ == "__main__":
    main()
