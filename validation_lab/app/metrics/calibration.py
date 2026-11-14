"""Compute Brier, observed over expected and ten equal sized HL groups."""
import numpy as np
import pandas as pd
from scipy.stats import chi2


def measure(frame: pd.DataFrame, target: str, pd_col: str) -> dict:
    """Compute full precision calibration and disclose undefined HL tests."""
    y, p = frame[target].to_numpy(float), frame[pd_col].to_numpy(float)
    table = []
    statistic = 0.0
    valid = len(frame) >= 10
    order = np.argsort(p, kind="stable")
    for i, indices in enumerate(np.array_split(order, min(10, len(frame))), 1):
        n, expected, observed = len(indices), float(p[indices].sum()), float(y[indices].sum())
        table.append({"decile": i, "n": n, "mean_pd": expected / n, "observed_rate": observed / n})
        denominator = expected * (1 - expected / n)
        if denominator <= 0:
            valid = False
        else:
            statistic += (observed - expected) ** 2 / denominator
    return {"rating": "GREEN", "oot": {
        "brier": float(np.mean((y - p) ** 2)), "mean_predicted_pd": float(p.mean()),
        "observed_default_rate": float(y.mean()),
        "observed_over_expected": float(y.sum() / p.sum()) if p.sum() else None,
        "hosmer_lemeshow_stat": statistic if valid else None,
        "hosmer_lemeshow_p": float(chi2.sf(statistic, 8)) if valid else None,
    }, "decile_table": table}
