# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies required for packages
# Note: portaudio19-dev removed as pyaudio is optional
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    python3-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip first to avoid installation issues
RUN pip install --upgrade pip setuptools wheel

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || \
    (echo "Some packages failed, installing core dependencies..." && \
     pip install --no-cache-dir fastapi uvicorn gunicorn pydantic python-multipart \
     requests httpx beautifulsoup4 google-generativeai \
     pymongo motor boto3 botocore \
     bcrypt python-jose passlib sqlalchemy \
     PyGithub GitPython bandit dnspython python-dotenv regex)

# Copy Google Cloud credentials (if exists) - using multi-stage approach
# Note: Using ARG to make this optional
ARG GOOGLE_CREDS_FILE=xverta-convo-e1ac5d825bfb.json
COPY ${GOOGLE_CREDS_FILE}* /app/

# Set Google Cloud credentials environment variable (if file exists)
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/xverta-convo-e1ac5d825bfb.json

# Copy the rest of the backend code
COPY . .

# Copy and set permissions for startup script
COPY start.sh .
RUN chmod +x start.sh

# Expose port (must match FastAPI port)
EXPOSE 8000

# Command to run both Monaco server and FastAPI
CMD ["./start.sh"]