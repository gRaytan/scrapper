FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and Playwright browser dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    # Playwright dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-unifont \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (skip install-deps as we installed them above)
RUN playwright install chromium

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/raw data/processed data/exports logs

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "scripts/run_scraper.py"]
