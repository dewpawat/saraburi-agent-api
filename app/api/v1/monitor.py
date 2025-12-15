from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

import socket
import platform
import psutil
from datetime import datetime

router = APIRouter()

# ---------------------------------------------------------
# 1) ตรวจสอบ API ว่ายังทำงานหรือไม่
# ---------------------------------------------------------
@router.get("/status", summary="Check API status")
async def status():
    return {"status": "running"}


# ---------------------------------------------------------
# 2) ตรวจสอบการเชื่อมต่อฐานข้อมูล
# ---------------------------------------------------------
@router.get("/database", summary="Check MySQL connection")
async def database_status(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"database": True, "error": None}
    except Exception as e:
        return {"database": False, "error": str(e)}


# ---------------------------------------------------------
# 3) ข้อมูลระบบ
# ---------------------------------------------------------
@router.get("/system-info", summary="Get system information")
async def system_info():
    return {
        "hostname": socket.gethostname(),
        "os": platform.platform(),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python": platform.python_version(),
    }


# ---------------------------------------------------------
# 4) Performance (เบามาก ไม่กินเครื่อง รพ.)
# ---------------------------------------------------------
@router.get("/performance", summary="Get basic performance usage")
async def performance():
    return {
        "cpu": psutil.cpu_percent(interval=0.1),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
    }


# ---------------------------------------------------------
# 5) Full-check: รวมทั้งหมดใน endpoint เดียว
# ---------------------------------------------------------
@router.get("/full-check", summary="Check API + DB + system performance")
async def full_check(db: AsyncSession = Depends(get_db)):
    # Database
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
        db_error = None
    except Exception as e:
        db_ok = False
        db_error = str(e)

    return {
        "system": "running",
        "database": db_ok,
        "database_error": db_error,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "performance": {
            "cpu": psutil.cpu_percent(interval=0.1),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage("/").percent,
        }
    }
