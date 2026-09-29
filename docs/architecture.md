# Proxy architecture

I built a small stateless service between the Insait conversation flow and the supplied
vehicle-information endpoint. Its job is to give the flow one predictable response shape for
successful lookups, invalid plates, and expected upstream failures.

## Live service

- Service: <https://onboarding-flow-2q2x6qga6a-uc.a.run.app>
- Swagger: <https://onboarding-flow-2q2x6qga6a-uc.a.run.app/schema/swagger>
- OpenAPI: <https://onboarding-flow-2q2x6qga6a-uc.a.run.app/schema/openapi.json>

The service scales to zero, so the first request after a quiet period can take a few seconds.

```bash
URL=https://onboarding-flow-2q2x6qga6a-uc.a.run.app
curl -sS "$URL/vehicle-info" \
  -H 'Content-Type: application/json' \
  -d '{"license_plate":"123-45-678"}'
```

## Request and response contract

`POST /vehicle-info` accepts:

```json
{"license_plate": "123-45-678"}
```

I remove surrounding whitespace and the separators space, `-`, and `.`, then require 7 or 8
ASCII digits. The normalized value is sent upstream and also validates a successful upstream
response.

Every applicant-facing lookup outcome returns HTTP 200:

```text
{
  success: bool,
  data: {license_plate, manufacturer, model, year, color} | null,
  error_code: ErrorCode | null,
  message: str | null,
  trace_id: str
}
```

| Condition | Result |
|---|---|
| Valid upstream success | `success: true` with vehicle data |
| Plate breaks the rule | `INVALID_REQUEST`; the upstream is not called |
| Upstream 400 or 422 | `INVALID_REQUEST` |
| Upstream not-found body on 200 or 404 | `VEHICLE_NOT_FOUND` |
| Total budget or httpx timeout | `UPSTREAM_TIMEOUT` |
| Network failure or unexpected status | `UPSTREAM_UNAVAILABLE` |
| Unreadable or invalid success body | `UPSTREAM_INVALID_RESPONSE` |

Malformed JSON, a missing field, a non-string plate, or a string over 32 characters returns
framework HTTP 400 because it indicates an integration bug rather than applicant input.
Unexpected application bugs retain Litestar's default HTTP 500 response.

## Key decisions

### Stable, speakable failures

I return expected lookup failures in the same typed envelope as success so the Insait API node
can route on `error_code` and say something useful. Static messages never include request data.

### One bounded call

Each lookup makes at most one upstream request. A five-second total budget covers connect, send,
and the complete response body. I deliberately do not retry automatically while an applicant is
waiting; the flow can offer one explicit retry instead.

### Minimal runtime stack

I use one outbound HTTP stack (`httpx`) and one logging pipeline (stdlib JSON logging).
Dependencies are wired once in the Litestar lifespan, and handlers receive the upstream port
through application state.

### PII-safe observability

Every request gets a validated caller trace ID or a generated UUIDv7. Logs contain the trace ID
and only a masked plate such as `****5678`; raw plates, bodies, names, phone numbers, and email
addresses are never logged.

The log surface is intentionally small:

| Event | Purpose |
|---|---|
| `app_started` / `app_stopping` | Process lifecycle |
| `upstream_request_failed` | Expected upstream or adapter failure |
| `vehicle_lookup_completed` | Final lookup outcome and masked plate |
| `request_failed` | Unexpected HTTP 500 path |

## Code boundaries

All application modules live under `src/onboarding_flow/`.

| Module | Responsibility |
|---|---|
| `app.py` | Application composition, lifespan, middleware, and OpenAPI |
| `config.py` | Environment-backed settings |
| `schemas.py` | Wire types and plate normalization |
| `upstream.py` | `UpstreamPort` and the httpx adapter |
| `vehicle.py` | Lookup handler, envelope mapping, and speakable messages |
| `observability.py` | Trace middleware, masking, JSON logs, and 500 logging |

Tests inject `MemoryUpstream` at the port or use `httpx.MockTransport`; unit tests never call the
real upstream.

## Deployment

The multi-stage image installs locked dependencies, runs as an unprivileged user, and starts
Granian as PID 1. Terraform provisions Artifact Registry and Cloud Run, while Cloud Build
produces an amd64 image tagged with the git short SHA.

See [`infra/README.md`](../infra/README.md) for deploy, verification, rollback, and teardown.

## Scope

I intentionally left authentication, persistence, caching, pricing, automatic retries,
OpenTelemetry, and Insait UI automation outside this assignment.

For production, I would add caller authentication and rate limiting, monitor upstream contract
drift, define a lookup SLO, and deploy from CI with workload identity. I would add caching,
circuit breaking, or minimum instances only when traffic and latency data justify them.
