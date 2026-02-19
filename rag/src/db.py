import uuid

import asyncpg
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    OptimizersConfigDiff,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from .config import settings
from .models import Chunk, Problem, ProblemListItem

COLLECTION = "leetcode"
VECTOR_DIM = 1536

pg_pool: asyncpg.Pool | None = None
qdrant: QdrantClient | None = None


async def init_pg() -> asyncpg.Pool:
    global pg_pool
    pg_pool = await asyncpg.create_pool(settings.POSTGRES_URL)
    async with pg_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS problems (
                problem_id   INTEGER PRIMARY KEY,
                slug         TEXT NOT NULL UNIQUE,
                title        TEXT NOT NULL,
                difficulty   TEXT NOT NULL,
                tags         TEXT[] DEFAULT '{}',
                statement    TEXT,
                editorial    TEXT,
                url          TEXT,
                created_at   TIMESTAMP DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_difficulty ON problems(difficulty);
            CREATE INDEX IF NOT EXISTS idx_tags ON problems USING GIN(tags);
            CREATE INDEX IF NOT EXISTS idx_slug ON problems(slug);
        """)
    return pg_pool


def init_qdrant() -> QdrantClient:
    global qdrant
    qdrant = QdrantClient(url=settings.QDRANT_URL)
    if not qdrant.collection_exists(COLLECTION):
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
            optimizers_config=OptimizersConfigDiff(memmap_threshold=1000),
        )
    qdrant.create_payload_index(COLLECTION, "difficulty", PayloadSchemaType.KEYWORD)
    qdrant.create_payload_index(COLLECTION, "tags", PayloadSchemaType.KEYWORD)
    qdrant.create_payload_index(COLLECTION, "chunk_type", PayloadSchemaType.KEYWORD)
    return qdrant


async def close_pg():
    global pg_pool
    if pg_pool:
        await pg_pool.close()
        pg_pool = None


def close_qdrant():
    global qdrant
    if qdrant:
        qdrant.close()
        qdrant = None


# ── PostgreSQL operations ──


async def upsert_problem(p: Problem):
    assert pg_pool is not None
    async with pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO problems (problem_id, slug, title, difficulty, tags,
                                  statement, editorial, url)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            ON CONFLICT (problem_id) DO UPDATE SET
                slug       = EXCLUDED.slug,
                title      = EXCLUDED.title,
                difficulty = EXCLUDED.difficulty,
                tags       = EXCLUDED.tags,
                statement  = EXCLUDED.statement,
                editorial  = EXCLUDED.editorial,
                url        = EXCLUDED.url
            """,
            p.problem_id,
            p.slug,
            p.title,
            p.difficulty,
            p.tags,
            p.statement,
            p.editorial,
            p.url,
        )


async def get_problems(
    difficulty: str | None = None,
    tags: list[str] | None = None,
    limit: int = 50,
) -> list[ProblemListItem]:
    conditions = []
    args: list = []
    idx = 1

    if difficulty is not None:
        conditions.append(f"difficulty = ${idx}")
        args.append(difficulty)
        idx += 1
    if tags:
        conditions.append(f"tags && ${idx}")
        args.append(tags)
        idx += 1

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    query = f"SELECT problem_id, slug, title, difficulty, tags, url FROM problems{where} ORDER BY problem_id LIMIT ${idx}"
    args.append(limit)

    assert pg_pool is not None
    async with pg_pool.acquire() as conn:
        rows = await conn.fetch(query, *args)

    return [
        ProblemListItem(
            problem_id=r["problem_id"],
            slug=r["slug"],
            title=r["title"],
            difficulty=r["difficulty"],
            tags=list(r["tags"]) if r["tags"] else [],
            url=r["url"],
        )
        for r in rows
    ]


async def get_loaded_slugs() -> list[str]:
    assert pg_pool is not None
    async with pg_pool.acquire() as conn:
        rows = await conn.fetch("SELECT slug FROM problems ORDER BY problem_id")
    return [r["slug"] for r in rows]


async def get_problem_text(problem_id: int, field: str) -> dict | None:
    if field not in ("statement", "editorial"):
        return None
    assert pg_pool is not None
    async with pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            f"SELECT problem_id, title, {field} AS text FROM problems WHERE problem_id = $1",
            problem_id,
        )
    if not row:
        return None
    return {"problem_id": row["problem_id"], "title": row["title"], "text": row["text"]}


# ── Qdrant operations ──


def qdrant_upsert_chunks(chunks: list[Chunk], vectors: list[list[float]]):
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={
                "problem_id": c.problem_id,
                "title": c.title,
                "difficulty": c.difficulty,
                "tags": c.tags,
                "chunk_type": c.chunk_type,
                "text": c.text[:500],
            },
        )
        for c, vec in zip(chunks, vectors)
    ]
    assert qdrant is not None
    qdrant.upsert(collection_name=COLLECTION, points=points)


def qdrant_search(
    vector: list[float],
    difficulty: str | None = None,
    tags: list[str] | None = None,
    chunk_type: str | None = None,
    limit: int = 10,
) -> list[dict]:
    must = []
    if difficulty:
        must.append(FieldCondition(key="difficulty", match=MatchValue(value=difficulty)))
    if tags:
        must.append(FieldCondition(key="tags", match=MatchAny(any=tags)))
    if chunk_type:
        must.append(FieldCondition(key="chunk_type", match=MatchValue(value=chunk_type)))

    q_filter = Filter(must=must) if must else None

    assert qdrant is not None
    hits = qdrant.query_points(
        collection_name=COLLECTION,
        query=vector,
        query_filter=q_filter,
        limit=limit,
        with_payload=True,
    ).points

    results = []
    for h in hits:
        p = h.payload
        if p is None:
            continue
        results.append(
            {
                "problem_id": p["problem_id"],
                "title": p["title"],
                "difficulty": p.get("difficulty", ""),
                "tags": p.get("tags", []),
                "score": h.score,
                "snippet": p.get("text", ""),
            }
        )
    return results
