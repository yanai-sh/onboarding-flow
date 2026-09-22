# =========================================================================
# Stage 1: Builder
# =========================================================================
FROM python:3.14-slim AS builder

# Pull a pinned official uv binary for reproducible builds.
COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation and copy mode for container file mapping
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install dependencies first to maximize Docker layer caching
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy application source code and pyproject metadata
COPY . /app

# Install the project itself into the virtual environment without editable links.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# =========================================================================
# Stage 2: Runtime
# =========================================================================
FROM python:3.14-slim

WORKDIR /app

# Create a non-root system user for security best practices
RUN useradd --create-home --shell /bin/bash appuser

# Copy the virtual environment containing the packaged application.
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Prepend the virtual environment binaries to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Enforce least-privilege execution
USER appuser

# Cloud Run defaults to port 8080.
ENV PORT=8080
EXPOSE 8080

# Serve the package-level ASGI application.
CMD ["granian", "--interface", "asgi", "onboarding_flow.app:app", "--host", "0.0.0.0", "--port", "8080"]