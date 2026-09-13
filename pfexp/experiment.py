"""Experiment configs: one YAML file per question, expanded into individual runs.

    title: Does the resampling scheme matter?
    question: ...
    hypothesis: ...
    filter: mcl                      # mcl or fastslam
    world: {}                        # overrides for the world generator
    fixed:                           # settings shared by every run
      n_particles: 500
      proposal: motion_model
    vary:                            # every combination of these is run
      resampler: [multinomial, residual, stratified, systematic]
    seeds: 20                        # seeds 0..19; each seed fixes both the world and the filter's randomness
    quick:                           # smaller version for `--quick`
      seeds: 3
      fixed: {n_particles: 200}
    report:
      metrics: [position_rmse, ess_mean, runtime_per_step_ms]
      traces: [ess, position_error]

Every variant with the same seed sees exactly the same world, so differences come from the technique.
"""
import hashlib
import itertools
import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

FILTERS = ("mcl", "fastslam")
DEFAULT_METRICS = ["position_rmse", "ate", "ess_mean", "unique_after_resampling", "nees_mean",
                   "runtime_per_step_ms"]
DEFAULT_TRACES = ["ess", "position_error"]


@dataclass
class RunSpec:
    experiment: str
    filter: str
    world: dict
    settings: dict      # fixed + this variant's values, passed to the filter
    variant: dict       # just the varied values, for grouping and labels
    seed: int

    @property
    def run_id(self):
        """Stable across computers: a hash of everything that determines the result."""
        key = {"filter": self.filter, "world": self.world, "settings": self.settings, "seed": self.seed}
        return hashlib.sha1(json.dumps(key, sort_keys=True).encode()).hexdigest()[:12]


@dataclass
class Experiment:
    id: str
    path: Path
    title: str
    question: str
    hypothesis: str
    filter: str
    world: dict
    fixed: dict
    vary: dict
    seeds: list
    report: dict = field(default_factory=dict)

    def runs(self):
        names = list(self.vary)
        for values in itertools.product(*(self.vary[name] for name in names)):
            variant = dict(zip(names, values))
            for seed in self.seeds:
                yield RunSpec(self.id, self.filter, self.world, {**self.fixed, **variant}, variant, seed)

    @property
    def metrics(self):
        return self.report.get("metrics", DEFAULT_METRICS)

    @property
    def traces(self):
        return self.report.get("traces", DEFAULT_TRACES)


def _seed_list(value):
    return list(range(value)) if isinstance(value, int) else list(value)


def load(path, quick=False):
    path = Path(path)
    config = yaml.safe_load(path.read_text())
    required = {"title", "question", "filter", "vary", "seeds"}
    missing = required - set(config)
    if missing:
        raise ValueError(f"{path.name}: missing {sorted(missing)}")
    if config["filter"] not in FILTERS:
        raise ValueError(f"{path.name}: filter must be one of {FILTERS}, got {config['filter']!r}")

    fixed, seeds, world = dict(config.get("fixed", {})), config["seeds"], dict(config.get("world", {}))
    if quick:
        small = config.get("quick", {})
        fixed.update(small.get("fixed", {}))
        world.update(small.get("world", {}))
        seeds = small.get("seeds", min(3, len(_seed_list(seeds))))

    overlap = set(fixed) & set(config["vary"])
    if overlap:
        raise ValueError(f"{path.name}: {sorted(overlap)} is both fixed and varied")
    return Experiment(
        id=path.stem, path=path, title=config["title"], question=config["question"],
        hypothesis=config.get("hypothesis", ""), filter=config["filter"], world=world, fixed=fixed,
        vary={name: list(values) for name, values in config["vary"].items()},
        seeds=_seed_list(seeds), report=config.get("report", {}),
    )


def label(value):
    """Readable label for a setting value: 'systematic' or 'ess_threshold (threshold=0.5)'."""
    if isinstance(value, dict):
        params = ", ".join(f"{k}={v}" for k, v in value.items() if k != "name")
        return f"{value['name']} ({params})" if params else value["name"]
    return str(value)
