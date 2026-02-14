# Quick Start

## Prerequisites

- Docker & Docker Compose
- [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just) (optional)
- OpenAI API key

## 1. Environment

```bash
cp envs/.env.rag.example envs/.env.rag
cp envs/.env.parser.example envs/.env.parser
cp envs/.env.postgres.example envs/.env.postgres
cp envs/.env.tui.example envs/.env.tui
```

Fill in `OPENAI_API_KEY` in `envs/.env.rag`. Other variables have working defaults for local development.

| Variable           | Default                                                    |
|--------------------|------------------------------------------------------------|
| `POSTGRES_URL`     | `postgresql://leetcode:leetcode@postgres:5432/leetcode`    |
| `QDRANT_URL`       | `http://qdrant:6333`                                       |
| `OPENAI_API_KEY`   | _(required)_                                               |
| `PARSER_BASE_URL`  | `http://parser:8000`                                       |
| `EMBEDDING_MODEL`  | `text-embedding-3-small`                                   |

## 2. Start all services

```bash
just up  # or: docker compose up -d --build
```

Starts RAG API (`:8000`), Parser (`:8001`), Qdrant (`:6333`), and PostgreSQL (`:5432`).

## 3. Health check

```bash
curl localhost:8000/health
```

```json
{"status": "ok", "postgres": true, "qdrant": true, "qdrant_points": 0}
```

## 4. Load a problem

```bash
curl -X POST localhost:8000/problems/load \
  -H "Content-Type: application/json" \
  -d '{"slug": "two-sum"}'
```

Pipeline: parser fetches problem via LeetCode GraphQL API, problem is saved to PostgreSQL, texts are chunked (2000 chars, 200 overlap), embedded via OpenAI, and stored in Qdrant.

## 5. Search

**Semantic search:**

```bash
curl -X POST localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "find two numbers that add up to target", "difficulty": "Easy", "limit": 5}'
```

All parameters except `query` are optional: `difficulty`, `tags`, `chunk_type`, `limit`.

**Filter by metadata:**

```bash
curl "localhost:8000/problems?difficulty=Easy&limit=10"
```

**Full problem text:**

```bash
curl localhost:8000/problems/1/statement
curl localhost:8000/problems/1/editorial
```

## 6. TUI

```bash
just tui
```

Interactive terminal UI for browsing and loading LeetCode problems.

## 7. Shutdown & cleanup

```bash
just down       # stop containers
just clean      # stop containers + delete images and .volumes/
```

## API docs

Swagger UI: http://localhost:8000/docs
