"""Verify missing rates, constants and development range evidence."""
import pandas as pd
from app.metrics.data_quality import measure


def test_column_quality_and_ranges():
    """Expose every measured data limitation in contract shaped checks."""
    dev = pd.DataFrame({"ID": [1, 2], "x": [0., 1.], "y": [0, 1]})
    oot = pd.DataFrame({"ID": [3, 4], "x": [2., None], "y": [1, 1]})
    result = measure(dev, oot, "ID", "y", ["x"])
    checks = {x["check"]: x["value"] for x in result["checks"]}
    assert checks["missing_rate:oot:x"] == .5
    assert checks["outside_dev_range:x"] == .5
    assert checks["constant:oot:x"] == 1
    assert result["target_rate"] == {"dev": .5, "oot": 1.}
