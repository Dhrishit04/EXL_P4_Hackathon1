"""Provide isolated synthetic repositories without touching other services."""
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app
from sample_data.make_sample import make_sample


@pytest.fixture
def repository(tmp_path, monkeypatch):
    """Create service owned synthetic inputs in an isolated repository root."""
    directory = tmp_path / "validation_lab" / "sample_data"
    make_sample(directory)
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def requests(repository):
    """Read all four executable request examples."""
    directory = repository / "validation_lab" / "sample_data"
    return {name: json.loads((directory / f"{name}_request.json").read_text())
            for name in ("validate", "report", "monitor_simulate", "monitor_run")}


@pytest.fixture
def client():
    """Create an in process HTTP client with ordinary service error handling."""
    return TestClient(app)
