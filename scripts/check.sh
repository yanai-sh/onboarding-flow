#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Plain root (containers, CI sandboxes) is fine; sudo from a user checkout would
# leave root-owned files in .venv and the tool caches.
if [[ -n "${SUDO_USER:-}" ]]; then
  echo "error: run without sudo (it leaves root-owned files in .venv and caches)." >&2
  exit 1
fi

uv run ruff check src tests
uv run ruff format --check src tests
uv run ty check src tests
uv run pytest tests/unit "$@"
