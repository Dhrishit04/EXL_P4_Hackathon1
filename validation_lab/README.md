# validation_lab

## What this is

ModelPassport's independent deterministic validation service, owned by Harshit. It measures supplied data and model scores, rates findings, creates charts, renders HTML and Word reports, simulates drift and decides when revalidation is needed. Port: **8002**. Only `factory_core` calls this service. No LLM client, keys or outbound service calls are used.

This package implements the validation service only. It does not create inventory agents, redevelopment, legacy estate, governance gates, dashboard, shared contracts or root configuration. It records supplied sign off information; approval and reviewer independence remain with `factory_core`. Commit and push this folder manually through your team's normal process.

Synthetic inputs let this folder run independently. They are not performance evidence for the real model estate. The external `contracts/examples/` and real estate were unavailable when this standalone package was prepared. Their integration test skips explicitly until the shared contracts are present.

## Folder map

| Path | Purpose |
|---|---|
| `README.md` | Setup, integration, limits and executable API examples |
| `requirements.txt` | Pinned runtime and test dependencies |
| `RESPONSIBLE_AI_INPUT.md` | Input for the team's Responsible AI note |
| `app/` | Validation API and deterministic engines |
| `app/main.py` | Health, validation, report and two monitoring endpoints; shared errors |
| `app/config.py` | Root detection, path boundaries, precision and JSON persistence |
| `app/schemas.py` | Section 9.2 request and response contracts |
| `app/data_loader.py` | CSV checks, exact ID joins and file hashes |
| `app/thresholds.py` | Illustrative defaults and validated overrides |
| `app/validate.py` | Complete validation orchestration |
| `app/findings.py` | Stable findings, test rules and section ratings |
| `app/charts.py` | PNG charts and identical dashboard series |
| `app/report_builder.py` | Self contained HTML and Word report rendering |
| `app/monitoring.py` | Seeded simulation, provenance and revalidation alerts |
| `app/metrics/` | Independent metric implementations |
| `app/metrics/data_quality.py` | Missingness, duplicates, constants and development ranges |
| `app/metrics/discrimination.py` | AUC, Gini, KS and deterioration |
| `app/metrics/calibration.py` | Brier, observed expected, HL and equal sized deciles |
| `app/metrics/stability.py` | Reference decile PSI and categorical or numeric CSI |
| `app/metrics/backtest.py` | Development quintiles and exact binomial tests |
| `app/metrics/fairness.py` | Fairlearn MetricFrame and pandas approval comparisons |
| `app/metrics/sensitivity.py` | Trusted scoring module shocks in a timed subprocess |
| `app/metrics/benchmark.py` | Development trained gradient boosting challenger |
| `app/templates/` | Report layout |
| `app/templates/validation_report.html` | Printable HTML with inline CSS and embedded PNGs |
| `sample_data/` | Service owned synthetic inputs and request examples |
| `sample_data/make_sample.py` | Seeded 6000 development and 3000 holdout rows and logistic scores |
| `sample_data/dev.csv`, `oot.csv` | Synthetic observations with five features and two protected columns |
| `sample_data/scored_dev.csv`, `scored_oot.csv` | `ID,pd,score,decision` outputs |
| `sample_data/*_request.json` | Four executable request bodies for the service |
| `tests/` | Module tests, hand calculations, HTTP integration and reports |
| `tests/conftest.py` | Isolated synthetic repositories for tests |
| `tests/test_contract_examples.py` | Read only shared contract checks, including `$include` |
| `tests/test_<module>.py` | Corresponding metric or service module tests |

There is no `mlflow_logger.py` or Dockerfile: optional P2 tracking and container packaging are not enabled. All runtime artifacts go to the repository's `artifacts/{model_id}/validation/` or `artifacts/{model_id}/monitoring/`. Synthetic CSVs are the explicit service sample-data exception. No changes to team owned root files are needed.

## How to run

Use Python **3.11 or newer**. Tested with Python 3.12. Create the environment outside this service folder, at the repository root. If this folder was extracted by itself, its parent acts as the standalone root. Do not create a replacement `contracts/` folder.

Windows PowerShell, starting from the repository root:

```powershell
py -3.12 -m venv .venv-validation
.\.venv-validation\Scripts\Activate.ps1
python -m pip install -r validation_lab/requirements.txt
$env:REPO_ROOT = (Get-Location).Path
Set-Location validation_lab
python sample_data/make_sample.py
uvicorn app.main:app --host 127.0.0.1 --port 8002 --workers 1
```

macOS or Linux, starting from the repository root:

```bash
python3 -m venv .venv-validation
source .venv-validation/bin/activate
python -m pip install -r validation_lab/requirements.txt
export REPO_ROOT="$PWD"
cd validation_lab
python sample_data/make_sample.py
uvicorn app.main:app --host 127.0.0.1 --port 8002 --workers 1
```

Health: `http://127.0.0.1:8002/health`. The service also starts with `uvicorn app.main:app --port 8002` from this folder. Keep the default single worker: operations are serialized within the process because frozen artifact paths store the latest run per model. Concurrent independent deployments need an external job queue or file locking. A new validation replaces the last result for that model; the report verifies `run_id` to reject stale requests.

The source can be copied directly into the real repository as `validation_lab/`. When Dhrishit supplies the estate, replace the data and score paths and feature lists in the request bodies. Use rebuilt score files for redeveloped models and golden scores for original Python models. Do not modify the estate or other services to do this.

## How to test

From `validation_lab/` in the activated environment:

```bash
python -m pytest tests -q -p no:cacheprovider
python -m pip check
```

Tests use isolated temporary repositories. They check hand calculated metrics, fairness agreement, ID mismatch failures, threshold boundaries, one class samples, report escaping and input hashes, deterministic simulation, no drift versus strong drift, sensitivity alignment and timeouts, and all four HTTP workflows. Symlink checks skip on Windows when the account lacks link privileges. Shared contract checks skip only if `contracts/examples/` is absent; run again in the shared repository before integration.

To inspect a full run, start the service and execute the API examples below in order. The HTML opens as a single file without a server, remote scripts, fonts or images. The Word report contains the same evidence and embedded charts. Neither report approves the model.

## Environment variables

| Name | Purpose |
|---|---|
| `REPO_ROOT` | Absolute repository path containing `validation_lab/`. Required standalone; otherwise the service walks upwards to a root containing both `validation_lab/` and `contracts/`. |
| `SENSITIVITY_TIMEOUT` | Scoring subprocess time limit in seconds; default `30`. |
| `MLFLOW_TRACKING_URI` | Not used; optional tracking is not enabled in this build. |

The service reads the shared root `.env` after root detection, without overriding process variables. Set `REPO_ROOT` in the shell for standalone use; a root `.env` cannot bootstrap a root that has not yet been found. LLM settings and service addresses are not used. Outputs deliberately follow the frozen `artifacts/` paths.

Sensitivity imports **trusted local scoring code only**. An import allow list, disabled socket connections and a subprocess timeout prevent common accidental calls and hangs. These are not an operating system security boundary. Use an isolated execution environment with denied network, read only mounts and resource limits before accepting untrusted modules. No code in this service calls an LLM or remote API.

## API

All paths in JSON are repository relative and use forward slashes. IDs must be unique and nonmissing in both data and scores; the two ID sets must match exactly. IDs are read as strings and joined by value. Score columns are validated: probabilities in `[0,1]`, integer score points, decisions `APPROVE` or `DECLINE`. Target `1` is the bad event. Protected, ID, target and score columns cannot be challenger inputs.

Errors use the HTTP status and `{"error":{"code":"CODE","message":"Readable explanation"}}`. Examples include `ID_MISMATCH`, `INVALID_ID`, `INVALID_PD`, `INVALID_PATH`, `INVALID_THRESHOLDS`, `RESULT_MISMATCH` and `INPUT_CHANGED`. A test that lacks statistical support returns null measurements and LOW findings, rather than fabricated evidence. An unexpected internal failure returns HTTP 500.

From `validation_lab/`, use `curl.exe` in Windows PowerShell or `curl` on macOS/Linux:

```bash
curl http://127.0.0.1:8002/health
curl -X POST http://127.0.0.1:8002/validate -H "Content-Type: application/json" --data-binary @sample_data/validate_request.json
curl -X POST http://127.0.0.1:8002/report -H "Content-Type: application/json" --data-binary @sample_data/report_request.json
curl -X POST http://127.0.0.1:8002/monitor/simulate -H "Content-Type: application/json" --data-binary @sample_data/monitor_simulate_request.json
curl -X POST http://127.0.0.1:8002/monitor/run -H "Content-Type: application/json" --data-binary @sample_data/monitor_run_request.json
```

| Endpoint | Result |
|---|---|
| `GET /health` | `{"status":"ok","service":"validation_lab","version":"0.1.0"}` |
| `POST /validate` | Section 9.2 ValidationResult, six decimal response precision, persisted at `artifacts/{model_id}/validation/result.json` |
| `POST /report` | `model_id`, nullable `html_path` and `docx_path`, `error` |
| `POST /monitor/simulate` | `model_id`, `simulated`, `batches_dir`, `batches`, `error` |
| `POST /monitor/run` | Section 9.2 MonitoringResult and revalidation trigger, persisted at `artifacts/{model_id}/monitoring/result.json` |

Metrics use full precision before response rounding. AUC uses probability of the bad event; KS is the maximum absolute cumulative gap. HL uses ten equal sized ordered groups and eight degrees of freedom; fewer than ten records or zero group variance makes HL unavailable. PSI uses development deciles and open extreme bins; repeated quantiles retain empty bins. CSI uses categories for at most ten reference values or nonnumeric features, otherwise reference deciles, with an explicit missing category. Both use epsilon `1e-6`. Empty risk bands remain visible with null statistics.

Favourable outcome is approval. Fairness compares the smallest with largest approval rate, the good-customer approval gap, and the maximum good/bad approval gap. Groups below fifty are reported and excluded from comparisons. A missing outcome class makes its group rate null and the affected comparison unavailable. Both opportunity and equalized odds gaps use the configurable `eo_diff_*` limits. Challenger preprocessing is fitted only on development data; missing numeric values use development medians. Sensitivity reruns the model baseline and shocks each numeric feature independently by plus/minus ten percent.

Section ratings follow their worst test. RED findings are HIGH, AMBER are MEDIUM, unavailable tests and small group notes are LOW. Overall is RED with any HIGH finding, AMBER with any MEDIUM, otherwise GREEN. GREEN is not approval and can coexist with tests that could not run; findings must be read. HL rejection alone is at most AMBER. Data quality failed checks are AMBER. The limits are illustrative and are not regulatory limits.

Monitoring resamples scored holdout rows with replacement and increasingly tilts toward higher PD ranks after the requested drift start. Repeated sampled IDs are allowed in batches. A hash manifest verifies which batches are simulated; externally modified or external batches are not labelled verified simulations. PSI greater than `psi_amber` or AUC deterioration greater than `auc_drop_trigger` gives RED. PSI at least `psi_green` or feature CSI greater than `psi_amber` gives AMBER. Undefined AUC comparisons produce a visible AMBER alert. Any RED triggers revalidation. Production provenance and a true temporal reference remain integration responsibilities.

Reports require matching model and run identities and reject changed input hashes. Raw narrative HTML is escaped, narrative images are disabled and the HTML restricts resource loading with a content security policy. The requested disclosure is included, alongside the actual pending or supplied review status; standalone example prose is explicitly pending review. The service does not verify human identity or cryptographic signatures.

### Contract additions

No additional required or optional fields are added to the section 9.2 wire contracts. Detailed quality measures use the existing `checks` array; extra dashboard chart data use the existing `series` dictionary. Fairness and feature stability series and `psi_features` chart identifiers are additional entries in those open collections. LOW unavailability findings use existing finding fields. Undefined statistical values are null as required by the brief.

Service owned artifact sidecars, outside the API shape: `validation/input_evidence.json` stores run identity and input hashes; `validation/report_result.json` stores report locations; `monitoring/simulation_manifest.json` stores simulation parameters and batch hashes; `monitoring/simulation_result.json` preserves simulation results after a monitoring run replaces `monitoring/result.json`.
