FROM nikolaik/python-nodejs:python3.11-nodejs24

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# git is required: requirements.txt installs kurigram from source
# ffmpeg/ffprobe are required by pytgcalls to stream audio and video
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates curl xz-utils \
    && rm -rf /var/lib/apt/lists/*

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
    && git init -q /app \
    && git -C /app remote add origin https://github.com/RahatCodes7/Music-Galaxy.git \
    && git config --global --add safe.directory /app

CMD ["python3", "-m", "ShrutixMusic"]
