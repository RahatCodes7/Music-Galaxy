"""Install the static ffmpeg and ffprobe builds into the bin directory.

pytgcalls needs ffmpeg and ffprobe to stream audio and video. The
deployment host cannot reach Docker Hub or the usual ffmpeg mirrors
reliably, so the binaries are taken from the static build published on
GitHub, which the host can reach.

The script only needs the python standard library, the image has no curl,
no xz and no package mirror to depend on.
"""

import gzip
import os
import sys
import urllib.request

BASE_URL = "https://github.com/eugeneware/ffmpeg-static/releases/download/b6.1.1/"
TARGET_DIR = os.environ.get("FFMPEG_TARGET_DIR", "/usr/local/bin")
BINARIES = ("ffmpeg", "ffprobe")


def install(name: str) -> None:
    url = f"{BASE_URL}{name}-linux-x64.gz"
    print(f"downloading {url}", flush=True)
    with urllib.request.urlopen(url, timeout=600) as response:
        payload = gzip.decompress(response.read())
    target = os.path.join(TARGET_DIR, name)
    with open(target, "wb") as handle:
        handle.write(payload)
    os.chmod(target, 0o755)
    print(f"installed {target} ({len(payload)} bytes)", flush=True)


def main() -> int:
    os.makedirs(TARGET_DIR, exist_ok=True)
    for name in BINARIES:
        install(name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
