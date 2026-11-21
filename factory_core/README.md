# factory_core

Service 1 of ModelPassport. Owner: Varun. Port 8000.

## What this is

The brain and the front door of ModelPassport:

* The only API the dashboard (factory_console) talks to.
* Runs the five stage pipeline for a model (discover, document, redevelop, validate, monitor) as a LangGraph state graph that pauses at a human gate after every stage.
* Hosts the LLM agents: discovery, documentation, document drift and the independent validator narrative.
* Checks what the agents write with code: every quoted piece of evidence is looked up in the cited file (evidence verifier), and every number in the validation narrative must exist in the computed results (number grounding).
* Calls redev_engine and validation_lab over HTTP for the rebuild, the parity proof, the validation metrics, the report and monitoring.
* Keeps the inventory, runs, gate decisions and a hash chained, tamper evident audit trail in SQLite (`artifacts/factory_core.db`).

How the three design rules are enforced here:

| Rule | Where |
|---|---|
| Every claim is cited | `agents/evidence_verifier.py` checks every quote of the discovery, documentation and drift agents; failures stay visible as `UNVERIFIED` or `SME_INPUT_NEEDED` |
| Every number is computed | Metrics come from validation_lab only; `agents/number_grounding.py` checks the validator's narrative, allows one rewrite, then lists `unverified_numbers` |
| Every gate is signed | `pipeline_graph.py` pauses at each gate; `gate_decisions.py` records the human decision, refuses the validate approval from the redevelop approver (409), and writes the audit event |

## Folder map

| Path | Contents |
|---|---|
| `README.md` | This file |
| `requirements.txt` | Pinned dependencies |
| `Dockerfile` | Container image for `docker compose up` at the repository root; built from the root so it keeps the repository layout |
| `app/main.py` | Entry point: creates the API, allows the dashboard origin, scans the estate and starts the pipeline runner at startup |
| `app/config.py` | Settings from the root `.env`, repository root detection |
| `app/database.py` | SQLite tables (models, runs, stage runs, stage outputs, audit events) and their read and write helpers |
| `app/schemas.py` | Shared enumerations (stages, statuses, tiers, ratings), base classes, the estate manifest shape |
| `app/api_schemas.py` | Public API shapes: model list, inventory record, runs, gates, audit, metrics, files (section 9.3) |
| `app/stage_result_schemas.py` | Documentation, validation view, compliance, and the `POST /report` request |
| `app/redev_engine_schemas.py` | Shapes exchanged with redev_engine (section 9.1) |
| `app/validation_lab_schemas.py` | Validate and report shapes of validation_lab (section 9.2) |
| `app/monitoring_schemas.py` | Monitoring shapes of validation_lab (section 9.2) |
| `app/llm_client.py` | One way to call the LLM, with the reply cache, replay mode, retries and JSON validation (section 12) |
| `app/provider_errors.py` | Reads a provider error: its own message and suggested retry delay (a used up daily quota stops at once) |
| `app/audit_trail.py` | Append only, hash chained audit trail, its verification, and the recorder the stages use |
| `app/artifact_store.py` | Writes run outputs under `artifacts/` and records each write in the audit trail |
| `app/estate_scanner.py` | Finds model folders, reads manifests and the register, registers models, safe file reader |
| `app/sample_model.py` | Built-in, read only sample model from the contract examples, used only while the estate is empty |
| `app/tiering_policy.py` | Deterministic risk tier, next validation date and document status |
| `app/service_clients.py` | Calls to redev_engine and validation_lab, with stub mode |
| `app/gate_decisions.py` | Approve and reject at a gate, review time, the independence rule, automatic approvals for seeding |
| `app/pipeline_context.py` | What every stage shares, and the stage lifecycle (running, awaiting review, failed, skipped) |
| `app/pipeline_stages.py` | The work of the discover, document and redevelop stages |
| `app/validation_lab_stages.py` | The work of the validate and monitor stages |
| `app/pipeline_graph.py` | The LangGraph state graph: five stages, a gate after each, and the final node |
| `app/pipeline_runner.py` | Starts and resumes runs in background threads, recovers stages left running after a restart |
| `app/api/` | One file per group of endpoints: `models_api.py`, `runs_api.py`, `results_api.py`, `audit_api.py`, `files_api.py`, and `api_errors.py` for the contract error body |
| `app/agents/discovery_agent.py` | Stamp 1: static code signals plus the LLM pass for the inventory fields |
| `app/agents/documentation_agent.py` | Stamp 2: the ten section document, one LLM call per section, claim markers and groundedness |
| `app/agents/document_drift.py` | Differences between the old model document and the code, both sides verified |
| `app/agents/evidence_verifier.py` | Checks quotes against the cited lines and corrects line numbers (no LLM) |
| `app/agents/source_context.py` | Model files with numbered lines for the agents' prompts, and records as prompt JSON without run specific fields (timestamps, run id, duration), so replay mode works on a fresh database |
| `app/agents/validator_agent.py` | The independent validator narrative |
| `app/agents/number_grounding.py` | Checks every number of the narrative against the computed results (no LLM) |
| `app/agents/compliance_matrix.py` | The SS1/23 matrix: the expectations under the five principles and how the matrix is built |
| `app/agents/compliance_checks.py` | The check behind each expectation of the matrix |
| `scripts/seed_demo.py` | Runs every estate model through the pipeline with automatic approvals |
| `scripts/export_snapshot.py` | Saves every GET response for the dashboard's snapshot mode (section 9.4) |
| `scripts/evaluate_discovery.py` | Field accuracy of the inventory records against the answer keys |
| `scripts/evaluate_document_drift.py` | Recall of the seeded document discrepancies |
| `scripts/answer_keys.py` | Reads `model_estate/_answer_keys/`; only the two evaluation scripts use it |
| `tests/` | `test_<module>.py` for each module; `test_schemas.py` checks every schema module against `contracts/examples/`; `test_scripts.py` covers `scripts/`; `conftest.py` holds the fixtures, a test estate and a scripted LLM |
| `llm_cache/` | Recorded LLM replies for replay mode, one JSON file per prompt. Created by the first live run; commit it |

## How to run

Python 3.11 or newer. From this folder:

```
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

Interactive API docs: http://localhost:8000/docs. Port 8000 must be free.

* At every start the service scans `model_estate/`. While the estate holds no models it shows one read only sample model (see Contract notes).
* `USE_STUBS=true` answers the redev_engine and validation_lab calls from `contracts/examples/`, so the pipeline runs without the other services.
* `LLM_MODE=live` needs `LLM_API_KEY` and `LLM_MODEL`; every reply is stored in `llm_cache/`. `LLM_MODE=replay` answers only from `llm_cache/`, with no key and no network; a prompt that was never recorded fails the stage with a clear message.
* Delete `artifacts/factory_core.db` and `artifacts/pipeline_checkpoints.db` to start from an empty state.

Scripts, from this folder:

```
python -m scripts.seed_demo                  # every estate model through all stages, automatic approvals
python -m scripts.export_snapshot            # artifacts/snapshot/, copy into factory_console/public/snapshot/
python -m scripts.evaluate_discovery         # field accuracy, saved to artifacts/evaluation/discovery.json
python -m scripts.evaluate_document_drift    # drift recall, saved to artifacts/evaluation/document_drift.json
```

Seeded runs are approved by `demo_developer` and `demo_validator`, marked automatic in the audit trail and left out of the human review minutes.

## How to test

```
pytest
```

The tests use temporary folders, a small test estate, a scripted LLM and stubbed or mocked services. They never touch `artifacts/`, `model_estate/` or the network, and need no key.

## Environment variables

Read from the root `.env` (see `.env.example` in the repository root). Values already set in the environment win.

| Variable | Used for | Default |
|---|---|---|
| `LLM_BASE_URL` | OpenAI compatible endpoint of the LLM provider | see `.env.example` |
| `LLM_API_KEY` | Key for that endpoint; never logged, printed or stored | empty |
| `LLM_MODEL` | Model id of the discovery, documentation and drift agents | empty |
| `LLM_MODEL_VALIDATOR` | Optional different model for the validator agent | empty (uses `LLM_MODEL`) |
| `LLM_MODE` | `live` or `replay`; anything else stops the service at startup | `live` |
| `LLM_TEMPERATURE` | Temperature of every LLM call | `0` |
| `USE_STUBS` | `true`: answer redev_engine and validation_lab calls from `contracts/examples/` | `false` |
| `REDEV_ENGINE_URL` | redev_engine address | `http://localhost:8001` |
| `VALIDATION_LAB_URL` | validation_lab address | `http://localhost:8002` |
| `REDEVELOP_TIMEOUT_SECONDS` | How long to wait for `POST /redevelop`; a live rebuild with healing can take over 20 minutes. Other service calls wait 600 seconds | `2400` |
| `ESTATE_DIR` | Model estate folder, relative to the repository root | `model_estate` |
| `ARTIFACTS_DIR` | Run outputs and the databases, relative to the repository root | `artifacts` |
| `MLFLOW_TRACKING_URI` | Optional MLflow tracking | empty |

## API

Full shapes: section 9.3 of [`docs/PROJECT_CONTEXT.md`](../docs/PROJECT_CONTEXT.md), examples in [`contracts/examples/`](../contracts/examples/).

| Method and path | Returns |
|---|---|
| `GET /health` | `{"status": "ok", "service": "factory_core", "version": "0.1.0"}` |
| `GET /api/models` | `{"models": [ModelSummary]}` |
| `POST /api/estate/scan` | `{"models_found": [...]}` |
| `GET /api/models/{model_id}` | InventoryRecord |
| `POST /api/models/{model_id}/runs` | `{"run_id": ...}` at once; the run continues in the background, so poll `GET /api/runs/{run_id}` |
| `GET /api/runs/{run_id}` | Run |
| `POST /api/runs/{run_id}/gates/{stage}/decision` | The updated Run |
| `GET /api/models/{model_id}/documentation` | Documentation, or `404 NOT_AVAILABLE` |
| `GET /api/models/{model_id}/redevelopment` | RedevelopResult as returned by redev_engine, or `404 NOT_AVAILABLE` |
| `GET /api/models/{model_id}/validation` | ValidationView, or `404 NOT_AVAILABLE` |
| `GET /api/models/{model_id}/monitoring` | MonitoringResult as returned by validation_lab, or `404 NOT_AVAILABLE` |
| `GET /api/models/{model_id}/compliance` | Compliance, computed on every request |
| `GET /api/audit?model_id=M001&limit=200` | Audit: the newest events, oldest first; `chain_valid` checks the whole chain |
| `GET /api/metrics/factory` | FactoryMetrics, computed from the database |
| `GET /api/files?path=...` | FileView of a text file under `model_estate/` or `artifacts/`, at most 1 MB |
| `GET /api/artifacts/{path}` | The file itself (png, html, docx) |

Every error has the body `{"error": {"code": ..., "message": ...}}`:

| Status | Codes |
|---|---|
| 400 | `INVALID_PATH` |
| 403 | `FORBIDDEN_PATH` (includes anything in `_answer_keys`) |
| 404 | `MODEL_NOT_FOUND`, `RUN_NOT_FOUND`, `NOT_AVAILABLE`, `FILE_NOT_FOUND`, `NOT_FOUND` |
| 405 | `METHOD_NOT_ALLOWED` |
| 409 | `INDEPENDENCE_VIOLATION`, `GATE_NOT_OPEN` (the stage is not awaiting review), `RUN_ACTIVE` (the model already has a running or paused run), `SAMPLE_MODEL` (the sample is read only) |
| 413, 415 | `FILE_TOO_LARGE`, `FILE_NOT_TEXT` |
| 422 | `INVALID_REQUEST`, `INVALID_MANIFEST`, `INVALID_REGISTER` |
| 500 | `INTERNAL_ERROR` |

A stage that fails (an LLM error, a service that is down, parity not reached, a validation that did not complete) is shown as `FAILED` with its error message in the run; the run stops there.

### Contract notes

* **Runs.** `POST /api/models/{model_id}/runs` accepts any subset of the five stages; the others are `SKIPPED` with the reason "Not requested in this run.". Redevelop is skipped when the manifest says `redevelop: false`, validate and monitor when the manifest has no data. Run ids are `run_{model_id}_{number}`. Gate `review_seconds` counts from the moment the stage started waiting for review. Approving the validate gate also clears `revalidation_required`.
* **Scores for validation.** A rebuild with status `PARITY_PASSED` or `TRANSLATED_NO_GOLDEN` (translated, tested and scored, but no legacy outputs exist, as for M001) is validated on its own scores in `artifacts/{model_id}/redevelop/`, and the report's parity summary says which. A model that was not redeveloped is validated on the golden files in the estate. `PARITY_FAILED` and `ERROR` stop the run at the redevelop stage.
* **Independence.** The validate gate cannot be approved by the reviewer (any letter case) who approved the redevelop gate of the same run, or of the latest earlier run when this run has no redevelop stage. A rejection is always allowed.
* **Before discovery.** A registered model that has not been through the discover stage has an InventoryRecord with only the register and file facts. `model_type`, `purpose`, `algorithm`, `target_variable`, `tiering`, `doc_status` and `next_validation_due` are `null` and the lists are empty; in ModelSummary `model_type`, `algorithm`, `tier` and `doc_status` can be `null`. Discovery also returns `null` with an open question when the files do not answer a field, and adds an open question for every field it filled without evidence.
* **Drift evidence.** In `doc_drift.json` and the `drift` list of `/api/models/{model_id}/documentation`, `legacy_evidence` or `code_evidence` of an item can be `null`: the agent cited nothing for that side, or cited a file other than the old document (legacy side) or the code files (code side). Such an item is `UNVERIFIED`.
* **Artifact links.** `{path}` in `/api/artifacts/{path}` is relative to `artifacts/`, so a payload path such as `artifacts/M001/validation/charts/roc_oot.png` becomes `/api/` followed by that path. A leading `artifacts/` is accepted either way.
* **Sample model.** While `model_estate/` holds no models, the service registers M001 from the contract examples, with its example run and outputs. Its name ends with "(sample from contract examples)", its values are illustrative and never results, it cannot be run or decided on (`409 SAMPLE_MODEL`), and it writes no audit events. It is removed as soon as a scan finds real models.
* **Metrics.** `avg_groundedness` and `avg_agent_minutes_per_model` are `null` until there is data. `docs_outdated_at_discovery` counts records with `doc_status` `OUTDATED` or `MISSING`. `human_review_minutes_logged` leaves out runs started with `auto_approve`.
* **Compliance.** A simplified team mapping to the five SS1/23 principle titles, never sub principle numbers; organisational controls are `OUT_OF_SCOPE`. It is computed on every request and saved to `artifacts/{model_id}/compliance/ss123_matrix.json` when a run completes.

### Contract additions

None.
