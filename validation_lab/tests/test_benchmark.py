"""Verify challenger discrimination and reproducibility on synthetic inputs."""
import numpy as np
import pandas as pd
from app.metrics.benchmark import compare


def test_challenger_uses_predictive_feature():
    """A perfectly predictive feature beats an uninformative champion."""
    frame = pd.DataFrame({"x": np.tile([0., 1.], 100), "y": np.tile([0, 1], 100), "pd": [.5] * 200})
    result = compare(frame, frame, ["x"], "y", "pd")
    assert result["champion_auc_oot"] == .5 and result["challenger_auc_oot"] == 1
    assert result == compare(frame, frame, ["x"], "y", "pd")
    assert compare(frame.assign(y=0), frame, ["x"], "y", "pd") is None
