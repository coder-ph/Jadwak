# Dockerfile
# Multi-stage Dockerfile for Django + Celery + GeoDjango

# Stage 1: Builder - installing Python dependencies and compilation
FROM python:3.13.5-slim-bullseye AS builder


ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app


COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt



FROM python:3.13.5-slim-bullseye


ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install *runtime* system dependencies for GeoDjango (GDAL, GEOS, PROJ actual libraries)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gdal-bin \
        libgdal28 \
        libgeos-c1v5 \
        libproj19 \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# --- CRITICAL FIX START ---

COPY --from=builder /usr/local /usr/local
# --- CRITICAL FIX END ---


WORKDIR /app


COPY . /app


EXPOSE 8000

# Default command (used by web service; celery overrides it in docker-compose.yml)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
