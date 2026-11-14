"""Verify exact boundary ratings and coherent threshold overrides."""
import pytest
from app.config import LabError
from app.thresholds import higher, limits, lower


def test_boundaries_and_overrides():
    """Apply strict green PSI and inclusive amber limits exactly."""
    assert lower(.1, .1, .25, strict_green=True) == "AMBER"
    assert lower(.25, .1, .25, strict_green=True) == "AMBER"
    assert lower(.251, .1, .25, strict_green=True) == "RED"
    assert higher(.7, .7, .6) == "GREEN"
    assert limits({"auc_green": .75})["auc_green"] == .75


@pytest.mark.parametrize("value", [{"typo": .2}, {"auc_green": .3}, {"psi_green": .5}, {"psi_green": -1}, {"psi_green": float("nan")}])
def test_invalid_thresholds(value):
    """Reject misspelled, incoherent, negative or nonfinite limits."""
    with pytest.raises(LabError):
        limits(value)
