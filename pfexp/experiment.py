"""Experiment configs: one YAML file per question, expanded into individual runs.

    title: Does the resampling scheme matter?
    question: ...
    hypothesis: ...
    filter: mcl                      # mcl, fastslam or gmapping
    world: {}                        # overrides for the world generator
    fixed:                           # settings shared by every run
      n_particles: 500
      proposal: motion_model
    vary:                            # every combination of these is run
      resampler: [multinomial, residual, stratified, systematic]
    seeds: 20                        # seeds 0..19; each seed fixes both the world and the filter's randomness
    quick:                           # smaller version for `--quick` (seeds, fixed, world and vary can be replaced)
      seeds: 3
      fixed: {n_particles: 200}
    report:
      metrics: [position_rmse, ess_mean, runtime_per_step_ms]
      traces: [ess, position_error]

Every variant with the same seed sees exactly the same world, so differences come from the technique.
If two numeric settings are varied, the last one goes on the x axis of the figures.
"""
import hashlib
import itertools
import json
from dataclasses import dataclass, field, replace
from pathlib import Path

import yaml

FILTERS = ("mcl", "fastslam", "gmapping")
TECHNIQUE_KINDS = ("proposal", "resampler", "trigger", "move")
DEFAULT_METRICS = ["position_rmse", "ate", "ess_mean", "unique_after_resampling", "nees_median",
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

    def problems(self):
        """Reasons this experiment cannot run yet (unknown technique, gmapping not built, ...), or []."""
        from pfexp import registry

        found = []
        values = {kind: set() for kind in TECHNIQUE_KINDS}
        for spec in self.runs():
            for kind in TECHNIQUE_KINDS:
                value = spec.settings.get(kind)
                if value is not None:
                    values[kind].add(value["name"] if isinstance(value, dict) else value)
        for kind, names in values.items():
            for name in sorted(names - set(registry.names(kind))):
                found.append(f"{kind} '{name}' does not exist yet, add pfexp/techniques/{kind}s/{name}.py "
                             f"(see pfexp/README.md)")
        if self.filter == "gmapping":
            from pfexp.filters import gmapping
            found += gmapping.problems(self.world)
        return found

    def parameters(self):
        """The settings that decide what is run. Seeds are left out: more seeds refine the same experiment."""
        return {"filter": self.filter, "world": self.world, "fixed": self.fixed, "vary": self.vary}

    def with_parameters(self, parameters, seeds=None):
        """The same experiment (title, question, report) with stored parameters, e.g. those of an earlier number."""
        return replace(self, filter=parameters["filter"], world=dict(parameters["world"]),
                       fixed=dict(parameters["fixed"]), vary={k: list(v) for k, v in parameters["vary"].items()},
                       seeds=self.seeds if seeds is None else list(seeds))

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
    vary = dict(config["vary"])
    if quick:
        small = config.get("quick", {})
        fixed.update(small.get("fixed", {}))
        world.update(small.get("world", {}))
        vary.update(small.get("vary", {}))
        seeds = small.get("seeds", min(3, len(_seed_list(seeds))))

    overlap = set(fixed) & set(vary)
    if overlap:
        raise ValueError(f"{path.name}: {sorted(overlap)} is both fixed and varied")
    return Experiment(
        id=path.stem, path=path, title=config["title"], question=config["question"],
        hypothesis=config.get("hypothesis", ""), filter=config["filter"], world=world, fixed=fixed,
        vary={name: list(values) for name, values in vary.items()},
        seeds=_seed_list(seeds), report=config.get("report", {}),
    )


def label(value):
    """Readable label for a setting value: 'systematic' or 'ess_threshold (threshold=0.5)'."""
    if isinstance(value, dict):
        params = ", ".join(f"{k}={v}" for k, v in value.items() if k != "name")
        return f"{value['name']} ({params})" if params else value["name"]
    return str(value)
