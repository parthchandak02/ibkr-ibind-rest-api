FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create a non-root user and set proper permissions
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

# Create and set working directory with proper permissions
WORKDIR /app
RUN chown appuser:appuser /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY --chown=appuser:appuser requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY --chown=appuser:appuser . .

# Create directories for OAuth files if they don't exist
RUN mkdir -p paper_trading_oauth_files live_trading_oauth_files && \
    chown -R appuser:appuser paper_trading_oauth_files live_trading_oauth_files

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 5001

# Healthcheck to ensure the API is running
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5001/health || exit 1

# Command to run the application using the new run_server.py script
CMD ["python", "run_server.py", "--env", "${IBIND_TRADING_ENV:-live_trading}", "--port", "5001"]
