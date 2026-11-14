"""Fit a reproducible holdout challenger using development data only."""
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from app.metrics.discrimination import measure


def compare(dev, oot, features: list[str], target: str, pd_col: str) -> dict | None:
    """Return champion and challenger AUC or null when fitting is inapplicable."""
    if not features or dev[target].nunique() < 2 or oot[target].nunique() < 2:
        return None
    if not all(pd.api.types.is_numeric_dtype(dev[f]) for f in features):
        return None
    if any(np.isinf(dev[f]).any() or np.isinf(oot[f]).any() for f in features):
        return None
    model = make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True),
                          GradientBoostingClassifier(n_estimators=80, max_depth=2, random_state=42))
    model.fit(dev[features], dev[target])
    champion = measure(oot[target], oot[pd_col])["auc"]
    challenger = measure(oot[target], model.predict_proba(oot[features])[:, 1])["auc"]
    return {"rating": "GREEN", "challenger": "gradient_boosting", "champion_auc_oot": champion,
            "challenger_auc_oot": challenger, "auc_uplift": challenger - champion}
