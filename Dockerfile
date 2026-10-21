# Docker Hub is not reachable from the deployment host, the base image is
# pulled from GitHub Container Registry instead. To build from another
# registry, pass a build argument:
#   --build-arg BASE_IMAGE=public.ecr.aws/docker/library/python:3.11-slim-bookworm
ARG BASE_IMAGE=ghcr.io/astral-sh/uv:python3.11-bookworm-slim
FROM ${BASE_IMAGE}

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# ffmpeg and ffprobe are required by pytgcalls to stream audio and video
COPY docker/setup_ffmpeg.py /tmp/setup_ffmpeg.py
RUN python3 /tmp/setup_ffmpeg.py && ffmpeg -version | head -1 && ffprobe -version | head -1

WORKDIR /app

COPY requirements.txt ./
RUN python3 -m ensurepip --default-pip >/dev/null 2>&1 || true; \
    python3 -m pip install --no-cache-dir --upgrade pip >/dev/null 2>&1 || true; \
    (python3 -m pip install --no-cache-dir -r requirements.txt \
    || uv pip install --system --no-cache -r requirements.txt)

COPY . /app/
RUN chmod +x /app/start /app/setup

CMD ["python3", "-m", "ShrutixMusic"]
