"""Repository settings, bounded paths and deterministic JSON persistence."""
import json
import math
import os
from pathlib import Path, PureWindowsPath
from typing import Any

from dotenv import load_dotenv


class LabError(Exception):
    """Carry a public error code and HTTP status."""

    def __init__(self, code: str, message: str, status: int = 400) -> None:
        """Initialize an actionable service error."""
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def repository_root() -> Path:
    """Find the shared repository or require an explicit standalone root."""
    if os.getenv("REPO_ROOT"):
        root = Path(os.environ["REPO_ROOT"]).resolve()
        if not root.is_dir() or not (root / "validation_lab").is_dir():
            raise LabError("CONFIG_ERROR", "REPO_ROOT must contain validation_lab/.", 500)
    else:
        root = next((p for p in Path(__file__).resolve().parents
                     if (p / "validation_lab").is_dir() and (p / "contracts").is_dir()), None)
        if root is None:
            raise LabError("CONFIG_ERROR", "Set REPO_ROOT for standalone use; shared contracts/ was not found.", 500)
    load_dotenv(root / ".env", override=False)
    return root


def safe_path(value: str, *, must_exist: bool = True) -> Path:
    """Resolve a forward slash repository path and reject traversal and symlinks outside it."""
    root = repository_root()
    if not value or "\\" in value or Path(value).is_absolute() or PureWindowsPath(value).drive:
        raise LabError("INVALID_PATH", "Paths must be relative to the repository with forward slashes.")
    path = (root / value).resolve()
    if not path.is_relative_to(root) or "_answer_keys" in path.parts:
        raise LabError("INVALID_PATH", "Path is outside the permitted repository.")
    if must_exist and not path.exists():
        raise LabError("FILE_NOT_FOUND", f"File not found: {value}", 404)
    return path


def output_directory(model_id: str, stage: str) -> Path:
    """Create a bounded output directory for a validation or monitoring run."""
    path = safe_path(f"artifacts/{model_id}/{stage}", must_exist=False)
    path.mkdir(parents=True, exist_ok=True)
    return path


def relative(path: Path) -> str:
    """Express a resolved output path relative to the repository."""
    return path.resolve().relative_to(repository_root()).as_posix()


def response_numbers(value: Any) -> Any:
    """Round at the response boundary and replace undefined numbers with null."""
    if isinstance(value, dict):
        return {k: response_numbers(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [response_numbers(v) for v in value]
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float):
        return round(value, 6) if math.isfinite(value) else None
    return value


def write_json(path: Path, value: Any) -> dict:
    """Write exactly the JSON object returned to the caller."""
    result = response_numbers(value)
    staging = path.with_suffix(".json.part")
    staging.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    staging.replace(path)
    return result
