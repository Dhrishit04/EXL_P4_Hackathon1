"""Compare observed and predicted bad event rates in development quintiles."""
import numpy as np
from scipy.stats import binomtest
from app.metrics.stability import edges


def measure(dev, oot, target: str, pd_col: str) -> dict:
    """Return five risk bands including empty bands with null statistics."""
    boundaries = edges(dev[pd_col], 5)
    assignments = np.searchsorted(boundaries[1:-1], oot[pd_col], side="left")
    result = []
    for i, name in enumerate("ABCDE"):
        group = oot.loc[assignments == i]
        n = len(group)
        mean = float(group[pd_col].mean()) if n else None
        probability = float(binomtest(int(group[target].sum()), n, mean).pvalue) if n else None
        light = "GREEN" if probability is None or probability >= .05 else "AMBER" if probability >= .01 else "RED"
        result.append({"band": name, "pd_min": float(max(0, boundaries[i])),
                       "pd_max": float(min(1, boundaries[i + 1])), "n": n, "mean_pd": mean,
                       "observed_rate": float(group[target].mean()) if n else None,
                       "binomial_p": probability, "light": light})
    return {"rating": "GREEN", "bands": result}
