from pydantic import BaseModel, Field
from typing import Optional, Any, List


class HIEBaseRequest(BaseModel):
    hospcode: str = Field(..., example="10815", description="รหัสสถานพยาบาล 5 หลัก")
    cid: str = Field(..., example="1103700999999", description="เลขประจำตัวประชาชน 13 หลัก")

class HIEPatientRequest(HIEBaseRequest):
    pass

class HIEServiceRequest(HIEBaseRequest):
    hn: str = Field(..., example="000123456", description="HN")
    vstdate: str = Field(..., example="2025-01-15", description="วันที่รับบริการ (YYYY-MM-DD)")

class HIEVisitRequest(HIEBaseRequest):
    hn: str = Field(..., example="000123456", description="HN")
    vn: str = Field(..., example="650101123456", description="VN")
    vstdate: str = Field(..., example="2025-01-15", description="วันที่รับบริการ (YYYY-MM-DD)")

class HIEAdmitRequest(HIEBaseRequest):
    hn: str = Field(..., example="000123456", description="HN")
    vn: str = Field(..., example="650101123456", description="VN ที่เข้ารักษา")
    an: str = Field(..., example="0000123456", description="AN")
    vstdate: str = Field(..., example="2025-01-15", description="วันที่เริ่ม admit (YYYY-MM-DD)")

class HIEDiagnosisItem(BaseModel):
    code3: Optional[str] = None
    tname: Optional[str] = None
    iname: Optional[str] = None

class HIEDrugItem(BaseModel):
    name: Optional[str] = None
    strength: Optional[str] = None
    shortlist: Optional[str] = None
    qty: Optional[float] = None
    sum_price: Optional[float] = None

class HIELabItem(BaseModel):
    lab_items_code: Optional[str] = None
    lab_items_name: Optional[str] = None
    lab_order_result: Optional[str] = None
    lab_items_normal_value: Optional[str] = None

class HIEAllergyItem(BaseModel):
    report_date: Optional[str] = None
    agent: Optional[str] = None
    symptom: Optional[str] = None
    department: Optional[str] = None

class HIEProcedureErItem(BaseModel):
    er_oper_code: Optional[str] = None
    er_oper_name: Optional[str] = None
    oper_qty: Optional[float] = None
    oper_cost: Optional[float] = None

class HIEProcedureOpdItem(BaseModel):
    opd_oper_code: Optional[str] = None
    opd_oper_name: Optional[str] = None
    price: Optional[float] = None

class HIEAnItem(BaseModel):
    an: Optional[str] = None
    regdate: Optional[str] = None
    dchtime: Optional[str] = None
    wname: Optional[str] = None
    admday: Optional[str] = None
    dname1: Optional[str] = None
    pname: Optional[str] = None
    ipname: Optional[str] = None
    prediag: Optional[str] = None
    dchdate: Optional[str] = None
    dchtime: Optional[str] = None
    dname2: Optional[str] = None
    dcname: Optional[str] = None
    dsname: Optional[str] = None
    
class HIEProcedureOpdItem(BaseModel):
    ref_date: Optional[str] = None
    oper_name: Optional[str] = None
    oper_qty: Optional[float] = None
    total_price: Optional[float] = None

class HIEPatientItem(BaseModel):
    cid: str = Field(..., example="1103700999999", description="เลขบัตรประชาชน (Citizen ID)")
    pname: Optional[str] = Field(None, example="น.ส.", description="คำนำหน้าชื่อ")
    fname: Optional[str] = None
    lname: Optional[str] = None
    hn: Optional[str] = None
    tel: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[str] = None
    address: Optional[str] = None
    moo: Optional[str] = None
    tambon: Optional[str] = None
    ampur: Optional[str] = None
    changwat: Optional[str] = None
    
class HIEServiceItem(BaseModel):
    cid: str
    hn: Optional[str] = None
    vn: Optional[str] = None
    an: Optional[str] = None
    vstdate: Optional[str] = None
    vsttime: Optional[str] = None
    code3: Optional[str] = None
    tname: Optional[str] = None
    iname: Optional[str] = None
    cname: Optional[str] = None
    dname: Optional[str] = None

class HIEVisitItem(BaseModel):
    cid: Optional[str] = None
    hn: Optional[str] = None
    vn: Optional[str] = None
    an: Optional[str] = None
    vstdate: Optional[str] = None
    vsttime: Optional[str] = None
    code3: Optional[str] = None
    tname: Optional[str] = None
    iname: Optional[str] = None
    cname: Optional[str] = None
    dname: Optional[str] = None
    pttypeno: Optional[str] = None
    birthday: Optional[str] = None
    so: Optional[str] = None
    pnname: Optional[str] = None
    novstist: Optional[str] = None
    novstost: Optional[str] = None
    bw: Optional[str] = None
    height: Optional[str] = None
    temperature: Optional[str] = None
    bps: Optional[str] = None
    bpd: Optional[str] = None
    rr: Optional[str] = None
    pulse: Optional[str] = None
    bmi: Optional[str] = None
    fbs: Optional[str] = None
    cc: Optional[str] = None
    hpi: Optional[str] = None
    fh: Optional[str] = None
    pmh: Optional[str] = None
    pe: Optional[str] = None
    pe_ga: Optional[str] = None
    pe_ga_text: Optional[str] = None
    pe_heent: Optional[str] = None
    pe_heent_text: Optional[str] = None
    pe_heart: Optional[str] = None
    pe_heart_text: Optional[str] = None
    pe_lung: Optional[str] = None
    pe_lung_text: Optional[str] = None
    pe_ab: Optional[str] = None
    pe_ab_text: Optional[str] = None
    diagnosis: List[HIEDiagnosisItem] = []
    drug: List[HIEDrugItem] = []
    lab: List[HIELabItem] = []
    allergy: List[HIEAllergyItem] = []
    procedure_er: List[HIEProcedureErItem] = []
    procedure_opd: List[HIEProcedureOpdItem] = []

class HIEAdmitItem(BaseModel):
    cid: Optional[str] = None
    hn: Optional[str] = None
    vn: Optional[str] = None
    an: Optional[str] = None
    vstdate: Optional[str] = None
    vsttime: Optional[str] = None
    code3: Optional[str] = None
    tname: Optional[str] = None
    iname: Optional[str] = None
    cname: Optional[str] = None
    dname: Optional[str] = None
    pttypeno: Optional[str] = None
    birthday: Optional[str] = None
    so: Optional[str] = None
    pnname: Optional[str] = None
    novstist: Optional[str] = None
    novstost: Optional[str] = None
    bw: Optional[str] = None
    height: Optional[str] = None
    temperature: Optional[str] = None
    bps: Optional[str] = None
    bpd: Optional[str] = None
    rr: Optional[str] = None
    pulse: Optional[str] = None
    bmi: Optional[str] = None
    fbs: Optional[str] = None
    cc: Optional[str] = None
    hpi: Optional[str] = None
    fh: Optional[str] = None
    pmh: Optional[str] = None
    pe: Optional[str] = None
    pe_ga: Optional[str] = None
    pe_ga_text: Optional[str] = None
    pe_heent: Optional[str] = None
    pe_heent_text: Optional[str] = None
    pe_heart: Optional[str] = None
    pe_heart_text: Optional[str] = None
    pe_lung: Optional[str] = None
    pe_lung_text: Optional[str] = None
    pe_ab: Optional[str] = None
    pe_ab_text: Optional[str] = None
    diagnosis: List[HIEDiagnosisItem] = []
    drug: List[HIEDrugItem] = []
    lab: List[HIELabItem] = []
    allergy: List[HIEAllergyItem] = []
    procedure_er: List[HIEProcedureErItem] = []
    procedure_opd: List[HIEProcedureOpdItem] = []
    list_an: List[HIEAnItem] = []
    procedure_an: List[HIEProcedureOpdItem] = []


class HIEBaseResponse(BaseModel):
    MessageCode: str = Field(..., example="200")
    Message: str = Field(..., example="Success")

class HIEPatientResponse(HIEBaseResponse):
    patient: Optional[HIEPatientItem] = None

class HIEServiceResponse(HIEBaseResponse):
    service: Optional[list[HIEServiceItem]] = None


class HIEVisitResponse(HIEBaseResponse):
    visit: Optional[HIEVisitItem] = None

class HIEAdmitResponse(HIEBaseResponse):
    admit: Optional[HIEAdmitItem] = None

