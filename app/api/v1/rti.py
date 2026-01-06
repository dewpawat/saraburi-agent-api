from fastapi import APIRouter, Request, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings

from app.api.v1.models.rti_model import (
    RTIAccidentRequest, RTIAccidentPlaceRequest,
    RTIAccidentResponse, RTIAccidentPlaceResponse,
)
from app.api.v1.deps.header import get_header_security
from app.api.v1.models.security_model import HeaderSecurity
from app.core.security import api_security
from app.core.database import get_db

router = APIRouter()

@router.post(
    "/accident",
    summary="RTI Accident",
    description="ข้อมูลการเกิดอุบัติเหตุ",
    response_model=RTIAccidentResponse,
    status_code=status.HTTP_200_OK,
)
async def rti_accident(
    body: RTIAccidentRequest,
    request: Request,
    headers: HeaderSecurity = Depends(get_header_security),
    db: AsyncSession = Depends(get_db),
):
    await api_security(request, body.hospcode)

    hospcode = settings.HOSP_CODE
    hospcode9 = settings.HOSP_CODE9
    vstdate = body.vstdate

    # 1) SET ตัวแปร – แยก execute
    await db.execute(text("SET @hospcode := :h"), {"h": hospcode})
    await db.execute(text("SET @hospcode9 := :h9"), {"h9": hospcode9})

    # 2) SELECT ข้อมูล
    sql = text("""
        SELECT
            @hospcode AS HOSPCODE,
            IF(ps.person_id IS NULL, o.hn, LPAD(ps.person_id, 6, '0')) AS PID,
            o.vn AS SEQ,
            DATE_FORMAT(CONCAT(o.vstdate, ' ', o.vsttime), '%Y%m%d%H%i%S') AS DATETIME_SERV,
            DATE_FORMAT(CONCAT(o.vstdate, ' ', o.vsttime), '%Y%m%d%H%i%S') AS DATETIME_AE,
            LPAD(ed.er_accident_type_id, 2, '0') AS AETYPE,
            h.export_code AS AEPLACE,
            ed.er_refer_sender_id AS TYPEIN_AE,
            ed.accident_person_type_id AS TRAFFIC,
            IF(tt.export_code IS NOT NULL, tt.export_code, '99') AS VEHICLE,
            ed.accident_alcohol_type_id AS ALCOHOL,
            ed.accident_drug_type_id AS NACROTIC_DRUG,
            ed.accident_belt_type_id AS BELT,
            ed.accident_helmet_type_id AS HELMET,
            ed.accident_airway_type_id AS AIRWAY,
            ed.accident_bleed_type_id AS STOPBLEED,
            ed.accident_splint_type_id AS SPLINT,
            ed.accident_fluid_type_id AS FLUID,
            IF(ed.er_emergency_type = 1, 2, IF(ed.er_emergency_type = 2, 3, 6)) AS URGENCY,
            ed.gcs_e AS COMA_EYE,
            ed.gcs_v AS COMA_SPEAK,
            ed.gcs_m AS COMA_MOVEMENT,
            DATE_FORMAT(CONCAT(o.vstdate, ' ', o.vsttime), '%Y%m%d%H%i%S') AS D_UPDATE,
            IF(v.cid IS NOT NULL, v.cid, p.cid) AS CID,
            @hospcode9 AS HOSPCODE9,
            h.stdcode_ok AS accident_stdcode,
            CONCAT(p.pname, p.fname, ' ', p.lname) AS pt_name,
            o.hn,
            IF(o.an IS NOT NULL, o.an, ed.accident_admit) AS an,
            o.rfrolct AS referhos,
            ed.accident_dead_in_hospital AS dead_in,
            ed.accident_dead_before_arrive AS dead_before,
            ed.support_information AS place_other,
            ed.accident_place_type_id AS accident_place_id

        FROM er_nursing_detail ed
        INNER JOIN accident_place_type h ON h.accident_place_type_id = ed.accident_place_type_id
        INNER JOIN ovst o ON o.vn = ed.vn
        LEFT JOIN vn_stat v ON v.vn = o.vn
        LEFT JOIN patient p ON p.hn = o.hn
        LEFT JOIN accident_transport_type tt ON tt.accident_transport_type_id = ed.accident_transport_type_id
        LEFT OUTER JOIN person ps ON o.hn = ps.patient_hn
        WHERE o.vstdate = :vstdate
        ORDER BY o.vstdate DESC;
    """)

    rows = await db.execute(sql, {"vstdate": vstdate})
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
            "HOSPCODE": str(row["HOSPCODE"]),
            "PID": str(row["PID"]),
            "SEQ": str(row["SEQ"]),
            "DATETIME_SERV": str(row["DATETIME_SERV"]),
            "DATETIME_AE": str(row["DATETIME_AE"]) if row["DATETIME_AE"] else None,
            "AETYPE": str(row["AETYPE"]) if row["AETYPE"] else None,
            "AEPLACE": str(row["AEPLACE"]) if row["AEPLACE"] else None,
            "TYPEIN_AE": str(row["TYPEIN_AE"]) if row["TYPEIN_AE"] else None,
            "TRAFFIC": str(row["TRAFFIC"]) if row["TRAFFIC"] else None,
            "VEHICLE": str(row["VEHICLE"]) if row["VEHICLE"] else None,
            "ALCOHOL": str(row["ALCOHOL"]) if row["ALCOHOL"] else None,
            "NACROTIC_DRUG": str(row["NACROTIC_DRUG"]) if row["NACROTIC_DRUG"] else None,
            "BELT": str(row["BELT"]) if row["BELT"] else None,
            "HELMET": str(row["HELMET"]) if row["HELMET"] else None,
            "AIRWAY": str(row["AIRWAY"]) if row["AIRWAY"] else None
            ,"STOPBLEED": str(row["STOPBLEED"]) if row["STOPBLEED"] else None,
            "SPLINT": str(row["SPLINT"]) if row["SPLINT"] else None,
            "FLUID": str(row["FLUID"]) if row["FLUID"] else None,
            "URGENCY": str(row["URGENCY"]) if row["URGENCY"] else None,
            "COMA_EYE": str(row["COMA_EYE"]) if row["COMA_EYE"] else None,
            "COMA_SPEAK": str(row["COMA_SPEAK"]) if row["COMA_SPEAK"] else None,
            "COMA_MOVEMENT": str(row["COMA_MOVEMENT"]) if row["COMA_MOVEMENT"] else None,
            "D_UPDATE": str(row["D_UPDATE"]) if row["D_UPDATE"] else None,
            "CID": str(row["CID"]) if row["CID"] else None,
            "HOSPCODE9": str(row["HOSPCODE9"]) if row["HOSPCODE9"] else None,
            "accident_stdcode": str(row["accident_stdcode"]) if row["accident_stdcode"] else None,
            "pt_name": str(row["pt_name"]) if row["pt_name"] else None,
            "hn": str(row["hn"]) if row["hn"] else None,
            "an": str(row["an"]) if row["an"] else None,
            "referhos": str(row["referhos"]) if row["referhos"] else None,
            "dead_in": str(row["dead_in"]) if row["dead_in"] else None,
            "dead_before": str(row["dead_before"]) if row["dead_before"] else None,
            "place_other": str(row["place_other"]) if row["place_other"] else None,
            "accident_place_id": str(row["accident_place_id"]) if row["accident_place_id"] else None,
        }
        list_data.append(temp)

    return {
        "MessageCode": "200",
        "Message": "Success",
        "result": list_data
    }

@router.post(
    "/place",
    summary="RTI AccidentPlace",
    description="ข้อมูลจุดเสี่ยง",
    response_model=RTIAccidentPlaceResponse,
    status_code=status.HTTP_200_OK,
)
async def rti_place(
    body: RTIAccidentPlaceRequest,
    request: Request,
    headers: HeaderSecurity = Depends(get_header_security),
    db: AsyncSession = Depends(get_db),
):
    await api_security(request, body.hospcode)

    sql = text("""
        SELECT ap.stdcode_ok AS accident_stdcode, ap.accident_place_type_name, ap.latitude, ap.longitude, ap.tamboncode, ap.ampurcode, ap.road, ap.export_code, ap.accident_place_type_id AS accident_id
        FROM accident_place_type ap
        WHERE (ap.latitude IS NOT NULL AND longitude IS NOT NULL) AND (ap.latitude != '' AND longitude != '')
        ORDER BY ap.stdcode_ok ASC
    """)

    rows = await db.execute(sql)
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
            "accident_stdcode": str(row["accident_stdcode"]),
            "accident_place_type_name": str(row["accident_place_type_name"]),
            "latitude": str(row["latitude"]),
            "longitude": str(row["longitude"]),
            "tamboncode": str(row["tamboncode"]),
            "ampurcode": str(row["ampurcode"]),
            "road": str(row["road"]),
            "export_code": str(row["export_code"]),
            "accident_id": str(row["accident_id"]),
        }
        list_data.append(temp)

    return {
        "MessageCode": "200",
        "Message": "Success",
        "result": list_data
    }