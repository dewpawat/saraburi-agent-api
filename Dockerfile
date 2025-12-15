FROM python:3.12-slim

# ป้องกัน pyc และ buffer log
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# ติดตั้ง dependency ที่จำเป็นสำหรับ aiomysql / mysqlclient
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ติดตั้ง python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy source code
COPY app ./app
COPY .env.example ./

EXPOSE 18080

# รัน FastAPI ด้วย uvicorn (production simple)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "18080"]
