# Architecture and Design Decisions

A stateless vehicle-lookup proxy, deployed on Cloud Run, used by a Conversation Flow Agent that
is built by hand in the Insait UI. The proxy gives the flow one typed, speakable contract for
every lookup outcome. ADRs under [`docs/adr/`](docs/adr/) record the contested decisions.

## System topology

```mermaid
graph LR
    A[Insait Conversation Flow] -->|POST /vehicle-info| B[Litestar app on Granian]
    B --> C[Plate rule and envelope]
    C --> D[UpstreamPort: httpx adapter]
    D -->|5 s total budget| E[Supplied vehicle-info endpoint]
    E --> D
    B --> F[JSON logs: trace_id + masked plate]
    B -->|HTTP 200 envelope| A
```

The service exposes `POST /vehicle-info`, `GET /health`, and the OpenAPI schema under
`/schema` (`/schema/openapi.json`, Swagger UI at `/schema/swagger`).

## Service contract

### Request and plate rule

`POST /vehicle-info` accepts JSON with one string field:

```json
{"license_plate": "123-45-678"}
```

The plate rule, shared by the request path and the upstream success parser: strip surrounding
whitespace, remove spaces, `-`, and `.`, then require a full match of `[0-9]{7,8}` (ASCII
digits only, so full-width digits fail). The digits-only result is what the upstream receives,
so `12-345-67` is sent as `1234567`. This is the upstream's own rule for Israeli plates; legacy
5- and 6-digit plates are rejected because the upstream rejects them.

### Response envelope

Every lookup outcome is a flat `VehicleInfoResponse` on HTTP 200:

```text
VehicleInfoResponse = {
  success: bool,
  data: {license_plate, manufacturer, model, year, color} | null,
  error_code: ErrorCode | null,
  message: str | null,
  trace_id: str
}
```

Vehicle text passes through as raw UTF-8; the live upstream returns Hebrew values. On failure,
`message` is a static English sentence written to be spoken to the applicant. It never contains
request data.

| Case | HTTP | Body |
|---|---|---|
| Vehicle found | 200 | `success: true`, `data` set, `error_code` and `message` null |
| Plate breaks the rule (`""`, `ABC`, `123456`, `12_345_67`) | 200 | `INVALID_REQUEST`; the upstream is not called |
| Any other lookup failure | 200 | The matching `error_code` and `message`, `data` null |
| Body not JSON, `license_plate` missing, not a string, or over 32 characters | 400 | Litestar validation body |
| Unexpected exception (a bug) | 500 | Litestar default body; logged as `request_failed` |

[ADR 0003](docs/adr/0003-invalid-plate-in-envelope.md) explains why an invalid plate is an
envelope outcome while a structural fault stays a 4xx. It supersedes
[ADR 0001](docs/adr/0001-proxy-validation-4xx.md).

### Outcome mapping

The handler applies the plate rule first; `EncoreUpstream` maps everything after it, in this
order. Each code's `message` is defined once, in `MESSAGES` in `vehicle.py`.

| Condition | Result |
|---|---|
| The plate rule fails (the upstream is not called) | `INVALID_REQUEST` |
| The total budget expires, or httpx raises `TimeoutException` | `UPSTREAM_TIMEOUT` |
| Any other httpx `RequestError` (connection, transport, decoding) | `UPSTREAM_UNAVAILABLE` |
| 200 with `{"success": true, "data": {...}}` and valid vehicle data | Vehicle |
| 200 with `success: true` but data that fails validation (plate rule, year 1900–2100, text 1–128 characters after stripping) | `UPSTREAM_INVALID_RESPONSE` |
| 200 or 404 with body `{"success": false}` or `{"detail": {"success": false, ...}}` | `VEHICLE_NOT_FOUND` |
| Any other 200 (not JSON, unknown shape) | `UPSTREAM_INVALID_RESPONSE` |
| 400 or 422 | `INVALID_REQUEST` |
| Anything else: 5xx, 401, 403, 429, or a 404 without the not-found body | `UPSTREAM_UNAVAILABLE` |

The live upstream answers a missing vehicle with 404 `{"detail": {"success": false, ...}}`. A
404 with any other body means a wrong `UPSTREAM_URL`, which must not pass for a missing vehicle.
The mapping is covered by `tests/unit/test_upstream.py` and, over HTTP, by
`tests/unit/test_vehicle_http.py`.

### Timeout and retries

`UPSTREAM_TIMEOUT_SECONDS` (default 5) is a total budget for one upstream exchange: connect,
send, and reading the full body. The adapter enforces it with `asyncio.timeout`. The httpx
per-phase timeouts use the same value, so they can only fire earlier, never later. There are
no automatic retries: a person is waiting, and retries would amplify load on an upstream that
is already failing. The flow offers the applicant one retry instead.

### Trace id

`X-Trace-ID` is accepted when, after stripping, it fully matches printable ASCII
`[\x21-\x7E]{1,128}`. Any other value is replaced with a UUIDv7. The response carries exactly
one `X-Trace-ID` header, and the body's `trace_id` has the same value.

## Module seams

Six modules under `src/onboarding_flow/`. `schemas`, `observability`, and `config` import
nothing from the package; `upstream` imports `schemas` and `observability`; `vehicle` adds
`upstream`; `app` imports `config`, `observability`, `upstream`, and `vehicle`.

| Module | Responsibility |
|---|---|
| `app.py` | Composition. `create_app(upstream=...)` registers the routes, middleware, and OpenAPI config. Its lifespan builds one `httpx.AsyncClient` and an `EncoreUpstream` unless a port is injected, stores the port on `app.state`, and closes the client on shutdown. |
| `config.py` | `Settings` (`UPSTREAM_URL`, `UPSTREAM_TIMEOUT_SECONDS`, `LOG_LEVEL`, all optional) and the cached `get_settings()`. |
| `schemas.py` | Wire types (`ErrorCode`, `VehicleRequest`, `VehicleData`, `VehicleInfoResponse`) and the plate rule (`normalize_license_plate`, `LicensePlate`). |
| `upstream.py` | The `UpstreamPort` protocol, `UpstreamOutcome = VehicleData \| ErrorCode`, and `EncoreUpstream`, the httpx adapter that owns the URL, the timeout, and the status mapping. |
| `vehicle.py` | The `POST /vehicle-info` handler: applies the plate rule, calls the port, maps the outcome to the envelope with its message, and logs completion. |
| `observability.py` | JSON formatter, `configure_logging`, the `TRACE_ID` ContextVar and log filter, `TraceMiddleware`, `mask_plate`, and the `after_exception` hook. |

`VehicleRequest` checks structure only; the handler applies the plate rule so a bad plate
becomes an envelope outcome. Handlers read the trace id from `request.state.trace_id`, set by
`TraceMiddleware`, and never mint one. Tests inject `tests/fakes.py::MemoryUpstream` at the
port, or drive `EncoreUpstream` through `httpx.MockTransport`; no test calls the real upstream.

## Logging and PII

Logs are single-line JSON on stdout with Cloud Logging field names (`severity`, `time`,
`message`, `stack_trace`). Every record emitted during a request carries `trace_id`, copied from
the ContextVar by a log filter. Fields whose value is null are omitted. The `httpx` and
`httpcore` loggers are set to WARNING, so their per-request lines do not appear. These five
events are the whole log surface:

| Event | Level | Fields |
|---|---|---|
| `app_started` | INFO | `upstream_adapter`, `version`; plus `upstream_host` and `upstream_timeout_seconds` for the real adapter |
| `app_stopping` | INFO | — |
| `upstream_request_failed` | WARNING | `error_code`, `status_code` or `exception` (class name; `TimeoutError` when the total budget expires), `duration_ms`. Emitted for every upstream failure except `VEHICLE_NOT_FOUND`, which is a business outcome. |
| `vehicle_lookup_completed` | INFO | `success`, `error_code`, `plate_mask`, `duration_ms`. `plate_mask` is omitted when the proxy's plate rule fails, because the input may not be a plate. |
| `request_failed` | ERROR | `method`, `path`, `stack_trace`; 5xx only, so client errors stay silent |

Raw plates, response bodies, names, phone numbers, and emails are never logged. A plate appears
only as a partial mask such as `****5678`. Stack traces render exception messages verbatim, so
code that raises states the rule, never the value. See
[ADR 0002](docs/adr/0002-httpx-stdlib-logging-granian-env.md).

The proxy persists nothing. Trace ids are correlation metadata, not authentication.
Authentication, rate limiting, caching, and OpenTelemetry export are out of scope for this
assignment.

## Cloud Run shape

A multi-stage Docker build: `uv` installs the locked dependencies, the runtime uses
`python:3.14-slim`, and the process runs as the unprivileged `appuser`. `.dockerignore` is an
allowlist, so only package metadata and `src/` enter the build context. Granian settings are
`GRANIAN_*` environment defaults in the image: ASGI interface, `0.0.0.0`, one worker, no
WebSockets, no access log, and an 8 s worker kill timeout inside Cloud Run's 10 s SIGTERM grace.
The shell resolves only `$PORT` (8080 by default), and `exec granian` keeps the server as PID 1
so SIGTERM runs the lifespan shutdown and closes the HTTP client.

Terraform deploys the image by its git short SHA (`image_tag`, which cannot be empty or
`latest`), so every deploy rolls a new revision and rollback is an `apply` with an earlier SHA.
The service has 1 CPU and 512 MiB, scales to zero, is capped by `max_instances`, and allows
unauthenticated invocation because the Insait API node calls it without credentials. Terraform
sets `UPSTREAM_URL`, `UPSTREAM_TIMEOUT_SECONDS`, `LOG_LEVEL`, and `GRANIAN_WORKERS_KILL_TIMEOUT`.
Deploy steps are in [`infra/README.md`](infra/README.md).

## Insait flow boundary

The only client is the Insait flow's Lookup API node, which routes on `success` and
`error_code`. The flow is configured by hand in the Insait UI, and this repository does not
automate it; its design and test record are in [`docs/insait-flow.md`](docs/insait-flow.md).
