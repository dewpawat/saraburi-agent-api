# app/api/v1/models/security_model.py
from pydantic import BaseModel, Field

class HeaderSecurity(BaseModel):
    x_api_key: str = Field(..., description="API key", example="my-secret-api-key")
    x_hospcode: str = Field(..., description="Hospcode", example="10815")
