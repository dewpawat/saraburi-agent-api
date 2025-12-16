from fastapi import Request, Header, HTTPException
from app.core.config import settings

def get_client_ip(request: Request) -> str:
    # 1) ใช้ X-Forwarded-For ก่อน (จาก Apache / Proxy)
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # กรณีมีหลาย proxy → เอาตัวแรกสุด (client จริง)
        return xff.split(",")[0].strip()

    # 2) fallback กรณีไม่ผ่าน proxy
    return request.client.host

async def api_security(request: Request, body_hospcode: str):
    x_api_key = request.headers.get("x-api-key")
    hospcode_header = request.headers.get("x-hospcode")

    # 1. ไม่มี API Key
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing X-API-KEY header")

    # 2. ตรวจ API KEY
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    if hospcode_header != body_hospcode:
        raise HTTPException(status_code=400, detail="Hospcode mismatch")

    if settings.HOSP_CODE != body_hospcode:
        raise HTTPException(status_code=400, detail="Hospcode not allowed")

    # 3. ตรวจ IP Address
    # client_ip = request.client.host
    client_ip = get_client_ip(request)
    allowed_ips = {settings.API_ALLOWED_IP1, settings.API_ALLOWED_IP2}

    # ลบ None ออกจาก set
    allowed_ips = {ip for ip in allowed_ips if ip}

    if client_ip not in allowed_ips:
        raise HTTPException(
            status_code=403,
            detail=f"IP {client_ip} is not allowed"
        )

    # ถ้าผ่านทุกอย่าง
    return True
