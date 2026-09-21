from typing import Optional
from fastapi import Header
from app.api.v1.models.security_model import HeaderSecurity

async def get_header_security(
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    x_hospcode: Optional[str] = Header(None, alias="x-hospcode")
) -> HeaderSecurity:
    return HeaderSecurity(
        x_api_key=x_api_key,
        x_hospcode=x_hospcode
    )
