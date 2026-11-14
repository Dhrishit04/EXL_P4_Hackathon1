"""Check quintile assignment and exact two sided band tests."""
import pandas as pd
import pytest
from scipy.stats import binomtest
from app.metrics.backtest import measure


def test_bands_and_binomial_probability():
    """Place each holdout record in its development quintile and verify band A."""
    dev = pd.DataFrame({"pd": [.1, .2, .3, .4, .5]})
    oot = pd.DataFrame({"pd": [.1, .2, .3, .4, .5], "y": [0, 0, 1, 0, 1]})
    bands = measure(dev, oot, "y", "pd")["bands"]
    assert [x["band"] for x in bands] == list("ABCDE")
    assert sum(x["n"] for x in bands) == 5
    assert bands[0]["binomial_p"] == pytest.approx(binomtest(0, 1, .1).pvalue)
    assert bands[0]["pd_min"] == 0 and bands[-1]["pd_max"] == 1


def test_constant_pd_empty_bands():
    """Retain empty quintiles honestly instead of silently dropping them."""
    frame = pd.DataFrame({"pd": [.2] * 10, "y": [0, 1] * 5})
    assert any(b["binomial_p"] is None for b in measure(frame, frame, "y", "pd")["bands"])
