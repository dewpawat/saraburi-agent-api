from fastapi import APIRouter, Request, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.api.v1.models.hie_model import (
    HIEPatientRequest, HIEServiceRequest, HIEVisitRequest, HIEAdmitRequest,
    HIEPatientResponse, HIEServiceResponse, HIEVisitResponse, HIEAdmitResponse,
    HIEPatientItem, HIEServiceItem, HIEVisitItem, HIEAdmitItem,
)
from app.api.v1.deps.header import get_header_security
from app.api.v1.models.security_model import HeaderSecurity
from app.core.security import api_security
from app.core.database import get_db

router = APIRouter()

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

    patient = {}
    patient["cid"] = result["cid"]
    patient["pname"] = result["pname"]
    patient["fname"] = result["fname"]
    patient["lname"] = result["lname"]
    patient["hn"] = result["hn"]
    patient["tel"] = result["hometel"]
    patient["gender"] = result["sex"]
    patient["birthday"] = result["birthday"].isoformat() if result["birthday"] else None
    patient["address"] = result["address"]
    patient["moo"] = result["moo"]
    patient["tambon"] = result["tambon"]
    patient["ampur"] = result["ampur"]
    patient["changwat"] = result["changwat"]

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
            "cid": str(body.cid),
            "hn": str(row["hn"]),
            "vn": str(row["vn"]),
            "an": row["an"] if row["an"] else None,
            "vstdate": row["vstdate"].isoformat() if row["vstdate"] else None,
            "vsttime": str(row["vsttime"]) if row["vsttime"] else None,
            "code3": row["code3"] if row["code3"] else None,
            "tname": row["tname"] if row["tname"] else None,
            "iname": row["iname"] if row["iname"] else None,
            "cname": row["name"] if row["name"] else None,
            "dname": row["dname"] if row["dname"] else None,
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
    
    sql_diag = text("""
        SELECT 
            i.code3, i.tname, i.name AS iname
        FROM ovst o
            INNER JOIN ovstdiag ov ON o.vn = ov.vn
            INNER JOIN icd101 i ON ov.icd10 = i.code
        WHERE o.vn = :vn AND ov.diagtype <> '1'
    """)
    rows_diag = await db.execute(sql_diag, {"vn": body.vn})
    result_diag = rows_diag.mappings().all()

    list_diag = []
    if result_diag:
        for row_diag in result_diag:
            list_diag.append({
                "code3": str(row_diag["code3"]) if str(row_diag["code3"]) else None,
                "tname": str(row_diag["tname"]) if str(row_diag["tname"]) else None,
                "iname": str(row_diag["iname"]) if str(row_diag["iname"]) else None,
            })
    else:
        list_diag = []


    sql_drug = text("""
        SELECT b.name,b.strength , a.qty,a.sum_price,d.shortlist 
        FROM opitemrece a 
        INNER JOIN s_drugitems b ON a.icode = b.icode 
        LEFT OUTER JOIN drugusage d ON d.drugusage = a.drugusage 
        WHERE a.vn = :vn;
    """)
    rows_drug = await db.execute(sql_drug, {"vn": body.vn})
    result_drug = rows_drug.mappings().all()
    
    list_drug = []
    if result_drug:
        for row_drug in result_drug:
            list_drug.append({
                "name": str(row_drug["name"]) if str(row_drug["name"]) else None,
                "strength": str(row_drug["strength"]) if str(row_drug["strength"]) else None,
                "shortlist": str(row_drug["shortlist"]) if str(row_drug["shortlist"]) else None,
                "qty": row_drug["qty"] if row_drug["qty"] else None,
                "sum_price": row_drug["sum_price"] if row_drug["sum_price"] else None,
            })
    else:
        list_drug = []


    sql_lab = text("""
        SELECT l.lab_items_code, i.lab_items_name, i.lab_items_normal_value,
        if(i.lab_items_name NOT LIKE '%hiv%' AND i.lab_items_name NOT LIKE '%interpretation%',l.lab_order_result,'ปกปิด') AS lab_order_result 
        FROM lab_head h 
        INNER JOIN lab_order l ON h.lab_order_number = l.lab_order_number
        INNER JOIN lab_items i ON i.lab_items_code = l.lab_items_code 
        WHERE h.vn = :vn
        ORDER BY h.order_date DESC;
    """)
    rows_lab = await db.execute(sql_lab, {"vn": body.vn})
    result_lab = rows_lab.mappings().all()
    
    list_lab = []
    if result_lab:
        for row_lab in result_lab:
            list_lab.append({
                "lab_items_code": str(row_lab["lab_items_code"]) if str(row_lab["lab_items_code"]) else None,
                "lab_items_name": str(row_lab["lab_items_name"]) if str(row_lab["lab_items_name"]) else None,
                "lab_order_result": row_lab["lab_order_result"] if row_lab["lab_order_result"] else None,
                "lab_items_normal_value": row_lab["lab_items_normal_value"] if row_lab["lab_items_normal_value"] else None,
            })
    else:
        list_lab = []


    sql_allergy = text("""
        SELECT oa.agent, oa.symptom, oa.report_date, oa.department
        FROM opd_allergy oa
        WHERE oa.hn = :hn
    """)
    rows_allergy = await db.execute(sql_allergy, {"hn": body.hn})
    result_allergy = rows_allergy.mappings().all()
    
    list_allergy = []
    if result_allergy:
        for row_allergy in result_allergy:
            list_allergy.append({
                "report_date": row_allergy["report_date"].isoformat() if row_allergy["report_date"] else None,
                "agent": str(row_allergy["agent"]) if str(row_allergy["agent"]) else None,
                "symptom": str(row_allergy["symptom"]) if str(row_allergy["symptom"]) else None,
                "department": str(row_allergy["department"]) if str(row_allergy["department"]) else None,
            })
    else:
        list_allergy = []

    sql_er_oper = text("""
        SELECT ero.*, eoc.name AS er_oper_name, d.name AS doctor_name
        FROM er_regist_oper ero
        LEFT OUTER JOIN er_oper_code eoc ON eoc.er_oper_code = ero.er_oper_code
        LEFT OUTER JOIN doctor d ON d.code = ero.doctor
        WHERE ero.vn = :vn
        ORDER BY ero.rec_no ASC
    """)
    rows_er_oper = await db.execute(sql_er_oper, {"vn": body.vn})
    result_er_oper = rows_er_oper.mappings().all()
    
    list_er_oper = []
    if result_er_oper:
        for row_er_oper in result_er_oper:
            list_er_oper.append({
                "er_oper_code": str(row_er_oper["er_oper_code"]) if str(row_er_oper["er_oper_code"]) else None,
                "er_oper_name": str(row_er_oper["er_oper_name"]) if str(row_er_oper["er_oper_name"]) else None,
                "oper_qty": row_er_oper["oper_qty"] if row_er_oper["oper_qty"] else None,
                "oper_cost": row_er_oper["oper_cost"] if row_er_oper["oper_cost"] else None,
            })
    else:
        list_er_oper = []

    sql_opd_oper = text("""
        SELECT dot.*, eoc.name AS opd_oper_name, d.name AS doctor_name
        FROM doctor_operation dot
        LEFT OUTER JOIN er_oper_code eoc ON eoc.er_oper_code=dot.er_oper_code
        LEFT OUTER JOIN doctor d ON d.code = dot.doctor
        WHERE dot.vn = :vn;
    """)
    rows_opd_oper = await db.execute(sql_opd_oper, {"vn": body.vn})
    result_opd_oper = rows_opd_oper.mappings().all()
    
    list_opd_oper = []
    if result_opd_oper:
        for row_opd_oper in result_opd_oper:
            list_opd_oper.append({
                "opd_oper_code": str(row_opd_oper["er_oper_code"]) if str(row_opd_oper["er_oper_code"]) else None,
                "opd_oper_name": str(row_opd_oper["opd_oper_name"]) if str(row_opd_oper["opd_oper_name"]) else None,
                "price": row_opd_oper["price"] if row_opd_oper["price"] else None,
            })
    else:
        list_opd_oper = []

    
    visit = {}
    visit["cid"] = str(result["cid"])
    visit["hn"] = str(result["hn_0"])
    visit["vn"] = str(result["vn_0"])
    visit["an"] = result["an_0"] if str(result["an_0"]) else None
    visit["vstdate"] =  result["vstdate_0"].isoformat() if result["vstdate_0"] else None
    visit["vsttime"] =  str(result["vsttime_0"]) if result["vsttime_0"] else None
    visit["code3"] = str(result["code3"])
    visit["tname"] = str(result["tname"])
    visit["iname"] = str(result["iname"])
    visit["cname"] = str(result["name"])
    visit["dname"] = str(result["dname"])
    visit["pttypeno"] = str(result["pttypeno"])
    visit["birthday"] =  result["birthday"].isoformat() if result["birthday"] else None
    visit["so"] = result["so"] if result["so"] else None
    visit["pnname"] = result["pnname"] if result["pnname"] else None
    visit["novstist"] = result["novstist"] if result["novstist"] else None
    visit["novstost"] = result["novstost"] if result["novstost"] else None
    visit["bw"] = result["bw"] if result["bw"] else None
    visit["height"] = result["height"] if result["height"] else None
    visit["temperature"] = result["temperature"] if result["temperature"] else None
    visit["bps"] = result["bps"] if result["bps"] else None
    visit["bpd"] = result["bpd"] if result["bpd"] else None
    visit["rr"] = result["rr"] if result["rr"] else None
    visit["pulse"] = result["pulse"] if result["pulse"] else None
    visit["bmi"] = result["bmi"] if result["bmi"] else None
    visit["fbs"] = result["fbs"] if result["fbs"] else None
    visit["cc"] = result["cc"] if result["cc"] else None
    visit["hpi"] = result["hpi"] if result["hpi"] else None
    visit["fh"] = result["fh"] if result["fh"] else None
    visit["pmh"] = result["pmh"] if result["pmh"] else None
    visit["pe"] = result["pe"] if result["pe"] else None
    visit["pe_ga"] = result["pe_ga"] if result["pe_ga"] else None
    visit["pe_ga_text"] = result["pe_ga_text"] if result["pe_ga_text"] else None
    visit["pe_heent"] = result["pe_heent"] if result["pe_heent"] else None
    visit["pe_heent_text"] = result["pe_heent_text"] if result["pe_heent_text"] else None
    visit["pe_heart"] = result["pe_heart"] if result["pe_heart"] else None
    visit["pe_heart_text"] = result["pe_heart_text"] if result["pe_heart_text"] else None
    visit["pe_lung"] = result["pe_lung"] if result["pe_lung"] else None
    visit["pe_lung_text"] = result["pe_lung_text"] if result["pe_lung_text"] else None
    visit["pe_ab"] = result["pe_ab"] if result["pe_ab"] else None
    visit["pe_ab_text"] = result["pe_ab_text"] if result["pe_ab_text"] else None
    visit["diagnosis"] = list_diag
    visit["drug"] = list_drug
    visit["lab"] = list_lab
    visit["allergy"] = list_allergy
    visit["procedure_er"] = list_er_oper
    visit["procedure_opd"] = list_opd_oper


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
    rows_diag = await db.execute(sql_diag, {"vn": body.vn})
    result_diag = rows_diag.mappings().all()

    list_diag = []
    if result_diag:
        for row_diag in result_diag:
            list_diag.append({
                "code3": str(row_diag["code3"]) if str(row_diag["code3"]) else None,
                "tname": str(row_diag["tname"]) if str(row_diag["tname"]) else None,
                "iname": str(row_diag["iname"]) if str(row_diag["iname"]) else None,
            })
    else:
        list_diag = []


    sql_drug = text("""
        SELECT b.name,b.strength , a.qty,a.sum_price,d.shortlist 
        FROM opitemrece a 
        INNER JOIN s_drugitems b ON a.icode = b.icode 
        LEFT OUTER JOIN drugusage d ON d.drugusage = a.drugusage 
        WHERE a.vn = :vn OR a.an = :an;
    """)
    rows_drug = await db.execute(sql_drug, {"vn": body.vn, "an": body.an})
    result_drug = rows_drug.mappings().all()
    
    list_drug = []
    if result_drug:
        for row_drug in result_drug:
            list_drug.append({
                "name": str(row_drug["name"]) if str(row_drug["name"]) else None,
                "strength": str(row_drug["strength"]) if str(row_drug["strength"]) else None,
                "shortlist": str(row_drug["shortlist"]) if str(row_drug["shortlist"]) else None,
                "qty": row_drug["qty"] if row_drug["qty"] else None,
                "sum_price": row_drug["sum_price"] if row_drug["sum_price"] else None,
            })
    else:
        list_drug = []


    sql_lab = text("""
        SELECT l.lab_items_code,i.lab_items_name,i.lab_items_normal_value,
        if(i.lab_items_name NOT LIKE '%hiv%' AND i.lab_items_name NOT LIKE '%interpretation%',l.lab_order_result,'ปกปิด') AS lab_order_result 
        FROM lab_head h 
        INNER JOIN lab_order l ON h.lab_order_number = l.lab_order_number
        INNER JOIN lab_items i ON i.lab_items_code = l.lab_items_code 
        WHERE h.vn = :vn
        ORDER BY h.order_date DESC;
    """)
    rows_lab = await db.execute(sql_lab, {"vn": body.vn})
    result_lab = rows_lab.mappings().all()
    
    list_lab = []
    if result_lab:
        for row_lab in result_lab:
            list_lab.append({
                "lab_items_code": str(row_lab["lab_items_code"]) if str(row_lab["lab_items_code"]) else None,
                "lab_items_name": str(row_lab["lab_items_name"]) if str(row_lab["lab_items_name"]) else None,
                "lab_order_result": row_lab["lab_order_result"] if row_lab["lab_order_result"] else None,
                "lab_items_normal_value": row_lab["lab_items_normal_value"] if row_lab["lab_items_normal_value"] else None,
            })
    else:
        list_lab = []


    sql_allergy = text("""
        SELECT oa.agent, oa.symptom, oa.report_date, oa.department
        FROM opd_allergy oa
        WHERE oa.hn = :hn
    """)
    rows_allergy = await db.execute(sql_allergy, {"hn": body.hn})
    result_allergy = rows_allergy.mappings().all()
    
    list_allergy = []
    if result_allergy:
        for row_allergy in result_allergy:
            list_allergy.append({
                "report_date": row_allergy["report_date"].isoformat() if row_allergy["report_date"] else None,
                "agent": str(row_allergy["agent"]) if str(row_allergy["agent"]) else None,
                "symptom": str(row_allergy["symptom"]) if str(row_allergy["symptom"]) else None,
                "department": str(row_allergy["department"]) if str(row_allergy["department"]) else None,
            })
    else:
        list_allergy = []

    sql_er_oper = text("""
        SELECT ero.*, eoc.name AS er_oper_name, d.name AS doctor_name
        FROM er_regist_oper ero
        LEFT OUTER JOIN er_oper_code eoc ON eoc.er_oper_code = ero.er_oper_code
        LEFT OUTER JOIN doctor d ON d.code = ero.doctor
        WHERE ero.vn = :vn
        ORDER BY ero.rec_no ASC
    """)
    rows_er_oper = await db.execute(sql_er_oper, {"vn": body.vn})
    result_er_oper = rows_er_oper.mappings().all()
    
    list_er_oper = []
    if result_er_oper:
        for row_er_oper in result_er_oper:
            list_er_oper.append({
                "er_oper_code": str(row_er_oper["er_oper_code"]) if str(row_er_oper["er_oper_code"]) else None,
                "er_oper_name": str(row_er_oper["er_oper_name"]) if str(row_er_oper["er_oper_name"]) else None,
                "oper_qty": row_er_oper["oper_qty"] if row_er_oper["oper_qty"] else None,
                "oper_cost": row_er_oper["oper_cost"] if row_er_oper["oper_cost"] else None,
            })
    else:
        list_er_oper = []

    sql_opd_oper = text("""
        SELECT dot.*, eoc.name AS opd_oper_name, d.name AS doctor_name
        FROM doctor_operation dot
        LEFT OUTER JOIN er_oper_code eoc ON eoc.er_oper_code=dot.er_oper_code
        LEFT OUTER JOIN doctor d ON d.code = dot.doctor
        WHERE dot.vn = :vn;
    """)
    rows_opd_oper = await db.execute(sql_opd_oper, {"vn": body.vn})
    result_opd_oper = rows_opd_oper.mappings().all()
    
    list_opd_oper = []
    if result_opd_oper:
        for row_opd_oper in result_opd_oper:
            list_opd_oper.append({
                "opd_oper_code": str(row_opd_oper["er_oper_code"]) if str(row_opd_oper["er_oper_code"]) else None,
                "opd_oper_name": str(row_opd_oper["opd_oper_name"]) if str(row_opd_oper["opd_oper_name"]) else None,
                "price": row_opd_oper["price"] if row_opd_oper["price"] else None,
            })
    else:
        list_opd_oper = []


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
    rows_an = await db.execute(sql_an, {"vn": body.vn})
    result_an = rows_an.mappings().all()
    
    list_an = []
    if result_an:
        for row_an in result_an:
            list_an.append({
                "an": str(row_an["an"]) if str(row_an["an"]) else None,
                "regdate": row_an["regdate"].isoformat() if row_an["regdate"] else None,
                "dchtime": str(row_an["dchtime"]) if str(row_an["dchtime"]) else None,
                "wname": str(row_an["wname"]) if str(row_an["wname"]) else None,
                "admday": str(row_an["admday"]) if str(row_an["admday"]) else None,
                "dname1": str(row_an["dname1"]) if str(row_an["dname1"]) else None,
                "pname": str(row_an["pname"]) if str(row_an["pname"]) else None,
                "ipname": str(row_an["ipname"]) if str(row_an["ipname"]) else None,
                "prediag": str(row_an["prediag"]) if str(row_an["prediag"]) else None,
                "dchdate": row_an["dchdate"].isoformat() if row_an["dchdate"] else None,
                "dchtime": str(row_an["dchtime"]) if str(row_an["dchtime"]) else None,
                "dname2": str(row_an["dname2"]) if str(row_an["dname2"]) else None,
                "dcname": str(row_an["dcname"]) if str(row_an["dcname"]) else None,
                "dsname": str(row_an["dsname"]) if str(row_an["dsname"]) else None,
            })
    else:
        list_an = []


    sql_ipt_oper = text("""
        SELECT ino.*, ioc.name AS oper_name, d.name AS doctor_name
        FROM ipt_nurse_oper ino
        LEFT OUTER JOIN ipt_oper_code ioc ON ioc.ipt_oper_code = ino.ipt_oper_code
        LEFT OUTER JOIN doctor d ON d.code = ino.doctor
        WHERE ino.an = :an
        ORDER BY ino.ref_date ASC;
    """)
    rows_ipt_oper = await db.execute(sql_ipt_oper, {"an": body.an})
    result_ipt_oper = rows_ipt_oper.mappings().all()
    
    list_ipt_oper = []
    if result_ipt_oper:
        for row_ipt_oper in result_ipt_oper:
            list_ipt_oper.append({
                "ref_date": str(row_ipt_oper["ref_date"]) if str(row_ipt_oper["ref_date"]) else None,
                "oper_name": str(row_ipt_oper["oper_name"]) if str(row_ipt_oper["oper_name"]) else None,
                "oper_qty": row_ipt_oper["oper_qty"] if row_ipt_oper["oper_qty"] else None,
                "total_price": row_ipt_oper["total_price"] if row_ipt_oper["total_price"] else None,
            })
    else:
        list_ipt_oper = []

    
    admit = {}
    admit["cid"] = str(result["cid"])
    admit["hn"] = str(result["hn_0"])
    admit["vn"] = str(result["vn_0"])
    admit["an"] = result["an_0"] if str(result["an_0"]) else None
    admit["vstdate"] =  result["vstdate_0"].isoformat() if result["vstdate_0"] else None
    admit["vsttime"] =  str(result["vsttime_0"]) if result["vsttime_0"] else None
    admit["code3"] = str(result["code3"])
    admit["tname"] = str(result["tname"])
    admit["iname"] = str(result["iname"])
    admit["cname"] = str(result["name"])
    admit["dname"] = str(result["dname"])
    admit["pttypeno"] = str(result["pttypeno"])
    admit["birthday"] =  result["birthday"].isoformat() if result["birthday"] else None
    admit["so"] = result["so"] if result["so"] else None
    admit["pnname"] = result["pnname"] if result["pnname"] else None
    admit["novstist"] = result["novstist"] if result["novstist"] else None
    admit["novstost"] = result["novstost"] if result["novstost"] else None
    admit["bw"] = result["bw"] if result["bw"] else None
    admit["height"] = result["height"] if result["height"] else None
    admit["temperature"] = result["temperature"] if result["temperature"] else None
    admit["bps"] = result["bps"] if result["bps"] else None
    admit["bpd"] = result["bpd"] if result["bpd"] else None
    admit["rr"] = result["rr"] if result["rr"] else None
    admit["pulse"] = result["pulse"] if result["pulse"] else None
    admit["bmi"] = result["bmi"] if result["bmi"] else None
    admit["fbs"] = result["fbs"] if result["fbs"] else None
    admit["cc"] = result["cc"] if result["cc"] else None
    admit["hpi"] = result["hpi"] if result["hpi"] else None
    admit["fh"] = result["fh"] if result["fh"] else None
    admit["pmh"] = result["pmh"] if result["pmh"] else None
    admit["pe"] = result["pe"] if result["pe"] else None
    admit["pe_ga"] = result["pe_ga"] if result["pe_ga"] else None
    admit["pe_ga_text"] = result["pe_ga_text"] if result["pe_ga_text"] else None
    admit["pe_heent"] = result["pe_heent"] if result["pe_heent"] else None
    admit["pe_heent_text"] = result["pe_heent_text"] if result["pe_heent_text"] else None
    admit["pe_heart"] = result["pe_heart"] if result["pe_heart"] else None
    admit["pe_heart_text"] = result["pe_heart_text"] if result["pe_heart_text"] else None
    admit["pe_lung"] = result["pe_lung"] if result["pe_lung"] else None
    admit["pe_lung_text"] = result["pe_lung_text"] if result["pe_lung_text"] else None
    admit["pe_ab"] = result["pe_ab"] if result["pe_ab"] else None
    admit["pe_ab_text"] = result["pe_ab_text"] if result["pe_ab_text"] else None
    admit["diagnosis"] = list_diag
    admit["drug"] = list_drug
    admit["lab"] = list_lab
    admit["allergy"] = list_allergy
    admit["procedure_er"] = list_er_oper
    admit["procedure_opd"] = list_opd_oper
    admit["list_an"] = list_an
    admit["procedure_an"] = list_ipt_oper

    return {
        "MessageCode": "200",
        "Message": "Success",
        "admit": admit
    }