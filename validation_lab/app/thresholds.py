"""Merge illustrative limits while rejecting unknown and incoherent overrides."""
import math
from app.config import LabError

DEFAULTS = {
    "auc_green": .70, "auc_amber": .60, "ks_green": .30, "ks_amber": .20,
    "gini_drop_green": .10, "gini_drop_amber": .20,
    "oe_band_green": .10, "oe_band_amber": .20, "hl_p_green": .05,
    "psi_green": .10, "psi_amber": .25, "dp_ratio_green": .80, "dp_ratio_amber": .70,
    "eo_diff_green": .05, "eo_diff_amber": .10, "benchmark_uplift_amber": .03,
}
MONITOR_DEFAULTS = {"psi_green": .10, "psi_amber": .25, "auc_drop_trigger": .05}


def limits(overrides: dict | None = None, *, monitoring: bool = False) -> dict:
    """Validate finite nonnegative threshold values and expected ordering."""
    base = dict(MONITOR_DEFAULTS if monitoring else DEFAULTS)
    for key, value in (overrides or {}).items():
        if key not in base or not math.isfinite(value) or value < 0:
            raise LabError("INVALID_THRESHOLDS", f"Unknown or invalid threshold: {key}")
        base[key] = value
    for key in ("auc", "ks", "gini_drop", "oe_band", "psi", "dp_ratio", "eo_diff"):
        green, amber = base.get(key + "_green"), base.get(key + "_amber")
        if green is not None and amber is not None:
            descending = key in {"auc", "ks", "dp_ratio"}
            if (descending and green < amber) or (not descending and green > amber):
                raise LabError("INVALID_THRESHOLDS", f"Inconsistent green and amber limits for {key}.")
    return base


def higher(value, green: float, amber: float) -> str:
    """Rate a metric where larger values are better."""
    return "GREEN" if value is None or value >= green else "AMBER" if value >= amber else "RED"


def lower(value, green: float, amber: float, *, strict_green: bool = False) -> str:
    """Rate a metric where smaller values are better."""
    if value is None or (value < green if strict_green else value <= green):
        return "GREEN"
    return "AMBER" if value <= amber else "RED"
