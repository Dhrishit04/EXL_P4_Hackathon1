"""Execute trusted repository scoring modules in a timed child process."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

from app.config import LabError, safe_path


def measure(module_path: str, frame: pd.DataFrame, features: list[str],
            id_col: str, pd_col: str, decision: str) -> tuple[dict | None, str | None]:
    """Run feature shocks with bounded time and return a diagnostic on failure."""
    path = safe_path(module_path)
    if path.suffix != ".py":
        raise LabError("INVALID_MODULE", "The scoring module must be a Python source file.")
    payload = {"path": str(path), "frame": frame.to_json(orient="split"), "features": features,
               "id_col": id_col, "pd_col": pd_col, "decision": decision}
    try:
        child = subprocess.run([sys.executable, "-m", "app.metrics.sensitivity"], input=json.dumps(payload),
                               text=True, capture_output=True, timeout=float(os.getenv("SENSITIVITY_TIMEOUT", "30")),
                               cwd=Path(__file__).resolve().parents[2], check=False)
        if child.returncode != 0:
            return None, "Scoring module failed or used an unsupported import; review it independently."
        parsed = json.loads(child.stdout)
        if "error" in parsed:
            return None, parsed["error"]
        return parsed, None
    except subprocess.TimeoutExpired:
        return None, "Scoring module exceeded the sensitivity execution timeout."
    except (ValueError, OSError):
        return None, "Scoring module did not return valid sensitivity results."


def worker(payload: dict) -> dict:
    """Evaluate a trusted local scorer with network access disabled in the child."""
    import importlib.util
    import io
    import socket
    from contextlib import redirect_stdout

    def block_network(*args, **kwargs):
        """Reject accidental outbound connections during local scoring."""
        raise RuntimeError("Network access is disabled during sensitivity scoring.")

    socket.socket = block_network
    socket.create_connection = block_network
    path = Path(payload["path"])
    tree = ast.parse(path.read_text(encoding="utf-8"))
    permitted = {"numpy", "pandas", "scipy", "sklearn", "statsmodels", "math", "json", "typing", "__future__"}
    for node in ast.walk(tree):
        names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
        if any(n.split(".")[0] not in permitted for n in names):
            return {"error": "Scoring module has unsupported imports; sensitivity was not run."}
    spec = importlib.util.spec_from_file_location("validation_scoring_model", path)
    module = importlib.util.module_from_spec(spec)
    with redirect_stdout(io.StringIO()):
        spec.loader.exec_module(module)
        frame = pd.read_json(io.StringIO(payload["frame"]), orient="split", dtype={payload["id_col"]: str})
        id_col, pd_col, decision = payload["id_col"], payload["pd_col"], payload["decision"]

        def score(data: pd.DataFrame) -> pd.DataFrame:
            """Align scoring outputs to inputs and validate probability and decision fields."""
            out = module.score(data.copy())
            if not {id_col, pd_col, decision}.issubset(out.columns):
                raise ValueError("Scorer returned missing fields")
            out = out.copy()
            out[id_col] = out[id_col].astype(str)
            if out[id_col].duplicated().any() or set(out[id_col]) != set(frame[id_col].astype(str)):
                raise ValueError("Scorer returned mismatched IDs")
            out = out.set_index(id_col).loc[frame[id_col].astype(str)]
            if not np.isfinite(out[pd_col]).all() or not out[pd_col].between(0, 1).all():
                raise ValueError("Scorer returned invalid probabilities")
            if not out[decision].isin(["APPROVE", "DECLINE"]).all():
                raise ValueError("Scorer returned invalid decisions")
            return out.reset_index()

        baseline = score(frame)
        results = []
        for feature in payload["features"]:
            if not pd.api.types.is_numeric_dtype(frame[feature]):
                continue
            for multiplier, label in ((1.1, "plus 10 percent"), (.9, "minus 10 percent")):
                shocked = frame.copy()
                shocked[feature] = shocked[feature] * multiplier
                out = score(shocked)
                results.append({"feature": feature, "shock": label,
                    "mean_pd_change": float((out[pd_col] - baseline[pd_col]).mean()),
                    "decision_flip_rate": float((out[decision] != baseline[decision]).mean())})
    return {"rating": "GREEN", "shocks": results}


if __name__ == "__main__":
    try:
        print(json.dumps(worker(json.load(sys.stdin)), allow_nan=False))
    except Exception:
        print(json.dumps({"error": "Scoring module execution failed; sensitivity is unavailable."}))
