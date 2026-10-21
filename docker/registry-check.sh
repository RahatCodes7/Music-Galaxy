#!/usr/bin/env bash
# Check which container registries and build hosts the deployment server can
# reach. Run it on the server:
#   bash <(curl -sL https://raw.githubusercontent.com/RahatCodes7/Music-Galaxy/main/docker/registry-check.sh)
set -u

echo "=== local images (a cached base image needs no registry) ==="
docker images --format '{{.Repository}}:{{.Tag}}  {{.Size}}' 2>/dev/null | head -30

echo
echo "=== docker daemon registry config ==="
cat /etc/docker/daemon.json 2>/dev/null || echo "no /etc/docker/daemon.json"

echo
echo "=== dns ==="
for h in auth.docker.io ghcr.io public.ecr.aws mirror.gcr.io quay.io \
         mcr.microsoft.com registry.gitlab.com github.com pypi.org \
         files.pythonhosted.org johnvansickle.com; do
  printf '%-28s %s\n' "$h" \
    "$(getent ahostsv4 "$h" 2>/dev/null | awk '{print $1}' | sort -u | tr '\n' ' ')"
done

echo
echo "=== tcp connect to :443 (5s) ==="
for h in auth.docker.io ghcr.io public.ecr.aws mirror.gcr.io quay.io \
         mcr.microsoft.com registry.gitlab.com github.com pypi.org \
         files.pythonhosted.org johnvansickle.com; do
  ip=$(getent ahostsv4 "$h" 2>/dev/null | awk '{print $1}' | head -1)
  if [ -z "$ip" ]; then
    printf '%-28s %-16s NO-DNS\n' "$h" "-"
  elif timeout 5 bash -c "cat < /dev/null > /dev/tcp/$ip/443" 2>/dev/null; then
    printf '%-28s %-16s OK\n' "$h" "$ip"
  else
    printf '%-28s %-16s TIMEOUT\n' "$h" "$ip"
  fi
done

echo
echo "=== docker pull probes (150s each) ==="
for img in \
  public.ecr.aws/docker/library/python:3.11-slim-bookworm \
  mirror.gcr.io/library/python:3.11-slim-bookworm \
  ghcr.io/astral-sh/uv:python3.11-bookworm-slim \
  mcr.microsoft.com/devcontainers/python:1-3.11-bookworm \
  quay.io/podman/hello ; do
  printf '%-58s ' "$img"
  if timeout 150 docker pull "$img" >/dev/null 2>&1; then
    echo "OK"
  else
    echo "FAIL"
  fi
done

echo
echo "=== can buildkit use a locally cached image as base (no registry) ? ==="
cat > /tmp/Dockerfile.probe <<'PROBE'
FROM docker.io/coollabsio/coolify-helper:1.0.17
RUN echo local-base-ok
PROBE
if timeout 180 docker build --pull=false -f /tmp/Dockerfile.probe -t localbase:probe /tmp 2>&1 | tail -4; then
  echo "local base probe finished"
fi

echo
echo "=== done ==="
