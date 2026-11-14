"""Compute PSI and CSI using reference edges and explicit missing categories."""
import numpy as np
import pandas as pd


def edges(reference, bins: int = 10) -> np.ndarray:
    """Build quantile edges retaining repeated boundaries and open end bins."""
    clean = pd.Series(reference).dropna().to_numpy(float)
    if not len(clean):
        return np.array([-np.inf, np.inf])
    values = np.quantile(clean, np.linspace(0, 1, bins + 1))
    values[0], values[-1] = -np.inf, np.inf
    return values


def shares(values, boundaries: np.ndarray) -> np.ndarray:
    """Count every value, including missingness, in reference defined bins."""
    series = pd.Series(values)
    counts = np.bincount(np.searchsorted(boundaries[1:-1], series.dropna(), side="left"),
                         minlength=len(boundaries) - 1)
    return np.append(counts, series.isna().sum()).astype(float) / len(series)


def population_index(expected: np.ndarray, actual: np.ndarray) -> float:
    """Calculate sum of share differences times log share ratios with epsilon."""
    e, a = np.maximum(expected, 1e-6), np.maximum(actual, 1e-6)
    return float(np.sum((a - e) * np.log(a / e)))


def psi(reference, actual) -> float:
    """Measure output drift on development deciles."""
    boundaries = edges(reference)
    return population_index(shares(reference, boundaries), shares(actual, boundaries))


def csi(reference, actual) -> float:
    """Use categories for low cardinality features and deciles for numeric features."""
    ref, act = pd.Series(reference), pd.Series(actual)
    if ref.nunique() <= 10 or not pd.api.types.is_numeric_dtype(ref):
        ref, act = ref.astype("string").fillna("<MISSING>"), act.astype("string").fillna("<MISSING>")
        categories = sorted(set(ref) | set(act))
        return population_index(ref.value_counts(normalize=True).reindex(categories, fill_value=0).to_numpy(),
                                act.value_counts(normalize=True).reindex(categories, fill_value=0).to_numpy())
    boundaries = edges(ref)
    return population_index(shares(ref, boundaries), shares(act, boundaries))


def measure(dev, oot, pd_col: str, features: list[str]) -> dict:
    """Measure model output and feature distribution changes."""
    return {"rating": "GREEN", "psi_score": psi(dev[pd_col], oot[pd_col]),
            "csi": [{"feature": f, "csi": csi(dev[f], oot[f]), "rating": "GREEN"} for f in features]}
