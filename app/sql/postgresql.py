"""
PostgreSQL versions of the HOSxP queries (DB_TYPE=postgresql).

Each query returns the same column names / aliases as its MySQL original in the endpoint
files, so the Python mapping code is shared. MySQL queries are NOT read from here.

Translation rules used (MySQL -> PostgreSQL):
- CONCAT(a, ' ', b)            -> a || ' ' || b   (NULL if any part is NULL, like MySQL CONCAT;
                                                   PostgreSQL CONCAT would skip NULLs)
- IF(c, a, b)                  -> CASE WHEN c THEN a ELSE b END / COALESCE(...)
- DATE_FORMAT(d + t, fmt)      -> TO_CHAR(d + t, 'YYYYMMDDHH24MISS')
- GROUP_CONCAT(x SEPARATOR '|')-> STRING_AGG(CAST(x AS VARCHAR), '|')
- GROUP BY with free columns   -> other columns wrapped in MIN() (PostgreSQL requires it)
- LIMIT 0,1 / DATE(NOW()) / YEAR() -> LIMIT 1 / CURRENT_DATE / EXTRACT(YEAR FROM ...)
- LIKE on names                -> ILIKE (MySQL comparisons are case-insensitive; matters for
                                  the HIV lab masking)
- date parameters              -> CAST(CAST(:x AS VARCHAR) AS DATE) so asyncpg accepts the
                                  'YYYY-MM-DD' string sent by callers
- values compared with ''/numbers on columns of unknown type -> CAST(col AS VARCHAR)
- UPPERCASE aliases            -> double-quoted ("HOSPCODE"), otherwise PostgreSQL returns
                                  them in lowercase and the RTI fields would come back null
- ORDER BY                     -> NULLS FIRST (ASC) / NULLS LAST (DESC), MySQL's NULL order
- `col != ''` on DATE columns  -> dropped (invalid in PostgreSQL; redundant next to `col = :date`)
"""

_THAIADDRESS_JOINS = """
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
            AND t3.tmbpart = p.tmbpart"""

# ---------------------------------------------------------------- HIE
HIE_PATIENT = """
        SELECT p.cid, p.hn, p.pname, p.fname, p.lname, p.birthday, p.hometel, p.sex,
        CAST(p.addrpart AS VARCHAR) || ' ' || CAST(p.road AS VARCHAR) AS address, p.moopart AS moo,
        t3.name AS tambon, t2.name AS ampur, t1.name AS changwat
        FROM patient p""" + _THAIADDRESS_JOINS + """
        WHERE p.cid = :cid
"""

HIE_SERVICE = """
        SELECT p.hn, o.vn, o.an, o.vstdate, o.vsttime, i.tname, pt.name, o.pttypeno, i.name AS iname, i.code3, v.paid_money, d.name AS dname
        FROM patient p
        LEFT JOIN ovst o ON p.hn = o.hn
        LEFT JOIN pttype pt ON o.pttype = pt.pttype
        LEFT JOIN vn_stat v ON o.vn = v.vn
        LEFT JOIN icd101 i ON v.pdx = i.code
        LEFT JOIN doctor d ON o.doctor = d.code
        WHERE p.cid = :cid AND p.hn = :hn
            AND o.vstdate BETWEEN CAST(CAST(:start_vstdate AS VARCHAR) AS DATE) AND CURRENT_DATE
        ORDER BY o.vstdate DESC NULLS LAST, o.vsttime DESC NULLS LAST
"""

# Main row of /hie/visit and /hie/admit (identical query in both endpoints)
HIE_VISIT_MAIN = """
        SELECT p.hn AS hn_0, p.cid, p.pname || ' ' || p.fname || ' ' || p.lname AS nm, p.birthday,
            (EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM p.birthday)) AS birthday_year,
            (SELECT hospitalname FROM opdconfig LIMIT 1) AS so,
            o.vn AS vn_0, o.an AS an_0, o.vstdate AS vstdate_0, o.vsttime AS vsttime_0,
            i.tname, pt.name, o.pttypeno, i.name AS iname, i.code3, v.paid_money, d.name AS dname,
            pn.name AS pnname, ost.name AS novstost, ist.name AS novstist, a.nextdate, sc.*
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
        LEFT OUTER JOIN oapp a ON a.vn = o.vn
        WHERE o.vn = :vn AND p.hn = :hn
"""

HIE_VISIT_DIAG = """
        SELECT
            i.code3, i.tname, i.name AS iname
        FROM ovst o
            INNER JOIN ovstdiag ov ON o.vn = ov.vn
            INNER JOIN icd101 i ON ov.icd10 = i.code
        WHERE o.vn = :vn AND ov.diagtype <> '1'
"""

HIE_ADMIT_DIAG = """
        SELECT o.vn, o.vstdate, o.vsttime, i.tname, pt.name, o.pttypeno, i.name AS iname, i.code3, v.paid_money, d.name AS dname
        FROM ovst o
        INNER JOIN ovstdiag ov ON o.vn = ov.vn
        INNER JOIN icd101 i ON ov.icd10 = i.code
        INNER JOIN pttype pt ON o.pttype = pt.pttype
        INNER JOIN vn_stat v ON o.vn = v.vn
        LEFT JOIN doctor d ON o.doctor = d.code
        WHERE o.vn = :vn AND ov.diagtype <> '1'
        ORDER BY o.vstdate NULLS FIRST, o.vsttime NULLS FIRST
"""

_DRUG_SELECT = """
        SELECT b.name, b.strength, a.qty, a.sum_price, d.shortlist
        FROM opitemrece a
        INNER JOIN {table} b ON a.icode = b.icode
        LEFT OUTER JOIN drugusage d ON d.drugusage = a.drugusage
        WHERE {where}
"""
HIE_VISIT_DRUG_S = _DRUG_SELECT.format(table="s_drugitems", where="a.vn = :vn")
HIE_VISIT_DRUG = _DRUG_SELECT.format(table="drugitems", where="a.vn = :vn")
HIE_ADMIT_DRUG_S = _DRUG_SELECT.format(table="s_drugitems", where="a.vn = :vn OR a.an = :an")
HIE_ADMIT_DRUG = _DRUG_SELECT.format(table="drugitems", where="a.vn = :vn OR a.an = :an")

HIE_LAB = """
        SELECT l.lab_items_code, i.lab_items_name, i.lab_items_normal_value,
        CASE WHEN i.lab_items_name NOT ILIKE '%hiv%' AND i.lab_items_name NOT ILIKE '%interpretation%'
             THEN l.lab_order_result ELSE 'ปกปิด' END AS lab_order_result
        FROM lab_head h
        INNER JOIN lab_order l ON h.lab_order_number = l.lab_order_number
        INNER JOIN lab_items i ON i.lab_items_code = l.lab_items_code
        WHERE h.vn = :vn
        ORDER BY h.order_date DESC NULLS LAST
"""

HIE_ALLERGY = """
        SELECT oa.agent, oa.symptom, oa.report_date, oa.department
        FROM opd_allergy oa
        WHERE oa.hn = :hn
"""

HIE_ER_OPER = """
        SELECT ero.*, eoc.name AS er_oper_name, d.name AS doctor_name
        FROM er_regist_oper ero
        LEFT OUTER JOIN er_oper_code eoc ON eoc.er_oper_code = ero.er_oper_code
        LEFT OUTER JOIN doctor d ON d.code = ero.doctor
        WHERE ero.vn = :vn
        ORDER BY ero.rec_no ASC NULLS FIRST
"""

HIE_OPD_OPER = """
        SELECT dot.*, eoc.name AS opd_oper_name, d.name AS doctor_name
        FROM doctor_operation dot
        LEFT OUTER JOIN er_oper_code eoc ON eoc.er_oper_code = dot.er_oper_code
        LEFT OUTER JOIN doctor d ON d.code = dot.doctor
        WHERE dot.vn = :vn
"""

HIE_ADMIT_AN = """
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
        WHERE a.vn = :vn
"""

HIE_ADMIT_IPT_OPER = """
        SELECT ino.*, ioc.name AS oper_name, d.name AS doctor_name
        FROM ipt_nurse_oper ino
        LEFT OUTER JOIN ipt_oper_code ioc ON ioc.ipt_oper_code = ino.ipt_oper_code
        LEFT OUTER JOIN doctor d ON d.code = ino.doctor
        WHERE ino.an = :an
        ORDER BY ino.ref_date ASC NULLS FIRST
"""

# ---------------------------------------------------------------- Stroke
_STROKE_PATIENT_COLUMNS = """
            MIN(p.pname) AS pname,
            MIN(p.fname) AS fname,
            MIN(p.lname) AS lname,
            MIN(p.sex) AS sex,
            MIN(p.nationality) AS nationality,
            MIN(p.birthday) AS birthday,
            MIN(id.icd10) AS icd10,"""

_STROKE_ADDRESS_COLUMNS = """
            MIN(d.name) AS status,
            MIN(CAST(p.addrpart AS VARCHAR) || ' ' || CAST(p.road AS VARCHAR)) AS address,
            MIN(p.moopart) AS moo,
            MIN(t3.name) AS tambon,
            MIN(t2.name) AS ampur,
            MIN(t1.name) AS changwat,
            MIN(p.tmbpart) AS tmbpart,
            MIN(p.amppart) AS ampart,
            MIN(p.chwpart) AS chwpart,
            MIN(p.hometel) AS phone,
            MIN(p.informtel) AS relation_phone,
            MIN(p.informname) AS relation_name,
            STRING_AGG(CAST(di.sticker_short_name AS VARCHAR), '|') AS drug_name"""

STROKE_IPD = """
        SELECT
            MIN(o.hcode) AS hospcode,
            MIN(o.vstdate) AS vstdate,
            MIN(p.cid) AS cid,
            MIN(o.hn) AS hn,
            o.vn,""" + _STROKE_PATIENT_COLUMNS + """
            MIN(o.an) AS an,
            MIN(i.regdate) AS regdate,
            MIN(CAST(id.modify_datetime AS DATE)) AS dxdate,
            MIN(i.dchdate) AS dchdate,""" + _STROKE_ADDRESS_COLUMNS + """
        FROM ovst o
        INNER JOIN ipt i ON i.an = o.an
        LEFT JOIN opitemrece r ON r.an = o.an
        LEFT JOIN drugitems di ON di.icode = r.icode
        LEFT JOIN iptdiag id ON id.an = i.an
        LEFT JOIN patient p ON p.hn = i.hn
        LEFT JOIN icd10 i1 ON i1.code = id.icd10
        LEFT JOIN dchtype d ON d.dchtype = i.dchtype""" + _THAIADDRESS_JOINS + """
        WHERE i.dchdate = CAST(CAST(:dchdate AS VARCHAR) AS DATE)
            AND id.icd10 BETWEEN 'I60' AND 'I69'
            AND r.icode LIKE '1%'
        GROUP BY o.vn
"""

STROKE_OPD = """
        SELECT
            MIN(o.hcode) AS hospcode,
            MIN(o.vstdate) AS vstdate,
            MIN(p.cid) AS cid,
            MIN(o.hn) AS hn,
            o.vn,""" + _STROKE_PATIENT_COLUMNS + """
            MIN(o.vstdate) AS regdate,
            MIN(CASE WHEN id.vstdate IS NOT NULL AND id.vsttime IS NOT NULL THEN id.vstdate END) AS dxdate,
            MIN(o.vstdate) AS dchdate,""" + _STROKE_ADDRESS_COLUMNS + """
        FROM ovst o
        LEFT JOIN opitemrece r ON r.vn = o.vn
        LEFT JOIN drugitems di ON di.icode = r.icode
        LEFT JOIN ovstdiag id ON id.vn = o.vn
        LEFT JOIN patient p ON p.hn = o.hn
        LEFT JOIN icd10 i1 ON i1.code = id.icd10
        LEFT JOIN ovstost d ON d.ovstost = o.ovstost""" + _THAIADDRESS_JOINS + """
        WHERE o.vstdate = CAST(CAST(:vstdate AS VARCHAR) AS DATE)
            AND id.icd10 BETWEEN 'I60' AND 'I69'
            AND r.icode LIKE '1%'
            AND o.an IS NULL
        GROUP BY o.vn
"""

# ---------------------------------------------------------------- RTI
RTI_ACCIDENT = """
        SELECT
            CAST(:hospcode AS VARCHAR) AS "HOSPCODE",
            CASE WHEN ps.person_id IS NULL THEN o.hn ELSE LPAD(CAST(ps.person_id AS VARCHAR), 6, '0') END AS "PID",
            o.vn AS "SEQ",
            TO_CHAR(o.vstdate + o.vsttime, 'YYYYMMDDHH24MISS') AS "DATETIME_SERV",
            TO_CHAR(o.vstdate + o.vsttime, 'YYYYMMDDHH24MISS') AS "DATETIME_AE",
            LPAD(CAST(ed.er_accident_type_id AS VARCHAR), 2, '0') AS "AETYPE",
            h.export_code AS "AEPLACE",
            ed.er_refer_sender_id AS "TYPEIN_AE",
            ed.accident_person_type_id AS "TRAFFIC",
            COALESCE(CAST(tt.export_code AS VARCHAR), '99') AS "VEHICLE",
            ed.accident_alcohol_type_id AS "ALCOHOL",
            ed.accident_drug_type_id AS "NACROTIC_DRUG",
            ed.accident_belt_type_id AS "BELT",
            ed.accident_helmet_type_id AS "HELMET",
            ed.accident_airway_type_id AS "AIRWAY",
            ed.accident_bleed_type_id AS "STOPBLEED",
            ed.accident_splint_type_id AS "SPLINT",
            ed.accident_fluid_type_id AS "FLUID",
            CASE CAST(ed.er_emergency_type AS VARCHAR) WHEN '1' THEN 2 WHEN '2' THEN 3 ELSE 6 END AS "URGENCY",
            ed.gcs_e AS "COMA_EYE",
            ed.gcs_v AS "COMA_SPEAK",
            ed.gcs_m AS "COMA_MOVEMENT",
            TO_CHAR(o.vstdate + o.vsttime, 'YYYYMMDDHH24MISS') AS "D_UPDATE",
            COALESCE(v.cid, p.cid) AS "CID",
            CAST(:hospcode9 AS VARCHAR) AS "HOSPCODE9",
            h.stdcode_ok AS accident_stdcode,
            p.pname || p.fname || ' ' || p.lname AS pt_name,
            o.hn,
            COALESCE(CAST(o.an AS VARCHAR), CAST(ed.accident_admit AS VARCHAR)) AS an,
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
        WHERE o.vstdate = CAST(CAST(:vstdate AS VARCHAR) AS DATE)
        ORDER BY o.vstdate DESC NULLS LAST
"""

RTI_PLACE = """
        SELECT ap.stdcode_ok AS accident_stdcode, ap.accident_place_type_name, ap.latitude, ap.longitude, ap.tamboncode, ap.ampurcode, ap.road, ap.export_code, ap.accident_place_type_id AS accident_id
        FROM accident_place_type ap
        WHERE (ap.latitude IS NOT NULL AND ap.longitude IS NOT NULL)
            AND (CAST(ap.latitude AS VARCHAR) <> '' AND CAST(ap.longitude AS VARCHAR) <> '')
        ORDER BY ap.stdcode_ok ASC NULLS FIRST
"""

# key -> SQL; keys are used by app.core.sql.sql_for() in the endpoint files
QUERIES = {
    "hie.patient": HIE_PATIENT,
    "hie.service": HIE_SERVICE,
    "hie.visit.main": HIE_VISIT_MAIN,
    "hie.visit.diag": HIE_VISIT_DIAG,
    "hie.visit.drug_s": HIE_VISIT_DRUG_S,
    "hie.visit.drug": HIE_VISIT_DRUG,
    "hie.visit.lab": HIE_LAB,
    "hie.visit.allergy": HIE_ALLERGY,
    "hie.visit.er_oper": HIE_ER_OPER,
    "hie.visit.opd_oper": HIE_OPD_OPER,
    "hie.admit.main": HIE_VISIT_MAIN,
    "hie.admit.diag": HIE_ADMIT_DIAG,
    "hie.admit.drug_s": HIE_ADMIT_DRUG_S,
    "hie.admit.drug": HIE_ADMIT_DRUG,
    "hie.admit.lab": HIE_LAB,
    "hie.admit.allergy": HIE_ALLERGY,
    "hie.admit.er_oper": HIE_ER_OPER,
    "hie.admit.opd_oper": HIE_OPD_OPER,
    "hie.admit.an": HIE_ADMIT_AN,
    "hie.admit.ipt_oper": HIE_ADMIT_IPT_OPER,
    "stroke.ipd": STROKE_IPD,
    "stroke.opd": STROKE_OPD,
    "rti.accident": RTI_ACCIDENT,
    "rti.place": RTI_PLACE,
}
