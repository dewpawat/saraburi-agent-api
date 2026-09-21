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
from app.utils.formatters import safe_str, safe_date_iso, safe_get

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

    sql = text("""
        SELECT
            :hospcode AS HOSPCODE,
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
            :hospcode9 AS HOSPCODE9,
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

    rows = await db.execute(sql, {
        "vstdate": vstdate,
        "hospcode": hospcode,
        "hospcode9": hospcode9
    })
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
            "HOSPCODE": safe_str(safe_get(row, "HOSPCODE")) or hospcode,
            "PID": safe_str(safe_get(row, "PID")),
            "SEQ": safe_str(safe_get(row, "SEQ")),
            "DATETIME_SERV": safe_str(safe_get(row, "DATETIME_SERV")),
            "DATETIME_AE": safe_str(safe_get(row, "DATETIME_AE")),
            "AETYPE": safe_str(safe_get(row, "AETYPE")),
            "AEPLACE": safe_str(safe_get(row, "AEPLACE")),
            "TYPEIN_AE": safe_str(safe_get(row, "TYPEIN_AE")),
            "TRAFFIC": safe_str(safe_get(row, "TRAFFIC")),
            "VEHICLE": safe_str(safe_get(row, "VEHICLE")),
            "ALCOHOL": safe_str(safe_get(row, "ALCOHOL")),
            "NACROTIC_DRUG": safe_str(safe_get(row, "NACROTIC_DRUG")),
            "BELT": safe_str(safe_get(row, "BELT")),
            "HELMET": safe_str(safe_get(row, "HELMET")),
            "AIRWAY": safe_str(safe_get(row, "AIRWAY")),
            "STOPBLEED": safe_str(safe_get(row, "STOPBLEED")),
            "SPLINT": safe_str(safe_get(row, "SPLINT")),
            "FLUID": safe_str(safe_get(row, "FLUID")),
            "URGENCY": safe_str(safe_get(row, "URGENCY")),
            "COMA_EYE": safe_str(safe_get(row, "COMA_EYE")),
            "COMA_SPEAK": safe_str(safe_get(row, "COMA_SPEAK")),
            "COMA_MOVEMENT": safe_str(safe_get(row, "COMA_MOVEMENT")),
            "D_UPDATE": safe_str(safe_get(row, "D_UPDATE")),
            "CID": safe_str(safe_get(row, "CID")),
            "HOSPCODE9": safe_str(safe_get(row, "HOSPCODE9")) or hospcode9,
            "accident_stdcode": safe_str(safe_get(row, "accident_stdcode")),
            "pt_name": safe_str(safe_get(row, "pt_name")),
            "hn": safe_str(safe_get(row, "hn")),
            "an": safe_str(safe_get(row, "an")),
            "referhos": safe_str(safe_get(row, "referhos")),
            "dead_in": safe_str(safe_get(row, "dead_in")),
            "dead_before": safe_str(safe_get(row, "dead_before")),
            "place_other": safe_str(safe_get(row, "place_other")),
            "accident_place_id": safe_str(safe_get(row, "accident_place_id")),
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
            "accident_stdcode": safe_str(safe_get(row, "accident_stdcode")),
            "accident_place_type_name": safe_str(safe_get(row, "accident_place_type_name")),
            "latitude": safe_str(safe_get(row, "latitude")),
            "longitude": safe_str(safe_get(row, "longitude")),
            "tamboncode": safe_str(safe_get(row, "tamboncode")),
            "ampurcode": safe_str(safe_get(row, "ampurcode")),
            "road": safe_str(safe_get(row, "road")),
            "export_code": safe_str(safe_get(row, "export_code")),
            "accident_id": safe_str(safe_get(row, "accident_id")),
        }
        list_data.append(temp)

    return {
        "MessageCode": "200",
        "Message": "Success",
        "result": list_data
    }