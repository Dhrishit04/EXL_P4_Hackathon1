"""Orchestrate independent validation and persist the exact returned result."""
from time import perf_counter
from app import charts
from app.config import output_directory, relative, write_json
from app.data_loader import file_hash, load_scored, required_columns
from app.findings import rate
from app.metrics import backtest, benchmark, calibration, data_quality, discrimination, fairness, sensitivity, stability
from app.schemas import ValidateRequest, ValidationResult
from app.thresholds import limits


def run(request: ValidateRequest) -> dict:
    """Compute measurements at full precision and round only the final JSON."""
    start = perf_counter()
    data, scores = request.data, request.scores
    thresholds = limits(request.thresholds)
    dev, oot = [load_scored(dp, sp, data.id_col, data.target_col, scores.pd_col, scores.score_col, scores.decision_col)
                for dp, sp in ((data.dev_path, scores.dev_path), (data.oot_path, scores.oot_path))]
    for frame in (dev, oot):
        required_columns(frame, request.feature_cols + request.protected_cols)
    notes = []
    sections = {
        "data_quality": data_quality.measure(dev, oot, data.id_col, data.target_col, request.feature_cols),
        "discrimination": discrimination.compare(dev, oot, data.target_col, scores.pd_col),
        "calibration": calibration.measure(oot, data.target_col, scores.pd_col),
        "stability": stability.measure(dev, oot, scores.pd_col, request.feature_cols),
        "backtest": backtest.measure(dev, oot, data.target_col, scores.pd_col),
        "fairness": fairness.measure(oot, request.protected_cols, data.target_col, scores.pd_col, scores.decision_col),
        "sensitivity": None,
        "benchmark": benchmark.compare(dev, oot, request.feature_cols, data.target_col, scores.pd_col),
    }
    if request.model_module_path:
        sections["sensitivity"], issue = sensitivity.measure(request.model_module_path, oot, request.feature_cols,
                                                           data.id_col, scores.pd_col, scores.decision_col)
        if issue:
            notes.append(("sensitivity", issue))
    else:
        notes.append(("sensitivity", "No model_module_path was supplied; feature shocks were not run."))
    if sections["benchmark"] is None:
        notes.append(("benchmark", "Challenger needs numeric features and both target classes in development and holdout."))
    findings, overall = rate(sections, thresholds, notes)
    directory = output_directory(request.model_id, "validation")
    chart_files, series = charts.render(directory / "charts", dev, oot, sections, data.target_col, scores.pd_col)
    path = directory / "result.json"
    result = {"model_id": request.model_id, "run_id": request.run_id, "status": "COMPLETED",
              "overall_rating": overall, "sample_sizes": {"dev": len(dev), "oot": len(oot)},
              "sections": sections, "findings": findings, "charts": chart_files, "series": series,
              "thresholds_used": thresholds, "result_path": relative(path),
              "duration_seconds": perf_counter() - start, "error": None}
    ValidationResult.model_validate(result)
    write_json(directory / "input_evidence.json", {"model_id": request.model_id, "run_id": request.run_id,
               "data_hashes": {p: file_hash(p) for p in (data.dev_path, data.oot_path, scores.dev_path, scores.oot_path)}})
    return write_json(path, result)
