# Implementation Roadmap

The roadmap is intentionally a short dependency sequence. A phase is complete
only when its behavior is tested and the relevant acceptance evidence exists.

## Phase 0: Planning baseline

**Status:** ready for implementation.

- Read the assignment and record its vocabulary in `CONTEXT.md`.
- Keep the service/Insait ownership boundary explicit.
- Treat the current health-only app and existing container files as scaffold,
  not completed milestones.

## Phase 1: Vehicle lookup vertical slice

**Blocked by:** Phase 0.

Build the smallest demonstrable path: validate a plate, call the upstream
through an injected adapter, map the result, and serve `POST /vehicle-info`.
Use Litestar, Pydantic, and `niquests.AsyncSession`; preserve `/health`.

**Exit evidence:** public HTTP tests cover success, invalid input, not found,
timeout, transport failure, upstream 5xx, and malformed payloads.

## Phase 2: Resilience and observability

**Blocked by:** Phase 1.

Add the five-second timeout, typed error envelope for expected upstream
failures, trace-ID middleware, structlog context cleanup, and deterministic PII
masking. Keep dependencies injected at app composition time.

**Exit evidence:** logs and response tests demonstrate trace correlation,
safe fields, and no unhandled upstream exception.

## Phase 3: Cloud Run packaging

**Blocked by:** Phase 2.

Verify the locked `uv` build, multi-stage `python:3.14-slim` image,
unprivileged runtime, Granian ASGI startup, and `$PORT`/8080 behavior.

**Exit evidence:** repository checks pass and the image starts the health
endpoint locally when Docker is available.

## Phase 4: Manual Insait flow

**Blocked by:** Phase 3 and approved Insait access.

The human creates the Conversation Flow Agent, connects the deployed proxy,
configures deterministic branches and conversational save tools, tests the
required paths, and records the submission. The graph remains six or fewer
nodes and excludes the Collect Node.

**Exit evidence:** flow link, workspace/agent name, debug-tested happy and
failure paths, correction loop, and approximately three-minute recording.

## Post-assignment exclusions

Persistence, policy pricing/issuance, authentication, rate limiting, caching,
automatic retries, OpenTelemetry export, semantic PII firewalls, and Insait UI
automation are deliberately excluded from this take-home slice.
