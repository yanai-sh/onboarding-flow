#!/usr/bin/env bash
# Build the service image with docker buildx (BuildKit), not the legacy builder.
# Used locally and by cloudbuild.yaml, so the build flags live in one place.
set -euo pipefail

usage() {
  echo "Usage: $0 [--push] IMAGE [PLATFORM]" >&2
  echo "  IMAGE     Full tag, e.g. us-central1-docker.pkg.dev/PROJECT/onboarding-flow/onboarding-flow:SHA" >&2
  echo "  PLATFORM  Default linux/amd64 (Cloud Run). Use linux/arm64 for a native aarch64 build." >&2
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

docker buildx version >/dev/null || { echo "error: docker buildx (BuildKit) required" >&2; exit 1; }

cd "$(dirname "$0")/.."
BUILDER_NAME="onboarding-flow-buildx"

if ! docker buildx inspect "$BUILDER_NAME" >/dev/null 2>&1; then
  docker buildx create --name "$BUILDER_NAME" --driver docker-container --use
else
  docker buildx use "$BUILDER_NAME"
fi
docker buildx inspect --bootstrap

BUILD_OPTS=(--platform "$PLATFORM" --provenance=false --sbom=false --tag "$IMAGE")
if [[ "$PUSH" -eq 1 ]]; then
  docker buildx build "${BUILD_OPTS[@]}" --push .
else
  docker buildx build "${BUILD_OPTS[@]}" --load .
fi
