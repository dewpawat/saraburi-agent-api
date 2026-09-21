from fastapi import APIRouter, Request, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.api.v1.deps.header import get_header_security
from app.api.v1.models.stroke_model import StrokeIPDRequest, StrokeIPDResponse, StrokeOPDRequest, StrokeOPDResponse
from app.api.v1.models.security_model import HeaderSecurity
from app.core.security import api_security
from app.core.database import get_db
from app.core.config import settings
from app.utils.formatters import safe_str, safe_date_iso, safe_get

router = APIRouter()

@router.post("/StrokeIPD", summary="Stroke IPD", description="ดึงข้อมูลผู้ป่วย Stroke จากข้อมูล IPD", response_model=StrokeIPDResponse, status_code=status.HTTP_200_OK)
async def stroke_ipd(
    body: StrokeIPDRequest,
    request: Request,
    headers: HeaderSecurity = Depends(get_header_security),
    db: AsyncSession = Depends(get_db)
):
    await api_security(request, body.hospcode)

    sql = text("""
        SELECT 
            o.hcode AS hospcode,
            o.vstdate,
            p.cid,
            o.hn,
            o.vn,
            p.pname,
            p.fname,
            p.lname,
            o.an,
            p.sex,
            p.nationality,
            p.birthday,
            id.icd10,
            i.regdate,
            DATE(id.modify_datetime) AS dxdate,
            i.dchdate,
            d.name AS status,
            CONCAT(p.addrpart,' ',p.road) AS address,
            p.moopart AS moo,
            t3.name AS tambon,
            t2.name AS ampur,
            t1.name AS changwat,
            p.tmbpart,
            p.amppart AS ampart,
            p.chwpart,
            p.hometel AS phone,
            p.informtel AS relation_phone,
            p.informname AS relation_name,
            GROUP_CONCAT(di.sticker_short_name SEPARATOR '|') AS drug_name
        FROM ovst o
        INNER JOIN ipt i ON i.an = o.an
        LEFT JOIN opitemrece r ON r.an = o.an
        LEFT JOIN drugitems di ON di.icode = r.icode
        LEFT JOIN iptdiag id ON id.an = i.an
        LEFT JOIN patient p ON p.hn = i.hn
        LEFT JOIN icd10 i1 ON i1.code = id.icd10
        LEFT JOIN dchtype d ON d.dchtype = i.dchtype
        LEFT JOIN thaiaddress t1 
            ON t1.chwpart = p.chwpart 
            AND t1.amppart = '00' 
            AND t1.tmbpart = '00'
        LEFT JOIN thaiaddress t2 
            ON t2.chwpart = p.chwpart 
            AND t2.amppart = p.amppart 
            AND t2.tmbpart = '00'
        LEFT JOIN thaiaddress t3 
            ON t3.chwpart = p.chwpart 
            AND t3.amppart = p.amppart 
            AND t3.tmbpart = p.tmbpart
        WHERE i.dchdate = :dchdate
            AND i.dchdate IS NOT NULL 
            AND i.dchdate != ''
            AND id.icd10 BETWEEN 'I60' AND 'I69'
            AND r.icode LIKE '1%%'
        GROUP BY o.vn
    """)

    rows = await db.execute(sql, {"dchdate": body.dchdate})
    result = rows.mappings().all()

    if not result:
        return {
            "MessageCode": "404",
            "Message": "Not Found Data",
            "result": []
        }

    list_data = []
    for row in result:
        temp = {
            "hospcode": safe_str(safe_get(row, "hospcode")) or settings.HOSP_CODE,
            "cid": safe_str(safe_get(row, "cid")),
            "hn": safe_str(safe_get(row, "hn")),
            "an": safe_str(safe_get(row, "an")),
            "pname": safe_str(safe_get(row, "pname")),
            "fname": safe_str(safe_get(row, "fname")),
            "lname": safe_str(safe_get(row, "lname")),
            "sex": safe_str(safe_get(row, "sex")),
            "nation": safe_str(safe_get(row, "nationality")),
            "birthday": safe_date_iso(safe_get(row, "birthday")),
            "icd10": safe_str(safe_get(row, "icd10")),
            "vstdate": safe_date_iso(safe_get(row, "vstdate")),
            "regdate": safe_date_iso(safe_get(row, "regdate")),
            "dxdate": safe_date_iso(safe_get(row, "dxdate")),
            "dchdate": safe_date_iso(safe_get(row, "dchdate")),
            "status": safe_str(safe_get(row, "status")),
            "address": safe_str(safe_get(row, "address")),
            "moo": safe_str(safe_get(row, "moo")),
            "tambon": safe_str(safe_get(row, "tambon")),
            "ampur": safe_str(safe_get(row, "ampur")),
            "changwat": safe_str(safe_get(row, "changwat")),
            "tmbpart": safe_str(safe_get(row, "tmbpart")),
            "ampart": safe_str(safe_get(row, "ampart")),
            "chwpart": safe_str(safe_get(row, "chwpart")),
            "phone": safe_str(safe_get(row, "phone")),
            "relation_phone": safe_str(safe_get(row, "relation_phone")),
            "relation_name": safe_str(safe_get(row, "relation_name")),
            "drug_name": safe_str(safe_get(row, "drug_name")),
        }
        list_data.append(temp)

    return {
        "MessageCode": "200",
        "Message": "Success",
        "result": list_data
    }


@router.post("/StrokeOPD", summary="Stroke OPD", description="ดึงข้อมูลผู้ป่วย Stroke จากข้อมูล OPD", response_model=StrokeOPDResponse, status_code=status.HTTP_200_OK)
async def stroke_opd(
    body: StrokeOPDRequest,
    request: Request,
    headers: HeaderSecurity = Depends(get_header_security),
    db: AsyncSession = Depends(get_db)
):
    await api_security(request, body.hospcode)

    sql = text("""
        SELECT 
            o.hcode AS hospcode,
            o.vstdate,
            p.cid,
            o.hn,
            o.vn,
            p.pname,
            p.fname,
            p.lname,
            p.sex,
            p.nationality,
            p.birthday,
            id.icd10,
            o.vstdate AS regdate,
            DATE(CONCAT(id.vstdate,' ',id.vsttime)) AS dxdate,
            o.vstdate AS dchdate,
            d.name AS status,
            CONCAT(p.addrpart,' ',p.road) AS address,
            p.moopart AS moo,
            t3.name AS tambon,
            t2.name AS ampur,
            t1.name AS changwat,
            p.tmbpart,
            p.amppart AS ampart,
            p.chwpart,
            p.hometel AS phone,
            p.informtel AS relation_phone,
            p.informname AS relation_name,
            GROUP_CONCAT(di.sticker_short_name SEPARATOR '|') AS drug_name
        FROM ovst o
        LEFT JOIN opitemrece r ON r.vn = o.vn
        LEFT JOIN drugitems di ON di.icode = r.icode
        LEFT JOIN ovstdiag id ON id.vn = o.vn
        LEFT JOIN patient p ON p.hn = o.hn
        LEFT JOIN icd10 i1 ON i1.code = id.icd10
        LEFT JOIN ovstost d ON d.ovstost = o.ovstost
        LEFT JOIN thaiaddress t1 
            ON t1.chwpart = p.chwpart 
            AND t1.amppart = '00' 
            AND t1.tmbpart = '00'
        LEFT JOIN thaiaddress t2 
            ON t2.chwpart = p.chwpart 
            AND t2.amppart = p.amppart 
            AND t2.tmbpart = '00'
        LEFT JOIN thaiaddress t3 
            ON t3.chwpart = p.chwpart 
            AND t3.amppart = p.amppart 
            AND t3.tmbpart = p.tmbpart
        WHERE o.vstdate = :vstdate
            AND id.icd10 BETWEEN 'I60' AND 'I69'
            AND r.icode LIKE '1%'
            AND o.an IS NULL
        GROUP BY o.vn
    """)

    rows = await db.execute(sql, {"vstdate": body.vstdate})
    result = rows.mappings().all()

    if not result:
        return {
            "MessageCode": "404",
            "Message": "Not Found Data",
            "result": []
        }

    list_data = []
    for row in result:
        temp = {
            "hospcode": safe_str(safe_get(row, "hospcode")) or settings.HOSP_CODE,
            "cid": safe_str(safe_get(row, "cid")),
            "hn": safe_str(safe_get(row, "hn")),
            "vn": safe_str(safe_get(row, "vn")),
            "pname": safe_str(safe_get(row, "pname")),
            "fname": safe_str(safe_get(row, "fname")),
            "lname": safe_str(safe_get(row, "lname")),
            "sex": safe_str(safe_get(row, "sex")),
            "nation": safe_str(safe_get(row, "nationality")),
            "birthday": safe_date_iso(safe_get(row, "birthday")),
            "icd10": safe_str(safe_get(row, "icd10")),
            "vstdate": safe_date_iso(safe_get(row, "vstdate")),
            "dxdate": safe_date_iso(safe_get(row, "dxdate")),
            "dchdate": safe_date_iso(safe_get(row, "dchdate")),
            "status": safe_str(safe_get(row, "status")),
            "address": safe_str(safe_get(row, "address")),
            "moo": safe_str(safe_get(row, "moo")),
            "tambon": safe_str(safe_get(row, "tambon")),
            "ampur": safe_str(safe_get(row, "ampur")),
            "changwat": safe_str(safe_get(row, "changwat")),
            "tmbpart": safe_str(safe_get(row, "tmbpart")),
            "ampart": safe_str(safe_get(row, "ampart")),
            "chwpart": safe_str(safe_get(row, "chwpart")),
            "phone": safe_str(safe_get(row, "phone")),
            "relation_phone": safe_str(safe_get(row, "relation_phone")),
            "relation_name": safe_str(safe_get(row, "relation_name")),
            "drug_name": safe_str(safe_get(row, "drug_name")),
        }
        list_data.append(temp)

    return {
        "MessageCode": "200",
        "Message": "Success",
        "result": list_data
    }
