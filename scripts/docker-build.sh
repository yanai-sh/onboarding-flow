#!/usr/bin/env bash
# Build the service image with docker buildx (BuildKit), not the legacy builder.
set -euo pipefail

usage() {
  echo "Usage: $0 [--push] IMAGE [PLATFORM]" >&2
  echo "  IMAGE     Full tag, e.g. us-central1-docker.pkg.dev/PROJECT/onboarding-flow/onboarding-flow:latest" >&2
  echo "  PLATFORM  Default linux/amd64 (Cloud Run). Use linux/arm64 for native local smoke." >&2
  exit 1
}

PUSH=0
if [[ "${1:-}" == --push ]]; then
  PUSH=1
  shift
fi

IMAGE="${1:-}"
PLATFORM="${2:-linux/amd64}"
[[ -n "$IMAGE" ]] || usage

if ! command -v docker >/dev/null 2>&1; then
  echo "error: docker not found" >&2
  exit 1
fi
if ! docker buildx version >/dev/null 2>&1; then
  echo "error: docker buildx required (sudo dnf install -y docker-buildx)" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILDER_NAME="onboarding-flow-buildx"

if ! docker buildx inspect "$BUILDER_NAME" >/dev/null 2>&1; then
  docker buildx create --name "$BUILDER_NAME" --driver docker-container --use
else
  docker buildx use "$BUILDER_NAME"
fi
docker buildx inspect --bootstrap

cd "$ROOT"
BUILD_OPTS=(--platform "$PLATFORM" --provenance=false --sbom=false --tag "$IMAGE")
if [[ "$PUSH" -eq 1 ]]; then
  docker buildx build "${BUILD_OPTS[@]}" --push .
else
  docker buildx build "${BUILD_OPTS[@]}" --load .
fi
