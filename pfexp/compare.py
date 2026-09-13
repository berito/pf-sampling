"""Compare stored results across experiments, without running anything.

    python -m pfexp.compare results/E01_resampling_scheme results/E05_resample_move --metrics position_rmse ess_mean
    python -m pfexp.compare results/E01_resampling_scheme results/E05_resample_move --name resample_move_vs_baseline

Reads each experiment's runs.csv and writes results/comparisons/<name>/ with a table (csv, md, tex) and a figure.
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pfexp import results as R
from pfexp import style
from pfexp.analysis import Z95, save


def load(folders):
    frames = []
    for folder in folders:
        table = Path(folder) / "runs.csv"
        if not table.exists():
            raise FileNotFoundError(f"{table} not found — run the experiment (or pfexp.analysis) first")
        frame = pd.read_csv(table)
        frame.insert(0, "experiment", Path(folder).name)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def compare(folders, metrics, name):
    style.apply()
    df = load(folders)
    metrics = [m for m in metrics if m in df]
    if not metrics:
        raise ValueError("none of the requested metrics are in these results")
    grouped = df.groupby(["experiment", "variant"], sort=False)
    stats = grouped[metrics].agg(["mean", "std", "count"])

    out = R.RESULTS / "comparisons" / name
    out.mkdir(parents=True, exist_ok=True)
    stats.to_csv(out / "table.csv", float_format="%.6g")
    readable = pd.DataFrame({
        "Experiment": [e for e, _ in stats.index], "Variant": [v for _, v in stats.index],
        **{style.metric_label(m): [f"{row[(m, 'mean')]:.3g} ± {row[(m, 'std')]:.2g}" for _, row in stats.iterrows()]
           for m in metrics},
    })
    (out / "table.md").write_text(readable.to_markdown(index=False) + "\n")
    (out / "table.tex").write_text(readable.to_latex(index=False, escape=True).replace("±", r"$\pm$"))

    labels = [f"{v}\n({e})" for e, v in stats.index]
    fig, axes = plt.subplots(1, len(metrics), figsize=(3.6 * len(metrics), 3.2), squeeze=False)
    experiment_colours = dict(zip(df["experiment"].unique(), style.CATEGORICAL))
    for ax, metric in zip(axes.flat, metrics):
        for i, ((experiment, _), row) in enumerate(stats.iterrows()):
            half = Z95 * row[(metric, "std")] / np.sqrt(max(1, row[(metric, "count")]))
            ax.errorbar(i, row[(metric, "mean")], yerr=half, fmt="o", color=experiment_colours[experiment],
                        markersize=6, elinewidth=2, capsize=0)
        ax.set_xticks(range(len(labels)), labels, rotation=30, ha="right", fontsize=7)
        ax.grid(axis="x", visible=False)
        ax.set_title(style.metric_label(metric), loc="left")
    fig.tight_layout()
    save(fig, out, "comparison")
    print(f"comparison written to {out.relative_to(R.RESULTS.parent)}")
    return stats


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folders", nargs="+", type=Path)
    ap.add_argument("--metrics", nargs="+", default=["position_rmse", "ess_mean", "runtime_per_step_ms"])
    ap.add_argument("--name", default=None, help="output folder name (default: joined experiment names)")
    args = ap.parse_args(argv)
    compare(args.folders, args.metrics, args.name or "_vs_".join(Path(f).name for f in args.folders))


if __name__ == "__main__":
    main()
