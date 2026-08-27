# ============================================================
# EduGuardian AI - Backend Dockerfile
# ============================================================
# Python version: 3.10 (matches local environment)
# Entry point:    chatbot.backend.api.main:app
# PYTHONPATH:     /app (so "chatbot.*" package imports resolve)
# ============================================================

FROM python:3.10-slim

# System dependencies needed by asyncpg / cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Copy only requirements first for layer caching
COPY chatbot/backend/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy the full chatbot package
COPY chatbot/ ./chatbot/

# Set PYTHONPATH to /app so chatbot package is cleanly discovered
ENV PYTHONPATH=/app

# Expose default Gateway port
EXPOSE 8000

# Default command (override in docker-compose for microservices)
CMD ["uvicorn", "chatbot.backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
