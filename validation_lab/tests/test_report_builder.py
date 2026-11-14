"""Verify report completeness, safe prose, identity and input provenance."""
from docx import Document


def test_reports_are_complete_and_escape_html(client, requests, repository):
    """Render both formats with inline images, every section and visible warnings."""
    assert client.post("/validate", json=requests["validate"]).status_code == 200
    report = requests["report"]
    report["narrative"]["executive_summary"] = "**Review needed** <script>alert(1)</script> ![external](https://example.com/a.png)"
    report["narrative"]["unverified_numbers"] = ["unverified 999"]
    response = client.post("/report", json=report)
    assert response.status_code == 200, response.text
    html = (repository / response.json()["html_path"]).read_text(encoding="utf-8")
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert '<img src="https:' not in html
    assert "data:image/png;base64," in html
    assert "unverified 999" in html and "Pending human sign off" in html
    assert "random holdout and not a true out of time" in html
    assert "not regulatory limits" in html and "data_file_hashes" not in html
    for section in ("Executive summary", "Model overview", "Scope and approach", "Data quality", "Conceptual soundness",
                    "Implementation verification", "Outcome analysis", "Stability", "Fairness", "Sensitivity and benchmark",
                    "Findings and recommendations", "Conclusion and sign off", "Appendix"):
        assert section in html
    doc = Document(repository / response.json()["docx_path"])
    assert len(doc.inline_shapes) >= 4
    assert doc.core_properties.author == "ModelPassport team"


def test_result_identity_mismatch(client, requests):
    """Reject report requests referencing a different run's stored result."""
    client.post("/validate", json=requests["validate"])
    report = requests["report"]
    report["run_id"] = "another_run"
    response = client.post("/report", json=report)
    assert response.status_code == 409 and response.json()["error"]["code"] == "RESULT_MISMATCH"


def test_input_changed(client, requests, repository):
    """Do not present current input hashes as evidence for stale metrics."""
    client.post("/validate", json=requests["validate"])
    path = repository / requests["validate"]["data"]["dev_path"]
    path.write_bytes(path.read_bytes() + b"\n")
    response = client.post("/report", json=requests["report"])
    assert response.status_code == 409 and response.json()["error"]["code"] == "INPUT_CHANGED"
