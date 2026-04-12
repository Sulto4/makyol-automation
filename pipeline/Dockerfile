# Python Pipeline Service
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-ron \
    tesseract-ocr-eng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy pipeline package (preserving directory structure)
COPY pipeline/ ./pipeline/

# Create non-root user
RUN addgroup --system --gid 1001 pipeline && \
    adduser --system --uid 1001 --ingroup pipeline pipeline && \
    chown -R pipeline:pipeline /app

USER pipeline

# Expose application port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8001/api/pipeline/health || exit 1

# Start the application
CMD ["uvicorn", "pipeline.api:app", "--host", "0.0.0.0", "--port", "8001"]
