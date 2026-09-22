# syntax=docker/dockerfile:1

# =========================================================================
# Stage 1: Builder (BuildKit cache mounts — requires BuildKit / buildx)
# =========================================================================
FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# =========================================================================
# Stage 2: Runtime
# =========================================================================
FROM python:3.14-slim

WORKDIR /app

RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "exec granian --interface asgi onboarding_flow.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
