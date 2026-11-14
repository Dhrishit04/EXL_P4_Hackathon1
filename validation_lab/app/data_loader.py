"""Load CSV observations and scores with exact one to one ID alignment."""
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from app.config import LabError, safe_path


def read_csv(path: str, id_col: str) -> pd.DataFrame:
    """Read identifiers as strings so leading zeros cannot disappear."""
    try:
        return pd.read_csv(safe_path(path), dtype={id_col: "string"})
    except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeError) as exc:
        raise LabError("INVALID_DATA", f"Cannot read CSV: {path}") from exc


def required_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    """Reject missing columns with a clear input error."""
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise LabError("MISSING_COLUMNS", f"Missing required columns: {', '.join(missing)}")


def validate_scored(frame: pd.DataFrame, target: str, pd_col: str,
                    decision: str, score: str) -> None:
    """Reject malformed model outputs and outcomes before measurement."""
    required_columns(frame, [target, pd_col, decision, score])
    if frame.empty:
        raise LabError("INVALID_DATA", "The sample is empty.")
    if frame[target].isna().any() or not frame[target].isin([0, 1]).all():
        raise LabError("INVALID_TARGET", "The target must be 0 or 1, with 1 the bad event.")
    probabilities = pd.to_numeric(frame[pd_col], errors="coerce")
    if not np.isfinite(probabilities).all() or not probabilities.between(0, 1).all():
        raise LabError("INVALID_PD", "Every PD must be finite and between 0 and 1.")
    points = pd.to_numeric(frame[score], errors="coerce")
    if not np.isfinite(points).all() or not (points == np.floor(points)).all():
        raise LabError("INVALID_SCORE", "Scores must be finite integers (use 0 if not applicable).")
    if not frame[decision].isin(["APPROVE", "DECLINE"]).all():
        raise LabError("INVALID_DECISION", "Decisions must be APPROVE or DECLINE.")
    frame[pd_col] = probabilities.astype(float)


def load_scored(data_path: str, scores_path: str, id_col: str, target_col: str,
                pd_col: str = "pd", score_col: str = "score",
                decision_col: str = "decision") -> pd.DataFrame:
    """Join exactly matching unique identifiers without dropping any observation."""
    data, scores = read_csv(data_path, id_col), read_csv(scores_path, id_col)
    required_columns(data, [id_col, target_col])
    required_columns(scores, [id_col, pd_col, score_col, decision_col])
    for frame in (data, scores):
        if frame[id_col].isna().any() or frame[id_col].duplicated().any():
            raise LabError("INVALID_ID", "IDs must be nonmissing and unique in both input files.")
    if set(data[id_col]) != set(scores[id_col]):
        raise LabError("ID_MISMATCH", "Data and scores must contain exactly the same identifiers.")
    overlapping = set(data.columns).intersection([pd_col, score_col, decision_col])
    if overlapping:
        raise LabError("COLUMN_CONFLICT", "Observation files must not already contain score columns.")
    merged = data.merge(scores[[id_col, pd_col, score_col, decision_col]],
                        on=id_col, how="left", validate="one_to_one", sort=False)
    validate_scored(merged, target_col, pd_col, decision_col, score_col)
    return merged


def file_hash(path: str | Path) -> str:
    """Hash complete input bytes for reproducible report evidence."""
    source = safe_path(path) if isinstance(path, str) else path
    return hashlib.sha256(source.read_bytes()).hexdigest()
