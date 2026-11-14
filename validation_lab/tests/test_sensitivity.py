"""Check timed scoring isolation, alignment and numeric shock evidence."""
import pandas as pd
from app.metrics.sensitivity import measure


def test_shock_measurements(repository):
    """A linear probability scorer changes mean PD by exactly one hundredth."""
    source = '''"""Simple deterministic scorer for sensitivity tests."""
import numpy as np
import pandas as pd
def score(frame):
    """Return model outputs in reverse order to exercise ID alignment."""
    p = frame["x"] * .1
    return pd.DataFrame({"ID": frame["ID"], "pd": p, "decision": np.where(p < .15, "APPROVE", "DECLINE")}).iloc[::-1]
'''
    (repository / "model.py").write_text(source, encoding="utf-8")
    frame = pd.DataFrame({"ID": ["001", "002"], "x": [1., 1.]})
    result, error = measure("model.py", frame, ["x"], "ID", "pd", "decision")
    assert error is None, error
    assert abs(result["shocks"][0]["mean_pd_change"] - .01) < 1e-12
    assert result["shocks"][0]["decision_flip_rate"] == 0


def test_timeout_is_reported(repository, monkeypatch):
    """An endless scoring import produces an unavailable result within the time limit."""
    (repository / "model.py").write_text('"""Endless scorer test."""\nwhile True: pass\n')
    monkeypatch.setenv("SENSITIVITY_TIMEOUT", "2")
    result, error = measure("model.py", pd.DataFrame({"ID": ["1"], "x": [1.]}), ["x"], "ID", "pd", "decision")
    assert result is None and "timeout" in error


def test_network_import_rejected(repository):
    """Do not import a scorer that requests a networking module."""
    (repository / "model.py").write_text('"""Unsupported import test."""\nimport urllib.request\n')
    result, error = measure("model.py", pd.DataFrame({"ID": ["1"]}), [], "ID", "pd", "decision")
    assert result is None and "unsupported imports" in error
