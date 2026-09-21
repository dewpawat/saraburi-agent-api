import logging
from fastapi import APIRouter, Request, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.api.v1.models.hie_model import (
    HIEPatientRequest, HIEServiceRequest, HIEVisitRequest, HIEAdmitRequest,
    HIEPatientResponse, HIEServiceResponse, HIEVisitResponse, HIEAdmitResponse,
)
from app.api.v1.deps.header import get_header_security
from app.api.v1.models.security_model import HeaderSecurity
from app.core.security import api_security
from app.core.database import get_db
from app.utils.formatters import safe_str, safe_date_iso, safe_float, safe_get

logger = logging.getLogger("saraburi_agent.hie")

router = APIRouter()

async def safe_fetch_all(db: AsyncSession, sql, params: dict, context: str = ""):
    """
    Safely executes an optional subquery.
    If a table/column does not exist in a hospital's database, logs a warning and returns []
    instead of failing the entire endpoint request.
    """
    try:
        rows = await db.execute(sql, params)
        return rows.mappings().all()
    except Exception as e:
        logger.warning(f"Optional subquery '{context}' failed (skipped): {e}")
        return []


@router.post(
    "/patient",
    summary="HIE Patient",
    description="ให้บริการข้อมูลประวัติผู้ป่วยขั้นพื้นฐานจากหน่วยบริการ เพื่อการใช้งานร่วมกันระหว่างระบบ",
    response_model=HIEPatientResponse,
    status_code=status.HTTP_200_OK,
)
async def hie_patient(
    body: HIEPatientRequest,
    request: Request,
    headers: HeaderSecurity = Depends(get_header_security),
    db: AsyncSession = Depends(get_db),
):
    await api_security(request, body.hospcode)

    sql = text("""
        SELECT p.cid, p.hn, p.pname, p.fname, p.lname, p.birthday, p.hometel, p.sex, 
        CONCAT(p.addrpart,' ',p.road) AS address, p.moopart AS moo, t3.name AS tambon, t2.name AS ampur, t1.name AS changwat
        FROM patient p 
        LEFT OUTER JOIN thaiaddress t1 ON t1.chwpart=p.chwpart AND t1.amppart='00' AND t1.tmbpart='00'
        LEFT OUTER JOIN thaiaddress t2 ON t2.chwpart=p.chwpart AND t2.amppart=p.amppart AND t2.tmbpart='00'
        LEFT OUTER JOIN thaiaddress t3 ON t3.chwpart=p.chwpart AND t3.amppart=p.amppart AND t3.tmbpart=p.tmbpart
        WHERE p.cid = :cid
    """)

    rows = await db.execute(sql, {"cid": body.cid})
    result = rows.mappings().first()

    if not result:
        return {
            "MessageCode": "404",
            "Message": "Not Found Data",
            "patient": None
        }

    patient = {
        "cid": safe_str(safe_get(result, "cid")),
        "pname": safe_str(safe_get(result, "pname")),
        "fname": safe_str(safe_get(result, "fname")),
        "lname": safe_str(safe_get(result, "lname")),
        "hn": safe_str(safe_get(result, "hn")),
        "tel": safe_str(safe_get(result, "hometel")),
        "gender": safe_str(safe_get(result, "sex")),
        "birthday": safe_date_iso(safe_get(result, "birthday")),
        "address": safe_str(safe_get(result, "address")),
        "moo": safe_str(safe_get(result, "moo")),
        "tambon": safe_str(safe_get(result, "tambon")),
        "ampur": safe_str(safe_get(result, "ampur")),
        "changwat": safe_str(safe_get(result, "changwat")),
    }

    return {
        "MessageCode": "200",
        "Message": "Success",
        "patient": patient
    }


@router.post(
    "/service",
    summary="HIE Service",
    description="ให้บริการข้อมูลการเข้ารับบริการของผู้ป่วยในหน่วยบริการ",
    response_model=HIEServiceResponse,
    status_code=status.HTTP_200_OK,
)
async def hie_service(
    body: HIEServiceRequest,
    request: Request,
    headers: HeaderSecurity = Depends(get_header_security),
    db: AsyncSession = Depends(get_db),
):
    await api_security(request, body.hospcode)

    sql = text("""
        SELECT p.hn, o.vn, o.an, o.vstdate, o.vsttime, i.tname, pt.name, o.pttypeno, i.name AS iname, i.code3, v.paid_money, d.name AS dname 
        FROM patient p 
        LEFT JOIN ovst o  ON p.hn = o.hn
        LEFT JOIN pttype pt ON o.pttype = pt.pttype  
        LEFT JOIN vn_stat v ON o.vn = v.vn 
        LEFT JOIN icd101 i ON v.pdx = i.code 
        LEFT JOIN doctor d ON o.doctor = d.code 
        WHERE p.cid = :cid AND p.hn = :hn AND o.vstdate BETWEEN :start_vstdate AND DATE(NOW()) 
        ORDER BY o.vstdate DESC, o.vsttime DESC
    """)

    rows = await db.execute(sql, {
        "cid": body.cid, 
        "hn": body.hn, 
        "start_vstdate": body.vstdate
    })
    result = rows.mappings().all()

    if not result:
        return {
            "MessageCode": "404",
            "Message": "Not Found Data",
            "service": None
        }
    
    list_data = []
    for row in result:
        temp = {
            "cid": safe_str(body.cid),
            "hn": safe_str(safe_get(row, "hn")),
            "vn": safe_str(safe_get(row, "vn")),
            "an": safe_str(safe_get(row, "an")),
            "vstdate": safe_date_iso(safe_get(row, "vstdate")),
            "vsttime": safe_str(safe_get(row, "vsttime")),
            "code3": safe_str(safe_get(row, "code3")),
            "tname": safe_str(safe_get(row, "tname")),
            "iname": safe_str(safe_get(row, "iname")),
            "cname": safe_str(safe_get(row, "name")),
            "dname": safe_str(safe_get(row, "dname")),
        }
        list_data.append(temp)

    return {
        "MessageCode": "200",
        "Message": "Success",
        "service": list_data
    }


@router.post(
    "/visit",
    summary="HIE Visit",
    description="ให้บริการข้อมูลรายละเอียดการเข้ารับบริการในแต่ละครั้งของผู้ป่วย",
    response_model=HIEVisitResponse,
    status_code=status.HTTP_200_OK,
)
async def hie_visit(
    body: HIEVisitRequest,
    request: Request,
    headers: HeaderSecurity = Depends(get_header_security),
    db: AsyncSession = Depends(get_db),
):
    await api_security(request, body.hospcode)

    sql = text("""
        SELECT p.hn AS hn_0 ,p.cid ,CONCAT(p.pname ,' ', p.fname ,' ', p.lname) AS nm, p.birthday, (YEAR(NOW()) - YEAR(p.birthday)) AS birthday_year, 
            (SELECT hospitalname FROM opdconfig LIMIT 0,1) AS so, 
            o.vn AS vn_0, o.an AS an_0, o.vstdate AS vstdate_0, o.vsttime AS vsttime_0, 
            i.tname, pt.name, o.pttypeno, i.name AS iname, i.code3, v.paid_money, d.name AS dname, 
            pn.name AS pnname ,ost.name AS novstost , ist.name AS novstist, a.nextdate, sc.* 
        FROM patient p 
        LEFT JOIN ovst o ON p.hn = o.hn
        LEFT JOIN opdscreen sc ON sc.vn = o.vn
        LEFT JOIN pttype pt ON o.pttype = pt.pttype  
        LEFT JOIN vn_stat v ON o.vn = v.vn 
        LEFT JOIN icd101 i ON v.pdx = i.code 
        LEFT JOIN doctor d ON o.doctor = d.code 
        LEFT JOIN spclty pn ON v.spclty = pn.spclty 
        LEFT JOIN ovstist ist ON o.ovstist = ist.ovstist 
        LEFT JOIN ovstost ost ON o.ovstost = ost.ovstost
        LEFT OUTER JOIN oapp a on a.vn = o.vn
        WHERE o.vn = :vn AND p.hn = :hn;
    """)

    rows = await db.execute(sql, {"vn": body.vn, "hn": body.hn})
    result = rows.mappings().first()

    if not result:
        return {
            "MessageCode": "404",
            "Message": "Not Found Data",
            "visit": None
        }
    
    # 1) Diagnosis
    sql_diag = text("""
        SELECT 
            i.code3, i.tname, i.name AS iname
        FROM ovst o
            INNER JOIN ovstdiag ov ON o.vn = ov.vn
            INNER JOIN icd101 i ON ov.icd10 = i.code
        WHERE o.vn = :vn AND ov.diagtype <> '1'
    """)
    result_diag = await safe_fetch_all(db, sql_diag, {"vn": body.vn}, "visit_diagnosis")
    list_diag = []
    for row_diag in result_diag:
        list_diag.append({
            "code3": safe_str(safe_get(row_diag, "code3")),
            "tname": safe_str(safe_get(row_diag, "tname")),
            "iname": safe_str(safe_get(row_diag, "iname")),
        })

    # 2) Drugs (supports s_drugitems or drugitems)
    sql_drug = text("""
        SELECT b.name, b.strength, a.qty, a.sum_price, d.shortlist 
        FROM opitemrece a 
        INNER JOIN s_drugitems b ON a.icode = b.icode 
        LEFT OUTER JOIN drugusage d ON d.drugusage = a.drugusage 
        WHERE a.vn = :vn;
    """)
    result_drug = await safe_fetch_all(db, sql_drug, {"vn": body.vn}, "visit_drugs_s_drugitems")
    if not result_drug:
        # Fallback to standard drugitems table if s_drugitems view doesn't exist
        sql_drug_alt = text("""
            SELECT b.name, b.strength, a.qty, a.sum_price, d.shortlist 
            FROM opitemrece a 
            INNER JOIN drugitems b ON a.icode = b.icode 
            LEFT OUTER JOIN drugusage d ON d.drugusage = a.drugusage 
            WHERE a.vn = :vn;
        """)
        result_drug = await safe_fetch_all(db, sql_drug_alt, {"vn": body.vn}, "visit_drugs_drugitems")

    list_drug = []
    for row_drug in result_drug:
        list_drug.append({
            "name": safe_str(safe_get(row_drug, "name")),
            "strength": safe_str(safe_get(row_drug, "strength")),
            "shortlist": safe_str(safe_get(row_drug, "shortlist")),
            "qty": safe_float(safe_get(row_drug, "qty")),
            "sum_price": safe_float(safe_get(row_drug, "sum_price")),
        })

    # 3) Lab
    sql_lab = text("""
        SELECT l.lab_items_code, i.lab_items_name, i.lab_items_normal_value,
        if(i.lab_items_name NOT LIKE '%hiv%' AND i.lab_items_name NOT LIKE '%interpretation%',l.lab_order_result,'ปกปิด') AS lab_order_result 
        FROM lab_head h 
        INNER JOIN lab_order l ON h.lab_order_number = l.lab_order_number
        INNER JOIN lab_items i ON i.lab_items_code = l.lab_items_code 
        WHERE h.vn = :vn
        ORDER BY h.order_date DESC;
    """)
    result_lab = await safe_fetch_all(db, sql_lab, {"vn": body.vn}, "visit_lab")
    list_lab = []
    for row_lab in result_lab:
        list_lab.append({
            "lab_items_code": safe_str(safe_get(row_lab, "lab_items_code")),
            "lab_items_name": safe_str(safe_get(row_lab, "lab_items_name")),
            "lab_order_result": safe_str(safe_get(row_lab, "lab_order_result")),
            "lab_items_normal_value": safe_str(safe_get(row_lab, "lab_items_normal_value")),
        })

    # 4) Allergy
    sql_allergy = text("""
        SELECT oa.agent, oa.symptom, oa.report_date, oa.department
        FROM opd_allergy oa
        WHERE oa.hn = :hn
    """)
    result_allergy = await safe_fetch_all(db, sql_allergy, {"hn": body.hn}, "visit_allergy")
    list_allergy = []
    for row_allergy in result_allergy:
        list_allergy.append({
            "report_date": safe_date_iso(safe_get(row_allergy, "report_date")),
            "agent": safe_str(safe_get(row_allergy, "agent")),
            "symptom": safe_str(safe_get(row_allergy, "symptom")),
            "department": safe_str(safe_get(row_allergy, "department")),
        })

    # 5) ER Procedure
    sql_er_oper = text("""
        SELECT ero.*, eoc.name AS er_oper_name, d.name AS doctor_name
        FROM er_regist_oper ero
        LEFT OUTER JOIN er_oper_code eoc ON eoc.er_oper_code = ero.er_oper_code
        LEFT OUTER JOIN doctor d ON d.code = ero.doctor
        WHERE ero.vn = :vn
        ORDER BY ero.rec_no ASC
    """)
    result_er_oper = await safe_fetch_all(db, sql_er_oper, {"vn": body.vn}, "visit_er_procedure")
    list_er_oper = []
    for row_er_oper in result_er_oper:
        list_er_oper.append({
            "er_oper_code": safe_str(safe_get(row_er_oper, "er_oper_code")),
            "er_oper_name": safe_str(safe_get(row_er_oper, "er_oper_name")),
            "oper_qty": safe_float(safe_get(row_er_oper, "oper_qty")),
            "oper_cost": safe_float(safe_get(row_er_oper, "oper_cost")),
        })

    # 6) OPD Procedure
    sql_opd_oper = text("""
        SELECT dot.*, eoc.name AS opd_oper_name, d.name AS doctor_name
        FROM doctor_operation dot
        LEFT OUTER JOIN er_oper_code eoc ON eoc.er_oper_code=dot.er_oper_code
        LEFT OUTER JOIN doctor d ON d.code = dot.doctor
        WHERE dot.vn = :vn;
    """)
    result_opd_oper = await safe_fetch_all(db, sql_opd_oper, {"vn": body.vn}, "visit_opd_procedure")
    list_opd_oper = []
    for row_opd_oper in result_opd_oper:
        list_opd_oper.append({
            "opd_oper_code": safe_str(safe_get(row_opd_oper, "er_oper_code")),
            "opd_oper_name": safe_str(safe_get(row_opd_oper, "opd_oper_name")),
            "price": safe_float(safe_get(row_opd_oper, "price")),
        })

    visit = {
        "cid": safe_str(safe_get(result, "cid")),
        "hn": safe_str(safe_get(result, "hn_0")),
        "vn": safe_str(safe_get(result, "vn_0")),
        "an": safe_str(safe_get(result, "an_0")),
        "vstdate": safe_date_iso(safe_get(result, "vstdate_0")),
        "vsttime": safe_str(safe_get(result, "vsttime_0")),
        "code3": safe_str(safe_get(result, "code3")),
        "tname": safe_str(safe_get(result, "tname")),
        "iname": safe_str(safe_get(result, "iname")),
        "cname": safe_str(safe_get(result, "name")),
        "dname": safe_str(safe_get(result, "dname")),
        "pttypeno": safe_str(safe_get(result, "pttypeno")),
        "birthday": safe_date_iso(safe_get(result, "birthday")),
        "so": safe_str(safe_get(result, "so")),
        "pnname": safe_str(safe_get(result, "pnname")),
        "novstist": safe_str(safe_get(result, "novstist")),
        "novstost": safe_str(safe_get(result, "novstost")),
        "bw": safe_str(safe_get(result, "bw")),
        "height": safe_str(safe_get(result, "height")),
        "temperature": safe_str(safe_get(result, "temperature")),
        "bps": safe_str(safe_get(result, "bps")),
        "bpd": safe_str(safe_get(result, "bpd")),
        "rr": safe_str(safe_get(result, "rr")),
        "pulse": safe_str(safe_get(result, "pulse")),
        "bmi": safe_str(safe_get(result, "bmi")),
        "fbs": safe_str(safe_get(result, "fbs")),
        "cc": safe_str(safe_get(result, "cc")),
        "hpi": safe_str(safe_get(result, "hpi")),
        "fh": safe_str(safe_get(result, "fh")),
        "pmh": safe_str(safe_get(result, "pmh")),
        "pe": safe_str(safe_get(result, "pe")),
        "pe_ga": safe_str(safe_get(result, "pe_ga")),
        "pe_ga_text": safe_str(safe_get(result, "pe_ga_text")),
        "pe_heent": safe_str(safe_get(result, "pe_heent")),
        "pe_heent_text": safe_str(safe_get(result, "pe_heent_text")),
        "pe_heart": safe_str(safe_get(result, "pe_heart")),
        "pe_heart_text": safe_str(safe_get(result, "pe_heart_text")),
        "pe_lung": safe_str(safe_get(result, "pe_lung")),
        "pe_lung_text": safe_str(safe_get(result, "pe_lung_text")),
        "pe_ab": safe_str(safe_get(result, "pe_ab")),
        "pe_ab_text": safe_str(safe_get(result, "pe_ab_text")),
        "diagnosis": list_diag,
        "drug": list_drug,
        "lab": list_lab,
        "allergy": list_allergy,
        "procedure_er": list_er_oper,
        "procedure_opd": list_opd_oper,
    }

    return {
        "MessageCode": "200",
        "Message": "Success",
        "visit": visit
    }


@router.post(
    "/admit",
    summary="HIE Admit",
    description="ให้บริการข้อมูลการรับไว้รักษาในโรงพยาบาล (ผู้ป่วยใน)",
    response_model=HIEAdmitResponse,
    status_code=status.HTTP_200_OK,
)
async def hie_admit(
    body: HIEAdmitRequest,
    request: Request,
    headers: HeaderSecurity = Depends(get_header_security),
    db: AsyncSession = Depends(get_db),
):
    await api_security(request, body.hospcode)

    sql = text("""
        SELECT p.hn AS hn_0 ,p.cid ,CONCAT(p.pname ,' ', p.fname ,' ', p.lname) AS nm, p.birthday, (YEAR(NOW()) - YEAR(p.birthday)) AS birthday_year, 
            (SELECT hospitalname FROM opdconfig LIMIT 0,1) AS so, 
            o.vn AS vn_0, o.an AS an_0, o.vstdate AS vstdate_0, o.vsttime AS vsttime_0, 
            i.tname, pt.name, o.pttypeno, i.name AS iname, i.code3, v.paid_money, d.name AS dname, 
            pn.name AS pnname ,ost.name AS novstost , ist.name AS novstist, a.nextdate, sc.* 
        FROM patient p 
        LEFT JOIN ovst o ON p.hn = o.hn
        LEFT JOIN opdscreen sc ON sc.vn = o.vn
        LEFT JOIN pttype pt ON o.pttype = pt.pttype  
        LEFT JOIN vn_stat v ON o.vn = v.vn 
        LEFT JOIN icd101 i ON v.pdx = i.code 
        LEFT JOIN doctor d ON o.doctor = d.code 
        LEFT JOIN spclty pn ON v.spclty = pn.spclty 
        LEFT JOIN ovstist ist ON o.ovstist = ist.ovstist 
        LEFT JOIN ovstost ost ON o.ovstost = ost.ovstost
        LEFT OUTER JOIN oapp a on a.vn = o.vn
        WHERE o.vn = :vn AND p.hn = :hn;
    """)

    rows = await db.execute(sql, {"vn": body.vn, "hn": body.hn})
    result = rows.mappings().first()

    if not result:
        return {
            "MessageCode": "404",
            "Message": "Not Found Data",
            "admit": None
        }
    
    # 1) Diagnosis
    sql_diag = text("""
        SELECT o.vn ,o.vstdate ,o.vsttime ,i.tname , pt.name ,o.pttypeno , i.name AS iname ,i.code3 , v.paid_money , d.name AS dname 
        FROM ovst o 
        INNER JOIN ovstdiag ov ON o.vn = ov.vn 
        INNER JOIN icd101 i ON ov.icd10 = i.code 
        INNER JOIN pttype pt ON o.pttype = pt.pttype 
        INNER JOIN vn_stat v ON o.vn = v.vn  
        LEFT JOIN doctor d ON o.doctor = d.code 
        WHERE o.vn = :vn AND ov.diagtype <> '1' 
        ORDER BY o.vstdate ,o.vsttime;
    """)
    result_diag = await safe_fetch_all(db, sql_diag, {"vn": body.vn}, "admit_diagnosis")
    list_diag = []
    for row_diag in result_diag:
        list_diag.append({
            "code3": safe_str(safe_get(row_diag, "code3")),
            "tname": safe_str(safe_get(row_diag, "tname")),
            "iname": safe_str(safe_get(row_diag, "iname")),
        })

    # 2) Drugs (supports s_drugitems or drugitems)
    sql_drug = text("""
        SELECT b.name, b.strength, a.qty, a.sum_price, d.shortlist 
        FROM opitemrece a 
        INNER JOIN s_drugitems b ON a.icode = b.icode 
        LEFT OUTER JOIN drugusage d ON d.drugusage = a.drugusage 
        WHERE a.vn = :vn OR a.an = :an;
    """)
    result_drug = await safe_fetch_all(db, sql_drug, {"vn": body.vn, "an": body.an}, "admit_drugs_s_drugitems")
    if not result_drug:
        sql_drug_alt = text("""
            SELECT b.name, b.strength, a.qty, a.sum_price, d.shortlist 
            FROM opitemrece a 
            INNER JOIN drugitems b ON a.icode = b.icode 
            LEFT OUTER JOIN drugusage d ON d.drugusage = a.drugusage 
            WHERE a.vn = :vn OR a.an = :an;
        """)
        result_drug = await safe_fetch_all(db, sql_drug_alt, {"vn": body.vn, "an": body.an}, "admit_drugs_drugitems")

    list_drug = []
    for row_drug in result_drug:
        list_drug.append({
            "name": safe_str(safe_get(row_drug, "name")),
            "strength": safe_str(safe_get(row_drug, "strength")),
            "shortlist": safe_str(safe_get(row_drug, "shortlist")),
            "qty": safe_float(safe_get(row_drug, "qty")),
            "sum_price": safe_float(safe_get(row_drug, "sum_price")),
        })

    # 3) Lab
    sql_lab = text("""
        SELECT l.lab_items_code, i.lab_items_name, i.lab_items_normal_value,
        if(i.lab_items_name NOT LIKE '%hiv%' AND i.lab_items_name NOT LIKE '%interpretation%',l.lab_order_result,'ปกปิด') AS lab_order_result 
        FROM lab_head h 
        INNER JOIN lab_order l ON h.lab_order_number = l.lab_order_number
        INNER JOIN lab_items i ON i.lab_items_code = l.lab_items_code 
        WHERE h.vn = :vn
        ORDER BY h.order_date DESC;
    """)
    result_lab = await safe_fetch_all(db, sql_lab, {"vn": body.vn}, "admit_lab")
    list_lab = []
    for row_lab in result_lab:
        list_lab.append({
            "lab_items_code": safe_str(safe_get(row_lab, "lab_items_code")),
            "lab_items_name": safe_str(safe_get(row_lab, "lab_items_name")),
            "lab_order_result": safe_str(safe_get(row_lab, "lab_order_result")),
            "lab_items_normal_value": safe_str(safe_get(row_lab, "lab_items_normal_value")),
        })

    # 4) Allergy
    sql_allergy = text("""
        SELECT oa.agent, oa.symptom, oa.report_date, oa.department
        FROM opd_allergy oa
        WHERE oa.hn = :hn
    """)
    result_allergy = await safe_fetch_all(db, sql_allergy, {"hn": body.hn}, "admit_allergy")
    list_allergy = []
    for row_allergy in result_allergy:
        list_allergy.append({
            "report_date": safe_date_iso(safe_get(row_allergy, "report_date")),
            "agent": safe_str(safe_get(row_allergy, "agent")),
            "symptom": safe_str(safe_get(row_allergy, "symptom")),
            "department": safe_str(safe_get(row_allergy, "department")),
        })

    # 5) ER Procedure
    sql_er_oper = text("""
        SELECT ero.*, eoc.name AS er_oper_name, d.name AS doctor_name
        FROM er_regist_oper ero
        LEFT OUTER JOIN er_oper_code eoc ON eoc.er_oper_code = ero.er_oper_code
        LEFT OUTER JOIN doctor d ON d.code = ero.doctor
        WHERE ero.vn = :vn
        ORDER BY ero.rec_no ASC
    """)
    result_er_oper = await safe_fetch_all(db, sql_er_oper, {"vn": body.vn}, "admit_er_procedure")
    list_er_oper = []
    for row_er_oper in result_er_oper:
        list_er_oper.append({
            "er_oper_code": safe_str(safe_get(row_er_oper, "er_oper_code")),
            "er_oper_name": safe_str(safe_get(row_er_oper, "er_oper_name")),
            "oper_qty": safe_float(safe_get(row_er_oper, "oper_qty")),
            "oper_cost": safe_float(safe_get(row_er_oper, "oper_cost")),
        })

    # 6) OPD Procedure
    sql_opd_oper = text("""
        SELECT dot.*, eoc.name AS opd_oper_name, d.name AS doctor_name
        FROM doctor_operation dot
        LEFT OUTER JOIN er_oper_code eoc ON eoc.er_oper_code=dot.er_oper_code
        LEFT OUTER JOIN doctor d ON d.code = dot.doctor
        WHERE dot.vn = :vn;
    """)
    result_opd_oper = await safe_fetch_all(db, sql_opd_oper, {"vn": body.vn}, "admit_opd_procedure")
    list_opd_oper = []
    for row_opd_oper in result_opd_oper:
        list_opd_oper.append({
            "opd_oper_code": safe_str(safe_get(row_opd_oper, "er_oper_code")),
            "opd_oper_name": safe_str(safe_get(row_opd_oper, "opd_oper_name")),
            "price": safe_float(safe_get(row_opd_oper, "price")),
        })

    # 7) AN
    sql_an = text("""
        SELECT *, d1.name AS dname1, d2.name AS dname2, pt.name AS pname, w.name AS wname, ip.name AS ipname, dc.name AS dcname, ds.name AS dsname  
        FROM an_stat a 
        INNER JOIN ipt i ON i.an = a.an
        LEFT JOIN doctor d1 ON i.admdoctor = d1.code 
        LEFT JOIN doctor d2 ON i.dch_doctor = d2.code 
        LEFT JOIN pttype pt ON i.pttype = pt.pttype  
        LEFT JOIN ward w ON i.ward = w.ward  
        LEFT JOIN iptadm it ON a.an = it.an
        LEFT JOIN ipt_spclty ip ON i.ipt_spclty = ip.ipt_spclty
        LEFT JOIN dchtype dc ON i.dchtype = dc.dchtype  
        LEFT JOIN dchstts ds ON i.dchstts = ds.dchstts  
        WHERE a.vn = :vn; 
    """)
    result_an = await safe_fetch_all(db, sql_an, {"vn": body.vn}, "admit_an_stat")
    list_an = []
    for row_an in result_an:
        list_an.append({
            "an": safe_str(safe_get(row_an, "an")),
            "regdate": safe_date_iso(safe_get(row_an, "regdate")),
            "dchtime": safe_str(safe_get(row_an, "dchtime")),
            "wname": safe_str(safe_get(row_an, "wname")),
            "admday": safe_str(safe_get(row_an, "admday")),
            "dname1": safe_str(safe_get(row_an, "dname1")),
            "pname": safe_str(safe_get(row_an, "pname")),
            "ipname": safe_str(safe_get(row_an, "ipname")),
            "prediag": safe_str(safe_get(row_an, "prediag")),
            "dchdate": safe_date_iso(safe_get(row_an, "dchdate")),
            "dname2": safe_str(safe_get(row_an, "dname2")),
            "dcname": safe_str(safe_get(row_an, "dcname")),
            "dsname": safe_str(safe_get(row_an, "dsname")),
        })

    # 8) IPT Procedure
    sql_ipt_oper = text("""
        SELECT ino.*, ioc.name AS oper_name, d.name AS doctor_name
        FROM ipt_nurse_oper ino
        LEFT OUTER JOIN ipt_oper_code ioc ON ioc.ipt_oper_code = ino.ipt_oper_code
        LEFT OUTER JOIN doctor d ON d.code = ino.doctor
        WHERE ino.an = :an
        ORDER BY ino.ref_date ASC;
    """)
    result_ipt_oper = await safe_fetch_all(db, sql_ipt_oper, {"an": body.an}, "admit_ipt_procedure")
    list_ipt_oper = []
    for row_ipt_oper in result_ipt_oper:
        list_ipt_oper.append({
            "ref_date": safe_date_iso(safe_get(row_ipt_oper, "ref_date")),
            "oper_name": safe_str(safe_get(row_ipt_oper, "oper_name")),
            "oper_qty": safe_float(safe_get(row_ipt_oper, "oper_qty")),
            "total_price": safe_float(safe_get(row_ipt_oper, "total_price")),
        })

    admit = {
        "cid": safe_str(safe_get(result, "cid")),
        "hn": safe_str(safe_get(result, "hn_0")),
        "vn": safe_str(safe_get(result, "vn_0")),
        "an": safe_str(safe_get(result, "an_0")),
        "vstdate": safe_date_iso(safe_get(result, "vstdate_0")),
        "vsttime": safe_str(safe_get(result, "vsttime_0")),
        "code3": safe_str(safe_get(result, "code3")),
        "tname": safe_str(safe_get(result, "tname")),
        "iname": safe_str(safe_get(result, "iname")),
        "cname": safe_str(safe_get(result, "name")),
        "dname": safe_str(safe_get(result, "dname")),
        "pttypeno": safe_str(safe_get(result, "pttypeno")),
        "birthday": safe_date_iso(safe_get(result, "birthday")),
        "so": safe_str(safe_get(result, "so")),
        "pnname": safe_str(safe_get(result, "pnname")),
        "novstist": safe_str(safe_get(result, "novstist")),
        "novstost": safe_str(safe_get(result, "novstost")),
        "bw": safe_str(safe_get(result, "bw")),
        "height": safe_str(safe_get(result, "height")),
        "temperature": safe_str(safe_get(result, "temperature")),
        "bps": safe_str(safe_get(result, "bps")),
        "bpd": safe_str(safe_get(result, "bpd")),
        "rr": safe_str(safe_get(result, "rr")),
        "pulse": safe_str(safe_get(result, "pulse")),
        "bmi": safe_str(safe_get(result, "bmi")),
        "fbs": safe_str(safe_get(result, "fbs")),
        "cc": safe_str(safe_get(result, "cc")),
        "hpi": safe_str(safe_get(result, "hpi")),
        "fh": safe_str(safe_get(result, "fh")),
        "pmh": safe_str(safe_get(result, "pmh")),
        "pe": safe_str(safe_get(result, "pe")),
        "pe_ga": safe_str(safe_get(result, "pe_ga")),
        "pe_ga_text": safe_str(safe_get(result, "pe_ga_text")),
        "pe_heent": safe_str(safe_get(result, "pe_heent")),
        "pe_heent_text": safe_str(safe_get(result, "pe_heent_text")),
        "pe_heart": safe_str(safe_get(result, "pe_heart")),
        "pe_heart_text": safe_str(safe_get(result, "pe_heart_text")),
        "pe_lung": safe_str(safe_get(result, "pe_lung")),
        "pe_lung_text": safe_str(safe_get(result, "pe_lung_text")),
        "pe_ab": safe_str(safe_get(result, "pe_ab")),
        "pe_ab_text": safe_str(safe_get(result, "pe_ab_text")),
        "diagnosis": list_diag,
        "drug": list_drug,
        "lab": list_lab,
        "allergy": list_allergy,
        "procedure_er": list_er_oper,
        "procedure_opd": list_opd_oper,
        "list_an": list_an,
        "procedure_an": list_ipt_oper,
    }

    return {
        "MessageCode": "200",
        "Message": "Success",
        "admit": admit
    }