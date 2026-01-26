# Hugging Face Spaces Dockerfile for Pelta AI Backend
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV and healthcheck
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose port 7860 (Hugging Face default)
EXPOSE 7860

# Set environment variables
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=7860
ENV FLASK_DEBUG=False
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run with Gunicorn (production WSGI server)
# --workers=1: Single worker for ML models (thread-safe)
# --threads=4: Handle concurrent requests within worker
# --timeout=120: Long timeout for ML inference
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers=1", "--threads=4", "--timeout=120", "app.final_design.app:app"]
