# redev_engine

## What this is

redev_engine turns a legacy SAS or R model from `model_estate/` into a tested Python module and proves that the Python version behaves the same as the legacy model. It is called only by factory_core (port 8001).

One `POST /redevelop` runs the whole flow:

1. **Analyse.** The legacy code is read with numbered lines, a static scan marks lines of interest, and one LLM call returns `logic_spec.json`. Each item in it cites file and lines, and the citations are checked by code.
2. **Translate.** One LLM call returns `model.py` with a fixed interface (`prepare`, `fit`, `score`). The legacy coefficient values are then written into `DEPLOYED_COEFFICIENTS` by code, never by the LLM. Every block carries a `# source:` comment, which becomes `line_mapping` after the cited lines are verified.
3. **Write tests.** One LLM call returns `test_model.py`, with expected values that follow the legacy semantics.
4. **Run and check.** The rebuilt code passes a static safety check, then runs in an isolated subprocess: the unit tests, scoring of dev and oot, and the refit. The deterministic parity engine then compares the outputs on four levels.
5. **Heal.** On failure, the mismatch profiler (no LLM) finds where mismatches concentrate. The healer (one LLM call) gets the failing tests, the 20 largest mismatches, the profile and the pitfall library, and returns a diagnosis, a one sentence fix and a corrected file. This repeats up to `max_heal_iterations` times, and stops early when the healer returns `model.py` unchanged. The best attempt is returned, not simply the last one: parity first, then scoring, parity levels and unit tests passed. When an earlier attempt is kept, it is run once more so the scores and parity files match it, and `translation_notes.md` says which attempt was kept. The test output in the heal prompt leaves out run times, the temporary sandbox folder, local paths and memory addresses, so recorded heal replies also replay.
6. **Certify.** A parity certificate is written in markdown and JSON with tolerances, numbers and SHA 256 hashes. The status is honest: `PARITY_PASSED`, `PARITY_FAILED`, `TRANSLATED_NO_GOLDEN` or `ERROR`.

Parity levels:

| Level | Passed when |
|---|---|
| L1 coefficients | Refitted Python coefficients are within 1e-4 of `coefficients_legacy.csv` (NOT_APPLICABLE without an estimation step) |
| L2 record scores | Every record's PD is within 1e-6 of the legacy PD on dev and oot, and no id is missing on either side |
| L3 decisions | Score points and decision are identical for every record |
| L4 distribution | PSI between the legacy and Python output distributions over 10 bins is at most 1e-9 |

Every number in the result is computed by code. The LLM only writes code, tests and diagnoses.

## Folder map

| Path | Contents |
|---|---|
| `README.md` | This file |
| `requirements.txt` | Pinned dependencies |
| `Dockerfile` | Container image for `docker compose up` at the repository root; built from the root so it keeps the repository layout |
| `docs/EVALUATION.md` | Measured results for the deck and how to reproduce them |
| `docs/MODEL_ESTATE.md` | The sample model estate in `model_estate/`: models, folder map, how to regenerate data and golden outputs |
| `docs/DATA_SOURCES.md` | Source, licence and citation of every dataset in the estate |
| `docs/M001_GOLDEN_RUN.md` | Steps to produce the M001 golden files on SAS OnDemand for Academics |
| `app/main.py` | Entry point: `/health`, `/redevelop`, `/parity`, `/pitfalls` |
| `app/config.py` | Settings from the root `.env`, repository root detection, path helper |
| `app/schemas.py` | Request and response models matching section 9.1 of the project context |
| `app/llm_client.py` | One function to call the LLM, with file cache, replay mode, retries and JSON validation |
| `app/redevelop_pipeline.py` | Runs the whole flow for `POST /redevelop` and the parity re-run for `POST /parity` |
| `app/code_analyzer.py` | Legacy code to `logic_spec.json` |
| `app/code_translator.py` | Logic spec plus source to `model.py`, coefficient injection, line mapping, translation notes |
| `app/test_writer.py` | Writes `test_model.py` for the rebuilt model |
| `app/code_sandbox.py` | Static safety check and isolated subprocess runner |
| `app/parity_engine.py` | Four level parity comparison, no LLM |
| `app/mismatch_profiler.py` | Finds where mismatches concentrate, no LLM |
| `app/self_healer.py` | Diagnose and repair step |
| `app/parity_certificate.py` | Certificate in markdown and JSON |
| `app/pitfall_library.py` | Known SAS and R translation traps |
| `app/mlflow_logger.py` | Optional MLflow tracking and model registration |
| `tests/` | `test_<module>.py` for each module in `app/`, plus `conftest.py` with a tiny synthetic estate and a scripted LLM |
| `llm_cache/` | Recorded LLM replies for replay mode (created by the first live run, committed) |

Run time output goes to `artifacts/{model_id}/redevelop/`: `model.py`, `test_model.py`, `logic_spec.json`, `translation_notes.md`, `scored_dev.csv`, `scored_oot.csv`, `parity_certificate.md`, `parity_certificate.json`, `mismatches.csv` (only on failure), `result.json`.

## How to run

Python 3.11 or newer. From the repository root:

```
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r redev_engine/requirements.txt
cd redev_engine
uvicorn app.main:app --port 8001
```

Example call (M002 is the hero model until the M001 SAS golden files exist):

```
curl -s -X POST localhost:8001/redevelop -H 'Content-Type: application/json' \
  -d '{"run_id": "run_M002_001", "model_id": "M002", "estate_path": "model_estate/M002_loan_pd_glm_r", "max_heal_iterations": 3, "use_pitfall_library": true}'
```

* Stub mode for integration without the LLM: `REDEV_STUB=true uvicorn app.main:app --port 8001`. `/redevelop` then returns `contracts/examples/redevelop_result.M001.json` with the model id and run id of the request.
* Replay mode with no key and no network: `LLM_MODE=replay`. Every LLM reply is served from `llm_cache/`.

## How to test

```
cd redev_engine
python -m pytest tests
```

The tests use a tiny synthetic estate and a scripted LLM, so they need no key and no network. They cover the parity failure cases (flipped sign fails L2, different rounding rule fails L3, missing ids fail L2, coefficient drift fails L1), the sandbox (forbidden imports rejected, endless loop stopped, secrets not visible), the full heal loop and the honest failure statuses.

## Environment variables

Read from the `.env` file at the repository root.

| Variable | Use |
|---|---|
| `LLM_BASE_URL` | OpenAI compatible endpoint |
| `LLM_API_KEY` | Key for that endpoint. Never written to any file or log, and never passed to the sandbox |
| `LLM_MODEL` | Model id used for every redevelopment step |
| `LLM_MODE` | `live` (cache first, then provider) or `replay` (cache only) |
| `LLM_TEMPERATURE` | Sampling temperature, default 0 |
| `ESTATE_DIR` | Estate folder relative to the repository root, default `model_estate` |
| `ARTIFACTS_DIR` | Output folder relative to the repository root, default `artifacts` |
| `REDEV_STUB` | `true` returns the contract example from `/redevelop` |
| `REDEV_LLM_CACHE_DIR` | Optional override of the cache folder, default `redev_engine/llm_cache` |
| `MLFLOW_TRACKING_URI` | Optional. When set and `mlflow` is installed, runs are logged and a passing model is registered as a pyfunc model named after the model id |

## API

| Method and path | Purpose |
|---|---|
| `GET /health` | `{"status": "ok", "service": "redev_engine", "version": "0.1.0"}` |
| `POST /redevelop` | Body `RedevelopRequest`, returns `RedevelopResult` (section 9.1). Synchronous, can take minutes |
| `POST /parity` | Body `{"model_id", "estate_path"}`. Re-runs the deterministic parity check on the existing `model.py` and returns the `parity` object |
| `GET /pitfalls` | `{"pitfalls": [{"id", "language", "title", "description", "python_fix"}]}` |

Errors use `{"error": {"code", "message"}}`. Codes: `INVALID_PATH` (400, path outside the estate), `MODEL_MISMATCH` (400), `NOT_FOUND` (404, no manifest), `NOT_AVAILABLE` (404, no rebuilt model for `/parity`), `NOT_REDEVELOPABLE` (422, Python model or no data), `SCORING_FAILED` (422), `INVALID_REQUEST` (422), `STUB_UNAVAILABLE` (503). A failure inside a run is not an HTTP error. It is returned as `status: "ERROR"` with `error.code` `LLM_ERROR`, `SCORING_FAILED` or `INTERNAL_ERROR`.

### Contract additions

Optional details, with no renamed fields and no new required fields:

* `error` is `null` or `{"code", "message"}`.
* `generated_files[].kind` also uses `certificate_md`, `certificate_json`, `mismatch_sample` and `result`.
* For `TRANSLATED_NO_GOLDEN`, `parity` holds four `NOT_APPLICABLE` levels and the certificate paths are `null`.
* `mlflow` is `null`, or `{"run_id", "registered_model"}`, or `{"error"}`.
* In the manifest of a model without estimation (M003), `golden.coefficients_path` is `null`.

### Sandbox limits

The static check blocks imports outside `pandas, numpy, math, statsmodels, scipy, sklearn, typing, dataclasses`, calls to `eval, exec, open, compile, __import__` and similar, any name or attribute that starts with two underscores, and file or pickle I/O attributes (`read_*`, `to_csv`, `load`, `save`, `fromfile` and similar). The rebuilt model never needs file access, because the trusted runner reads the data and writes the scores. The code then runs in a separate process with a temporary working folder, an empty environment, a 120 second limit and OS resource limits (written file size, memory where the platform allows it).

This is a denylist plus process isolation, not a security boundary. A determined escape through the allowed libraries remains possible. A bank deployment must run the sandbox in a real isolation layer: a container or nsjail/gVisor with no network, a read only filesystem apart from the working folder, read only mounts of only the dev and oot files, and seccomp. The static check then stays as an extra lint.
