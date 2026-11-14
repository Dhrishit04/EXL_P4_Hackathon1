"""Confirm charts and dashboard series contain the same measured evidence."""
import pandas as pd
from app.charts import render
from app.metrics import calibration, stability, fairness


def test_png_and_series(repository):
    """Keep all ten distribution bins and persist valid PNG figures."""
    frame = pd.DataFrame({"y": [0, 1] * 50, "pd": [.1, .9] * 50,
                          "x": range(100), "group": ["a"] * 50 + ["b"] * 50,
                          "decision": ["APPROVE", "DECLINE"] * 50})
    sections = {"calibration": calibration.measure(frame, "y", "pd"),
                "stability": stability.measure(frame, frame, "pd", ["x"]),
                "fairness": fairness.measure(frame, ["group"], "y", "pd", "decision")}
    charts, series = render(repository / "artifacts" / "charts", frame, frame, sections, "y", "pd")
    assert len(series["score_distribution"]) == 10
    assert sum(r["dev_share"] for r in series["score_distribution"]) == 1
    assert series["calibration_oot"][0]["mean_pd"] == sections["calibration"]["decile_table"][0]["mean_pd"]
    for chart in charts:
        assert chart["id"] in series
        assert (repository / chart["path"]).read_bytes().startswith(b"\x89PNG")
