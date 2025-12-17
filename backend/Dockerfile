# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for PyAudio and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    portaudio19-dev \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Google Cloud credentials
COPY xverta-convo-e1ac5d825bfb.json /app/xverta-convo-e1ac5d825bfb.json

# Set Google Cloud credentials environment variable
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