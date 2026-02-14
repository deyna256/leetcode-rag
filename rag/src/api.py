from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query

from . import db
from .embedder import embed_texts
from .indexer import index_problem
from .models import LoadProblemRequest, ProblemListItem, SearchRequest, SearchResult
from .parser_client import fetch_problem


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pg()
    db.init_qdrant()
    yield
    db.close_qdrant()
    await db.close_pg()


app = FastAPI(title="LeetCode RAG", lifespan=lifespan)


@app.get("/health")
async def health():
    pg_ok = False
    qdrant_ok = False
    qdrant_points = 0
    try:
        if db.pg_pool is not None:
            async with db.pg_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            pg_ok = True
    except Exception:
        pass
    try:
        if db.qdrant is not None:
            info = db.qdrant.get_collection(db.COLLECTION)
            qdrant_ok = True
            qdrant_points = info.points_count
    except Exception:
        pass
    status = "ok" if (pg_ok and qdrant_ok) else "degraded"
    return {
        "status": status,
        "postgres": pg_ok,
        "qdrant": qdrant_ok,
        "qdrant_points": qdrant_points,
    }


@app.post("/problems/load")
async def load_problem(body: LoadProblemRequest):
    pp = await fetch_problem(body.slug)
    problem_id = await index_problem(pp)
    return {"problem_id": problem_id, "title": pp.title}


@app.post("/search", response_model=list[SearchResult])
async def search(req: SearchRequest):
    vectors = embed_texts([req.query])
    hits = db.qdrant_search(
        vector=vectors[0],
        difficulty=req.difficulty,
        tags=req.tags,
        chunk_type=req.chunk_type,
        limit=req.limit,
    )
    return hits


@app.get("/problems", response_model=list[ProblemListItem])
async def list_problems(
    difficulty: str | None = Query(None),
    tags: list[str] | None = Query(None),
    limit: int = Query(50, le=200),
):
    return await db.get_problems(
        difficulty=difficulty,
        tags=tags,
        limit=limit,
    )


@app.get("/problems/slugs", response_model=list[str])
async def loaded_slugs():
    return await db.get_loaded_slugs()


@app.get("/problems/{problem_id}/statement")
async def problem_statement(problem_id: int):
    result = await db.get_problem_text(problem_id, "statement")
    if not result:
        raise HTTPException(404, "Problem not found")
    return result


@app.get("/problems/{problem_id}/editorial")
async def problem_editorial(problem_id: int):
    result = await db.get_problem_text(problem_id, "editorial")
    if not result:
        raise HTTPException(404, "Problem not found")
    return result
