"""Verify severity, overall ratings and stable test identities."""
from app.findings import finding, worst


def test_stable_ids_and_severity():
    """Keep a finding's identity stable when values or rating change."""
    red = finding("calibration", "oe", 2., "RED", "Within .1")
    amber = finding("calibration", "oe", 1.15, "AMBER", "Within .1")
    assert red["id"] == amber["id"]
    assert red["severity"] == "HIGH" and amber["severity"] == "MEDIUM"
    assert worst(["GREEN", "AMBER", "RED"]) == "RED"


def test_hl_rejection_alone_cannot_be_red(client, requests):
    """Every HL finding is at most medium even when the p value is very small."""
    result = client.post("/validate", json=requests["validate"]).json()
    hl = [f for f in result["findings"] if f["evidence"]["metric"] == "hosmer_lemeshow_p"]
    assert all(f["severity"] != "HIGH" for f in hl)
    severities = {f["severity"] for f in result["findings"]}
    assert result["overall_rating"] == ("RED" if "HIGH" in severities else "AMBER" if "MEDIUM" in severities else "GREEN")
