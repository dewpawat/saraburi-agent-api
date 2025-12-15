# app/api/v1/deps/header.py

from fastapi import Header
from app.api.v1.models.security_model import HeaderSecurity

async def get_header_security(
    x_api_key: str = Header(..., alias="x-api-key"),
    x_hospcode: str = Header(..., alias="x-hospcode")
) -> HeaderSecurity:
    return HeaderSecurity(
        x_api_key=x_api_key,
        x_hospcode=x_hospcode
    )
