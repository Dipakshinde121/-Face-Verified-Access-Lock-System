# ==============================================================================
# Dockerfile - Lab Face-Verified Access Lock System
# Central Server & Testing Environment
# ==============================================================================
FROM python:3.11-slim

# Avoid buffering and bytecode generation in container
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies (build tools, cmake, and graphics libs for OpenCV/dlib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY server/ ./server/
COPY frontend/ ./frontend/
COPY config.json ./config.json
COPY config.py ./config.py
COPY crypto_utils.py ./crypto_utils.py
COPY log_viewer.py ./log_viewer.py
COPY liveness_check.py ./liveness_check.py
COPY lock.py ./lock.py
COPY alerting.py ./alerting.py
COPY test_integration.py ./test_integration.py
COPY test_adversarial_suite.py ./test_adversarial_suite.py
COPY test_auth_modes.py ./test_auth_modes.py

# Expose HTTPS port for central API
EXPOSE 8000

# Default command: launch the Central HTTPS FastAPI Server
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "server/key.pem", "--ssl-certfile", "server/cert.pem"]
