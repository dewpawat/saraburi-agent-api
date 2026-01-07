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
- Uvicorn (ASGI Server)
- Docker / Docker Compose
- MySQL / MariaDB
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
API_ALLOWED_IP1=203.157.115.86 #อันนี้เป็น ip จาก สสจ.
API_ALLOWED_IP2=127.0.0.1 #อันนี้สำหรับทดสอบที่ รพ.

HOSP_CODE=YOUR_HOSP_CODE
HOSP_CODE9=YOUR_HOSP_CODE9
HOSP_NAME=Test Hospital
```

---

### 3. รันระบบด้วย Docker Compose

ใช้คำสั่งต่อไปนี้เพื่อสร้างและรัน container ของระบบ

```bash
docker compose up -d --build
```
แก้ไขไฟล์ .env ให้ตรงกับสภาพแวดล้อมของหน่วยงาน

ตรวจสอบว่า container ของระบบทำงานอยู่หรือไม่
```bash
docker ps
```
ผลลัพธ์ที่ควรเห็น
จะต้องมี container ของระบบปรากฏอยู่ในรายการ เช่น
```text
saraburi_agent_api-api   saraburi-agent-api   0.0.0.0:18080->18080/tcp
```
> โดยมีความหมายดังนี้:
> saraburi_agent_api-api
> ชื่อ container ของระบบ
> saraburi-agent-api
> ชื่อ image ที่ถูก build ขึ้นมา
> 0.0.0.0:18080->18080/tcp
> ระบบเปิดให้เรียกใช้งานผ่าน port 18080 ของเครื่อง serve

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
  "status": "running"
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

### การเข้าใช้งานเมื่อใช้ Reverse Proxy
เมื่อใช้ Reverse Proxy แล้ว
สามารถเรียกใช้งาน API ผ่าน URL ของ Web Server ได้ทันที เช่น

```bash
http://<SERVER_IP>/api/v1/monitor/status
```
หรือ 
```bash
https://<DOMAIN>.moph.go.th/api/v1/monitor/status
)
```

### ขอรับ API_KEY และ UPDATE Endpoint
ได้ที่ LINE OA ดิจิทัล สสจ.สระบุรี ลงทะเบียนด้วย Provider ID
https://line.me/R/ti/p/@580nooeh

> **สำนักงานสาธารณสุขจังหวัดสระบุรี  
> กลุ่มงานสุขภาพดิจิทัล**

