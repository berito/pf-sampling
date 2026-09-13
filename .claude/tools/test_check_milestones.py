"""Test for the private milestone checker.

    docker exec pf-sampling-dev python -m pytest -q .claude/tools
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT))

from pfexp import analysis  # noqa: E402
from pfexp import experiment as E  # noqa: E402
from pfexp import results as R  # noqa: E402
from pfexp import run as runner  # noqa: E402

CONFIG = """
title: Small
question: Does the checker follow an experiment?
filter: mcl
world: {n_steps: 4}
fixed: {proposal: motion_model}
vary:
  resampler: [multinomial, residual, stratified, systematic]
  n_particles: [10, 20]
seeds: 1
"""


@pytest.fixture
def results(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "RESULTS", tmp_path / "results")
    monkeypatch.setattr(R, "QUICK_RESULTS", tmp_path / "results" / "quick")
    return tmp_path


def write(folder, name, text):
    path = folder / f"{name}.yaml"
    path.write_text(text)
    return path


def checker():
    spec = importlib.util.spec_from_file_location("check_milestones", Path(__file__).with_name("check_milestones.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_milestone_checker_follows_an_experiment_from_missing_to_done(results):
    check = checker()
    config = write(results, "T03_small", CONFIG)
    experiment = E.load(config)

    status = check.experiment_check(config)
    assert status.status == check.TODO and "0 of 8 runs" in status.detail and "make run E=T03_small" in status.fix

    runner.run_experiment(experiment, jobs=2, report=False)
    status = check.experiment_check(config)
    assert status.status == check.TODO and "not up to date" in status.detail

    analysis.build(experiment, R.experiment_dir(experiment.id))
    assert check.experiment_check(config).status == check.OK

    first = next((R.experiment_dir(experiment.id) / "runs").glob("*.json"))
    record = json.loads(first.read_text())
    first.write_text(json.dumps({**record, "code": "older"}))
    status = check.experiment_check(config)
    assert status.status == check.TODO and "older code" in status.detail and "--rerun" in status.fix




def test_shared_files_do_not_refer_to_private_material():
    assert checker().private_references().status == "ok"


@pytest.mark.parametrize("text", ["used F * P * F.T; now the matrix product", "the repo is no longer fetched",
                                  "(earlier runs suggest about 300)", "verified byte-identical on 2026-09-13",
                                  "long dash — here", "arrow → here"])
def test_history_wording_and_typography_are_flagged(text, monkeypatch, tmp_path):
    check = checker()
    (tmp_path / "experiments").mkdir()
    (tmp_path / "experiments" / "probe.yaml").write_text(text)
    for name in check.SHARED_FILES:
        (tmp_path / name).write_text("plain\n")
    monkeypatch.setattr(check, "PROJECT", tmp_path)
    assert check.private_references().status == check.TODO
