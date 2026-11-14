"""Render PNG evidence and the identical underlying dashboard data series."""
import re
from threading import Lock
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from sklearn.metrics import roc_curve
from app.config import relative
from app.metrics.stability import edges, shares

CHART_LOCK = Lock()


def render(directory, dev, oot, sections: dict, target: str, pd_col: str) -> tuple[list, dict]:
    """Persist every figure from the data returned in its matching series."""
    directory.mkdir(parents=True, exist_ok=True)
    series, charts = {}, []
    if oot[target].nunique() >= 2:
        fpr, tpr, _ = roc_curve(oot[target], oot[pd_col])
        series["roc_oot"] = [{"fpr": float(x), "tpr": float(y)} for x, y in zip(fpr, tpr)]
    else:
        series["roc_oot"] = []
    series["calibration_oot"] = [{k: d[k] for k in ("decile", "mean_pd", "observed_rate")} for d in sections["calibration"]["decile_table"]]
    boundaries = edges(dev[pd_col])
    development, holdout = shares(dev[pd_col], boundaries), shares(oot[pd_col], boundaries)
    series["score_distribution"] = [{"bin": f"D{i+1:02}", "dev_share": float(x), "oot_share": float(y)}
                                     for i, (x, y) in enumerate(zip(development[:-1], holdout[:-1]))]
    series["psi_features"] = [{"feature": row["feature"], "csi": row["csi"]} for row in sections["stability"]["csi"]]
    definitions = [("roc_oot", "ROC curve, holdout", "fpr", ["tpr"]),
                   ("calibration_oot", "Calibration by decile, holdout", "decile", ["mean_pd", "observed_rate"]),
                   ("score_distribution", "Model output distribution, development against holdout", "bin", ["dev_share", "oot_share"]),
                   ("psi_features", "Feature stability indices", "feature", ["csi"])]
    for i, attr in enumerate(sections["fairness"]["by_attribute"]):
        identifier = "fairness_" + re.sub(r"[^A-Za-z0-9_-]", "_", attr["attribute"])
        if identifier in series:
            identifier += f"_{i}"
        series[identifier] = [{"group": g["group"], "approval_rate": g["approval_rate"]} for g in attr["groups"]]
        definitions.append((identifier, f"Approval rate by {attr['attribute']}", "group", ["approval_rate"]))
    with CHART_LOCK:
        for identifier, title, x_key, y_keys in definitions:
            fig, axis = plt.subplots(figsize=(8, 4.3), layout="constrained")
            rows = series[identifier]
            for y_key in y_keys:
                axis.plot([r[x_key] for r in rows], [r[y_key] for r in rows], marker="o", markersize=3, label=y_key.replace("_", " "))
            if not rows:
                axis.text(.5, .5, "Not available for this sample", transform=axis.transAxes, ha="center")
            else:
                axis.legend(frameon=False)
            axis.set_title(title, fontsize=11, wrap=True)
            axis.set_xlabel(x_key.replace("_", " "))
            axis.grid(alpha=.2)
            path = directory / f"{identifier}.png"
            fig.savefig(path, dpi=140)
            plt.close(fig)
            charts.append({"id": identifier, "title": title, "path": relative(path)})
    return charts, series
