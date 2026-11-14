"""Create seeded drift batches and measure monitoring alerts without model refitting."""
import json
import numpy as np
from app.config import LabError, output_directory, relative, safe_path, write_json
from app.data_loader import file_hash, load_scored, read_csv, required_columns, validate_scored
from app.metrics.discrimination import measure as discrimination
from app.metrics.stability import csi, psi
from app.thresholds import limits


def simulate(request) -> dict:
    """Resample scored holdout rows and increasingly tilt toward high PD ranks."""
    frame = load_scored(request.data_path, request.scores_path, request.id_col, request.target_col,
                        request.pd_col, request.score_col)
    required_columns(frame, request.feature_cols)
    directory = output_directory(request.model_id, "monitoring")
    batches_dir = directory / "batches"
    batches_dir.mkdir(exist_ok=True)
    rng = np.random.default_rng(request.seed)
    ranks = frame[request.pd_col].rank(method="average", pct=True).to_numpy()
    rows, hashes = [], {}
    planned = set()
    for i in range(1, request.n_batches + 1):
        injected = i >= request.drift_start_batch and request.drift_strength > 0
        tilt = request.drift_strength * (i - request.drift_start_batch + 1) * 4 if injected else 0
        weights = np.exp(tilt * (ranks - 1))
        weights /= weights.sum()
        indices = rng.choice(len(frame), request.batch_size, replace=True, p=weights)
        batch = f"{2026 + (i-1)//12}_{(i-1)%12+1:02}"
        path = safe_path(relative(batches_dir / f"batch_{batch}.csv"), must_exist=False)
        frame.iloc[indices].to_csv(path, index=False)
        planned.add(path.name)
        rows.append({"batch": batch, "path": relative(path), "n": request.batch_size, "drift_injected": injected})
        hashes[path.name] = file_hash(path)
    # Remove only prior batches listed in this service's own simulation manifest.
    manifest_path = directory / "simulation_manifest.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        for filename in previous.get("hashes", {}):
            if filename not in planned and filename.startswith("batch_") and "/" not in filename and "\\" not in filename:
                old = safe_path(relative(batches_dir / filename), must_exist=False)
                old.unlink(missing_ok=True)
    write_json(manifest_path, {"simulated": True, "hashes": hashes, "request": request.model_dump()})
    result = {"model_id": request.model_id, "simulated": True, "batches_dir": relative(batches_dir),
              "batches": rows, "error": None}
    write_json(directory / "simulation_result.json", result)
    return write_json(directory / "result.json", result)


def run(request) -> dict:
    """Compute reference based PSI, CSI, performance and revalidation rules."""
    thresholds = limits(request.thresholds, monitoring=True)
    reference = load_scored(request.reference.data_path, request.reference.scores_path,
                            request.id_col, request.target_col, request.pd_col, request.score_col)
    required_columns(reference, request.feature_cols)
    directory = safe_path(request.batches_dir)
    if not directory.is_dir():
        raise LabError("INVALID_BATCHES", "batches_dir must be a directory.")
    files = sorted(directory.glob("batch_*.csv"))
    if not files:
        raise LabError("NO_BATCHES", "No batch_*.csv files were found.")
    manifest_path = directory.parent / "simulation_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    simulated = bool(manifest.get("simulated")) and set(manifest.get("hashes", {})) == {p.name for p in files}
    baseline_auc = discrimination(reference[request.target_col], reference[request.pd_col])["auc"]
    batches, alerts = [], []
    reasons = []
    for path in files:
        path = safe_path(relative(path))
        simulated = simulated and manifest.get("hashes", {}).get(path.name) == file_hash(path)
        frame = read_csv(relative(path), request.id_col)
        required_columns(frame, request.feature_cols + [request.id_col])
        if frame[request.id_col].isna().any():
            raise LabError("INVALID_ID", "Monitoring batch IDs must be nonmissing; repeated sampled IDs are allowed.")
        validate_scored(frame, request.target_col, request.pd_col, "decision", request.score_col)
        score_psi = psi(reference[request.pd_col], frame[request.pd_col])
        indices = [{"feature": f, "csi": csi(reference[f], frame[f])} for f in request.feature_cols]
        maximum = max(indices, key=lambda x: x["csi"], default={"feature": None, "csi": None})
        auc = discrimination(frame[request.target_col], frame[request.pd_col])["auc"]
        batch_name = path.stem.removeprefix("batch_")
        rules = []
        if score_psi > thresholds["psi_amber"]:
            rules.append(("RED", f"score PSI above {thresholds['psi_amber']}", score_psi))
        elif score_psi >= thresholds["psi_green"]:
            rules.append(("AMBER", f"score PSI at least {thresholds['psi_green']}", score_psi))
        if auc is not None and baseline_auc is not None and baseline_auc - auc > thresholds["auc_drop_trigger"]:
            rules.append(("RED", f"AUC drop above {thresholds['auc_drop_trigger']}", baseline_auc - auc))
        if maximum["csi"] is not None and maximum["csi"] > thresholds["psi_amber"]:
            rules.append(("AMBER", f"feature CSI above {thresholds['psi_amber']}", maximum["csi"]))
        if auc is None or baseline_auc is None:
            rules.append(("AMBER", "AUC comparison unavailable because a sample has one class", None))
        light = "RED" if any(r[0] == "RED" for r in rules) else "AMBER" if rules else "GREEN"
        for level, rule, value in rules:
            alerts.append({"batch": batch_name, "level": level, "rule": rule, "value": value})
            if level == "RED":
                reasons.append(f"{rule} in batch {batch_name}")
        batches.append({"batch": batch_name, "n": len(frame), "psi_score": score_psi, "max_csi": maximum,
                        "auc": auc, "observed_default_rate": float(frame[request.target_col].mean()),
                        "mean_pd": float(frame[request.pd_col].mean()), "alert": light})
    path = output_directory(request.model_id, "monitoring") / "result.json"
    return write_json(path, {"model_id": request.model_id, "status": "COMPLETED", "simulated": simulated,
                            "reference_sample": "dev", "batches": batches, "alerts": alerts,
                            "revalidation_triggered": bool(reasons), "trigger_reason": "; ".join(reasons) or None,
                            "thresholds_used": thresholds, "result_path": relative(path), "error": None})
