FROM nikolaik/python-nodejs:python3.10-nodejs20

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# The base image already ships git, curl, ca-certificates and xz.
# Refresh them when the package mirror is reachable, but never fail the
# build on it, the deployment host cannot always reach the mirrors.
RUN (apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates curl xz-utils \
    && rm -rf /var/lib/apt/lists/*) \
    || echo "package mirror unreachable, using the bundled packages"

# ffmpeg and ffprobe are required by pytgcalls to stream audio and video
RUN curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
        -o /tmp/ffmpeg.tar.xz \
    && tar -xJf /tmp/ffmpeg.tar.xz -C /tmp \
    && install -m 0755 /tmp/ffmpeg-*-static/ffmpeg /usr/local/bin/ffmpeg \
    && install -m 0755 /tmp/ffmpeg-*-static/ffprobe /usr/local/bin/ffprobe \
    && rm -rf /tmp/ffmpeg* \
    || (apt-get update \
        && apt-get install -y --no-install-recommends ffmpeg \
        && rm -rf /var/lib/apt/lists/*)

WORKDIR /app

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /app/
RUN chmod +x /app/start /app/setup \
    && (git init -q /app \
        && git -C /app remote add origin https://github.com/RahatCodes7/Music-Galaxy.git \
        && git config --global --add safe.directory /app) \
    || echo "git unavailable, runtime auto update stays disabled"

CMD ["python3", "-m", "ShrutixMusic"]
