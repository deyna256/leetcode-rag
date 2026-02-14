# List available commands
default:
    @just --list

# Build and start all services
up:
    docker compose up -d --build

# Stop all services
down:
    docker compose down

# Stop services and remove volumes
clean:
    docker compose down --rmi local
    rm -rf .volumes

# Run all tests
test:
    @printf '\033[1;36m%s\033[0m\n' '● Running tests: parser'
    cd parser && uv run pytest
    @printf '\033[1;36m%s\033[0m\n' '● Running tests: rag'
    cd rag && uv run pytest

# Check code style (ruff check)
style:
    @printf '\033[1;36m%s\033[0m\n' '● Checking style: parser'
    cd parser && uv run ruff check .
    @printf '\033[1;36m%s\033[0m\n' '● Checking style: rag'
    cd rag && uv run ruff check .

# Type checking (ty)
type:
    @printf '\033[1;36m%s\033[0m\n' '● Type checking: parser'
    cd parser && uv run ty check
    @printf '\033[1;36m%s\033[0m\n' '● Type checking: rag'
    cd rag && uv run ty check

# Launch TUI for loading problems
tui:
    set -a && . envs/.env.tui && set +a && cd tui && uv run python -m src.app

# Format code (ruff format)
format:
    @printf '\033[1;36m%s\033[0m\n' '● Formatting: parser'
    cd parser && uv run ruff format .
    @printf '\033[1;36m%s\033[0m\n' '● Formatting: rag'
    cd rag && uv run ruff format .
