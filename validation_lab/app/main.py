"""FastAPI entry point for deterministic validation, report and monitoring endpoints."""
import logging
from threading import Lock
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from app.config import LabError
from app import monitoring, report_builder, validate
from app.schemas import (ValidateRequest, ValidationResult, ReportRequest, ReportResult,
                         MonitorSimulateRequest, MonitorSimulateResult, MonitorRunRequest, MonitoringResult)

app = FastAPI(title="ModelPassport validation_lab", version="0.1.0")
RUN_LOCK = Lock()


@app.exception_handler(LabError)
async def lab_error(request: Request, exc: LabError) -> JSONResponse:
    """Return the shared public service error envelope."""
    return JSONResponse(status_code=exc.status, content={"error": {"code": exc.code, "message": exc.message}})


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Report request schema violations in the shared envelope."""
    messages = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
    return JSONResponse(status_code=422, content={"error": {"code": "INVALID_REQUEST", "message": messages}})


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
    """Keep missing routes and unsupported methods in the shared error shape."""
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}})


@app.exception_handler(Exception)
async def internal_error(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected failures without exposing local paths or internals."""
    logging.getLogger(__name__).exception("Validation service failed", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "The operation failed; inspect service logs."}})


@app.get("/health")
def health() -> dict:
    """Return the shared liveness contract without requiring other services."""
    return {"status": "ok", "service": "validation_lab", "version": "0.1.0"}


@app.post("/validate", response_model=ValidationResult)
def validate_model(request: ValidateRequest) -> dict:
    """Compute independent validation evidence for one model."""
    with RUN_LOCK:
        return validate.run(request)


@app.post("/report", response_model=ReportResult)
def report(request: ReportRequest) -> dict:
    """Render supplied prose and stored deterministic validation evidence."""
    with RUN_LOCK:
        return report_builder.build(request)


@app.post("/monitor/simulate", response_model=MonitorSimulateResult)
def simulate(request: MonitorSimulateRequest) -> dict:
    """Create explicitly simulated scored monthly batches."""
    with RUN_LOCK:
        return monitoring.simulate(request)


@app.post("/monitor/run", response_model=MonitoringResult)
def monitor(request: MonitorRunRequest) -> dict:
    """Measure batch drift and decide whether revalidation is required."""
    with RUN_LOCK:
        return monitoring.run(request)
