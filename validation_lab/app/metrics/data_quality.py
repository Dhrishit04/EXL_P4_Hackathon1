"""Expose per column missingness, constant features and development range breaches."""
import pandas as pd


def measure(dev, oot, id_col: str, target: str, features: list[str]) -> dict:
    """Return quality evidence entirely within the frozen checks array."""
    checks = []
    for label, frame in (("dev", dev), ("oot", oot)):
        for column in frame.columns:
            value = float(frame[column].isna().mean())
            checks.append({"check": f"missing_rate:{label}:{column}", "value": value,
                           "threshold": .05, "passed": value <= .05})
        duplicate = int(frame[id_col].duplicated().sum())
        checks.append({"check": f"duplicate_ids:{label}", "value": duplicate, "threshold": 0, "passed": duplicate == 0})
        for feature in features:
            constant = int(frame[feature].nunique(dropna=True) <= 1)
            checks.append({"check": f"constant:{label}:{feature}", "value": constant, "threshold": 0, "passed": constant == 0})
    for feature in features:
        if pd.api.types.is_numeric_dtype(dev[feature]) and dev[feature].notna().any():
            value = float(((oot[feature] < dev[feature].min()) | (oot[feature] > dev[feature].max())).mean())
            checks.append({"check": f"outside_dev_range:{feature}", "value": value, "threshold": 0, "passed": value == 0})
    return {"rating": "GREEN", "checks": checks,
            "target_rate": {"dev": float(dev[target].mean()), "oot": float(oot[target].mean())}}
