#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
  echo "error: do not run this script with sudo." >&2
  echo "  uv and the project .venv live in your user account (~/.local/bin, .venv)." >&2
  echo "  Run: bash scripts/check.sh" >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv not found on PATH." >&2
  echo "  Install: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

uv run ruff check src tests
uv run ruff format --check src tests
uv run ty check src tests
uv run pytest tests/unit "$@"
