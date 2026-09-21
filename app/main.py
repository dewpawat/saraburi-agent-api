import time
import logging
import traceback
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.routes import router as v1_router
from app.core.config import settings
from app.core.security import get_client_ip
from app.utils.logger import log_access

# Setup logger for production Docker logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("saraburi_agent")

app = FastAPI(
    title="Saraburi Agent API",
    description="Central Agent API for Saraburi Provincial Health Office",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
)

# ---------------------------------------------------------
# Request Access Logging Middleware (Daily Log: 365 files/yr)
# ---------------------------------------------------------
@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    client_ip = get_client_ip(request)
    x_hospcode = request.headers.get("x-hospcode", "-")
    method = request.method
    path = request.url.path

    try:
        response = await call_next(request)
        process_time_ms = (time.perf_counter() - start_time) * 1000
        
        log_access(
            client_ip=client_ip,
            method=method,
            path=path,
            hospcode=x_hospcode,
            status_code=response.status_code,
            process_time_ms=process_time_ms,
        )
        return response
    except Exception as exc:
        process_time_ms = (time.perf_counter() - start_time) * 1000
        log_access(
            client_ip=client_ip,
            method=method,
            path=path,
            hospcode=x_hospcode,
            status_code=500,
            process_time_ms=process_time_ms,
            detail=f"Exception: {type(exc).__name__} - {str(exc)}"
        )
        raise exc

# ---------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Standardize HTTP exceptions (e.g. 401, 403, 400 from api_security).
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "MessageCode": str(exc.status_code),
            "Message": str(exc.detail),
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Standardize Pydantic validation errors (422) into standard format.
    """
    error_parts = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "")
        error_parts.append(f"{loc}: {msg}")
    summary = "; ".join(error_parts) if error_parts else "Invalid request data"
    
    return JSONResponse(
        status_code=422,
        content={
            "MessageCode": "422",
            "Message": f"Validation Error: {summary}",
        }
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Catches all database errors (missing tables, columns, connection failures).
    Logs full traceback to server console while returning clean JSON format to client.
    """
    logger.error(f"Database error on {request.method} {request.url.path}: {exc}\n{traceback.format_exc()}")
    
    orig_err = getattr(exc, "orig", None)
    err_message = str(orig_err) if orig_err else str(exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "MessageCode": "500",
            "Message": f"Database Error: {err_message}",
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    General catch-all handler for unhandled code exceptions.
    Prevents raw Python traceback from leaking to client.
    """
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}\n{traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "MessageCode": "500",
            "Message": f"Internal Server Error: {type(exc).__name__} - {str(exc)}",
        }
    )

# ---------------------------------------------------------
# Routers
# ---------------------------------------------------------
app.include_router(v1_router, prefix="/api/v1")
