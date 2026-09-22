# ADR 0001: Proxy validation uses framework 4xx

## Status

Accepted

## Context

The Insait integration contract centers on HTTP 200 responses with
`VehicleInfoResponse` (`success`, `error_code`, `message`, `trace_id`) for
vehicle registry outcomes. The proxy also validates `license_plate` on ingress
via Pydantic (`VehicleRequest`).

`ErrorCode.INVALID_REQUEST` exists in the public enum for documentation and
possible future envelope-unified validation, but emitting it would require
either bypassing Litestar body validation or a global exception handler that
maps validation failures to HTTP 200.

## Decision

Keep proxy ingress validation at the **Litestar/Pydantic seam**: invalid plates
return HTTP **4xx** with the framework validation body. Do **not** call the
upstream port. Do **not** return `INVALID_REQUEST` in the response envelope on
that path for this assignment.

Insait should pre-validate license plates where possible and/or branch on HTTP
client errors when calling the proxy. Upstream timeouts, not-found, and
transport failures remain HTTP **200** with stable `error_code` values.

## Consequences

- Two error surfaces for API clients: 4xx for malformed ingress, envelope for
  lookup outcomes.
- Tests assert client errors separately from envelope mapping tests.
- Future unification to HTTP 200 + `INVALID_REQUEST` would deepen the vehicle
  lookup module and narrow Insait HTTP branching.
