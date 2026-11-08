import json
import logging

import asyncpg

from config import DATABASE_URL

from ..logging import LOGGER

log = logging.getLogger(__name__)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS bot_kv (
    id SERIAL PRIMARY KEY,
    collection TEXT NOT NULL,
    doc JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS bot_kv_collection_idx ON bot_kv (collection);
CREATE INDEX IF NOT EXISTS bot_kv_doc_gin_idx ON bot_kv USING GIN (doc);
"""

_pool = None


async def _ensure_pool():
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set in your environment (.env).")
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
        async with _pool.acquire() as conn:
            await conn.execute(CREATE_TABLE)
    return _pool


async def connect():
    log.info("Connecting to your PostgreSQL Database...")
    try:
        pool = await _ensure_pool()
        mongodb = Database()
        log.info("Connected to your PostgreSQL Database.")
        return mongodb
    except Exception:
        log.exception("Failed to connect to your PostgreSQL Database.")
        raise


class _Cursor:
    """Async cursor mirroring motor's AsyncIOMotorCursor (find / to_list)."""

    def __init__(self, collection, filter):
        self.collection = collection
        self.filter = filter
        self._rows = []
        self._index = 0
        self._fetched = False

    async def _ensure(self):
        if self._fetched:
            return
        self._fetched = True
        pool = await _ensure_pool()
        eq, ops = _split_filter(self.filter)
        if eq:
            sql = (
                "SELECT doc FROM bot_kv "
                "WHERE collection = $1 AND doc @> $2::jsonb"
            )
            params = [self.collection, json.dumps(eq, default=str)]
        else:
            sql = "SELECT doc FROM bot_kv WHERE collection = $1"
            params = [self.collection]
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
        self._rows = [json.loads(r["doc"]) for r in rows]
        self._rows = [d for d in self._rows if _match(d, ops)]

    def __aiter__(self):
        return self

    async def __anext__(self):
        await self._ensure()
        if self._index >= len(self._rows):
            raise StopAsyncIteration
        doc = self._rows[self._index]
        self._index += 1
        return doc

    async def to_list(self, length=None):
        await self._ensure()
        if length is None:
            return list(self._rows)
        return self._rows[:length]


class Collection:
    """Motor-compatible collection backed by PostgreSQL JSONB."""

    def __init__(self, collection):
        self.collection = collection

    async def _pool(self):
        return await _ensure_pool()

    async def find_one(self, filter):
        eq, ops = _split_filter(filter)
        if eq:
            sql = (
                "SELECT doc FROM bot_kv "
                "WHERE collection = $1 AND doc @> $2::jsonb LIMIT 1"
            )
            params = [self.collection, json.dumps(eq, default=str)]
        else:
            sql = "SELECT doc FROM bot_kv WHERE collection = $1 LIMIT 1"
            params = [self.collection]
        pool = await self._pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(sql, *params)
        if not row:
            return None
        doc = json.loads(row["doc"])
        return doc if _match(doc, ops) else None

    async def insert_one(self, doc):
        pool = await self._pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO bot_kv (collection, doc) VALUES ($1, $2::jsonb)",
                self.collection,
                json.dumps(doc, default=str),
            )

    async def update_one(self, filter, update, upsert=False):
        eq, ops = _split_filter(filter)
        set_ops = update.get("$set", {}) if isinstance(update, dict) else {}
        if eq:
            where_sql = "WHERE collection = $1 AND doc @> $2::jsonb"
            params = [self.collection, json.dumps(eq, default=str)]
        else:
            where_sql = "WHERE collection = $1"
            params = [self.collection]
        modified = False
        if set_ops:
            sql = f"UPDATE bot_kv SET doc = doc || $3::jsonb {where_sql}"
            pool = await self._pool()
            async with pool.acquire() as conn:
                result = await conn.execute(
                    sql, *params, json.dumps(set_ops, default=str)
                )
            modified = result.split()[-1] != "0"
        if not modified and upsert:
            new_doc = {}
            new_doc.update(eq)
            new_doc.update(set_ops)
            await self.insert_one(new_doc)
            modified = True
        return _UpdateResult(matched_count=1 if modified else 0, modified_count=int(modified))

    async def delete_one(self, filter):
        eq, ops = _split_filter(filter)
        if eq:
            sql = "DELETE FROM bot_kv WHERE collection = $1 AND doc @> $2::jsonb"
            params = [self.collection, json.dumps(eq, default=str)]
        else:
            sql = "DELETE FROM bot_kv WHERE collection = $1"
            params = [self.collection]
        pool = await self._pool()
        async with pool.acquire() as conn:
            result = await conn.execute(sql, *params)
        return _DeleteResult(deleted_count=int(result.split()[-1]))

    def find(self, filter):
        return _Cursor(self.collection, filter)


class _UpdateResult:
    def __init__(self, matched_count, modified_count):
        self.matched_count = matched_count
        self.modified_count = modified_count


class _DeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


class Database:
    """Motor-compatible database handle; attribute access returns a Collection."""

    async def command(self, cmd, *args, **kwargs):
        if cmd == "dbstats":
            return await _dbstats()
        return {}

    async def close(self):
        global _pool
        if _pool is not None:
            await _pool.close()
            _pool = None

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return Collection(name)


async def _dbstats():
    pool = await _ensure_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM bot_kv")
        collections = await conn.fetchval(
            "SELECT COUNT(DISTINCT collection) FROM bot_kv"
        )
    return {
        "dataSize": 0,
        "storageSize": 0,
        "collections": int(collections or 0),
        "objects": int(count or 0),
    }


def _split_filter(filter):
    eq = {}
    ops = {}
    for key, val in (filter or {}).items():
        if isinstance(val, dict) and any(k in val for k in ("$gt", "$gte", "$lt", "$lte")):
            ops[key] = val
        else:
            eq[key] = val
    return eq, ops


def _match(doc, ops):
    for key, spec in ops.items():
        actual = doc.get(key)
        if actual is None:
            return False
        try:
            actual = float(actual)
        except (TypeError, ValueError):
            return False
        for op, val in spec.items():
            try:
                val = float(val)
            except (TypeError, ValueError):
                return False
            if op == "$gt" and not actual > val:
                return False
            if op == "$gte" and not actual >= val:
                return False
            if op == "$lt" and not actual < val:
                return False
            if op == "$lte" and not actual <= val:
                return False
    return True


mongodb = Database()
