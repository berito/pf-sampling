"""Experiment configs, the resumable runner, the analysis and show_results.py — all on a temporary results folder."""
import importlib.util
import json

import pytest

from pfexp import analysis
from pfexp import experiment as E
from pfexp import results as R
from pfexp import run as runner
from pfexp.vendor import PROJECT

CONFIG = """
title: Test experiment
question: Does the pipeline work?
hypothesis: It does.
filter: mcl
world: {n_steps: 6}
fixed: {n_particles: 30, proposal: motion_model}
vary:
  resampler: [multinomial, systematic]
seeds: 3
quick:
  seeds: 2
  fixed: {n_particles: 10}
report:
  metrics: [position_rmse, ess_mean]
  traces: [ess]
"""


@pytest.fixture
def config(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "RESULTS", tmp_path / "results")
    monkeypatch.setattr(R, "QUICK_RESULTS", tmp_path / "results" / "quick")
    path = tmp_path / "T01_test.yaml"
    path.write_text(CONFIG)
    return path


def test_config_expands_every_combination(config):
    experiment = E.load(config)
    runs = list(experiment.runs())
    assert experiment.id == "T01_test" and len(runs) == 2 * 3
    assert {r.settings["resampler"] for r in runs} == {"multinomial", "systematic"}
    assert all(r.settings["n_particles"] == 30 for r in runs)


def test_quick_overrides(config):
    quick = E.load(config, quick=True)
    assert quick.seeds == [0, 1] and quick.fixed["n_particles"] == 10


def test_run_ids_are_stable_and_distinct(config):
    first = [r.run_id for r in E.load(config).runs()]
    again = [r.run_id for r in E.load(config).runs()]
    assert first == again and len(set(first)) == len(first)


def test_invalid_configs_are_rejected(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("title: x\nquestion: y\nfilter: nope\nvary: {resampler: [systematic]}\nseeds: 1\n")
    with pytest.raises(ValueError, match="filter"):
        E.load(bad)
    bad.write_text("title: x\nquestion: y\nfilter: mcl\nfixed: {resampler: a}\nvary: {resampler: [b]}\nseeds: 1\n")
    with pytest.raises(ValueError, match="both fixed and varied"):
        E.load(bad)


def test_runner_stores_runs_skips_done_ones_and_builds_the_report(config, capsys):
    experiment = E.load(config)
    folder = R.experiment_dir(experiment.id)

    runner.run_experiment(experiment, jobs=2)
    assert len(list((folder / "runs").glob("*.json"))) == 6
    assert len(list((folder / "traces").glob("*.csv.gz"))) == 6

    record = json.loads(next((folder / "runs").glob("*.json")).read_text())
    assert {"settings", "metrics", "host", "code", "vendor_commits", "seed"} <= set(record)

    capsys.readouterr()
    runner.run_experiment(experiment, jobs=2)
    assert "6 already done, 0 to run" in capsys.readouterr().out

    summary = json.loads((folder / "summary.json").read_text())
    assert summary["runs"] == 6 and summary["notes"] == []
    assert [row[0] for row in summary["table"]["rows"]] == ["Multinomial", "Systematic"]
    for figure in summary["figures"]:
        assert (folder / figure).exists() and (folder / figure).with_suffix(".pdf").exists()
    for table in ("summary.csv", "summary.md", "summary.tex"):
        assert (folder / "tables" / table).exists()


def test_missing_runs_are_reported_and_then_filled_in(config):
    experiment = E.load(config)
    folder = R.experiment_dir(experiment.id)
    runner.run_experiment(experiment, jobs=1)
    removed = sorted((folder / "runs").glob("*.json"))[:2]
    for path in removed:
        path.unlink()
    summary = analysis.build(experiment, folder)
    assert summary["runs"] == 4 and any("Incomplete" in note for note in summary["notes"])
    specs, todo = runner.pending_runs(experiment, folder)
    assert len(todo) == 2
    runner.run_experiment(experiment, jobs=1)
    assert len(list((folder / "runs").glob("*.json"))) == 6


def test_show_results_uses_only_the_standard_library_and_writes_the_report(config, tmp_path, monkeypatch):
    experiment = E.load(config)
    runner.run_experiment(experiment, jobs=1)

    spec = importlib.util.spec_from_file_location("show_results", PROJECT / "show_results.py")
    show = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(show)
    allowed = {"argparse", "base64", "html", "json", "os", "subprocess", "sys", "webbrowser", "datetime", "pathlib"}
    source = (PROJECT / "show_results.py").read_text()
    top_level_imports = {line.split()[1].split(".")[0] for line in source.splitlines()
                         if line.startswith(("import ", "from "))}
    assert top_level_imports <= allowed, top_level_imports - allowed

    monkeypatch.setattr(show, "PROJECT", tmp_path)
    summaries = show.find_summaries(R.RESULTS)
    assert [s["id"] for s in summaries] == ["T01_test"]
    report = show.write_report(summaries, R.RESULTS, quick=False)
    page = report.read_text()
    assert "Test experiment" in page and page.count("data:image/png;base64") == len(summaries[0]["figures"])
