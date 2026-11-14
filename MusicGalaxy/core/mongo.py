"""MongoDB connection handling.

The driver connects lazily, so a bare ``AsyncIOMotorClient(uri)`` never touches
the network: the previous version logged "Connected to your Mongo Database."
even when mongod was not running, the URI was still the .env.example
placeholder or the password was not URL escaped, and the only thing a broken
setup produced was a silent ``exit()``.  The client is still created here (the
rest of the bot imports ``mongodb`` at module level), but ``verify_connection()``
pings the server for real at startup and explains *why* it failed.
"""

from __future__ import annotations

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

import config
from mongo_utils import (
    build_client_kwargs,
    describe_target,
    error_hints,
    error_summary,
    looks_like_placeholder,
    normalize_uri,
    resolve_db_name,
    sanitize_uri,
)

from ..logging import LOGGER

LOG = LOGGER(__name__)


class MongoConnectionError(RuntimeError):
    """The configured MongoDB server could not be reached."""


URI = normalize_uri(config.MONGO_DB_URI)
DB_NAME = resolve_db_name(URI, config.MONGO_DB_NAME)

_mongo_async_: AsyncIOMotorClient | None = None
mongodb = None


def create_client(uri: str = URI) -> AsyncIOMotorClient:
    """Build a client for ``uri`` using the configured timeouts."""
    return AsyncIOMotorClient(
        uri,
        **build_client_kwargs(
            uri,
            timeout_ms=config.MONGO_TIMEOUT_MS,
            direct_connection=config.MONGO_DIRECT_CONNECTION,
        ),
    )


def _startup_error(reason: str) -> str:
    return (
        "MongoDB is not configured correctly.\n"
        f"  Reason : {reason}\n"
        "  Fix    : set MONGO_DB_URI in .env, for example\n"
        "             local : mongodb://127.0.0.1:27017\n"
        "             atlas : mongodb+srv://user:pass@cluster.mongodb.net/musicgalaxy\n"
        "  Check  : python3 dbcheck.py"
    )


def _connect_at_import() -> None:
    global _mongo_async_, mongodb

    if not URI:
        LOG.error(
            _startup_error("MONGO_DB_URI is empty (no .env found or the key is missing).")
        )
        raise SystemExit(1)

    if looks_like_placeholder(URI):
        LOG.error(
            _startup_error(
                "MONGO_DB_URI still contains the .env.example placeholder: "
                f"{sanitize_uri(URI)}"
            )
        )
        raise SystemExit(1)

    if (config.MONGO_DB_URI or "").strip() != URI:
        LOG.info(f"MONGO_DB_URI normalized to {sanitize_uri(URI)}")
    LOG.info(
        "Connecting to your Mongo Database "
        f"({describe_target(URI)}, database '{DB_NAME}')..."
    )
    try:
        _mongo_async_ = create_client()
        mongodb = _mongo_async_[DB_NAME]
    except Exception as exc:  # InvalidURI / ConfigurationError from the parser
        LOG.error(_startup_error(error_summary(exc)))
        for hint in error_hints(exc, URI):
            LOG.error(f"  Hint   : {hint}")
        raise SystemExit(1) from None


async def verify_connection(retries: int = 3, delay: float = 2.0):
    """Ping the server; raise ``MongoConnectionError`` with a readable report."""
    if _mongo_async_ is None or mongodb is None:
        _connect_at_import()

    assert _mongo_async_ is not None
    last_exc: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            await _mongo_async_.admin.command("ping")
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                LOG.warning(
                    "Mongo Database not reachable "
                    f"(attempt {attempt}/{retries}): {error_summary(exc)}. "
                    f"Retrying in {delay:g}s..."
                )
                await asyncio.sleep(delay)
                continue
        else:
            LOG.info(
                "Connected to your Mongo Database "
                f"({describe_target(URI)}, database '{DB_NAME}')."
            )
            return mongodb

    report = [
        "Failed to connect to your Mongo Database.",
        f"  Server : {describe_target(URI)}",
        f"  DB     : {DB_NAME}",
        f"  URI    : {sanitize_uri(URI)}",
        f"  Error  : {error_summary(last_exc) if last_exc else 'unknown error'}",
    ]
    hints = error_hints(last_exc, URI) if last_exc else []
    for hint in hints:
        report.append(f"  Hint   : {hint}")
    report.append("  Debug  : python3 dbcheck.py")
    raise MongoConnectionError("\n".join(report))


async def close_connection() -> None:
    if _mongo_async_ is not None:
        _mongo_async_.close()


_connect_at_import()

__all__ = [
    "MongoConnectionError",
    "close_connection",
    "mongodb",
    "verify_connection",
]
