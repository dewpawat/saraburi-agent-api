from pydantic import BaseModel, Field
from typing import Optional, Any, List


class RTIBaseRequest(BaseModel):
    hospcode: str = Field(..., example="10815", description="รหัสสถานพยาบาล 5 หลัก")

class RTIAccidentRequest(RTIBaseRequest):
    vstdate: str = Field(..., example="2025-01-15", description="วันที่รับบริการ (YYYY-MM-DD)")
    pass

class RTIAccidentPlaceRequest(RTIBaseRequest):
    pass


class RTIAccidentItem(BaseModel):
    HOSPCODE: str = Field(..., example="10815")
    PID: str = Field(..., example="1234567890123")
    SEQ: str = Field(..., example="1")
    DATETIME_SERV: str = Field(..., example="2025-01-15 08:30:00")
    DATETIME_AE: Optional[str] = Field(None, example="2025-01-15 09:00:00")
    AETYPE: Optional[str] = Field(None, example="1")
    AEPLACE: Optional[str] = Field(None, example="2")
    TYPEIN_AE: Optional[str] = Field(None, example="1")
    TRAFFIC: Optional[str] = Field(None, example="1")
    VEHICLE: Optional[str] = Field(None, example="2")
    ALCOHOL: Optional[str] = Field(None, example="0")
    NACROTIC_DRUG: Optional[str] = Field(None, example="0")
    BELT: Optional[str] = Field(None, example="1")
    HELMET: Optional[str] = Field(None, example="1")
    AIRWAY: Optional[str] = Field(None, example="1")
    STOPBLEED: Optional[str] = Field(None, example="0")
    SPLINT: Optional[str] = Field(None, example="0")
    FLUID: Optional[str] = Field(None, example="1")
    URGENCY: Optional[str] = Field(None, example="2")
    COMA_EYE: Optional[str] = Field(None, example="4")
    COMA_SPEAK: Optional[str] = Field(None, example="5")
    COMA_MOVEMENT: Optional[str] = Field(None, example="6")
    D_UPDATE: Optional[str] = Field(None, example="2025-01-15 10:00:00")
    CID: Optional[str] = Field(None, example="1234567890123")
    HOSPCODE9: Optional[str] = Field(None, example="EA0010815")
    accident_stdcode: Optional[str] = Field(None, example="A01")
    pt_name: Optional[str] = Field(None, example="สมชาย ใจดี")
    hn: Optional[str] = Field(None, example="00012345")
    an: Optional[str] = Field(None, example="00054321")
    referhos: Optional[str] = Field(None, example="10810")
    dead_in: Optional[str] = Field(None, example="0")
    dead_before: Optional[str] = Field(None, example="0")
    place_other: Optional[str] = Field(None, example="ตลาดสด")
    accident_place_id: Optional[str] = Field(None, example="3")


class RTIAccidentPlaceItem(BaseModel):
    accident_stdcode: str = Field(None, example="C027")
    accident_place_type_name: str = Field(None, example="ทางแยก")
    latitude: str = Field(None, example="14.123456")
    longitude: str = Field(None, example="100.123456")
    tamboncode: str = Field(None, example="100101")
    ampurcode: str = Field(None, example="1001")
    road: str = Field(None, example="ถนนสุขุมวิท")
    export_code: str = Field(None, example="07")
    accident_id: str = Field(None, example="1")


class RTIBaseResponse(BaseModel):
    MessageCode: str = Field(..., example="200")
    Message: str = Field(..., example="Success")

    
class RTIAccidentResponse(RTIBaseResponse):
    result: list[RTIAccidentItem] = None

class RTIAccidentPlaceResponse(RTIBaseResponse):
    result: list[RTIAccidentPlaceItem] = None