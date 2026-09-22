# ADR 0002: httpx, stdlib JSON logging, and Granian settings as image env

## Status

Accepted

## Context

A dependency audit found two runtime dependencies whose documented
justification did not match their use:

- `niquests` was chosen for HTTP/3 and OS trust-store support. The adapter
  used neither. The proxy makes one bounded HTTPS `POST` per lookup from
  Cloud Run to another Cloud Run service; no mobile client or browser is on
  that hop, Cloud Run's front end owns the outer TLS/protocol negotiation, and
  Granian serves HTTP/1.1 and HTTP/2 only. Litestar already requires `httpx`
  for `TestClient`, so the tree carried two HTTP stacks.
- `structlog` was imported but never configured: no processors, no JSON
  renderer, and the trace id bound in middleware never reached the single
  completion event.

Granian was launched with all settings inlined as `CMD` flags, including a
30s worker kill timeout that exceeds Cloud Run's 10s SIGTERM grace and could
not be changed without rebuilding the image.

## Decision

1. **Outbound HTTP uses `httpx.AsyncClient`**, created once in the Litestar
   lifespan and closed on shutdown. `TimeoutException` maps to
   `UPSTREAM_TIMEOUT`, any other `TransportError` to `UPSTREAM_UNAVAILABLE`.
   HTTP/3 is out of scope for this service.
2. **Logging is stdlib `logging` with a JSON formatter** on stdout using
   Cloud Logging field names (`severity`, `time`, `message`, `stack_trace`).
   `TraceMiddleware` sets a `ContextVar`; a handler filter copies it onto
   every record, so upstream warnings and error tracebacks carry the same
   `trace_id` as the response header. Litestar's default `LoggingConfig` is
   disabled and an `after_exception` hook logs 5xx causes through the same
   handler. The Granian worker logger (`_granian`) is routed through the same
   handler; Granian configures logging before loading the app, so the app's
   configuration wins for worker-side lines. Main-process Granian lines remain
   plain text, which Cloud Logging ingests as `textPayload`.
3. **Four events, no access log.** `app_started` (adapter, upstream host,
   timeout, version), `upstream_request_failed` (kind, status code, exception
   class, duration; not emitted for not-found), `vehicle_lookup_completed`
   (outcome, masked plate, duration), and `request_failed` (5xx with stack
   trace). Cloud Run already records every request at the edge. Response
   bodies and raw plates are never logged.
4. **Granian settings live as `GRANIAN_*` image environment defaults**, not
   `CMD` flags. Image facts (`asgi` interface, `0.0.0.0`, one worker, no
   WebSockets, no access log) are fixed by the image; deployment facts
   (`LOG_LEVEL`, `GRANIAN_WORKERS_KILL_TIMEOUT`) have image defaults and
   Terraform overrides. The kill timeout is 8s to finish inside Cloud Run's
   10s grace. `PORT` is the only value resolved by the shell because Cloud Run
   injects it and Granian reads `GRANIAN_PORT`, not `PORT`.

## Consequences

- Two fewer runtime dependencies; one HTTP stack; one logging pipeline whose
  output is tested through the real formatter rather than a mocked logger.
- `LOG_LEVEL` is a validated `Settings` field, so an invalid level fails at
  startup rather than silently defaulting.
- Unhandled exceptions still return Litestar's default 500 body; mapping
  them into the response envelope would be a separate contract decision.
- Reintroducing structlog or HTTP/3 requires a measured need, not a stack
  preference. Revisit if the service gains many log sites with shared context
  or browsers start calling the proxy directly.
