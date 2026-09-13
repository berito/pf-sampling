"""Show the experiment results.

    python3 show_results.py              show the stored results (needs only Python 3, nothing to install)
    python3 show_results.py --quick      first rerun a small version of every experiment, then show it
    python3 show_results.py --no-open    don't open the report in a browser

Prints a summary of each experiment and writes one self-contained page, results/report.html,
with all tables and figures.
"""
import argparse
import base64
import html
import json
import os
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
RESULTS = PROJECT / "results"
NOT_EXPERIMENTS = {"quick", "baseline", "comparisons"}


def find_summaries(folder):
    summaries = []
    for path in sorted(folder.glob("*/summary.json")):
        if path.parent.name not in NOT_EXPERIMENTS:
            summary = json.loads(path.read_text())
            summary["folder"] = path.parent
            summaries.append(summary)
    return summaries


# --- terminal ------------------------------------------------------------------------------

def text_table(header, rows):
    widths = [max(len(str(cell)) for cell in column) for column in zip(header, *rows)]
    line = lambda cells: "  ".join(str(c).ljust(w) for c, w in zip(cells, widths))  # noqa: E731
    return "\n".join([line(header), line("-" * w for w in widths)] + [line(row) for row in rows])


def print_summary(summary):
    print("=" * 100)
    print(summary["title"])
    print("=" * 100)
    print(f"Question: {summary['question']}\n")
    print(text_table(summary["table"]["header"], summary["table"]["rows"]))
    print("(mean ± standard deviation over seeds)\n")
    for finding in summary["findings"]:
        print(f"  • {finding}")
    for note in summary["notes"]:
        print(f"  ! {note}")
    print()


# --- html ----------------------------------------------------------------------------------

STYLE = """
body { font: 15px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; color: #0b0b0b; background: #fcfcfb;
       margin: 0; padding: 0 16px; }
main { max-width: 1040px; margin: 0 auto; padding: 32px 0 64px; }
h1 { font-size: 26px; margin: 0 0 4px; }
h2 { font-size: 20px; margin: 48px 0 4px; padding-top: 24px; border-top: 1px solid #e4e3df; }
.muted { color: #52514e; }
nav a { display: block; color: #2a78d6; text-decoration: none; }
.question { font-size: 16px; }
ul.setup, ul.findings { padding-left: 20px; }
.findings li { margin-bottom: 4px; }
.note { color: #8a5a00; }
.table { overflow-x: auto; }
table { border-collapse: collapse; font-size: 13px; font-variant-numeric: tabular-nums; margin: 12px 0 4px; }
th, td { padding: 6px 10px; text-align: left; border-bottom: 1px solid #e4e3df; white-space: nowrap; }
th { color: #52514e; font-weight: 600; }
img { max-width: 100%; height: auto; display: block; margin: 16px 0; }
footer { margin-top: 48px; font-size: 13px; }
"""


def image_tag(path):
    if not path.exists():
        return ""
    data = base64.b64encode(path.read_bytes()).decode()
    return f'<img alt="{html.escape(path.stem)}" src="data:image/png;base64,{data}">'


def experiment_section(summary):
    e = html.escape
    header = "".join(f"<th>{e(h)}</th>" for h in summary["table"]["header"])
    rows = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in row) + "</tr>" for row in summary["table"]["rows"])
    parts = [
        f'<h2 id="{e(summary["id"])}">{e(summary["title"])}</h2>',
        f'<p class="question">{e(summary["question"])}</p>',
    ]
    if summary.get("hypothesis"):
        parts.append(f'<p class="muted"><b>Hypothesis.</b> {e(summary["hypothesis"])}</p>')
    parts.append('<ul class="setup muted">' + "".join(f"<li>{e(s)}</li>" for s in summary["setup"]) + "</ul>")
    parts.append(f'<div class="table"><table><tr>{header}</tr>{rows}</table></div>')
    parts.append('<p class="muted">Mean ± standard deviation over seeds.</p>')
    if summary["findings"]:
        parts.append("<p><b>Findings</b> <span class=muted>(computed automatically)</span></p>")
        parts.append('<ul class="findings">' + "".join(f"<li>{e(f)}</li>" for f in summary["findings"]) + "</ul>")
    parts += [f'<p class="note">{e(n)}</p>' for n in summary["notes"]]
    parts += [image_tag(summary["folder"] / figure) for figure in summary["figures"]]
    return "\n".join(parts)


def write_report(summaries, folder, quick):
    title = "Particle Filters for Inference in Continuous State Space"
    kind = "Quick rerun (few seeds, smaller settings)" if quick else "Stored results"
    runs = sum(s["runs"] for s in summaries)
    hosts = sorted({h for s in summaries for h in s.get("hosts", [])})
    nav = "".join(f'<a href="#{html.escape(s["id"])}">{html.escape(s["title"])}</a>' for s in summaries)
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Results — {html.escape(title)}</title><style>{STYLE}</style></head>
<body><main>
<h1>{html.escape(title)}</h1>
<p class="muted">{kind} · {len(summaries)} experiment{"s" if len(summaries) != 1 else ""} · {runs} runs · computed on {html.escape(", ".join(hosts))}</p>
<nav>{nav}</nav>
{"".join(experiment_section(s) for s in summaries)}
<footer class="muted">Generated {datetime.now():%Y-%m-%d %H:%M} by show_results.py.
Each experiment's tables (csv, md, tex) and figures (pdf, png) are in its folder under {html.escape(str(folder.relative_to(PROJECT)))}/.</footer>
</main></body></html>
"""
    path = folder / "report.html"
    path.write_text(page, encoding="utf-8")
    return path


# --- quick rerun ---------------------------------------------------------------------------

USE_CONTAINER = """Run it inside the dev container instead (see README.md, "How to run"):
    docker exec pf-sampling-dev python show_results.py --quick"""


def rerun_quick():
    try:
        import matplotlib, numpy, pandas, yaml  # noqa: F401, E401
    except ImportError as missing:
        sys.exit(f"--quick needs the project's Python libraries ({missing.name} is missing).\n{USE_CONTAINER}")
    if not (PROJECT / "pfexp").is_dir() or not (PROJECT / "vendor" / "particle_filter_tutorial").is_dir():
        sys.exit(f"--quick needs the project code and the downloaded upstream code (vendor/).\n{USE_CONTAINER}")
    configs = sorted(str(p) for p in (PROJECT / "experiments").glob("*.yaml"))
    env = {**os.environ, "PYTHONPATH": str(PROJECT) + os.pathsep + os.environ.get("PYTHONPATH", "")}
    print(f"Running a small version of {len(configs)} experiment{'s' if len(configs) != 1 else ''}...\n")
    if subprocess.run([sys.executable, "-m", "pfexp.run", *configs, "--quick"], env=env, cwd=PROJECT).returncode != 0:
        sys.exit(f"The quick rerun did not finish (see the messages above).\n{USE_CONTAINER}")
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true", help="rerun a small version of every experiment first")
    ap.add_argument("--no-open", action="store_true", help="don't open the report in a browser")
    args = ap.parse_args()

    if args.quick:
        rerun_quick()
    folder = RESULTS / "quick" if args.quick else RESULTS
    summaries = find_summaries(folder)
    if not summaries:
        print(f"No results found in {folder.relative_to(PROJECT)}/.")
        print("Run the experiments first, or try:  docker exec pf-sampling-dev python show_results.py --quick")
        return 1

    for summary in summaries:
        print_summary(summary)
    report = write_report(summaries, folder, args.quick)
    print(f"Full report with figures: {report.relative_to(PROJECT)}")
    if not args.no_open:
        webbrowser.open(report.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
