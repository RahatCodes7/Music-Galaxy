"""Pure helpers shared by the bot and by ``dbcheck.py``.

Nothing in here talks to the network, so it is safe to import from a plain
script (``python3 dbcheck.py``) without booting pyrogram.  ``MusicGalaxy/core/
mongo.py`` uses the same helpers for the real client, which keeps the
diagnostic tool and the bot behaviour in sync.
"""

from __future__ import annotations

import os
import re
from typing import Dict, List
from urllib.parse import unquote, urlsplit

DEFAULT_DB_NAME = "MusicGalaxy"

# Hosts that mean "the mongod on this machine".  Atlas / docker hostnames are
# never rewritten.
_LOOPBACK_ALIASES = {"localhost": "127.0.0.1"}

# Values that are copied from .env.example and never edited.
_PLACEHOLDERS = (
    "your_mongodb_uri",
    "user:password@cluster.mongodb.net",
    "<username>",
    "mongodb_uri_here",
)

_CREDENTIALS_RE = re.compile(r"^(?P<scheme>mongodb(?:\+srv)?://)[^@/]+@", re.IGNORECASE)

_ERROR_HINTS = {
    "connection refused": (
        "Nothing is listening on the port, so MongoDB itself is not running.",
        "Start it:   sudo systemctl start mongod   (Linux)"
        "  |  brew services start mongodb-community  (macOS)",
        "Check it:   sudo systemctl status mongod  |  ss -ltnp | grep 27017",
        "In Docker:  the host is 'mongo' (service name), not 127.0.0.1.",
    ),
    "authentication failed": (
        "The username/password were rejected by the server.",
        "Add authSource when the user lives in the admin db:"
        "  ?authSource=admin",
        "Escape special characters in the password with"
        " python3 -c \"import urllib.parse,sys;print(urllib.parse.quote_plus(sys.argv[1]))\" 'p@ss'",
    ),
    "escaped according to rfc 3986": (
        "The password contains characters that must be URL encoded (@ : / # ? % &).",
        "Encode it:  python3 -c \"import urllib.parse,sys;print(urllib.parse.quote_plus(sys.argv[1]))\" 'p@ss'",
    ),
    "no servers found": (
        "The +srv DNS lookup failed or the Atlas cluster is paused/unreachable.",
        "Atlas free clusters pause after 60 days of inactivity - resume it in the dashboard.",
    ),
    "replicasetno": (
        "The server is a replica set member, but the driver cannot see the set.",
        "For a single local node add ?directConnection=true "
        "(or set MONGO_DIRECT_CONNECTION=true).",
    ),
    "ssl": (
        "TLS negotiation failed.",
        "Local mongod usually has TLS off - use mongodb:// (not mongodb+srv://) "
        "for a local server and do not pass tls=true.",
    ),
    "timed out": (
        "The connection attempt timed out (firewall, wrong port or sleeping host).",
        "Raise the wait time with MONGO_TIMEOUT_MS=15000 while debugging.",
    ),
}

_LOCAL_HINT = (
    "Local server: mongod must be running and listening on 27017 "
    "(sudo systemctl start mongod, or docker start <mongo-container>)."
)


def env(name: str, default: str = "") -> str:
    """os.getenv plus the cleanup people forget: spaces, quotes, empties."""
    value = os.getenv(name, default)
    if value is None:
        return default
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1].strip()
    return value


def env_int(name: str, default: int) -> int:
    try:
        return int(env(name, str(default)) or default)
    except (TypeError, ValueError):
        return default


def sanitize_uri(uri: str) -> str:
    """Hide ``user:password@`` so URIs can be written to log.txt safely."""
    if not uri:
        return "<not set>"
    return _CREDENTIALS_RE.sub(lambda m: f"{m.group('scheme')}***:***@", uri.strip())


def looks_like_placeholder(uri: str) -> bool:
    lowered = (uri or "").lower()
    return any(marker in lowered for marker in _PLACEHOLDERS)


def _split_authority(uri: str):
    scheme, _, rest = uri.partition("://")
    authority, sep, tail = rest.partition("/")
    return scheme, authority, sep, tail


def normalize_uri(uri: str) -> str:
    """Clean up the value that came from the environment / .env file.

    Handles the mistakes that are easy to make by hand: surrounding quotes and
    whitespace, a missing ``mongodb://`` scheme and ``localhost`` pointing at
    IPv6 while mongod only listens on IPv4.
    """
    uri = (uri or "").strip()
    if len(uri) >= 2 and uri[0] == uri[-1] and uri[0] in "\"'":
        uri = uri[1:-1].strip()
    if not uri:
        return ""
    if not uri.lower().startswith(("mongodb://", "mongodb+srv://")):
        uri = "mongodb://" + uri
    if uri.lower().startswith("mongodb+srv://"):
        return uri
    scheme, authority, sep, tail = _split_authority(uri)
    # only touch the host part: a password may legitimately contain "localhost"
    credentials, at, hosts = authority.rpartition("@")
    if not at:
        credentials, hosts = "", authority
    for alias, target in _LOOPBACK_ALIASES.items():
        if alias in hosts.lower():
            hosts = re.sub(alias, target, hosts, flags=re.IGNORECASE)
    return f"{scheme}://{credentials}{at}{hosts}{sep}{tail}"


def has_credentials(uri: str) -> bool:
    return bool(_CREDENTIALS_RE.match(uri or ""))


def host_list(uri: str) -> List[str]:
    """Return ``['127.0.0.1:27017']`` style hosts without credentials."""
    if "://" not in (uri or ""):
        return []
    _, authority, _, _ = _split_authority(uri)
    if "@" in authority:
        authority = authority.rsplit("@", 1)[1]
    return [host for host in authority.split(",") if host]


def describe_target(uri: str) -> str:
    hosts = host_list(uri)
    return ", ".join(hosts) if hosts else "<no host>"


def is_local(uri: str) -> bool:
    return any(
        host.split(":")[0].strip("[]") in {"127.0.0.1", "::1", "localhost"}
        for host in host_list(uri)
    )


def resolve_db_name(uri: str, override: str = "") -> str:
    """Pick the database the bot writes into.

    ``mongodb://host:27017/musicgalaxy`` -> ``musicgalaxy``
    ``mongodb://host:27017``             -> ``MusicGalaxy`` (default)
    ``mongodb://user:pass@host/admin``   -> ``admin`` is the auth database, so
                                            keep the default app database.
    """
    override = (override or "").strip()
    if override:
        return override
    if "://" not in (uri or ""):
        return DEFAULT_DB_NAME
    path = (urlsplit(uri).path or "").lstrip("/")
    candidate = unquote(path.split("/")[0])
    if not candidate:
        return DEFAULT_DB_NAME
    if candidate == "admin" and has_credentials(uri):
        return DEFAULT_DB_NAME
    return candidate


def build_client_kwargs(
    uri: str,
    timeout_ms: int = 8000,
    direct_connection: bool = False,
) -> Dict[str, object]:
    """Driver options, without overriding anything the user set in the URI."""
    kwargs: Dict[str, object] = {"appname": "MusicGalaxy"}
    lowered = (uri or "").lower()
    if "serverselectiontimeoutms" not in lowered:
        kwargs["serverSelectionTimeoutMS"] = timeout_ms
    if "connecttimeoutms" not in lowered:
        kwargs["connectTimeoutMS"] = timeout_ms
    if direct_connection and "directconnection" not in lowered:
        kwargs["directConnection"] = True
    return kwargs


def error_summary(exc: BaseException) -> str:
    """One compact line: the driver message minus the giant topology dump."""
    text = " ".join(str(exc).split())
    for marker in (", Timeout:", " Topology Description:", " (configured timeouts"):
        index = text.find(marker)
        if index != -1:
            text = text[:index]
    name = type(exc).__name__
    return f"{name}: {text[:400]}" if text else name


def error_hints(exc: BaseException, uri: str) -> List[str]:
    name = type(exc).__name__.lower()
    message = str(exc).lower()
    hints: List[str] = []
    for marker, marker_hints in _ERROR_HINTS.items():
        if marker in message or marker in name:
            hints.extend(marker_hints)
    if "serverselectiontimeout" in name and not hints:
        hints.extend(_ERROR_HINTS["timed out"])
    if is_local(uri) and not hints:
        hints.append(_LOCAL_HINT)
    if looks_like_placeholder(uri):
        hints.insert(0, "MONGO_DB_URI still holds the .env.example placeholder - set the real URI.")
    return hints
