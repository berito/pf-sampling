"""Experiment configs, the resumable runner, numbered result sets, the analysis and show_results.py, all on a
temporary results folder."""
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
    folder = R.experiment_dir(experiment.id) / "001"

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
    folder = R.experiment_dir(experiment.id) / "001"
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


# --- numbered result sets -------------------------------------------------------------------

def changed(config, old, new):
    config.write_text(config.read_text().replace(old, new))
    return E.load(config)


def run_ids(folder):
    return sorted(p.stem for p in (folder / "runs").glob("*.json"))


def test_first_run_is_number_001_with_its_parameters(config):
    experiment = E.load(config)
    runner.run_experiment(experiment, jobs=2, report=False)
    parent = R.experiment_dir(experiment.id)
    assert R.numbers(parent) == [1] and (parent / "current.txt").read_text().strip() == "001"
    stored = R.read_parameters(parent / "001")
    assert stored["fixed"] == {"n_particles": 30, "proposal": "motion_model"} and stored["seeds"] == [0, 1, 2]
    assert {"number", "note", "host", "date", "code"} <= set(R.read_info(parent / "001"))


def test_changed_parameters_are_not_mixed_into_the_stored_set(config, capsys):
    runner.run_experiment(E.load(config), jobs=2, report=False)
    parent = R.experiment_dir("T01_test")
    before = run_ids(parent / "001")

    experiment = changed(config, "n_particles: 30", "n_particles: 40")
    assert runner.run_experiment(experiment, jobs=2, report=False) is False
    out = capsys.readouterr().out
    assert "parameters changed since 001" in out and "make redo" in out and "make new" in out
    assert run_ids(parent / "001") == before and R.numbers(parent) == [1]


def test_new_keeps_the_earlier_number_and_becomes_current(config):
    runner.run_experiment(E.load(config), jobs=2, report=False)
    parent = R.experiment_dir("T01_test")
    first = run_ids(parent / "001")

    experiment = changed(config, "n_particles: 30", "n_particles: 40")
    runner.run_experiment(experiment, new=True, note="more particles", jobs=2, report=False)
    assert R.numbers(parent) == [1, 2] and R.current_number(parent) == 2
    assert run_ids(parent / "001") == first and len(run_ids(parent / "002")) == 6
    assert R.read_parameters(parent / "001")["fixed"]["n_particles"] == 30
    assert R.read_parameters(parent / "002")["fixed"]["n_particles"] == 40
    assert R.read_info(parent / "002")["note"] == "more particles"


def test_redo_replaces_the_current_number_only(config, capsys):
    runner.run_experiment(E.load(config), jobs=2, report=False)
    parent = R.experiment_dir("T01_test")
    runner.run_experiment(changed(config, "n_particles: 30", "n_particles: 40"), new=True, jobs=2, report=False)
    kept = run_ids(parent / "001")

    experiment = changed(config, "n_particles: 40", "n_particles: 50")
    runner.run_experiment(experiment, redo=True, jobs=2, report=False)
    assert R.numbers(parent) == [1, 2] and run_ids(parent / "001") == kept
    assert R.read_parameters(parent / "002")["fixed"]["n_particles"] == 50
    assert set(run_ids(parent / "002")) == {spec.run_id for spec in experiment.runs()}


def test_more_seeds_continue_the_same_number(config, capsys):
    runner.run_experiment(E.load(config), jobs=2, report=False)
    experiment = changed(config, "seeds: 3", "seeds: 4")
    assert runner.run_experiment(experiment, jobs=2, report=False)
    parent = R.experiment_dir("T01_test")
    assert R.numbers(parent) == [1] and len(run_ids(parent / "001")) == 8
    assert R.read_parameters(parent / "001")["seeds"] == [0, 1, 2, 3]
    assert "6 already done, 2 to run" in capsys.readouterr().out


def test_other_code_blocks_only_unfinished_sets(config, capsys):
    experiment = E.load(config)
    runner.run_experiment(experiment, jobs=2, report=False)
    folder = R.experiment_dir("T01_test") / "001"
    first = next((folder / "runs").glob("*.json"))
    first.write_text(json.dumps({**json.loads(first.read_text()), "code": "older"}))
    assert runner.run_experiment(experiment, jobs=2, report=False)  # finished: nothing would be mixed

    next(p for p in (folder / "runs").glob("*.json") if p != first).unlink()  # one run still to do
    capsys.readouterr()
    assert runner.run_experiment(experiment, jobs=2, report=False) is False
    assert "different version of the code" in capsys.readouterr().out
    assert runner.run_experiment(experiment, jobs=2, report=False, code_change_ok=True)
    assert len(run_ids(folder)) == 6


def test_quick_results_are_redone_instead_of_blocked(config):
    runner.run_experiment(E.load(config, quick=True), quick=True, jobs=2, report=False)
    config.write_text(config.read_text().replace("fixed: {n_particles: 10}", "fixed: {n_particles: 12}"))
    assert runner.run_experiment(E.load(config, quick=True), quick=True, jobs=2, report=False)
    parent = R.experiment_dir("T01_test", quick=True)
    assert R.numbers(parent) == [1] and R.read_parameters(parent / "001")["fixed"]["n_particles"] == 12


def test_use_picks_the_set_that_analysis_show_results_and_compare_read(config, tmp_path, monkeypatch):
    runner.run_experiment(E.load(config), jobs=2)
    runner.run_experiment(changed(config, "n_particles: 30", "n_particles: 40"), new=True, note="N=40", jobs=2)
    parent = R.experiment_dir("T01_test")

    spec = importlib.util.spec_from_file_location("show_results", PROJECT / "show_results.py")
    show = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(show)
    assert show.find_summaries(R.RESULTS)[0]["number"] == "002"

    runner.use(E.load(config), 1)
    summary = show.find_summaries(R.RESULTS)[0]
    assert summary["number"] == "001" and summary["numbers"] == 2

    rebuilt = analysis.build(E.load(config), parent / "001")  # config now says 40, the set was run with 30
    assert any("n_particles = 30" in line for line in rebuilt["setup"])
    assert any("N=40" in line for line in json.loads((parent / "002" / "summary.json").read_text())["setup"])

    from pfexp import compare
    stats = compare.compare([parent / "001", parent / "002"], ["position_rmse"], "sets")
    assert {name for name, _ in stats.index} == {"T01_test 001", "T01_test 002"}
    assert compare.result_set(parent)[0] == parent / "001"


def test_findings_compare_variants_only_at_the_same_value_of_the_other_setting(config):
    changed(config, "fixed: {n_particles: 30, proposal: motion_model}", "fixed: {proposal: motion_model}")
    config.write_text(config.read_text().replace("resampler: [multinomial, systematic]",
                                                 "resampler: [multinomial, systematic]\n  n_particles: [20, 40]"))
    experiment = E.load(config)
    runner.run_experiment(experiment, jobs=2)
    summary = json.loads((R.experiment_dir(experiment.id) / "001" / "summary.json").read_text())
    assert summary["findings"]
    for sentence in summary["findings"]:
        # a statement that holds in both groups is merged into one, and still never mixes the two
        assert sentence.startswith(("At n particles = 20: ", "At n particles = 40: ", "At every n particles: "))
        assert "n_particles" not in sentence.split(": ", 1)[1]
