# Project Structure

## Module dependency graph

```
                         ┌───────────┐
                         │  api.py   │
                         └─────┬─────┘
              ┌────────────┬───┼───┬────────────┐
              ▼            ▼   │   ▼            ▼
        ┌──────────┐ ┌────────┐│┌─────────┐┌───────────────┐
        │models.py │ │ db.py  │││embedder. ││parser_client. │
        └──────────┘ └───┬────┘││  py      ││    py         │
              ▲      ▲   │    ▼▼└────┬────┘└──────┬────────┘
              │      │   │ ┌──────────┐    │      │
              │      │   │ │indexer.py │◄───┘      │
              │      │   │ └─────┬────┘           │
              │      │   │    ┌──┴──┐              │
              │      │   │    ▼     ▼              │
              │      │   │ ┌─────────────┐         │
              │      │   │ │ chunker.py  │         │
              │      │   │ └──────┬──────┘         │
              │      │   │        │                │
              │      ├───┼────────┘                │
              │      │   ▼                         ▼
              │  ┌───────────┐              ┌───────────┐
              └──│ config.py │              │  parser/  │
                 └───────────┘              └───────────┘
                      │
                      ▼
                    .env
```

All modules live in `rag/src/`. Parser is a separate service in `parser/`.

## Modules

### `config.py`

Settings via `pydantic-settings`. Looks for `.env` in both current dir and parent (`".env", "../.env"`), so it works from `rag/` or repo root.

### `models.py`

Pydantic data models. No internal dependencies.

| Model             | Purpose                              |
|-------------------|--------------------------------------|
| `ParserProblem`   | Problem from parser response         |
| `Problem`         | Problem stored in DB                 |
| `Chunk`           | Text fragment for indexing           |
| `SearchRequest`   | POST /search body                    |
| `SearchResult`    | Search response item                 |
| `ProblemListItem` | GET /problems response item          |
| `LoadProblemRequest` | POST /problems/load body          |

### `db.py`

Data access layer for PostgreSQL (asyncpg) and Qdrant.

- `init_pg()` / `close_pg()` — connection pool + `problems` table
- `upsert_problem(problem)` — INSERT ... ON CONFLICT DO UPDATE
- `get_problems(filters)` — filtered SELECT
- `get_problem_text(problem_id, field)` — full statement or editorial
- `init_qdrant()` / `close_qdrant()` — client + `leetcode` collection (1536 dim, cosine)
- `qdrant_upsert_chunks(chunks, vectors)` — upsert points with payload
- `qdrant_search(vector, filters)` — semantic search with payload filters

### `embedder.py`

OpenAI Embeddings API wrapper. Batches requests (100 texts per call).

- `embed_texts(texts) -> list[list[float]]`

### `chunker.py`

Splits problem texts into indexable chunks (2000 chars, 200 overlap). Produces `statement` and `editorial` chunk types.

- `chunk_problem(problem) -> list[Chunk]`

### `parser_client.py`

HTTP client for the parser service (`parser/`).

- `fetch_problem(slug) -> ParserProblem`

### `indexer.py`

Problem indexing pipeline: maps parser response to problem, upserts to PostgreSQL, chunks texts, embeds via OpenAI, upserts to Qdrant.

- `index_problem(parser_problem) -> int`

### `api.py`

FastAPI app. Entry point: `src.api:app`.

| Endpoint                           | Method | Description                  |
|------------------------------------|--------|------------------------------|
| `/health`                          | GET    | DB connectivity check        |
| `/problems/load`                   | POST   | Load and index a problem     |
| `/search`                          | POST   | Semantic search              |
| `/problems`                        | GET    | Filter problems by metadata  |
| `/problems/{problem_id}/statement` | GET    | Full problem statement       |
| `/problems/{problem_id}/editorial` | GET    | Full editorial               |

## Docker services

```
docker-compose.yml
├── api:8000         — RAG API (build: ./rag)
├── parser:8001      — LeetCode parser (build: ./parser)
├── qdrant:6333      — vector DB
└── postgres:5432    — relational DB
```
