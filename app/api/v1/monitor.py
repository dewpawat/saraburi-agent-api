from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.v1.deps.header import get_header_security
from app.api.v1.models.security_model import HeaderSecurity
from app.core.database import get_db
from app.core.config import settings
from app.core.security import api_security_header, is_authorized

import socket
import platform
import psutil
from datetime import datetime

router = APIRouter()


def _short_db_error(exc: Exception) -> str:
    """
    Error text for callers that are not authorized: exception type and MySQL error code
    only (e.g. "OperationalError (2013)"), so DB host/user details are not exposed.
    """
    orig = getattr(exc, "orig", None) or exc
    code = orig.args[0] if getattr(orig, "args", None) and isinstance(orig.args[0], int) else None
    return f"{type(orig).__name__} ({code})" if code is not None else type(orig).__name__


async def _check_db(db: AsyncSession, full_error: bool):
    try:
        await db.execute(text("SELECT 1"))
        return True, None
    except Exception as e:
        return False, (str(e) if full_error else _short_db_error(e))


# ---------------------------------------------------------
# 1) ตรวจสอบ API ว่ายังทำงานหรือไม่ (เปิดสาธารณะ)
# ---------------------------------------------------------
@router.get("/status", summary="Check API status")
async def status():
    return {
        "status": "running",
        "version": settings.APP_VERSION,
    }


# ---------------------------------------------------------
# 2) ตรวจสอบการเชื่อมต่อฐานข้อมูล (เปิดสาธารณะ)
#    ส่ง x-api-key + x-hospcode จาก IP ที่อนุญาต -> ได้ข้อความ error เต็ม
#    ไม่ส่ง / ไม่ผ่าน -> ได้แค่ชนิด error + รหัส เช่น "OperationalError (2013)"
# ---------------------------------------------------------
@router.get("/database", summary="Check MySQL connection")
async def database_status(request: Request, db: AsyncSession = Depends(get_db)):
    db_ok, db_error = await _check_db(db, full_error=is_authorized(request))
    return {
        "database": db_ok,
        "error": db_error,
        "version": settings.APP_VERSION,
    }


# ---------------------------------------------------------
# 3) ข้อมูลระบบ (ต้องยืนยันตัวตน)
# ---------------------------------------------------------
@router.post("/system-info", summary="Get system information")
async def system_info(
    request: Request,
    headers: HeaderSecurity = Depends(get_header_security),
):
    await api_security_header(request)
    return {
        "hostname": socket.gethostname(),
        "os": platform.platform(),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python": platform.python_version(),
        "version": settings.APP_VERSION,
    }


# ---------------------------------------------------------
# 4) Performance (เบามาก ไม่กินเครื่อง รพ.) (ต้องยืนยันตัวตน)
# ---------------------------------------------------------
@router.post("/performance", summary="Get basic performance usage")
async def performance(
    request: Request,
    headers: HeaderSecurity = Depends(get_header_security),
):
    await api_security_header(request)
    return {
        "cpu": psutil.cpu_percent(interval=0.1),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
    }


# ---------------------------------------------------------
# 5) Full-check: รวมทั้งหมดใน endpoint เดียว (ต้องยืนยันตัวตน)
# ---------------------------------------------------------
@router.post("/full-check", summary="Check API + DB + system performance")
async def full_check(
    request: Request,
    headers: HeaderSecurity = Depends(get_header_security),
    db: AsyncSession = Depends(get_db),
):
    await api_security_header(request)
    db_ok, db_error = await _check_db(db, full_error=True)

    return {
        "system": "running",
        "version": settings.APP_VERSION,
        "database": db_ok,
        "database_error": db_error,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "performance": {
            "cpu": psutil.cpu_percent(interval=0.1),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage("/").percent,
        }
    }
