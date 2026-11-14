"""Compute approval fairness with fairlearn and a pandas reference implementation."""
import numpy as np
import pandas as pd


def approval(y, selected) -> float:
    """Return the approval rate for a group."""
    return float(np.mean(selected))


def good_approval(y, selected) -> float:
    """Return approval among target zero records, or NaN if none exist."""
    mask = np.asarray(y) == 0
    return float(np.mean(np.asarray(selected)[mask])) if mask.any() else float("nan")


def bad_approval(y, selected) -> float:
    """Return approval among target one records, or NaN if none exist."""
    mask = np.asarray(y) == 1
    return float(np.mean(np.asarray(selected)[mask])) if mask.any() else float("nan")


def gap(groups: list[dict], field: str) -> float | None:
    """Compare at least two eligible groups only when every rate is defined."""
    values = [g[field] for g in groups]
    if len(values) < 2 or any(v is None for v in values):
        return None
    return max(values) - min(values)


def measure(frame, protected: list[str], target: str, pd_col: str,
            decision: str, *, backend: str = "fairlearn") -> dict:
    """Report all groups but exclude groups below fifty records from comparisons."""
    attributes = []
    for attribute in protected:
        labels = frame[attribute].astype("string").fillna("<MISSING>")
        metric_frame = None
        if backend == "fairlearn":
            try:
                from fairlearn.metrics import MetricFrame
                metric_frame = MetricFrame(metrics={"approval_rate": approval,
                    "approval_rate_good_customers": good_approval,
                    "approval_rate_bad_customers": bad_approval}, y_true=frame[target],
                    y_pred=(frame[decision] == "APPROVE").astype(int), sensitive_features=labels).by_group
            except ImportError:
                pass
        groups = []
        for name in sorted(labels.unique()):
            group = frame.loc[labels == name]
            selected, outcomes = (group[decision] == "APPROVE").to_numpy(), group[target].to_numpy()
            rates = {"approval_rate": approval(outcomes, selected),
                     "approval_rate_good_customers": good_approval(outcomes, selected),
                     "approval_rate_bad_customers": bad_approval(outcomes, selected)}
            if metric_frame is not None:
                rates = {key: float(metric_frame.loc[name, key]) for key in rates}
            groups.append({"group": str(name), "n": len(group),
                           **{k: v if np.isfinite(v) else None for k, v in rates.items()},
                           "observed_default_rate": float(group[target].mean()),
                           "mean_pd": float(group[pd_col].mean())})
        eligible = [g for g in groups if g["n"] >= 50]
        high = max((g["approval_rate"] for g in eligible), default=0)
        dp = min(g["approval_rate"] for g in eligible) / high if len(eligible) >= 2 and high else None
        good_gap, bad_gap = gap(eligible, "approval_rate_good_customers"), gap(eligible, "approval_rate_bad_customers")
        odds = max(good_gap, bad_gap) if good_gap is not None and bad_gap is not None else None
        attributes.append({"attribute": attribute, "groups": groups, "demographic_parity_ratio": dp,
                           "equal_opportunity_diff": good_gap, "equalized_odds_diff": odds, "rating": "GREEN"})
    return {"rating": "GREEN", "favourable_outcome": "APPROVE", "by_attribute": attributes}
