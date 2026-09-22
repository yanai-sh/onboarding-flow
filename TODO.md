# Actionable Tasks: Onboarding Flow Proxy

## Milestone 1: Core API & Anti-Corruption Layer
- [x] **Initialize Package Layout (`src/onboarding_flow/__init__.py`)**
- [ ] **Implement Schemas (`src/onboarding_flow/schemas.py`)**
  - [ ] Define generic `APIResponse[T]` structure (`success`, `data`, `error_code`, `message`).
  - [ ] Define `VehicleRequest` model for inbound payloads.
  - [ ] Define `VehicleData` model for outbound/upstream data contracts.
  - [ ] Implement a Pydantic `@field_validator` on license plate fields to enforce strict 7–8 character alphanumeric sanitization.
- [ ] **Implement Async Client (`src/onboarding_flow/client.py`)**
  - [ ] Instantiate an async `niquests` client targeting `https://insurance-webhook-945894769129.us-central1.run.app/vehicle-info`.
  - [ ] Enforce a strict 5.0-second timeout constraint.
  - [ ] Wrap execution in try/except blocks to catch timeouts, connection errors, and HTTP status codes, mapping them cleanly into `APIResponse`.
- [ ] **Implement Litestar Controller & App (`src/onboarding_flow/app.py`)**
  - [ ] Create a `VehicleController` exposing a `POST /vehicle-info` endpoint.
  - [ ] Configure `structlog` middleware to extract or generate an `X-Trace-ID` for contextvar propagation.
  - [ ] Implement inline PII masking for license plates in structured audit logs.
  - [ ] Initialize the top-level Litestar application instance (`app`).

## Milestone 2: Infrastructure & Packaging
- [x] **Verify Toolchain Configurations**
  - [x] Validate `pyproject.toml` dependencies and `ruff.toml` lint/format settings.
- [x] **Generate Container Artifacts**
  - [x] Write optimized multi-stage `Dockerfile` (Astral `uv` builder + `python:3.14-slim` runner).
  - [x] Create `.dockerignore` targeting build caches, version control, and local documentation.

## Milestone 3: Insait Canvas Setup (Manual UI Task)
- [ ] **Configure Conversational Nodes (N1–N6)**
  - [ ] Map N1 (Greeting & Intent) and N2 (Data Collection via Natural Language).
  - [ ] Connect N3 (Proxy Invocation), ensuring separate handling for `TIMEOUT` vs `NOT_FOUND` responses.
  - [ ] Configure N4 (Summary & Confirmation) with state mutability loops for user edits.
  - [ ] Finalize N5 (Payload Submission) and N6 (Completion & Policy Issuance).