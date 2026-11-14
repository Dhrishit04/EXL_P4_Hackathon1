"""Check seeded no drift and strong drift outcomes and simulation provenance."""
import json
from app.schemas import MonitoringResult, MonitorSimulateResult


def test_no_drift_and_strong_drift(client, requests, repository):
    """A stationary seed has no red batches and a large late tilt triggers revalidation."""
    simulation = requests["monitor_simulate"]
    simulation["drift_strength"] = 0
    response = client.post("/monitor/simulate", json=simulation)
    assert response.status_code == 200, response.text
    MonitorSimulateResult.model_validate(response.json())
    stationary = client.post("/monitor/run", json=requests["monitor_run"]).json()
    MonitoringResult.model_validate(stationary)
    assert stationary["simulated"] is True
    assert not stationary["revalidation_triggered"]
    assert all(b["alert"] != "RED" for b in stationary["batches"])
    simulation["drift_strength"] = 2
    first = client.post("/monitor/simulate", json=simulation).json()
    bytes_first = (repository / first["batches"][-1]["path"]).read_bytes()
    client.post("/monitor/simulate", json=simulation)
    assert (repository / first["batches"][-1]["path"]).read_bytes() == bytes_first
    drifted = client.post("/monitor/run", json=requests["monitor_run"]).json()
    assert drifted["revalidation_triggered"] and drifted["batches"][-1]["alert"] == "RED"
    assert drifted == json.loads((repository / drifted["result_path"]).read_text())


def test_changed_batch_is_not_labelled_simulated(client, requests, repository):
    """A batch changed outside simulation loses verified simulation provenance."""
    response = client.post("/monitor/simulate", json=requests["monitor_simulate"]).json()
    path = repository / response["batches"][0]["path"]
    path.write_bytes(path.read_bytes() + b"\n")
    result = client.post("/monitor/run", json=requests["monitor_run"]).json()
    assert result["simulated"] is False
