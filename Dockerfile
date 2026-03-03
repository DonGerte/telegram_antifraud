FROM python:3.14-slim

LABEL maintainer="hasbulla <hasbullita007@gmail.com>"
LABEL description="Telegram Anti-Fraud System - Production-ready moderation engine"
LABEL version="0.1.0"
LABEL license="MIT"
LABEL repository="https://github.com/DonGerte/telegram_antifraud"

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Default entrypoint
CMD ["python", "-m", "engine.worker"]
