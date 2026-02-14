FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_DEV=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies first (cached separately from code changes)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy source and install the project itself
COPY src/ src/
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Runtime stage — no uv, no build tools
FROM python:3.12-slim

ENV PATH="/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY --from=builder /app/.venv .venv
COPY src/ src/

EXPOSE 8000
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0"]
