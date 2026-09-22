#!/usr/bin/env bash
# Container smoke: build the image for the native platform, run it on a
# non-default $PORT, and check /health plus a network-free POST /vehicle-info
# (a malformed plate is rejected before any upstream call).
set -euo pipefail
cd "$(dirname "$0")/.."

IMAGE="${IMAGE:-onboarding-flow:smoke}"
PORT=9090

command -v curl >/dev/null || { echo "error: curl not found" >&2; exit 1; }
docker buildx version >/dev/null || { echo "error: docker buildx (BuildKit) required" >&2; exit 1; }

docker buildx build --load --tag "$IMAGE" .

cid="$(docker run --detach -e PORT="$PORT" -p "127.0.0.1::$PORT" "$IMAGE")"
trap 'docker rm --force "$cid" >/dev/null 2>&1 || true' EXIT
base="http://$(docker port "$cid" "$PORT/tcp")"

fail() {
  echo "error: $*" >&2
  docker logs "$cid" >&2 || true
  exit 1
}

for attempt in $(seq 60); do
  [[ "$(curl -fsS --max-time 2 "$base/health" 2>/dev/null)" == *'"status":"ok"'* ]] && break
  ((attempt < 60)) || fail "/health did not answer on PORT=$PORT within 30s"
  sleep 0.5
done

out="$(curl -sS --max-time 10 -w '\n%{http_code} %{content_type}' \
  -H 'Content-Type: application/json' -d '{"license_plate":"12-3"}' "$base/vehicle-info")" \
  || fail "POST /vehicle-info request failed"
meta="${out##*$'\n'}"
body="${out%$'\n'*}"
[[ "$meta" == "200 application/json"* ]] || fail "POST /vehicle-info: expected 200 JSON, got '$meta'"
[[ "$body" == *'"error_code":"INVALID_REQUEST"'* ]] \
  || fail "POST /vehicle-info: expected INVALID_REQUEST, got $body"

echo "ok: $IMAGE serves /health and POST /vehicle-info on PORT=$PORT"
