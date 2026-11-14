"""Recreate the service's synthetic credit observations and logistic model scores."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.linear_model import LogisticRegression

FEATURES = ["income", "balance", "utilisation", "arrears", "tenure"]


def make_sample(destination: Path | None = None) -> dict:
    """Write 6000 development and 3000 random holdout rows with fixed seed 42."""
    destination = destination or Path(__file__).resolve().parent
    destination.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    x = rng.normal(size=(9000, 5))
    linear = -1.85 + x @ np.array([-.55, .40, .65, .85, -.25])
    frame = pd.DataFrame(x, columns=FEATURES)
    frame.insert(0, "ID", [f"S{i:05}" for i in range(9000)])
    frame["SEX"] = rng.choice([1, 2], len(frame))
    frame["AGE_BAND"] = rng.choice(["18_29", "30_39", "40_49", "50_plus"], len(frame))
    frame["default_flag"] = rng.binomial(1, expit(linear))
    model = LogisticRegression(penalty=None, max_iter=1000, random_state=42)
    model.fit(frame.iloc[:6000][FEATURES], frame.iloc[:6000]["default_flag"])
    for label, data in (("dev", frame.iloc[:6000]), ("oot", frame.iloc[6000:])):
        pd_values = model.predict_proba(data[FEATURES])[:, 1]
        scores = pd.DataFrame({"ID": data["ID"].to_numpy(), "pd": pd_values,
                               "score": np.rint(600 - 50 * np.log(np.clip(pd_values, 1e-12, 1-1e-12) / (1-pd_values))).astype(int),
                               "decision": np.where(pd_values < .30, "APPROVE", "DECLINE")})
        data.to_csv(destination / f"{label}.csv", index=False)
        scores.to_csv(destination / f"scored_{label}.csv", index=False)
    prefix = "validation_lab/sample_data/"
    request = {"run_id": "run_SAMPLE_001", "model_id": "SAMPLE", "model_type": "credit_pd",
               "data": {"dev_path": prefix + "dev.csv", "oot_path": prefix + "oot.csv", "id_col": "ID", "target_col": "default_flag"},
               "scores": {"dev_path": prefix + "scored_dev.csv", "oot_path": prefix + "scored_oot.csv", "pd_col": "pd", "score_col": "score", "decision_col": "decision"},
               "feature_cols": FEATURES, "protected_cols": ["SEX", "AGE_BAND"], "model_module_path": None, "thresholds": None}
    (destination / "validate_request.json").write_text(json.dumps(request, indent=2), encoding="utf-8")
    simulate = {"model_id": "SAMPLE", "data_path": prefix + "oot.csv", "scores_path": prefix + "scored_oot.csv",
                "id_col": "ID", "target_col": "default_flag", "pd_col": "pd", "score_col": "score", "feature_cols": FEATURES,
                "n_batches": 6, "batch_size": 3000, "drift_start_batch": 4, "drift_strength": .5, "seed": 42}
    (destination / "monitor_simulate_request.json").write_text(json.dumps(simulate, indent=2), encoding="utf-8")
    monitor = {"model_id": "SAMPLE", "reference": {"data_path": prefix + "dev.csv", "scores_path": prefix + "scored_dev.csv"},
               "batches_dir": "artifacts/SAMPLE/monitoring/batches", "id_col": "ID", "target_col": "default_flag",
               "pd_col": "pd", "score_col": "score", "feature_cols": FEATURES, "thresholds": None}
    (destination / "monitor_run_request.json").write_text(json.dumps(monitor, indent=2), encoding="utf-8")
    report = {"run_id": "run_SAMPLE_001", "model_id": "SAMPLE", "validation_result_path": "artifacts/SAMPLE/validation/result.json",
              "inventory_record": {"model_id": "SAMPLE", "model_name": "Synthetic credit demonstration", "tiering": {"tier": "Tier 2"},
                                   "purpose": "Synthetic service demonstration only; not a bank model."}, "parity_summary": None,
              "narrative": {"executive_summary": "Narrative pending independent review.", "conceptual_soundness": "Review pending.",
                            "findings_commentary": "Review the computed findings below.", "conclusion": "Pending human review.", "unverified_numbers": []},
              "sign_off": {"validator_agent_model": "not_used_in_standalone_demo", "human_validator": None, "signed_at": None}, "formats": ["html", "docx"]}
    (destination / "report_request.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return request


if __name__ == "__main__":
    make_sample()
    print("Created synthetic dev (6000) and random holdout (3000), scores and four request examples.")
