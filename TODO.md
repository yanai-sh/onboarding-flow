# Implementation Checklist

Part A (sections 1–3) is complete: the proxy exposes `POST /vehicle-info` with
typed envelopes, boundary hardening, and automated tests. Remaining work is the
manual Insait handoff in section 4. Track phase context in `ROADMAP.md`.

## 1. Contract and lookup slice

- [x] Add typed Pydantic models for `VehicleRequest`, `VehicleData`, error
  codes, and generic `APIResponse[T]`.
- [x] Normalize and validate non-empty ASCII alphanumeric plates with a
  documented defensive maximum length; do not impose a country-specific
  format.
- [x] Define the vehicle lookup interface and inject it into the Litestar
  controller.
- [x] Implement the httpx upstream adapter with the supplied URL, JSON POST, and
  strict five-second timeout.
- [x] Map not found, timeout, transport, upstream status, and invalid payload
  failures to stable error codes and safe messages.
- [x] Expose `POST /vehicle-info`; preserve `/health`.

## 2. Boundary hardening

- [x] Add trace-ID middleware for incoming or generated `X-Trace-ID` values.
- [x] Emit PII-safe JSON completion logs with trace id per request.
- [x] Verify logs contain no raw plate, name, phone, or email values.
- [x] Ensure expected upstream failures produce structured responses rather
  than unhandled 5xx errors.

## 3. Verification

- [x] Test valid normalization and invalid request rejection.
- [x] Test success, not found, timeout, connection failure, upstream 5xx, and
  malformed upstream payloads through the adapter seam.
- [x] Test controller routing and trace-ID propagation through Litestar's
  public HTTP seam.
- [x] Test the real container startup and Cloud Run `$PORT` behavior if Docker
  is available (`./scripts/check-image.sh --container-force-build`).
- [x] Run `./scripts/check.sh`.

## 4. Manual Insait handoff

- [ ] Human registers and obtains approved Insait access.
- [ ] Create a Conversation Flow Agent, not a Single Prompt Agent.
- [ ] Build the six-or-fewer-node flow described in `ARCHITECTURE.md`.
- [ ] Configure deterministic API success/error and insurance-type branches.
- [ ] Configure validation and correction loops for applicant details and the
  summary.
- [ ] Deploy the proxy to Cloud Run ([`infra/README.md`](infra/README.md)) and connect
  the public endpoint in Insait.
- [ ] Test happy path, invalid input, vehicle not found, timeout/unavailable,
  correction, and Mandatory-without-add-ons paths in debug view.
- [ ] Record the approximately three-minute end-to-end submission video and
  capture workspace/agent/flow links.
