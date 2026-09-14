"""The experiment configs in experiments/, experiments that cannot run yet, numeric sweeps and gmapping output,
on temporary results folders."""
import json

import pytest

from pfexp import analysis
from pfexp import experiment as E
from pfexp import results as R
from pfexp import run as runner
from pfexp.filters import gmapping
from pfexp.vendor import PROJECT

CONFIGS = sorted((PROJECT / "experiments").glob("*.yaml"))


@pytest.fixture
def results(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "RESULTS", tmp_path / "results")
    monkeypatch.setattr(R, "QUICK_RESULTS", tmp_path / "results" / "quick")
    return tmp_path


def write(folder, name, text):
    path = folder / f"{name}.yaml"
    path.write_text(text)
    return path


@pytest.mark.parametrize("path", CONFIGS, ids=[p.stem for p in CONFIGS])
def test_every_experiment_config_loads(path):
    for quick in (False, True):
        experiment = E.load(path, quick=quick)
        assert list(experiment.runs())
        assert experiment.question.strip() and experiment.metrics


def test_only_planned_techniques_are_missing():
    """E05 waits for the resample-move technique; every other experiment must be runnable."""
    for path in CONFIGS:
        problems = [p for p in E.load(path).problems() if "gmapping is not built" not in p and "datasets/" not in p]
        if path.stem == "E05_resample_move" and problems:
            assert all("resample_move_mh" in p for p in problems)
        else:
            assert problems == [], (path.stem, problems)


SWEEP = """
title: Sweep
question: Does a numeric sweep with many variants plot?
filter: mcl
world: {n_steps: 4}
fixed: {proposal: motion_model}
vary:
  resampler: [multinomial, residual, stratified, systematic, nonexistent]
  n_particles: [10, 20]
seeds: 2
quick:
  seeds: 1
  vary: {resampler: [multinomial, residual, stratified, systematic], n_particles: [10, 20, 40]}
report:
  metrics: [position_rmse, ess_mean]
  traces: [ess]
"""


def test_quick_can_replace_the_varied_values(results):
    experiment = E.load(write(results, "T02_sweep", SWEEP), quick=True)
    assert experiment.vary["n_particles"] == [10, 20, 40] and len(list(experiment.runs())) == 12


def test_unknown_technique_is_reported_and_the_experiment_skipped(results, capsys):
    path = write(results, "T02_sweep", SWEEP)
    problems = E.load(path).problems()
    assert len(problems) == 1 and "resampler 'nonexistent'" in problems[0]
    assert runner.main([str(path)]) == 0
    out = capsys.readouterr().out
    assert "skipped, cannot run yet" in out and "nonexistent" in out
    assert not (R.RESULTS / "T02_sweep").exists()


def test_numeric_sweep_with_more_variants_than_colours(results):
    experiment = E.load(write(results, "T02_sweep", SWEEP), quick=True)  # 12 variants, 8 colours
    assert analysis.sweep_key(experiment) == "n_particles"
    runner.run_experiment(experiment, quick=True, jobs=2)
    summary = json.loads((R.QUICK_RESULTS / "T02_sweep" / "001" / "summary.json").read_text())
    assert summary["runs"] == 12 and summary["notes"] == []


def test_gmapping_output_is_parsed(tmp_path):
    output = tmp_path / "run.gfs"
    output.write_text("PARAM particles 3\nFRAME 1\nNEFF 3.0\nODOM 0 0 0\nFRAME 2\nNEFF 1.2\n"
                      "RESAMPLE 3 0 0 1\nFRAME 3\nNEFF 2.5\n")
    ess, resampled = gmapping.read_output(output)
    assert ess.tolist() == [3.0, 1.2, 2.5] and resampled.tolist() == [False, True, False]


def test_gmapping_problems_name_the_fix():
    assert any("unknown dataset" in p for p in gmapping.problems({"dataset": "nope"}))


def test_findings_do_not_judge_noise_from_a_single_seed():
    import pandas as pd

    stats = pd.DataFrame({"seeds": [1, 1], "position_rmse_mean": [0.2, 0.4], "position_rmse_std": [0.0, 0.0]},
                         index=["a", "b"])
    (sentence,) = analysis.findings(stats, ["position_rmse"])
    assert "not tested" in sentence and "clearly" not in sentence
