"""Plug-in registry: every sampling technique and metric is registered under a kind and a name.

A technique file registers itself with a decorator:

    @register("resampler", "systematic")
    class Systematic(Resampler):
        ...

Experiment configs then refer to it by name, either as a plain string or with parameters:

    resampler: systematic
    trigger: {name: ess_threshold, threshold: 0.5}

All modules under pfexp.techniques and pfexp.metrics are imported automatically, so adding a
technique means adding one file; nothing else needs to change.
"""
import importlib
import pkgutil

KINDS = ("resampler", "trigger", "proposal", "move", "metric")

_registry = {kind: {} for kind in KINDS}
_loaded = False


def register(kind, name):
    if kind not in _registry:
        raise ValueError(f"unknown kind '{kind}', expected one of {KINDS}")

    def decorator(cls):
        existing = _registry[kind].get(name)
        if existing is not None and existing is not cls:
            raise ValueError(f"{kind} '{name}' is already registered by {existing.__module__}")
        cls.kind, cls.name = kind, name
        _registry[kind][name] = cls
        return cls

    return decorator


def load_all():
    """Import every module under pfexp.techniques and pfexp.metrics so they register themselves."""
    global _loaded
    if _loaded:
        return
    for package_name in ("pfexp.techniques", "pfexp.metrics"):
        package = importlib.import_module(package_name)
        for module in pkgutil.walk_packages(package.__path__, package_name + "."):
            importlib.import_module(module.name)
    _loaded = True


def names(kind):
    load_all()
    return sorted(_registry[kind])


def get(kind, name):
    load_all()
    try:
        return _registry[kind][name]
    except KeyError:
        raise KeyError(f"no {kind} named '{name}'; available: {', '.join(names(kind)) or 'none'}") from None


def create(kind, spec):
    """Build a technique from a config entry: a name, or a dict with 'name' plus parameters."""
    if isinstance(spec, str):
        name, params = spec, {}
    else:
        params = dict(spec)
        name = params.pop("name")
    return get(kind, name)(**params)
