# Music Galaxy — Dokploy / Docker deployment
# Build: docker build -t music-galaxy .
# Run:   docker run --env-file .env music-galaxy
# Dokploy: point at this repo; inject env vars via the Dokploy dashboard.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# System dependencies:
#   git           -> runtime auto update
#   ca-certificates -> TLS for outbound requests
#   ffmpeg        -> required by pytgcalls / yt-dlp audio/video processing
#   build-essential, libffi-dev, libssl-dev -> build wheels with C extensions
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        ffmpeg \
        build-essential \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . /app/
RUN chmod +x /app/start /app/setup

# Dokploy injects DATABASE_URL, BOT_TOKEN, API_ID, etc. as environment variables.
# The .env file is intentionally excluded from the image (.dockerignore).
CMD ["python3", "-m", "MusicGalaxy"]
