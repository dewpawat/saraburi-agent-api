# Saraburi Agent API

Saraburi Agent API เป็นระบบ API กลาง (Central Agent API)  
สำหรับเชื่อมโยงและให้บริการข้อมูลด้านสาธารณสุขระดับจังหวัด  
พัฒนาด้วย **FastAPI (Python)** และ deploy ด้วย **Docker**

ระบบออกแบบมาเพื่อใช้งานในหน่วยงานภาครัฐ / โรงพยาบาล  
โดยคำนึงถึงความปลอดภัย การควบคุมสิทธิ์ และการนำไปใช้งานจริงในระบบ Production

---

## รับรองการทำงาน
- ระบบ HIE
- ระบบ Stroke Alert Saraburi
- ระบบ RTI Saraburi
---

## Technology Stack

- Python 3.12
- FastAPI
- Uvicorn (ASGI Server - Dual Workers)
- Docker / Docker Compose (Host Network Mode)
- MySQL / MariaDB (ค่าเริ่มต้น) หรือ PostgreSQL (v1.3.0+ ตั้งค่า `DB_TYPE=postgresql`)
- REST API (JSON)

---

## Default Service

- API Server: **Uvicorn**
- Default Port: **18080**
- Protocol: **HTTP**
- Swagger UI (Docs): `/docs` (ขึ้นกับ Environment)

---

## ข้อกำหนดระบบ (System Requirements)

- Ubuntu 22.04 / 24.04 (แนะนำ)
- Docker Engine 20+
- Docker Compose v2+
- Network สามารถเชื่อมต่อ GitHub และ Docker Registry ได้

---

## Network Requirement (สำคัญ)

ในบางหน่วยงาน (เช่น โรงพยาบาล)  
อาจมี Firewall / FortiGate ที่บล็อก Docker Registry

กรุณาประสานงานทีม Network เพื่อเปิด **Outbound HTTPS (TCP 443)**  
สำหรับ Domain ต่อไปนี้:

- registry-1.docker.io
- auth.docker.io
- production.cloudflare.docker.com
- index.docker.io
- hub.docker.com
- download.docker.com


> ใช้เฉพาะการ pull Docker image  
> ไม่จำเป็นต้อง disable Firewall หรือ SSL Inspection

---

## วิธีการติดตั้ง (Installation)

### 1. Clone Repository จาก GitHub

```bash
cd /opt
git clone https://github.com/dewpawat/saraburi-agent-api.git
cd saraburi-agent-api
```

> หมายเหตุ:
> การติดตั้งที่ `/opt` ต้องใช้สิทธิ์ root หรือ sudo
> หากไม่มีสิทธิ์ สามารถติดตั้งใน directory อื่นได้ตามความเหมาะสม
---

### 2. สร้างไฟล์ Environment (.env)

คัดลอกไฟล์ตัวอย่าง

```bash
cp .env.example .env
```
แก้ไขไฟล์ .env ให้ตรงกับสภาพแวดล้อมของหน่วยงาน

```env
APP_NAME=Saraburi Agent API
APP_ENV=production
APP_PORT=18080

# MySQL
DB_HOST=YOUR_DB_HOST
DB_PORT=3306
DB_USER=YOUR_DB_USER
DB_PASS=YOUR_DB_PASSWORD
DB_NAME=YOUR_DB_NAME

API_KEY=YOUR_API_KEY
# IP ที่อนุญาต คั่นด้วย comma: IP ของ สสจ. + 127.0.0.1 สำหรับทดสอบที่ รพ.
API_ALLOWED_IPS=203.157.115.86,203.157.115.88,127.0.0.1

HOSP_CODE=YOUR_HOSP_CODE
HOSP_CODE9=YOUR_HOSP_CODE9
HOSP_NAME=Test Hospital
```

> **แนะนำ:** `DB_USER` ควรเป็น user ที่มีสิทธิ์ **SELECT อย่างเดียว** บนฐานข้อมูล HOSxP  
> Agent อ่านข้อมูลอย่างเดียว ไม่มีการเขียนหรือแก้ไขข้อมูลของโรงพยาบาล

#### โรงพยาบาลที่ใช้ HOSxP บน PostgreSQL (v1.3.0+)

เพิ่ม `DB_TYPE=postgresql` และใส่ค่าการเชื่อมต่อของ PostgreSQL (ไม่ใส่ `DB_PORT` จะใช้ `5432`)

```env
DB_TYPE=postgresql
DB_HOST=YOUR_DB_HOST
DB_PORT=5432
DB_USER=YOUR_DB_USER
DB_PASS=YOUR_DB_PASSWORD
DB_NAME=YOUR_DB_NAME
```

ตัวอย่างการสร้าง user อ่านอย่างเดียวบน PostgreSQL (รันด้วยสิทธิ์ผู้ดูแลฐานข้อมูล)

```sql
CREATE ROLE agent_read LOGIN PASSWORD 'รหัสผ่าน';
GRANT CONNECT ON DATABASE ชื่อฐานข้อมูล TO agent_read;
GRANT USAGE ON SCHEMA public TO agent_read;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_read;
```

> - ต้องอนุญาต IP ของเครื่อง Agent ใน `pg_hba.conf` ของเครื่องฐานข้อมูล  
> - Agent เปิด session แบบ **read-only** เสมอ (`default_transaction_read_only=on`) แม้ user จะมีสิทธิ์เขียนก็แก้ไขข้อมูลไม่ได้  
> - รองรับ PostgreSQL 9.6 ขึ้นไป (ทดสอบกับ 9.6 และ 16)  
> - `.env` ของโรงพยาบาลที่ใช้ MySQL **ไม่ต้องแก้อะไร** ไม่มี `DB_TYPE` = ใช้ MySQL เหมือนเดิม

#### ค่าใน .env ทั้งหมด

| ค่า | จำเป็น | คำอธิบาย |
|---|---|---|
| `APP_NAME`, `APP_ENV`, `APP_PORT` | ✔ | `APP_ENV=production` จะปิด `/docs`, `/redoc`, `/openapi.json` |
| `DB_TYPE` | | ชนิดฐานข้อมูล `mysql` (ค่าเริ่มต้น ใช้กับ MariaDB ด้วย) หรือ `postgresql` (v1.3.0+) |
| `DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME` | ✔ | ฐานข้อมูล HOSxP |
| `DB_PORT` | | ไม่ใส่ = `3306` (mysql) / `5432` (postgresql) |
| `API_KEY` | ✔ | key ที่ได้รับจาก สสจ. |
| `API_ALLOWED_IPS` | ✔ * | IP ที่อนุญาต คั่นด้วย comma ใส่เป็นช่วง CIDR ได้ (เช่น `203.157.115.0/24`) |
| `API_ALLOWED_IP1`, `API_ALLOWED_IP2` | | แบบเดิม (ก่อน v1.2.0) ยังใช้ได้ และรวมกับ `API_ALLOWED_IPS` อัตโนมัติ |
| `HOSP_CODE`, `HOSP_CODE9`, `HOSP_NAME` | ✔ | รหัสหน่วยบริการ |
| `TRUSTED_PROXIES` | | Reverse proxy ที่เชื่อ `X-Forwarded-For` ค่าเริ่มต้น `127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16` |
| `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE` | | ค่าเริ่มต้น `5`, `5`, `1800` (ต่อ 1 worker, รัน 2 workers) |

\* ต้องมีอย่างน้อยหนึ่งแบบ (`API_ALLOWED_IPS` หรือ `API_ALLOWED_IP1/IP2`) ถ้าใส่ IP ผิดรูปแบบ ระบบจะข้ามค่านั้นและเขียนเตือนใน log ไม่ทำให้โปรแกรมหยุด

---

### 3. รันระบบด้วย Docker Compose

ใช้คำสั่งต่อไปนี้เพื่อสร้างและรัน container ของระบบ

```bash
docker compose up -d --build
```

> **หมายเหตุสถาปัตยกรรม (Network & Concurrency v1.1.2+):**  
> 1. **Network Mode:** ปรับใช้ `network_mode: "host"` เป็นมาตรฐาน เพื่อให้เชื่อมต่อกับฐานข้อมูล HOSxP/MySQL บนเครื่องแม่ได้โดยตรง ไม่ติดปัญหา Reverse DNS Lookup Timeout (ค้าง 2 นาที) บนเครื่องที่ไม่ได้ตั้ง `skip-name-resolve`  
> 2. **Dual-Worker:** รัน Uvicorn ด้วย `--workers 2` เพื่อแยกเลนคำขอฉุกเฉิน (Stroke Alert, RTI Alert) ออกจากงานดึงข้อมูลรายงานทั่วไป ไม่ให้เกิดคิวบล็อกกัน  
> 3. **DB Connection Pool:** แต่ละ worker มี pool ของตัวเอง (ค่าเริ่มต้น 5 + overflow 5) รวม 2 workers ใช้ได้สูงสุด 20 connection ปรับได้ด้วย `DB_POOL_SIZE` / `DB_MAX_OVERFLOW`

ตรวจสอบว่า container ของระบบทำงานอยู่หรือไม่
```bash
docker ps
```
ผลลัพธ์ที่ควรเห็น
จะต้องมี container ของระบบปรากฏอยู่ในรายการ เช่น
```text
saraburi-agent-api   saraburi-agent-api:prod   Up ...
```
> ระบบเปิดให้เรียกใช้งานผ่าน port 18080 ของเครื่อง server โดยตรง

---

### 4. การเข้าใช้งานระบบ

API Endpoint
```bash
http://<SERVER_IP>:18080/
```
ตัวอย่าง:
```bash
http://192.168.6.89:18080
```

ทดสอบสถานะ ผ่านหน้าเว็บไซต์
```bash
http://<SERVER_IP>:18080/api/v1/monitor/status
```
Response ตัวอย่าง:
```json
{
  "status": "running",
  "version": "1.3.0"
}
```

หรือเข้าใช้งาน Swagger / API Documentation
```bash
http://<SERVER_IP>:18080/docs
```

หมายเหตุ:
> /docs ใช้สำหรับนักพัฒนาและทีม IT
> ในระบบ Production แนะนำให้ปิดหรือจำกัดสิทธิ์การเข้าถึง
> สามารถควบคุมได้ด้วยค่า APP_ENV

#### Monitor Endpoints (v1.2.0+)

| Endpoint | Method | ยืนยันตัวตน | ข้อมูลที่ได้ |
|---|---|---|---|
| `/api/v1/monitor/status` | GET | ไม่ต้อง | สถานะ + version |
| `/api/v1/monitor/database` | GET | ไม่ต้อง (ถ้าส่ง header ผ่าน จะได้ข้อความ error เต็ม) | ผลทดสอบ `SELECT 1` |
| `/api/v1/monitor/system-info` | **POST** | ต้อง | hostname, OS, เวลา, Python, `database_type`, `database_version` (v1.3.0+) |
| `/api/v1/monitor/performance` | **POST** | ต้อง | CPU / RAM / Disk % |
| `/api/v1/monitor/full-check` | **POST** | ต้อง | รวมทั้งหมด (รวม `database_type`, `database_version` ตั้งแต่ v1.3.0) |

`database_type` บอกว่า Agent เชื่อมฐานข้อมูลชนิดไหน (`mysql` หรือ `postgresql`) และ `database_version` คือเวอร์ชันของเครื่องฐานข้อมูล เช่น `10.6.21-MariaDB` หรือ `16.4`

"ต้องยืนยันตัวตน" คือ ส่ง header `x-api-key` และ `x-hospcode` จาก IP ที่อยู่ใน `API_ALLOWED_IPS` (ไม่ต้องส่ง body)

```bash
curl -X POST http://127.0.0.1:18080/api/v1/monitor/system-info \
  -H "x-api-key: YOUR_API_KEY" -H "x-hospcode: YOUR_HOSP_CODE"
```

`/monitor/database` ที่เรียกโดยไม่ส่ง header จะได้แค่ชนิด error + รหัส เช่น `OperationalError (2003)` เพื่อไม่เปิดเผย IP / ชื่อเครื่องฐานข้อมูล

---

### อัปเดตเวอร์ชัน (Update)

```bash
cd /opt/saraburi-agent-api
git pull
docker compose up -d --build
```

ตรวจสอบเวอร์ชันหลังอัปเดตที่ `/api/v1/monitor/status` และดู log ด้วย `docker compose logs -f`  
`.env` เดิมใช้ต่อได้ทันที ไม่ต้องแก้ไข (ดูการเปลี่ยนแปลงแต่ละเวอร์ชันใน `CHANGELOG.md`)

### แก้ปัญหาที่พบบ่อย (Troubleshooting)

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| `(2013, 'Lost connection to MySQL server during query')` หรือ `TCPTransport closed ... the handler is closed` | Connection ที่ค้างใน pool ถูก firewall / MySQL ตัดทิ้ง ตั้งแต่ v1.2.0 Agent ทดสอบ connection ก่อนใช้ทุกครั้งและเชื่อมต่อใหม่ให้อัตโนมัติ ถ้ายังใช้ v1.1.x ให้อัปเดต ใน log จะเห็นบรรทัด `DB connection dropped and will be reopened` ทุกครั้งที่มีการต่อใหม่ |
| `IP x.x.x.x is not allowed` (403) | IP ที่แสดงคือ IP ที่ Agent เห็น ถ้าเป็น IP ของ สสจ. ให้เพิ่มใน `API_ALLOWED_IPS` ถ้าเป็น IP ของ reverse proxy ที่อยู่คนละเครื่องและเป็น IP สาธารณะ ให้เพิ่ม IP นั้นใน `TRUSTED_PROXIES` |
| ชื่อไฟล์ log / เวลาไม่ตรง | ตั้งแต่ v1.2.0 container ใช้เวลา `Asia/Bangkok` ต้อง `docker compose up -d --build` ใหม่ |


### 5. การใช้งานร่วมกับ Web Server ที่มีอยู่แล้ว (Reverse Proxy)

ในกรณีที่หน่วยบริการหรือโรงพยาบาล
มี Web Server (เช่น Apache หรือ Nginx) ใช้งานอยู่แล้ว
แนะนำให้ตั้งค่า Reverse Proxy เพื่อเรียกใช้งาน Saraburi Agent API
โดยไม่ต้องเปิด port 18080 ออกสู่ภายนอกโดยตรง

แนวคิดการทำงาน

```text
Client
  |
  |  HTTPS :443
  v
Apache / Nginx (Web Server)
  |
  |  HTTP :18080 (Internal)
  v
Saraburi Agent API (Docker / Uvicorn)
```

### ตัวอย่างการตั้งค่า Apache (Reverse Proxy)
1) เปิดใช้งาน module ที่จำเป็น
```bash
a2enmod proxy
a2enmod proxy_http
a2enmod headers
systemctl restart apache2
```
2) ตัวอย่าง VirtualHost
```bash
<VirtualHost *:443>
    ServerName api.saraburi.moph.go.th

    ProxyPreserveHost On
    ProxyRequests Off

    ProxyPass / http://127.0.0.1:18080/
    ProxyPassReverse / http://127.0.0.1:18080/

    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-Port "443"

    ErrorLog ${APACHE_LOG_DIR}/saraburi-agent-api-error.log
    CustomLog ${APACHE_LOG_DIR}/saraburi-agent-api-access.log combined
</VirtualHost>
```
3) หลังจากตั้งค่าแล้ว restart Apache:
```bash
systemctl restart apache2
```

### ตัวอย่างการตั้งค่า Nginx (Reverse Proxy)
1) เปิดการใช้งาน
```bash
server {
    listen 443 ssl;
    server_name api.saraburi.moph.go.th;

    location / {
        proxy_pass http://127.0.0.1:18080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```
2) Reload Nginx:
```bash
systemctl reload nginx
```

> **IP ของผู้เรียกเมื่อใช้ Reverse Proxy (v1.2.0+):**  
> Agent จะอ่าน IP จริงจาก header `X-Forwarded-For` เฉพาะเมื่อ request มาจาก proxy ใน `TRUSTED_PROXIES`  
> (ค่าเริ่มต้นคือเครื่องตัวเองและวง LAN ภายใน ซึ่งครอบคลุมกรณี Apache / Nginx อยู่เครื่องเดียวกันหรือใน LAN)  
> request ที่เข้า port 18080 โดยตรงจะไม่สนใจ header นี้ เพื่อป้องกันการปลอม IP

### การเข้าใช้งานเมื่อใช้ Reverse Proxy
เมื่อใช้ Reverse Proxy แล้ว
สามารถเรียกใช้งาน API ผ่าน URL ของ Web Server ได้ทันที เช่น

```bash
http://<SERVER_IP>/api/v1/monitor/status
```
หรือ 
```bash
https://<DOMAIN>.moph.go.th/api/v1/monitor/status
```

### ขอรับ API_KEY และ UPDATE Endpoint
ได้ที่ LINE OA ดิจิทัล สสจ.สระบุรี ลงทะเบียนด้วย Provider ID
https://line.me/R/ti/p/@580nooeh

> **สำนักงานสาธารณสุขจังหวัดสระบุรี  
> กลุ่มงานสุขภาพดิจิทัล**
