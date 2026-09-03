# Use lightweight official Python image
FROM python:3.14-slim

# Prevent Python from writing .pyc files & buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Use file-based keyring backend in headless Docker environments (no D-Bus / Keychain available)
ENV PYTHON_KEYRING_BACKEND=keyrings.alt.file.PlaintextKeyring

# Set working directory
WORKDIR /app

# Install base system tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser & all required system dependencies inside image, then purge apt archives
RUN python -m playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* /tmp/*

# Copy application files
COPY . .

# Run CLI by default
CMD ["python", "main.py"]
