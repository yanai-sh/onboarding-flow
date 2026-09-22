# syntax=docker/dockerfile:1

# =========================================================================
# Stage 1: Builder (BuildKit cache mounts — requires BuildKit / buildx)
# =========================================================================
FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.14@sha256:1025398289b62de8269e70c45b91ffa37c373f38118d7da036fb8bb8efc85d97 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# The build context is allowlisted in .dockerignore (package metadata + src/ only).
COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# =========================================================================
# Stage 2: Runtime
# =========================================================================
FROM python:3.14-slim

WORKDIR /app

RUN useradd --create-home --shell /usr/sbin/nologin appuser

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Image facts: how this application is served, true in every environment.
# Deployment-specific values (LOG_LEVEL, GRANIAN_WORKERS_KILL_TIMEOUT) have
# sane defaults here and are overridden by Terraform per environment.
#   - one worker: scale on Cloud Run replicas; the app owns one httpx client per process
#   - kill timeout under Cloud Run's 10s SIGTERM grace so lifespan shutdown runs
#   - no access log: Cloud Run records every request at the edge already
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    LOG_LEVEL=INFO \
    GRANIAN_HOST=0.0.0.0 \
    GRANIAN_INTERFACE=asgi \
    GRANIAN_WORKERS=1 \
    GRANIAN_WEBSOCKETS=false \
    GRANIAN_WORKERS_KILL_TIMEOUT=8s \
    GRANIAN_LOG_ACCESS_ENABLED=false

USER appuser

EXPOSE 8080

# Cloud Run injects PORT at runtime; Granian only reads GRANIAN_PORT, so it is
# the one value resolved by the shell. `exec` keeps Granian as PID 1 for signals.
CMD ["sh", "-c", "exec granian --port \"${PORT}\" onboarding_flow.app:app"]
