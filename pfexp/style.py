"""One look for every figure: fixed colours per technique, readable names, units, and which way is better.

Colours follow the technique, never its position in a particular figure, so 'systematic' has the same colour in
every experiment. Categorical colours come from a validated colour-blind-safe palette in a fixed order; numeric
sweeps (particle count, thresholds) use one hue from light to dark. Because some colours have low contrast
on white, figures always label techniques in text as well.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SEQUENTIAL = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]  # light → dark blue
INK, INK_MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"

# Fixed slot per technique, grouped by kind so a figure never shows two techniques with the same slot.
SLOTS = {
    "multinomial": 0, "residual": 1, "stratified": 2, "systematic": 3,
    "every_step": 0, "ess_threshold": 1, "max_weight": 2, "never": 3,
    "motion_model": 0, "auxiliary": 1, "extended_kalman": 2,
    "fastslam1": 0, "fastslam2": 1,
    "none": 0, "resample_move_mh": 1,
}

NAMES = {
    "multinomial": "Multinomial", "residual": "Residual", "stratified": "Stratified", "systematic": "Systematic",
    "every_step": "Every step", "ess_threshold": "ESS threshold", "max_weight": "Max weight", "never": "Never",
    "motion_model": "Motion model", "auxiliary": "Auxiliary PF", "extended_kalman": "Extended Kalman PF",
    "fastslam1": "FastSLAM 1.0", "fastslam2": "FastSLAM 2.0",
    "none": "No move", "resample_move_mh": "Resample-move (MH)",
}

# metric → (display name, unit, which direction is better: "lower", "higher", or a target value)
METRICS = {
    "position_rmse": ("Position RMSE", "m", "lower"),
    "heading_rmse": ("Heading RMSE", "rad", "lower"),
    "final_position_error": ("Final position error", "m", "lower"),
    "ate": ("ATE (aligned)", "m", "lower"),
    "map_error": ("Map error", "m", "lower"),
    "map_error_aligned": ("Map error (aligned)", "m", "lower"),
    "ess_mean": ("Mean ESS / N", "", "higher"),
    "ess_min": ("Min ESS / N", "", "higher"),
    "unique_after_resampling": ("Distinct particles after resampling / N", "", "higher"),
    "resample_rate": ("Resampling rate", "", None),
    "collapses": ("Weight collapses", "", "lower"),
    "nees_mean": ("Mean NEES", "", 3.0),
    "nees_median": ("Median NEES", "", 3.0),
    "runtime_per_step_ms": ("Runtime per step", "ms", "lower"),
    "runtime_total_s": ("Total runtime", "s", "lower"),
}

TRACES = {
    "position_error": ("Position error", "m"),
    "heading_error": ("Heading error", "rad"),
    "ess": ("ESS before resampling", "particles"),
    "unique_after": ("Distinct particles after resampling", "particles"),
    "max_weight": ("Largest weight", ""),
}


def metric_label(name):
    display, unit, _ = METRICS.get(name, (name, "", None))
    return f"{display} ({unit})" if unit else display


def trace_label(name):
    display, unit = TRACES.get(name, (name, ""))
    return f"{display} ({unit})" if unit else display


def better(name):
    return METRICS.get(name, (name, "", None))[2]


def technique_name(value):
    """'systematic' → 'Systematic'; {'name': 'ess_threshold', 'threshold': 0.5} → 'ESS threshold (0.5)'."""
    if isinstance(value, dict):
        params = ", ".join(str(v) for k, v in value.items() if k != "name")
        base = NAMES.get(value["name"], value["name"])
        return f"{base} ({params})" if params else base
    return NAMES.get(value, str(value))


def colours(values):
    """Colour per varied value: sequential for a numeric sweep, else the technique's fixed slot."""
    if all(isinstance(v, (int, float)) for v in values):
        step = max(1, len(SEQUENTIAL) // max(1, len(values)))
        return [SEQUENTIAL[min(i * step, len(SEQUENTIAL) - 1)] for i in range(len(values))]
    used, result = set(), []
    for value in values:
        name = value["name"] if isinstance(value, dict) else value
        slot = SLOTS.get(name)
        if slot is None or slot in used:  # unknown technique or a second variant of the same one
            slot = next(i for i in range(len(CATEGORICAL)) if i not in used)
        used.add(slot)
        result.append(CATEGORICAL[slot % len(CATEGORICAL)])
    return result


def apply():
    """Matplotlib defaults for all figures: thin marks, recessive grid and axes, text in ink colours."""
    plt.rcParams.update({
        "figure.dpi": 120, "savefig.dpi": 160, "savefig.bbox": "tight",
        "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
        "axes.edgecolor": GRID, "axes.labelcolor": INK_MUTED, "axes.titlecolor": INK,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
        "xtick.color": INK_MUTED, "ytick.color": INK_MUTED, "xtick.major.size": 0, "ytick.major.size": 0,
        "lines.linewidth": 2, "legend.frameon": False, "legend.fontsize": 8,
        "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb",
    })
