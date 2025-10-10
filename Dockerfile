# Dockerfile for Medical ETL System
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TESSERACT_CMD=/usr/bin/tesseract
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libmagic1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs temp

# Create non-root user
RUN useradd --create-home --shell /bin/bash etl_user && \
    chown -R etl_user:etl_user /app

# Switch to non-root user
USER etl_user

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from config.config import load_environment_config; print('OK')" || exit 1

# Default command
CMD ["python", "main.py", "--help"]

# Example usage:
# docker build -t medical-etl .
# docker run -v /path/to/data:/app/input -v /path/to/output:/app/output medical-etl \
#   python main.py --source /app/input --destination /app/output