"""Turn stored runs into report-ready output for one experiment.

    results/<experiment>/<number>/runs.csv                 every run with its settings and metrics
    results/<experiment>/<number>/tables/summary.{csv,md,tex}   mean ± std per variant
    results/<experiment>/<number>/figures/*.{pdf,png}      metrics per variant and values over time
    results/<experiment>/<number>/summary.md               question, setup, table, findings, figures
    results/<experiment>/<number>/summary.json             the same, read by show_results.py

Rebuild without running anything (the current number, or --number N):
    python -m pfexp.analysis experiments/E01_resampling_scheme_localization.yaml [--number 2] [--quick]
"""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pfexp import experiment as E
from pfexp import results as R
from pfexp import style

Z95 = 1.96


# --- tables ---------------------------------------------------------------------------------

def variant_label(experiment, variant):
    if len(experiment.vary) == 1:
        return style.technique_name(next(iter(variant.values())))
    return ", ".join(f"{key}: {style.technique_name(value)}" for key, value in variant.items())


def variants_in_order(experiment):
    seen, ordered = set(), []
    for spec in experiment.runs():
        key = json.dumps(spec.variant, sort_keys=True)
        if key not in seen:
            seen.add(key)
            ordered.append(spec.variant)
    return ordered


def runs_table(experiment, records):
    """One row per stored run of the current config. Runs from older versions of the config are left out."""
    wanted = {spec.run_id for spec in experiment.runs()}
    rows = []
    for record in records:
        if record["run_id"] not in wanted:
            continue
        row = {"run_id": record["run_id"], "seed": record["seed"],
               "variant": variant_label(experiment, record["variant"]),
               "host": record["host"], "date": record["date"], "code": record["code"]}
        row.update({key: E.label(value) for key, value in record["variant"].items()})
        row.update(record["metrics"])
        rows.append(row)
    return pd.DataFrame(rows), len(records) - len(rows)


def summary_stats(df, order, metrics):
    grouped = df.groupby("variant")
    stats = pd.DataFrame(index=order)
    stats["seeds"] = grouped.size().reindex(order)
    for metric in metrics:
        if metric in df:
            stats[f"{metric}_mean"] = grouped[metric].mean().reindex(order)
            stats[f"{metric}_std"] = grouped[metric].std(ddof=1).reindex(order).fillna(0.0)
    return stats


def formatted_table(stats, metrics, experiment):
    """Header and rows of the summary table. With several varied settings, each gets its own column."""
    split = len(experiment.vary) > 1
    settings = list(experiment.vary)
    variants = {variant_label(experiment, v): v for v in variants_in_order(experiment)}
    header = ([style.setting_label(k) for k in settings] if split else ["Variant"]) + ["Seeds"]
    header += [style.metric_label(m) for m in metrics if f"{m}_mean" in stats]
    rows = []
    for variant, row in stats.iterrows():
        names = [style.technique_name(variants[variant][k]) for k in settings] if split else [variant]
        cells = names + [str(int(row["seeds"]))]
        for metric in metrics:
            if f"{metric}_mean" in stats:
                cells.append(f"{row[f'{metric}_mean']:.3g} ± {row[f'{metric}_std']:.2g}")
        rows.append(cells)
    return header, rows


def write_tables(folder, stats, header, rows):
    tables = folder / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    stats.to_csv(tables / "summary.csv", index_label="variant", float_format="%.6g")
    table = pd.DataFrame(rows, columns=header)
    (tables / "summary.md").write_text(table.to_markdown(index=False) + "\n")
    latex = table.to_latex(index=False, escape=True).replace("±", r"$\pm$")
    lines = latex.splitlines()
    header_line = next(i for i, line in enumerate(lines) if line.strip() == r"\toprule") + 1
    lines[header_line] = " & ".join(_wrapped_header(h) for h in header) + r" \\"
    (tables / "summary.tex").write_text("\n".join(lines) + "\n")
    return table


def _wrapped_header(text, width=14):
    """A LaTeX table header cell broken into lines of about `width` characters, so wide tables need less scaling."""
    words, lines = text.replace("%", r"\%").replace("_", r"\_").split(), [""]
    for word in words:
        if lines[-1] and len(lines[-1]) + 1 + len(word) > width:
            lines.append(word)
        else:
            lines[-1] = f"{lines[-1]} {word}".strip()
    return lines[0] if len(lines) == 1 else r"\shortstack[l]{" + r"\\".join(lines) + "}"


# --- findings -------------------------------------------------------------------------------

def findings(stats, metrics, prefix=""):
    """Plain sentences about which variant is best on each metric, and whether the gap is beyond noise."""
    sentences = []
    if len(stats) < 2:
        return sentences
    for metric in metrics:
        direction = style.better(metric)
        if f"{metric}_mean" not in stats or direction is None:
            continue
        mean, std, n = stats[f"{metric}_mean"], stats[f"{metric}_std"], stats["seeds"]
        half_width = Z95 * std / np.sqrt(n)
        if isinstance(direction, float):
            distance = (mean - direction).abs()
            best, worst = distance.idxmin(), distance.idxmax()
            what = f"closest to the ideal {direction:g}"
        elif direction == "lower":
            best, worst = mean.idxmin(), mean.idxmax()
            what = "lowest"
        else:
            best, worst = mean.idxmax(), mean.idxmin()
            what = "highest"
        if best == worst:
            continue
        separated = abs(mean[best] - mean[worst]) > half_width[best] + half_width[worst]
        change = abs(mean[best] - mean[worst]) / abs(mean[worst]) * 100 if mean[worst] else float("nan")
        if min(n[best], n[worst]) < 2:  # one seed has no spread to compare against
            verdict = "not tested (needs at least 2 seeds)"
        else:
            verdict = "clearly beyond the seed-to-seed spread" if separated else "within the seed-to-seed spread"
        sentences.append(
            f"{prefix}{style.METRICS.get(metric, (metric,))[0]}: {what} is {best} ({mean[best]:.3g}), "
            f"vs {worst} ({mean[worst]:.3g}), a {change:.0f}% difference, {verdict} (95% intervals)."
        )
    return sentences


def grouped_findings(experiment, df, metrics):
    """Findings that only compare like with like.

    With one varied setting, its variants are compared. With more, the first setting that is not the numeric
    sweep is compared within each combination of the others (e.g. resamplers at each particle count).
    """
    if len(experiment.vary) == 1:
        order = [variant_label(experiment, v) for v in variants_in_order(experiment)]
        order = [v for v in order if v in set(df["variant"])]
        return findings(summary_stats(df, order, metrics), metrics)
    sweep = sweep_key(experiment)
    compared = next((k for k in experiment.vary if k != sweep), next(iter(experiment.vary)))
    others = [k for k in experiment.vary if k != compared]
    sentences = []
    for values, group in df.groupby(others, sort=False):
        values = values if isinstance(values, tuple) else (values,)
        where = ", ".join(f"{k.replace('_', ' ')} = {style.technique_name(v)}" for k, v in zip(others, values))
        labels = {E.label(v): style.technique_name(v) for v in experiment.vary[compared]}
        group = group.assign(variant=group[compared].map(labels))
        order = [labels[E.label(v)] for v in experiment.vary[compared] if labels[E.label(v)] in set(group["variant"])]
        sentences += findings(summary_stats(group, order, metrics), metrics, prefix=f"At {where}: ")
    return sentences


# --- figures --------------------------------------------------------------------------------

def end_labels(ax, labels):
    """Label lines at their right end, nudging labels apart vertically so they don't overlap."""
    if not labels:
        return
    low, high = ax.get_ylim()
    gap = 0.06 * (high - low)
    labels = sorted(labels, key=lambda item: item[2])
    placed = []
    for text, x, y in labels:
        if placed and y - placed[-1] < gap:
            y = placed[-1] + gap
        placed.append(y)
        ax.annotate(text, (x, y), xytext=(4, 0), textcoords="offset points", fontsize=7,
                    color=style.INK_MUTED, va="center", annotation_clip=False)


def save(fig, figures, name):
    figures.mkdir(parents=True, exist_ok=True)
    for extension in ("pdf", "png"):
        fig.savefig(figures / f"{name}.{extension}")
    plt.close(fig)
    return f"figures/{name}.png"


def sweep_key(experiment):
    """The varied setting to put on the x axis if the experiment is a numeric sweep, else None.

    With two varied settings the other one gives one line each; if both are numeric, the last one is the x axis.
    """
    numeric = [k for k, v in experiment.vary.items() if all(isinstance(x, (int, float)) for x in v)]
    return numeric[-1] if numeric and len(experiment.vary) <= 2 else None


def metrics_figure(experiment, df, stats, order, metrics, figures):
    metrics = [m for m in metrics if m in df]
    columns = min(3, len(metrics))
    rows = int(np.ceil(len(metrics) / columns))
    fig, axes = plt.subplots(rows, columns, figsize=(3.4 * columns, 2.9 * rows), squeeze=False)
    sweep = sweep_key(experiment)
    for ax, metric in zip(axes.flat, metrics):
        if sweep:
            _metric_vs_sweep(ax, experiment, df, metric, sweep)
        else:
            _metric_per_variant(ax, experiment, df, stats, order, metric)
        ax.set_title(style.metric_label(metric), loc="left")
        if metric in style.LOG_SCALE:
            ax.set_yscale("log")
    for ax in axes.flat[len(metrics):]:
        ax.set_visible(False)
    fig.suptitle(experiment.title, x=0.01, ha="left", fontsize=11, color=style.INK)
    fig.tight_layout()
    return save(fig, figures, "metrics")


def _metric_per_variant(ax, experiment, df, stats, order, metric):
    colours = style.colours([next(iter(v.values())) if len(v) == 1 else json.dumps(v) for v in
                             variants_in_order(experiment)])
    rng = np.random.RandomState(0)
    for i, (variant, colour) in enumerate(zip(order, colours)):
        values = df.loc[df["variant"] == variant, metric].to_numpy()
        ax.scatter(i + rng.uniform(-0.12, 0.12, len(values)), values, s=10, color=colour, alpha=0.35,
                   linewidths=0)
        mean, std = stats.loc[variant, f"{metric}_mean"], stats.loc[variant, f"{metric}_std"]
        half = Z95 * std / np.sqrt(max(1, len(values)))
        below = min(half, 0.9 * mean) if metric in style.LOG_SCALE else half  # a log axis has no zero
        ax.errorbar(i, mean, yerr=[[below], [half]], fmt="o", color=colour, markersize=6, elinewidth=2, capsize=0,
                    markeredgecolor="#fcfcfb", markeredgewidth=1)
    ax.set_xticks(range(len(order)), order, rotation=25 if max(map(len, order)) > 10 else 0, ha="right"
                  if max(map(len, order)) > 10 else "center")
    ax.grid(axis="x", visible=False)
    target = style.better(metric)
    if isinstance(target, float):
        ax.axhline(target, color=style.INK_MUTED, linewidth=0.8, linestyle="--")


def _metric_vs_sweep(ax, experiment, df, metric, sweep):
    others = [k for k in experiment.vary if k != sweep]
    df = df.assign(**{sweep: pd.to_numeric(df[sweep])})  # the runs table stores settings as labels (text)
    groups = [(None, df)] if not others else list(df.groupby(others[0], sort=False))
    names = [g for g, _ in groups]
    colours = style.colours(names) if others else [style.CATEGORICAL[0]]
    ends = []
    for (name, group), colour in zip(groups, colours):
        grouped = group.groupby(sweep)[metric]
        x = np.array(sorted(grouped.groups))
        mean = grouped.mean().reindex(x).to_numpy()
        half = (Z95 * grouped.std(ddof=1) / np.sqrt(grouped.size())).reindex(x).fillna(0).to_numpy()
        label = None if name is None else style.technique_name(name)
        if label and others and all(isinstance(x, (int, float)) for x in experiment.vary[others[0]]):
            label = f"{others[0].replace('_', ' ')} = {name}"  # a bare number needs its setting's name
        ax.plot(x, mean, color=colour, marker="o", markersize=4, label=label)
        low = mean - half
        if metric in style.LOG_SCALE:  # a band below zero cannot be drawn on a log axis
            low = np.maximum(low, mean / 10)
        ax.fill_between(x, low, mean + half, color=colour, alpha=0.15, linewidth=0)
        if label:
            ends.append((label, x[-1], mean[-1]))
    values = np.array(experiment.vary[sweep], dtype=float)
    if values.min() > 0 and values.max() / values.min() >= 10:
        ax.set_xscale("log")
    ax.set_xlabel(style.technique_name(sweep).replace("_", " "))
    if others:
        ax.legend(loc="best")
    end_labels(ax, ends)


def traces_figure(experiment, folder, df, order, trace, figures):
    colours = style.colours([next(iter(v.values())) if len(v) == 1 else json.dumps(v) for v in
                             variants_in_order(experiment)])
    fig, ax = plt.subplots(figsize=(8.0, 3.4))
    for variant, colour in zip(order, colours):
        series = [R.load_traces(folder, run_id)[trace].to_numpy()
                  for run_id in df.loc[df["variant"] == variant, "run_id"]]
        if not series:
            continue
        length = min(map(len, series))
        stacked = np.array([s[:length] for s in series], dtype=float)
        mean = stacked.mean(axis=0)
        half = Z95 * stacked.std(axis=0, ddof=1) / np.sqrt(len(stacked)) if len(stacked) > 1 else 0 * mean
        steps = np.arange(length)
        ax.plot(steps, mean, color=colour, label=variant)
        ax.fill_between(steps, mean - half, mean + half, color=colour, alpha=0.15, linewidth=0)
    ax.set_xlabel("Time step   (line: mean over seeds, shaded: 95% interval)")
    ax.set_title(style.trace_label(trace), loc="left")
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False)
    fig.tight_layout()
    return save(fig, figures, f"trace_{trace}")


# --- summary --------------------------------------------------------------------------------

def setup_lines(experiment, n_runs, info=None):
    fixed = ", ".join(f"{k} = {E.label(v)}" for k, v in experiment.fixed.items()) or "defaults"
    varied = "; ".join(f"{k}: {', '.join(E.label(x) for x in v)}" for k, v in experiment.vary.items())
    info = info or {}
    number = [f"Result set {info['number']}" + (f": {info['note']}" if info.get("note") else "")] if info else []
    return number + [
        f"Filter: {experiment.filter}" + (f", world settings: {experiment.world}" if experiment.world else ""),
        f"Fixed: {fixed}",
        f"Varied: {varied}",
        f"Seeds: {len(experiment.seeds)} (each seed fixes the world and the filter's randomness, "
        f"the same for every variant), {n_runs} runs",
    ]


def build(experiment, folder):
    """Build tables, figures and summaries from whatever runs are stored in one numbered result set.

    The set's own parameters are used, so an earlier number is described as it was run."""
    style.apply()
    if (folder / "parameters.yaml").exists():
        experiment = R.experiment_for(folder, experiment)
    info = R.read_info(folder)
    records = R.load_runs(folder)
    df, outdated = runs_table(experiment, records)
    if df.empty:
        print(f"{experiment.id}: no runs of the current config yet")
        return None
    order = [variant_label(experiment, v) for v in variants_in_order(experiment)]
    order = [v for v in order if v in set(df["variant"])]
    df = df.sort_values(["variant", "seed"], key=lambda column: column.map(order.index)
                        if column.name == "variant" else column).reset_index(drop=True)
    df.to_csv(folder / "runs.csv", index=False, float_format="%.6g")
    metrics = [m for m in experiment.metrics if m in df]

    stats = summary_stats(df, order, metrics)
    header, rows = formatted_table(stats, metrics, experiment)
    write_tables(folder, stats, header, rows)
    figures_dir = folder / "figures"
    figures = [metrics_figure(experiment, df, stats, order, metrics, figures_dir)]
    for trace in experiment.traces:
        if trace in R.load_traces(folder, df["run_id"].iloc[0]):
            figures.append(traces_figure(experiment, folder, df, order, trace, figures_dir))

    expected = len(list(experiment.runs()))
    current = R.code_fingerprint()
    stale = int((df["code"] != current).sum())
    notes = []
    if len(df) < expected:
        notes.append(f"Incomplete: {len(df)} of {expected} runs stored.")
    if stale:
        notes.append(f"{stale} of {len(df)} runs were made with a different version of the code than the current one.")
    if outdated:
        notes.append(f"{outdated} stored runs have settings outside this result set's parameters and are not shown.")

    summary = {
        "id": experiment.id, "title": experiment.title, "question": experiment.question.strip(),
        "number": info.get("number", folder.name), "note": info.get("note", ""),
        "hypothesis": experiment.hypothesis.strip(), "setup": setup_lines(experiment, len(df), info),
        "table": {"header": header, "rows": rows}, "findings": grouped_findings(experiment, df, metrics),
        "figures": figures, "notes": notes, "runs": len(df), "expected_runs": expected,
        "hosts": sorted(df["host"].unique().tolist()),
    }
    (folder / "summary.json").write_text(json.dumps(summary, indent=1))
    (folder / "summary.md").write_text(summary_markdown(summary))
    print(f"{experiment.id}: report written to {folder.relative_to(R.RESULTS.parent)}/summary.md")
    return summary


def summary_markdown(summary):
    lines = [f"# {summary['title']} ({summary['number']})", "", f"**Question.** {summary['question']}", ""]
    if summary["hypothesis"]:
        lines += [f"**Hypothesis.** {summary['hypothesis']}", ""]
    lines += ["## Setup", ""] + [f"- {line}" for line in summary["setup"]] + [""]
    lines += ["## Results", "", pd.DataFrame(summary["table"]["rows"], columns=summary["table"]["header"])
              .to_markdown(index=False), "", "Mean ± standard deviation over seeds.", ""]
    if summary["findings"]:
        lines += ["## Findings (computed automatically)", ""] + [f"- {s}" for s in summary["findings"]] + [""]
    if summary["notes"]:
        lines += ["## Notes", ""] + [f"- {s}" for s in summary["notes"]] + [""]
    lines += ["## Figures", ""] + [f"![{Path(f).stem}]({f})" for f in summary["figures"]] + [""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("configs", nargs="+", type=Path)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--number", type=int, help="the numbered result set to rebuild (default: the current one)")
    args = ap.parse_args(argv)
    for config in args.configs:
        experiment = E.load(config, quick=args.quick)
        parent = R.experiment_dir(experiment.id, args.quick)
        number = args.number if args.number is not None else R.current_number(parent)
        if number is None or number not in R.numbers(parent):
            print(f"{experiment.id}: no result set to analyse yet")
            continue
        build(experiment, R.number_dir(parent, number))


if __name__ == "__main__":
    main()
