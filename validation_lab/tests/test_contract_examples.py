"""Validate integration lead examples read only when the shared skeleton is present."""
import json
import os
from pathlib import Path
import pytest
from app.schemas import (ValidateRequest, ValidationResult, ReportRequest, ReportResult,
                         MonitorSimulateRequest, MonitorSimulateResult, MonitorRunRequest, MonitoringResult)

MODELS = {"validate_request": ValidateRequest, "validation_result": ValidationResult,
          "report_request": ReportRequest, "report_result": ReportResult,
          "monitor_simulate_request": MonitorSimulateRequest, "monitor_simulate_result": MonitorSimulateResult,
          "monitor_run_request": MonitorRunRequest, "monitoring_result": MonitoringResult}


def resolve_includes(value, folder: Path, visited: tuple = ()):
    """Resolve frozen example includes without writing or leaving the examples folder."""
    if isinstance(value, dict):
        if set(value) == {"$include"}:
            path = (folder / value["$include"]).resolve()
            if not path.is_relative_to(folder.resolve()) or path in visited:
                raise ValueError("Unsafe or recursive contract include")
            return resolve_includes(json.loads(path.read_text(encoding="utf-8")), folder, visited + (path,))
        return {k: resolve_includes(v, folder, visited) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_includes(v, folder, visited) for v in value]
    return value


def test_shared_contract_examples():
    """Check every available validation service example against its wire schema."""
    root = Path(os.environ.get("REPO_ROOT", Path(__file__).resolve().parents[2]))
    folder = root / "contracts" / "examples"
    if not folder.is_dir():
        pytest.skip("Shared contracts/examples/ is not available in the standalone package")
    found = []
    for path in sorted(folder.glob("*.json")):
        model = MODELS.get(path.name.split(".")[0])
        if model:
            model.model_validate(resolve_includes(json.loads(path.read_text(encoding="utf-8")), folder))
            found.append(path)
    assert found, "Shared contracts folder exists but contains no validation service examples"
