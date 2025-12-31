# NSE Scraper - Production Dockerfile
# Optimized for Oracle Cloud ARM64 (Ampere) instances

FROM python:3.11-slim-bookworm

# Build arguments
ARG TARGETARCH=arm64

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=Asia/Kolkata \
    DISPLAY=:99

# Set timezone to IST
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chrome dependencies
    wget \
    gnupg \
    unzip \
    curl \
    # Required for Chrome/Selenium
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libdrm2 \
    libgbm1 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libpango-1.0-0 \
    libcairo2 \
    fonts-liberation \
    xdg-utils \
    # Virtual display for headless Chrome
    xvfb \
    # Build tools
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Chromium (works on ARM64)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome binary location for ARM64
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Create app directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/Logs /app/output /app/ipo_data

# Create non-root user for security
RUN useradd -m -u 1000 nseuser && \
    chown -R nseuser:nseuser /app

# Switch to non-root user
USER nseuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:1020/health || exit 1

# Expose API port
EXPOSE 1020

# Start the application
CMD ["python", "main.py"]
