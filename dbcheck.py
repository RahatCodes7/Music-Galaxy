#!/usr/bin/env python3
"""Check the MongoDB connection without starting the whole bot.

    python3 dbcheck.py                          # uses MONGO_DB_URI from .env
    python3 dbcheck.py mongodb://127.0.0.1:27017
    python3 dbcheck.py "mongodb://user:pass@127.0.0.1:27017/musicgalaxy?authSource=admin"

Three checks, in order, so the failure is unambiguous:

    1. configuration  - is MONGO_DB_URI set and parseable (placeholder? quotes?)
    2. TCP reachability - is anything actually listening on host:port?
    3. driver ping    - does MongoDB accept the credentials / replica set?

Exit code 0 when the ping succeeds, 1 otherwise.
"""

from __future__ import annotations

import asyncio
import socket
import sys
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

import mongo_utils
from mongo_utils import (
    build_client_kwargs,
    describe_target,
    error_hints,
    error_summary,
    host_list,
    looks_like_placeholder,
    normalize_uri,
    resolve_db_name,
    sanitize_uri,
)

BASE_DIR = Path(__file__).resolve().parent

OK = "  [ OK ]"
BAD = "  [FAIL]"
INFO = "  [ .. ]"


def _load_env() -> None:
    env_file = BASE_DIR / ".env"
    load_dotenv(env_file)
    load_dotenv()
    if env_file.exists():
        print(f"{INFO} .env loaded from {env_file}")
    else:
        print(f"{INFO} no .env next to dbcheck.py - using process environment")


def _tcp_check(uri: str, timeout: float) -> tuple[bool, str]:
    if uri.lower().startswith("mongodb+srv://"):
        return True, "SRV URI - TCP probe skipped, the driver resolves the seed list"
    hosts = host_list(uri)
    if not hosts:
        return False, "URI does not contain a host (expected 127.0.0.1:27017)"

    first = hosts[0]
    if first.startswith("["):          # [::1]:27017
        host, _, port = first.rpartition("]:")
        host, port = host.lstrip("["), port or "27017"
    elif first.count(":") == 1:        # 127.0.0.1:27017
        host, _, port = first.partition(":")
    else:                              # bare hostname
        host, port = first, "27017"

    try:
        port_number = int(port)
    except ValueError:
        return False, f"invalid port in {first!r}"

    try:
        with socket.create_connection((host, port_number), timeout=timeout):
            return True, f"{host}:{port_number} is reachable"
    except OSError as exc:
        return False, f"{host}:{port_number} -> {exc.__class__.__name__}: {exc}"


async def _ping(uri: str, timeout_ms: int, direct: bool) -> tuple[bool, str]:
    client = AsyncIOMotorClient(
        uri,
        **build_client_kwargs(uri, timeout_ms=timeout_ms, direct_connection=direct),
    )
    try:
        await client.admin.command("ping")
    except Exception as exc:
        hints = error_hints(exc, uri)
        lines = [f"ping failed -> {error_summary(exc)}"]
        lines.extend(f"  hint: {hint}" for hint in hints)
        return False, "\n".join(lines)
    finally:
        client.close()
    return True, "admin.ping answered by the server"


def main(argv: list[str]) -> int:
    print("Music Galaxy - MongoDB connectivity check\n")
    _load_env()

    raw_uri = argv[1] if len(argv) > 1 else mongo_utils.env("MONGO_DB_URI")
    uri = normalize_uri(raw_uri)
    timeout_ms = mongo_utils.env_int("MONGO_TIMEOUT_MS", 8000)
    db_name = resolve_db_name(uri, mongo_utils.env("MONGO_DB_NAME"))
    direct = mongo_utils.env("MONGO_DIRECT_CONNECTION", "false").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    print(f"{INFO} URI           : {sanitize_uri(uri)}")
    print(f"{INFO} Server        : {describe_target(uri) or '<none>'}")
    print(f"{INFO} Database      : {db_name}")
    print(f"{INFO} Timeout       : {timeout_ms} ms\n")

    # 1. configuration
    if not uri:
        print(f"{BAD} MONGO_DB_URI is empty. Add it to .env:")
        print("         local : mongodb://127.0.0.1:27017")
        print("         atlas : mongodb+srv://user:pass@cluster.mongodb.net/musicgalaxy")
        return 1
    if looks_like_placeholder(uri):
        print(f"{BAD} MONGO_DB_URI still contains the .env.example placeholder value.")
        print("         Replace it with your real connection string.")
        return 1
    if raw_uri.strip() != uri:
        print(f"{OK} URI cleaned up (quotes/spaces/localhost -> 127.0.0.1): {sanitize_uri(uri)}")
    else:
        print(f"{OK} URI looks like a MongoDB connection string")

    # 2. TCP
    reachable, detail = _tcp_check(uri, timeout=max(timeout_ms / 1000, 1.0))
    print(f"{OK if reachable else BAD} TCP  : {detail}")
    if not reachable:
        print("\nThe driver can never connect while nothing listens on that port.")
        print("  local server : sudo systemctl start mongod   (or: docker compose up -d mongo)")
        print("  inside docker: use the service name, e.g. mongodb://mongo:27017")
        print("  wrong port   : mongod listens on 27017 by default")
        return 1

    # 3. driver
    ok, detail = asyncio.run(_ping(uri, timeout_ms, direct))
    print(f"{OK if ok else BAD} PING : {detail}")
    if not ok:
        print("\nChecklist:")
        print("  - user/password URL escaped (quote_plus) and authSource=admin when needed")
        print("  - single-node replica set: add ?directConnection=true")
        print("  - Atlas: your IP is allowlisted and the cluster is not paused")
        return 1

    print(f"\n{OK} MongoDB connection works. The bot will write into '{db_name}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
