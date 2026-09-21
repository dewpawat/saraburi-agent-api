from typing import Optional
from pydantic import BaseModel, Field

class HeaderSecurity(BaseModel):
    x_api_key: Optional[str] = Field(None, description="API key", example="my-secret-api-key")
    x_hospcode: Optional[str] = Field(None, description="Hospcode", example="10815")
