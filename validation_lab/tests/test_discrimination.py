"""Check discrimination against exact pair counts and known limiting cases."""
import numpy as np
import pytest
from app.metrics.discrimination import measure


def test_hand_calculated_auc_and_ks():
    """Three of four bad good pairs are ordered correctly and KS is one half."""
    result = measure([0, 0, 1, 1], [.1, .4, .3, .8])
    assert result == {"auc": .75, "gini": .5, "ks": .5}


def test_perfect_random_and_single_class():
    """Confirm perfect scores, deterministic random scores and undefined one class AUC."""
    assert measure([0, 0, 1, 1], [.1, .2, .8, .9])["auc"] == 1
    rng = np.random.default_rng(7)
    assert measure(rng.integers(0, 2, 30000), rng.random(30000))["auc"] == pytest.approx(.5, abs=.02)
    assert measure([1, 1], [.1, .2]) == {"auc": None, "gini": None, "ks": None}


def test_tied_scores():
    """Award half credit to tied bad good pairs."""
    assert measure([0, 1], [.5, .5])["auc"] == .5
