from pydantic import BaseModel, Field
from typing import Optional

class StrokeIPDRequest(BaseModel):
    hospcode: str = Field(..., example="10815", description="รหัสสถานพยาบาล 5 หลัก")
    dchdate: str = Field(..., example="2025-01-15", description="วันที่จำหน่าย (YYYY-MM-DD)")

class StrokeIPDItem(BaseModel):
    hospcode: Optional[str] = Field(None, example="10807")
    cid: Optional[str] = Field(None, example="1103700999999")
    hn: Optional[str] = Field(None, example="000123456")
    an: Optional[str] = Field(None, example="0000123456")
    pname: Optional[str] = Field(None, example="นาง")
    fname: Optional[str] = Field(None, example="จันทร์เจ้า")
    lname: Optional[str] = Field(None, example="ศรีสุข")
    sex: Optional[str] = Field(None, example="2")
    nation: Optional[str] = Field(None, example="99")
    birthday: Optional[str] = Field(None, example="1957-07-01")
    icd10: Optional[str] = Field(None, example="I64")
    vstdate: Optional[str] = Field(None, example="2025-01-10")
    regdate: Optional[str] = Field(None, example="2025-01-10")
    dxdate: Optional[str] = Field(None, example="2025-01-10")
    dchdate: Optional[str] = Field(None, example="2025-01-10")
    status: Optional[str] = Field(None, example="กลับบ้าน")
    address: Optional[str] = Field(None, example="140/1 หมู่บ้านสุขสบาย")
    moo: Optional[str] = Field(None, example="07")
    tambon: Optional[str] = Field(None, example="บ้านป่า")
    ampur: Optional[str] = Field(None, example="แก่งคอย")
    changwat: Optional[str] = Field(None, example="สระบุรี")
    tmbpart: Optional[str] = Field(None, example="08")
    ampart: Optional[str] = Field(None, example="02")
    chwpart: Optional[str] = Field(None, example="19")
    phone: Optional[str] = Field(None, example="0821131209")
    relation_phone: Optional[str] = Field(None, example="0914213481")
    relation_name: Optional[str] = Field(None, example="นายสมหมาย ศรีสุข")
    drug_name: Optional[str] = Field(None, example="CEF-3 1 gm.(B)|Amlodipine 10 mg.(C)|Atorvastatin 40 mg.(X)|Paracetamol 500 mg.(A)")

class StrokeIPDResponse(BaseModel):
    MessageCode: str
    Message: str
    result: list[StrokeIPDItem]

class StrokeOPDRequest(BaseModel):
    hospcode: str = Field(..., example="10815", description="รหัสสถานพยาบาล 5 หลัก")
    vstdate: str = Field(..., example="2025-01-15", description="วันที่เข้ารับบริการ (YYYY-MM-DD)")

class StrokeOPDItem(BaseModel):
    hospcode: Optional[str] = Field(None, example="10807")
    cid: Optional[str] = Field(None, example="1103700999999")
    hn: Optional[str] = Field(None, example="000123456")
    vn: Optional[str] = Field(None, example="650101123456")
    pname: Optional[str] = Field(None, example="นาย")
    fname: Optional[str] = Field(None, example="สมพงษ์")
    lname: Optional[str] = Field(None, example="ศรีสุข")
    sex: Optional[str] = Field(None, example="1")
    nation: Optional[str] = Field(None, example="99")
    birthday: Optional[str] = Field(None, example="1960-08-15")
    icd10: Optional[str] = Field(None, example="I63")
    vstdate: Optional[str] = Field(None, example="2025-01-10")
    dxdate: Optional[str] = Field(None, example="2025-01-10")
    dchdate: Optional[str] = Field(None, example="2025-01-10")
    status: Optional[str] = Field(None, example="ตรวจแล้ว")
    address: Optional[str] = Field(None, example="120/3 หมู่บ้านสุขสันต์")
    moo: Optional[str] = Field(None, example="03")
    tambon: Optional[str] = Field(None, example="หนองแซง")
    ampur: Optional[str] = Field(None, example="หนองแซง")
    changwat: Optional[str] = Field(None, example="สระบุรี")
    tmbpart: Optional[str] = Field(None, example="05")
    ampart: Optional[str] = Field(None, example="02")
    chwpart: Optional[str] = Field(None, example="19")
    phone: Optional[str] = Field(None, example="0812345678")
    relation_phone: Optional[str] = Field(None, example="0898765432")
    relation_name: Optional[str] = Field(None, example="นายมนัส ศรีสุข")
    drug_name: Optional[str] = Field(None, example="CEF-3 1 gm.(B)|Amlodipine 10 mg.(C)|Enalapril 5 mg.(C)|Atorvastatin 40 mg.(X)|NSS 0.9% 100 ml IV|Paracetamol 500 mg.(A)")

class StrokeOPDResponse(BaseModel):
    MessageCode: str
    Message: str
    result: list[StrokeOPDItem]