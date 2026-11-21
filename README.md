# ModelPassport

An agentic model risk factory. EXL x UCD Data and AI Hackathon 2026, Challenge 04.

A Tier 1 UK retail bank runs about 250 credit, fraud and pricing models in SAS, R and Python. Under PRA SS1/23 each model needs current documentation and independent validation, yet the documents are outdated and one validation takes 8 to 12 weeks. ModelPassport takes a legacy model folder (code, a stale model document, data) and produces a **Model Passport**: one evidence pack per model with five stamps. An AI agent or a deterministic engine produces each stamp, and a human reviewer countersigns it before the next stage starts.

| Stamp | Stage | What is produced | Produced by |
|---|---|---|---|
| 1 | Discover | Inventory record and risk tier | factory_core |
| 2 | Document | Current model documentation where every claim cites code lines, plus the differences against the old document | factory_core |
| 3 | Redevelop | Python rebuild of the SAS or R model, unit tests, four level parity certificate | redev_engine |
| 4 | Validate | Discrimination, calibration, stability, fairness, findings, report | validation_lab (numbers), factory_core (words) |
| 5 | Monitor | Drift monitoring on simulated production batches with an automatic revalidation trigger | validation_lab, factory_core |

Three design rules:

* **Every claim is cited.** Anything an LLM writes about a model points to file and line evidence, and code checks that the evidence exists. Unverified claims are flagged, never hidden.
* **Every number is computed.** Metrics, coefficients and statistics come from deterministic code only. The LLM writes words around them, and a checker confirms every number in those words.
* **Every gate is signed.** Agents never approve their own work. Human decisions go into a tamper evident audit trail, and the person who approves validation cannot be the person who approved redevelopment.

The full specification, including every API contract, is in [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md).

## Repository map

| Path | What it is | Owner |
|---|---|---|
| `README.md` | Start here: what the project is, repository map, how to run it | Varun |
| `.env.example` | Every setting, each with a comment | Varun |
| `.gitignore` | Files git never tracks | Varun |
| `docker-compose.yml` | Starts all four services with one command | Varun |
| `.dockerignore` | Keeps `.env`, local builds and run outputs out of the images | Varun |
| `docs/` | Project documents: `PROJECT_CONTEXT.md` (specification and contracts), `ARCHITECTURE.md`, `RESPONSIBLE_AI.md` | Varun |
| `contracts/` | Example request and response for every API, generated from the project context | Varun |
| `model_estate/` | The sample bank: legacy models, data, golden outputs | Dhrishit |
| `factory_core/` | Service 1: orchestrator, agents, human gates, audit trail, API for the dashboard | Varun |
| `redev_engine/` | Service 2: SAS and R to Python rebuild, parity proof | Dhrishit |
| `validation_lab/` | Service 3: validation, fairness, monitoring, report | Harshit |
| `factory_console/` | Service 4: web dashboard | Aayush |
| `artifacts/` | Run outputs, created at run time, ignored by git | (generated) |

Each folder is created and maintained by its owner.

## Architecture

```
Browser: factory_console (React, port 5173)
   => factory_core (FastAPI, port 8000): REST API, LangGraph pipeline with human gates, SQLite, audit trail
         => redev_engine (FastAPI, port 8001): rebuild and parity proof
         => validation_lab (FastAPI, port 8002): validation, report, monitoring (no LLM)
         => LLM provider (any OpenAI compatible endpoint)
   redev_engine => LLM provider
   The Python services read model_estate/ and read and write artifacts/ on the same disk.
```

The dashboard talks only to factory_core. Services exchange file paths, not file contents. The diagram, the run sequence and where each design rule is enforced are in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Team and ownership

| Member | Service | Owns these paths (and nothing else) | Port |
|---|---|---|---|
| Varun | factory_core: agent orchestrator, inventory, documentation agents, governance API. Integration lead. | `factory_core/`, `contracts/`, `docs/`, root files | 8000 |
| Dhrishit | redev_engine: the sample model estate, SAS and R to Python rebuild, parity proof. Repository owner. | `redev_engine/`, `model_estate/` | 8001 |
| Harshit | validation_lab: validation metrics, fairness, monitoring, report rendering | `validation_lab/` | 8002 |
| Aayush | factory_console: the web dashboard | `factory_console/` | 5173 |

Each member works on `main` in their own fork of this repository, creates and changes files only inside their own paths, and commits by hand with one plain line in the form `[service] what changed`. Work reaches this repository through a pull request from the fork's `main`, which the repository owner merges. A problem in someone else's folder goes to its owner.

## Quick start

Prerequisites: Python 3.11 or newer, Node.js with npm.


**One command, with Docker.** `cp .env.example .env`, fill it in as in step 1, then `docker compose up --build`. Open http://localhost:5173. Run outputs land in `artifacts/` on your machine and the LLM reply caches stay in `factory_core/llm_cache/` and `redev_engine/llm_cache/`, so they survive restarts. The dashboard is built in live mode; set `VITE_API_MODE=mock` or `snapshot` in the root `.env` and rebuild to change it. Stop with `docker compose down`.

1. Settings: `cp .env.example .env`. With a key, fill in `LLM_API_KEY` and `LLM_MODEL` and keep `LLM_MODE=live`. Without a key, set `LLM_MODE=replay` to use the recorded replies in `factory_core/llm_cache/` and `redev_engine/llm_cache/`.
2. Start the services, each in its own terminal (commands below).
3. Open the dashboard at http://localhost:5173.
4. Optional: seed every model with automatic approvals: `cd factory_core && python -m scripts.seed_demo`.

**Replay mode, no key.** Every live LLM reply is stored, keyed by the model and the prompt. After one recorded run is committed, anyone can repeat it with `LLM_MODE=replay`: no key and no network. A prompt that was never recorded stops its stage with a clear message instead of calling a provider.

**factory_core alone.** With `USE_STUBS=true`, factory_core answers the redev_engine and validation_lab calls from `contracts/examples/`, so the whole pipeline can be clicked through without the other two services.

| Service | Port | Start, inside the service folder |
|---|---|---|
| factory_core | 8000 | `python3.11 -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt`, `uvicorn app.main:app --port 8000` |
| redev_engine | 8001 | see `redev_engine/README.md` |
| validation_lab | 8002 | see `validation_lab/README.md` |
| factory_console | 5173 | see `factory_console/README.md` |

## Environment variables

All settings live in one `.env` file at the repository root; [`.env.example`](.env.example) lists each one with a comment. The main ones:

| Variable | Meaning |
|---|---|
| `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` | The OpenAI compatible LLM endpoint used by factory_core and redev_engine |
| `LLM_MODEL_VALIDATOR` | Optional different model for the validator agent, for validation independence |
| `LLM_MODE` | `live` (cache, then provider) or `replay` (cache only, no key) |
| `USE_STUBS` | `true` lets factory_core run without redev_engine and validation_lab |
| `REDEV_ENGINE_URL`, `VALIDATION_LAB_URL` | Service addresses |
| `ESTATE_DIR`, `ARTIFACTS_DIR` | Model estate and run output folders, relative to the repository root |

The dashboard keeps its own settings in `factory_console/.env`.

## Contracts

`contracts/examples/` holds one JSON example per API shape. Regenerate or check them from the repository root:

```
python contracts/extract_examples.py
python contracts/extract_examples.py --check
```

## Data sources and licences

Public or synthetic data only, never personal data. Model owners appear as role titles.

| Model | Data | Licence |
|---|---|---|
| M001 credit card PD scorecard (SAS) | UCI Default of Credit Card Clients, 30,000 rows: https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients | CC BY 4.0 |
| M002 personal loan PD (R) | UCI Statlog (German Credit Data), 1,000 rows: https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data | CC BY 4.0 |
| M003 card transaction fraud (Python) | Synthetic, generated by a seeded script | Synthetic |
| M004 risk based loan pricing (SAS) | No data | Not applicable |

## Limitations

* Parity proves equivalence on the tested records, not on every possible input.
* The "oot" sample of M001 and M002 is a random holdout, not a true out of time sample. Monitoring batches are simulated.
* The Taiwan (2005) and German (1994) datasets are not UK portfolios. All thresholds are illustrative defaults, not regulatory limits.
* The SS1/23 matrix is a simplified team mapping, not a legal or regulatory assessment.
* Generated documents, narratives and reports are drafts for expert review; a human signs every gate.

The Responsible AI note is in [`docs/RESPONSIBLE_AI.md`](docs/RESPONSIBLE_AI.md).
