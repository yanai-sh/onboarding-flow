# FDE: Encore AI Car Insurance Onboarding Flow

This repository plans and implements a small production-shaped vertical slice
for the Encore AI home assignment:

1. a resilient API proxy for the supplied vehicle-info endpoint; and
2. a manually configured Insait Conversation Flow Agent that uses the proxy.

The application code is intentionally still a scaffold. The implementation
phase starts only after the contracts and manual-platform boundary in the
tracked planning documents are agreed.

## Assignment references

- [`docs/FDE_Home_Assignment.pdf`](docs/FDE_Home_Assignment.pdf) — local source
  material (ignored by Git).
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — service boundary, contracts, failure
  mapping, and deployment shape.
- [`ROADMAP.md`](ROADMAP.md) — implementation sequence and acceptance gates.
- [`TODO.md`](TODO.md) — actionable implementation checklist.
- [`CONTEXT.md`](CONTEXT.md) — domain vocabulary and scope.

## Planned service

The proxy will run Litestar on Granian and expose `POST /vehicle-info`. It
will normalize and validate an alphanumeric license plate, call the supplied
upstream endpoint through an injected `niquests.AsyncSession`, and return a
typed Pydantic response envelope for both success and expected upstream
failures. Structured logs carry a trace ID and a masked plate only. The
service will not impose a country-specific plate length that the assignment
does not define.

The container is designed for an unprivileged Cloud Run deployment on port
8080. Tests will exercise the HTTP contract and the upstream adapter through
public seams, without requiring the real upstream service.

**Configuration:** `UPSTREAM_URL` and `UPSTREAM_TIMEOUT_SECONDS` (optional;
see `onboarding_flow.config.Settings`). Local overrides may live in a
git-ignored `.env` file.

**OpenAPI:** Litestar serves the integration schema at `/schema/openapi.json`
(Swagger UI at `/schema/swagger` when enabled by default render plugins).

## Manual Insait boundary

The Insait Conversation Flow Agent cannot be created or submitted from this
repository. A human with platform access must create the flow, connect the
deployed endpoint, test debug paths, and record the submission video. The
planned node behavior and handoff checklist are documented in
[`ARCHITECTURE.md`](ARCHITECTURE.md) and [`TODO.md`](TODO.md); no document
claims those UI steps are automated.
