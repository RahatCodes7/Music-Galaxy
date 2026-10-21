#!/usr/bin/env bash
# Diagnose the outbound network of the deployment host.
# Run it on the server:
#   bash <(curl -sL https://raw.githubusercontent.com/RahatCodes7/Music-Galaxy/main/docker/network-check.sh)
set -u

HOSTS="github.com pypi.org files.pythonhosted.org objects.githubusercontent.com registry.npmjs.org"

echo "=== basic connectivity ==="
for target in 1.1.1.1 8.8.8.8 140.82.112.3; do
  printf '%-16s ' "$target"
  if ping -c 2 -W 3 "$target" >/dev/null 2>&1; then echo "ping OK"; else echo "ping FAIL"; fi
done

echo
echo "=== dns ==="
cat /etc/resolv.conf
for h in $HOSTS; do
  printf '%-32s %s\n' "$h" \
    "$(getent ahostsv4 "$h" 2>/dev/null | awk '{print $1}' | sort -u | tr '\n' ' ')"
done

echo
echo "=== https reachability, ipv4 first then ipv6 (20s each) ==="
for h in $HOSTS; do
  printf '%-32s ' "$h"
  v4=$(curl -4 -s -o /dev/null -w '%{http_code} %{time_total}s' --max-time 20 "https://$h" 2>/dev/null || echo "v4-FAIL")
  v6=$(curl -6 -s -o /dev/null -w '%{http_code} %{time_total}s' --max-time 20 "https://$h" 2>/dev/null || echo "v6-FAIL")
  echo "ipv4: $v4 | ipv6: $v6"
done

echo
echo "=== git clone probe ==="
rm -rf /tmp/net-probe
if timeout 180 git clone --depth=1 -q https://github.com/RahatCodes7/Music-Galaxy /tmp/net-probe 2>&1; then
  echo "git clone OK"
else
  echo "git clone FAILED"
fi
rm -rf /tmp/net-probe

echo
echo "=== docker pull probe ==="
timeout 120 docker pull ghcr.io/astral-sh/uv:python3.11-bookworm-slim >/dev/null 2>&1 \
  && echo "docker pull ghcr.io OK" || echo "docker pull ghcr.io FAILED"

echo
echo "=== done ==="
