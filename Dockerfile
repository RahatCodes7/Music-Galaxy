# The deployment host reaches the registry only intermittently, so the base
# image can be swapped without touching anything else:
#   --build-arg BASE_IMAGE=nikolaik/python-nodejs:python3.10-nodejs20
#   --build-arg BASE_IMAGE=8ct6zrnooesy0o7yczhmlck8:b612dfc1a6736fd60796760063af2e2248c07fe7
ARG BASE_IMAGE=ghcr.io/astral-sh/uv:python3.11-bookworm-slim
FROM ${BASE_IMAGE}

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# git powers the runtime auto update, the package mirror is optional, the bot
# starts fine without it
RUN (apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*) \
    || echo "git could not be installed, the runtime auto update stays disabled"

# ffmpeg and ffprobe are required by pytgcalls, they are only fetched when
# the base image does not ship them
COPY docker/setup_ffmpeg.py /tmp/setup_ffmpeg.py
RUN command -v ffmpeg >/dev/null 2>&1 || python3 /tmp/setup_ffmpeg.py

WORKDIR /app

COPY requirements.txt ./
RUN python3 -m ensurepip --default-pip >/dev/null 2>&1 || true; \
    python3 -m pip install --no-cache-dir --upgrade pip >/dev/null 2>&1 || true; \
    (python3 -m pip install --no-cache-dir -r requirements.txt \
    || uv pip install --system --no-cache -r requirements.txt)

COPY . /app/
RUN chmod +x /app/start /app/setup

CMD ["python3", "-m", "ShrutixMusic"]
