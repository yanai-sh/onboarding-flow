# Implementation Checklist

The repository is still at the scaffold stage: only `/health` and its test are
implemented. Complete the tickets in `ROADMAP.md` in order; keep the Insait
items as a human handoff.

## 1. Contract and lookup slice

- [x] Add typed Pydantic models for `VehicleRequest`, `VehicleData`, error
  codes, and generic `APIResponse[T]`.
- [x] Normalize and validate non-empty ASCII alphanumeric plates with a
  documented defensive maximum length; do not impose a country-specific
  format.
- [x] Define the vehicle lookup interface and inject it into the Litestar
  controller.
- [x] Implement the niquests adapter with the supplied URL, JSON POST, and
  strict five-second timeout.
- [x] Map not found, timeout, transport, upstream status, and invalid payload
  failures to stable error codes and safe messages.
- [x] Expose `POST /vehicle-info`; preserve `/health`.

## 2. Boundary hardening

- [x] Add trace-ID middleware for incoming or generated `X-Trace-ID` values.
- [x] Bind and clear structlog context per request.
- [x] Verify logs contain no raw plate, name, phone, or email values.
- [x] Ensure expected upstream failures produce structured responses rather
  than unhandled 5xx errors.

## 3. Verification

- [x] Test valid normalization and invalid request rejection.
- [x] Test success, not found, timeout, connection failure, upstream 5xx, and
  malformed upstream payloads through the adapter seam.
- [x] Test controller routing and trace-ID propagation through Litestar's
  public HTTP seam.
- [ ] Test the real container startup and Cloud Run `$PORT` behavior if Docker
  is available.
- [x] Run `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run ty check .`, and `uv run pytest`.

## 4. Manual Insait handoff

- [ ] Human registers and obtains approved Insait access.
- [ ] Create a Conversation Flow Agent, not a Single Prompt Agent.
- [ ] Build the six-or-fewer-node flow described in `ARCHITECTURE.md`.
- [ ] Configure deterministic API success/error and insurance-type branches.
- [ ] Configure validation and correction loops for applicant details and the
  summary.
- [ ] Deploy the proxy to Cloud Run and connect the public endpoint.
- [ ] Test happy path, invalid input, vehicle not found, timeout/unavailable,
  correction, and Mandatory-without-add-ons paths in debug view.
- [ ] Record the approximately three-minute end-to-end submission video and
  capture workspace/agent/flow links.
