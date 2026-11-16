FROM python:3.12-slim

# ป้องกัน pyc และ buffer log
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# เวลาในเครื่อง (ชื่อไฟล์ log รายวัน, เวลาใน /monitor) เป็นเวลาไทย
ENV TZ=Asia/Bangkok

WORKDIR /app

# tzdata สำหรับ TZ ด้านบน (driver ฐานข้อมูลเป็น pure Python ไม่ต้องใช้ compiler)
RUN apt-get update && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

# ติดตั้ง python packages (เวอร์ชันล็อกไว้ใน requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy source code
COPY app ./app

# สร้างไดเรกทอรี logs พร้อมกำหนดสิทธิ์ 777 ป้องกันปัญหา Permission ใน Docker
RUN mkdir -p /app/logs && chmod -R 777 /app/logs

EXPOSE 18080

# รัน FastAPI ด้วย uvicorn (docker-compose.yml กำหนด command เดียวกันนี้)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "18080", "--workers", "2"]
