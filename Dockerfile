# The deployment host cannot reach any container registry, every build stops
# while buildkit resolves the base image, so the new build starts from the
# image of the last working deployment, which is already cached on the host.
# When a registry is reachable again, override the base image:
#   --build-arg BASE_IMAGE=nikolaik/python-nodejs:python3.10-nodejs20
ARG BASE_IMAGE=8ct6zrnooesy0o7yczhmlck8:b612dfc1a6736fd60796760063af2e2248c07fe7
FROM ${BASE_IMAGE}

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ffmpeg and ffprobe are required by pytgcalls, the base image already ships
# them, they are only fetched when they are missing
COPY docker/setup_ffmpeg.py /tmp/setup_ffmpeg.py
RUN command -v ffmpeg >/dev/null 2>&1 || python3 /tmp/setup_ffmpeg.py

WORKDIR /app

COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir --upgrade pip >/dev/null 2>&1 || true; \
    python3 -m pip install --no-cache-dir -r requirements.txt

COPY . /app/
RUN chmod +x /app/start /app/setup

CMD ["python3", "-m", "ShrutixMusic"]
