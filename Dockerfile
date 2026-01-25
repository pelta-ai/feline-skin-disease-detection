# Hugging Face Spaces Dockerfile for Pelta AI Backend
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git-lfs \
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

# Run the Flask app
CMD ["python", "app/final_design/app.py"]
