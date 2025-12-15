from fastapi import FastAPI
from app.api.v1.routes import router as v1_router

app = FastAPI(
    title="Saraburi Agent API",
    description="API สำหรับ Saraburi Agent",
    version="1.0"
)

app.include_router(v1_router, prefix="/api/v1")
