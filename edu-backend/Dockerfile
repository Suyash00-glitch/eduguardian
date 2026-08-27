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

# Copy and install requirements first for layer caching
COPY requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
