"""Cross check fairlearn against pandas and hand computed approval statistics."""
import pandas as pd
import pytest
from app.metrics.fairness import measure


def population():
    """Make two fifty record groups and one small group with known approvals."""
    return pd.DataFrame({"group": ["a"] * 50 + ["b"] * 50 + ["c"] * 10,
        "y": ([0] * 40 + [1] * 10) * 2 + [0] * 10,
        "pd": [.2] * 110,
        "decision": ["APPROVE"] * 32 + ["DECLINE"] * 8 + ["APPROVE"] * 4 + ["DECLINE"] * 6
                  + ["APPROVE"] * 24 + ["DECLINE"] * 16 + ["APPROVE"] * 2 + ["DECLINE"] * 8 + ["DECLINE"] * 10})


def test_hand_calculated_fairness_and_cross_check():
    """Compare 36 versus 26 approvals and class conditional gaps of 0.2."""
    frame = population()
    pandas_result = measure(frame, ["group"], "y", "pd", "decision", backend="pandas")
    fairlearn_result = measure(frame, ["group"], "y", "pd", "decision")
    assert pandas_result == fairlearn_result
    attr = pandas_result["by_attribute"][0]
    assert attr["demographic_parity_ratio"] == pytest.approx(26 / 36)
    assert attr["equal_opportunity_diff"] == pytest.approx(.2)
    assert attr["equalized_odds_diff"] == pytest.approx(.2)
    assert attr["groups"][2]["approval_rate_bad_customers"] is None


def test_no_eligible_groups():
    """Return null ratios when no two groups have enough records."""
    attr = measure(population().iloc[:10], ["group"], "y", "pd", "decision")["by_attribute"][0]
    assert attr["demographic_parity_ratio"] is None
