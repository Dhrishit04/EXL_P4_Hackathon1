"""Compute rank discrimination with explicit undefined results for one class."""
import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve


def measure(y, pd) -> dict:
    """Return AUC, Gini and maximum cumulative distribution separation."""
    if len(set(y)) < 2:
        return {"auc": None, "gini": None, "ks": None}
    auc = float(roc_auc_score(y, pd))
    fpr, tpr, _ = roc_curve(y, pd)
    return {"auc": auc, "gini": 2 * auc - 1, "ks": float(np.max(np.abs(tpr - fpr)))}


def compare(dev, oot, target: str, pd_col: str) -> dict:
    """Measure both samples and relative deterioration from a positive dev Gini."""
    development, holdout = measure(dev[target], dev[pd_col]), measure(oot[target], oot[pd_col])
    gini = development["gini"]
    drop = (gini - holdout["gini"]) / gini if gini and gini > 0 and holdout["gini"] is not None else None
    return {"rating": "GREEN", "dev": development, "oot": holdout, "gini_relative_drop": drop}
