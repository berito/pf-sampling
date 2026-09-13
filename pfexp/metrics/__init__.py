"""Metrics computed from run logs, one file per metric. Files here register themselves (see pfexp.registry)."""
from pfexp import registry


def compute_all(log, names=None):
    """Run the named metrics (default: all registered) and merge their results into one flat dict."""
    results = {}
    for name in names or registry.names("metric"):
        metric = registry.create("metric", name)
        if metric.applies_to(log):
            results.update(metric.compute(log))
    return results
