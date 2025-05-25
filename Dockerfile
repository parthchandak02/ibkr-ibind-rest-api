# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    IBIND_TRADING_ENV=live_trading \
    IBIND_USE_OAUTH=true \
    PORT=8080 \
    PYTHONPATH=/app

# Create and set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code first
COPY . .

# Create a non-root user and set up permissions
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /sbin/nologin -c "Docker image user" appuser && \
    chown -R appuser:appuser /app

# Make sure OAuth directory exists and has right permissions
RUN mkdir -p /app/live_trading_oauth_files && \
    chmod 755 /app/live_trading_oauth_files

# Print files for debugging during build
RUN ls -la /app/live_trading_oauth_files/

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8080

# Healthcheck to ensure the API is running
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/cloud-run-health || exit 1

# Command to run the application
CMD ["python", "run_server.py"]
