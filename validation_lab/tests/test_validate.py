"""Exercise complete validation on reproducible synthetic and degenerate inputs."""
import json
import pandas as pd
from app.schemas import ValidationResult


def test_complete_validation(client, requests, repository):
    """Compute a contract shaped result and ensure persistence equals the response."""
    response = client.post("/validate", json=requests["validate"])
    assert response.status_code == 200, response.text
    result = response.json()
    ValidationResult.model_validate(result)
    assert result["sample_sizes"] == {"dev": 6000, "oot": 3000}
    assert .7 < result["sections"]["discrimination"]["oot"]["auc"] < .9
    assert result["sections"]["benchmark"] is not None
    assert result["sections"]["sensitivity"] is None
    assert result == json.loads((repository / result["result_path"]).read_text())
    assert set(result) == {"model_id", "run_id", "status", "overall_rating", "sample_sizes", "sections", "findings", "charts", "series", "thresholds_used", "result_path", "duration_seconds", "error"}
    assert all((repository / c["path"]).is_file() for c in result["charts"])


def test_one_class_returns_nulls_and_low_findings(client, requests, repository):
    """Do not crash when one outcome class makes discrimination inapplicable."""
    path = repository / requests["validate"]["data"]["oot_path"]
    frame = pd.read_csv(path)
    frame["default_flag"] = 0
    frame.to_csv(path, index=False)
    response = client.post("/validate", json=requests["validate"])
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["sections"]["discrimination"]["oot"]["auc"] is None
    assert any(f["severity"] == "LOW" and f["evidence"]["metric"] == "oot.auc" for f in result["findings"])
