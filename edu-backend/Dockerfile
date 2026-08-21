# ============================================================
# EduGuardian - edu-backend Dockerfile
# FastAPI REST API (students, teachers, assignments)
# Runs on port 5000
# ============================================================
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir \
    fastapi==0.115.5 \
    uvicorn[standard]==0.32.1 \
    sqlalchemy==2.0.36 \
    psycopg2-binary==2.9.12 \
    bcrypt==5.0.0 \
    python-jose[cryptography]==3.3.0 \
    python-dotenv==1.2.2 \
    pydantic>=2.0.0 \
    python-multipart==0.0.19

EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
