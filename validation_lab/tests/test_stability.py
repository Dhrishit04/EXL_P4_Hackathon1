"""Test hand calculated PSI, identity, empty bins and new categories."""
import math
import numpy as np
import pytest
from app.metrics.stability import csi, population_index, psi


def test_hand_calculated_index():
    """Use two categories with expected halves and actual quarter three quarters."""
    expected = -.25 * math.log(.5) + .25 * math.log(1.5)
    assert population_index(np.array([.5, .5]), np.array([.25, .75])) == pytest.approx(expected)
    assert csi([0, 0, 1, 1], [0, 1, 1, 1]) == pytest.approx(expected)


def test_identity_constant_and_novel_category():
    """Keep identity exactly zero and detect previously unseen categories."""
    assert psi(np.linspace(0, 1, 100), np.linspace(0, 1, 100)) == 0
    assert psi([.5] * 20, [.5] * 20) == 0
    assert csi(["a"] * 10, ["b"] * 10) > 1
    assert math.isfinite(psi([.1] * 10, [.9] * 10))
