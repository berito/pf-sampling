"""Every registered plug-in is exercised here automatically, so a newly added technique is tested without
writing a new test. Techniques that need parameters get their defaults."""
from pathlib import Path

import numpy as np
import pytest

from pfexp import registry
from pfexp.filters.fastslam import run_fastslam
from pfexp.filters.mcl import run_mcl
from pfexp.metrics import compute_all
from pfexp.worlds import localization_world, slam_world

PROJECT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def worlds():
    return {"mcl": localization_world(seed=0, n_steps=5), "fastslam": slam_world(seed=0, sim_time=1.0)}


@pytest.mark.parametrize("name", registry.names("resampler"))
def test_resampler(name):
    np.random.seed(0)
    weights = np.random.dirichlet(np.ones(40))
    indices = registry.create("resampler", name).resample(weights)
    assert indices.shape == (40,) and 0 <= indices.min() and indices.max() < 40


@pytest.mark.parametrize("name", registry.names("trigger"))
def test_trigger(name):
    decision = registry.create("trigger", name).should_resample(np.full(20, 0.05))
    assert isinstance(decision, bool)


@pytest.mark.parametrize("name", registry.names("proposal"))
def test_proposal_runs_in_its_filter(name, worlds):
    proposal = registry.create("proposal", name)
    run = {"mcl": run_mcl, "fastslam": run_fastslam}[proposal.filter]
    log = run(worlds[proposal.filter], n_particles=20, proposal=name, filter_seed=0)
    assert log.n_steps > 0 and np.isfinite(log.array("est_pose")).all()


@pytest.mark.parametrize("name", registry.names("move"))
@pytest.mark.parametrize("filter_name", ["mcl", "fastslam"])
def test_move_runs_in_every_filter(name, filter_name, worlds):
    run = {"mcl": run_mcl, "fastslam": run_fastslam}[filter_name]
    proposal = {"mcl": "motion_model", "fastslam": "fastslam1"}[filter_name]
    log = run(worlds[filter_name], n_particles=20, proposal=proposal, move=name, trigger="every_step",
              filter_seed=0)
    assert np.isfinite(log.array("est_pose")).all()


def test_every_metric_returns_numbers(worlds):
    for log in (run_mcl(worlds["mcl"], n_particles=20), run_fastslam(worlds["fastslam"], n_particles=20)):
        values = compute_all(log)
        assert values and all(isinstance(v, (int, float)) for v in values.values())


def test_describe_is_recorded_for_every_technique():
    for kind in ("resampler", "trigger", "proposal", "move"):
        for name in registry.names(kind):
            assert registry.create(kind, name).describe()["name"] == name


def test_code_does_not_depend_on_docs():
    """docs/ is private and removed before sharing, so nothing that is shared may refer to it."""
    offenders = []
    for folder in ("pfexp", "tools", "tests", ".devcontainer"):
        for path in (PROJECT / folder).rglob("*"):
            if path.is_file() and path.suffix in {".py", ".sh", ".json", ".yaml", ".toml", ".md"}:
                if path != Path(__file__).resolve() and "docs/" in path.read_text(errors="ignore"):
                    offenders.append(str(path.relative_to(PROJECT)))
    for name in ("README.md", "THIRD_PARTY.md", "vendors.yaml", "datasets.yaml", "pyproject.toml"):
        if "docs/" in (PROJECT / name).read_text():
            offenders.append(name)
    assert not offenders, offenders


def test_vendor_code_is_untouched():
    """Upstream repos must stay exactly at their pinned commits, with no files added (e.g. __pycache__)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("fetch_vendors", PROJECT / "tools" / "fetch_vendors.py")
    fetch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fetch)
    for name, entry in __import__("pfexp.vendor", fromlist=["manifest"]).manifest().items():
        ok, message = fetch.status(PROJECT / "vendor" / name, entry["commit"])
        assert ok, f"vendor/{name}: {message}"
