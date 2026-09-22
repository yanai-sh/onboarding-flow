# Domain Context

## Purpose

This is a focused take-home implementation for a car-insurance onboarding
experience. The repository owns a small proxy that gives an Insait
conversation a stable, typed vehicle lookup contract. Insait owns the
conversation state and orchestration.

## Vocabulary

- **Applicant**: the person providing identity, contact, vehicle, and coverage
  details during onboarding.
- **Vehicle lookup**: a request to the supplied upstream endpoint using the
  applicant's license plate.
- **Proxy**: this repository's stateless HTTP service. It validates requests,
  invokes the upstream vehicle lookup, maps failures, and returns the
  response envelope.
- **Upstream**: the supplied Encore vehicle-info endpoint. Its availability,
  response shape, and status codes are outside this repository's control.
- **Response envelope**: the stable JSON contract returned by the proxy for
  both successful data and expected errors.
- **Conversation flow**: the manually configured Insait graph that collects
  applicant details, calls the proxy, supports corrections, and reaches a
  final confirmation.
- **Manual platform step**: work requiring Insait account access, platform
  UI interaction, deployment credentials, or the recorded submission.

## Scope

In scope: one vehicle lookup endpoint, typed validation and error handling,
dependency-injected upstream access, PII-safe structured logs, focused tests,
Cloud Run packaging, and a documented Insait handoff.

Out of scope: policy pricing or issuance logic, persistence, authentication,
retries that could amplify upstream load, caching, LLM-based PII detection,
OpenTelemetry export, and automating the Insait UI.
