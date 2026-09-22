#!/usr/bin/env bash
# Tier-2 packaging smoke: build OCI image and hit /health (requires Docker + buildx).
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
  echo "error: do not run with sudo (uv and docker group are per-user)." >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv not found on PATH." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "error: docker not found. See docs/runbook-dev-environment.md." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "error: docker daemon not reachable. Log in to WSL anew after usermod -aG docker." >&2
  exit 1
fi

export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

uv run pytest tests/integration -m container "$@"
