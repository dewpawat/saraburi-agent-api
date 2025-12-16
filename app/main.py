from fastapi import FastAPI
from app.api.v1.routes import router as v1_router
from app.core.config import settings

app = FastAPI(
    title="Saraburi Agent API",
    description="Central Agent API for Saraburi Provincial Health Office",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
)

app.include_router(v1_router, prefix="/api/v1")
