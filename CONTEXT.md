# Domain Context

The domain glossary for a car-insurance onboarding take-home. The repository owns a small proxy
that gives an Insait conversation a stable, typed vehicle lookup; Insait owns the conversation
state and orchestration.

## Language

**Applicant**:
The person giving insurance type, vehicle, contact, and coverage details during onboarding.
_Avoid_: user, customer (in code and docs)

**License plate**:
An Israeli plate of 7 or 8 digits. Spaces, dashes, and dots are separators, so `12-345-67` is
the plate `1234567`.

**Vehicle lookup**:
One request to the supplied upstream endpoint for one license plate.

**Upstream**:
The supplied vehicle-info endpoint. Its availability, response shape, and status codes are
outside this repository's control.

**Proxy**:
This repository's stateless HTTP service between the conversation flow and the upstream.

**Response envelope**:
The JSON contract (`success`, `data`, `error_code`, `message`, `trace_id`) returned on HTTP 200
for every lookup outcome, including a plate that breaks the rule (`INVALID_REQUEST`). Only a
structurally malformed request gets a framework 4xx
([ADR 0003](docs/adr/0003-invalid-plate-in-envelope.md)).

**Conversation flow**:
The Insait Conversation Flow Agent that collects applicant details, calls the proxy, supports
corrections, and ends on a final confirmation.

**Manual platform step**:
Work that needs Insait account access or the platform UI, such as building the flow or recording
the submission video.

## Scope

In scope: one vehicle lookup endpoint, typed validation and error handling, an injected upstream
adapter, PII-safe structured logs, focused tests, Cloud Run packaging, and a documented Insait
flow.

Out of scope: pricing or policy issuance, persistence, authentication, automatic retries,
caching, LLM-based PII detection, OpenTelemetry export, and automating the Insait UI.
