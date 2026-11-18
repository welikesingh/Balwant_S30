# SENTINEL Investigator Assistant - production image.
#
# Two stages keep the image small:
#   1. builder: uv installs ONLY the runtime dependencies (no pytest, pandas, matplotlib)
#      into /app/.venv straight from uv.lock.
#   2. runtime: a clean python slim image receives just that venv and the app/ package.
#      No uv, no build tools, no tests, no evaluation data and no .env end up in it.
#
# Secrets are never baked in: pass them at run time with  docker run --env-file .env

# ---------- stage 1: build the virtual environment ----------
FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.2 /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=0 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app
COPY pyproject.toml uv.lock ./

# --no-default-groups drops the dev (pytest) and tools (pandas, matplotlib) groups.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-default-groups --no-install-project \
 && find /app/.venv -type d \( -name "__pycache__" -o -name "tests" \) -prune -exec rm -rf {} + \
 && find /app/.venv -name "*.pyi" -delete

# ---------- stage 2: minimal runtime ----------
FROM python:3.12-slim-bookworm AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 sentinel
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY app ./app

USER sentinel
EXPOSE 8000

# /health checks Supabase, Neo4j and Qdrant, so keep the interval relaxed.
HEALTHCHECK --interval=60s --timeout=15s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=10).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
