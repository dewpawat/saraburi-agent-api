import traceback 
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.v1.routes import router as v1_router
from app.core.config import settings

app = FastAPI(
    title="Saraburi Agent API",
    description="Central Agent API for Saraburi Provincial Health Office",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):

    error_traceback = traceback.format_exc()

    print(f"Error occurred: {error_traceback}")
    
    return JSONResponse(
        status_code=500,
        content={
            "MessageCode": "500",
            "Message": "Internal Server Error",
            "debug": {
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": error_traceback 
            }
        }
    )
# ----------------------------------

app.include_router(v1_router, prefix="/api/v1")
