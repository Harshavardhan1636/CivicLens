# CivicLens — Production Dockerfile
FROM python:3.11-slim

LABEL maintainer="CivicLens DevOps Lab"
LABEL description="Civic Issue Reporter — Smart City"

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps (layer cached)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Uploads dir + permissions
RUN mkdir -p uploads && chmod 777 uploads

EXPOSE 5000

ENV PORT=5000
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "app:app"]
