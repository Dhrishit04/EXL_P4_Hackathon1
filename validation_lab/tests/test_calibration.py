"""Verify Brier, observed expected and the stated HL degrees of freedom."""
import pandas as pd
import pytest
from scipy.stats import chi2
from app.metrics.calibration import measure


def test_hand_calculated_brier():
    """Mean squared error is 0.025 and observed expected ratio is one over 0.9."""
    result = measure(pd.DataFrame({"y": [0, 1], "p": [.1, .8]}), "y", "p")
    assert result["oot"]["brier"] == pytest.approx(.025)
    assert result["oot"]["observed_over_expected"] == pytest.approx(1 / .9)
    assert result["oot"]["hosmer_lemeshow_stat"] is None


def test_hl_ten_equal_groups():
    """Ten one record groups each contribute one to HL giving statistic ten."""
    result = measure(pd.DataFrame({"y": [0, 1] * 5, "p": [.5] * 10}), "y", "p")
    assert len(result["decile_table"]) == 10
    assert result["oot"]["hosmer_lemeshow_stat"] == 10
    assert result["oot"]["hosmer_lemeshow_p"] == pytest.approx(chi2.sf(10, 8))


def test_zero_expected_is_undefined():
    """Do not invent observed expected or HL when the expected count is zero."""
    out = measure(pd.DataFrame({"y": [0] * 10, "p": [0.] * 10}), "y", "p")["oot"]
    assert out["observed_over_expected"] is None and out["hosmer_lemeshow_p"] is None
