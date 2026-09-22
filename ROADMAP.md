# Strategic Roadmap: Onboarding Flow Proxy

## Phase 1: Core Anti-Corruption Layer (Milestone 1)
- **Objective:** Establish the high-performance Litestar service layer to safely proxy inbound conversational requests from the Insait AI graph to the upstream Encore webhook.
- **Key Deliverables:**
  - Standardized generic `APIResponse[T]` envelope for deterministic client consumption.
  - Robust error-mapping isolating network timeouts, validation failures, and upstream 404s.
  - Strict Pydantic v2 data validation and PII masking pipeline.

## Phase 2: Cloud-Native Containerization (Milestone 2)
- **Objective:** Package the service into an optimized OCI container built for zero-trust, stateless execution on Google Cloud Run.
- **Key Deliverables:**
  - Multi-stage Docker build utilizing Astral's `uv` for sub-second dependency layering.
  - Hardened unprivileged runtime (`appuser`) running on `python:3.14-slim`.
  - Granian ASGI server binding to port 8080 with pre-compiled bytecode optimization.

## Phase 3: Conversational Orchestration & Hardening (Milestone 3)
- **Objective:** Integrate the proxy into the Insait platform canvas (Nodes 1–6) and ensure enterprise-grade resilience.
- **Key Deliverables:**
  - Deterministic routing edges handling API success/error payloads.
  - Graceful fallback paths for upstream gateway timeouts (preventing conversational dead-ends).
  - State mutability loops allowing users to modify data fields prior to final submission.

## Phase 4: Production Scale (Post-Assignment)
- **Objective:** Expand telemetry and security guardrails for enterprise traffic.
- **Key Deliverables:**
  - OpenTelemetry (OTel) trace propagation exported to centralized SIEM tools.
  - Semantic LLM firewall integration (e.g., DataFog) for unstructured PII scrubbing.