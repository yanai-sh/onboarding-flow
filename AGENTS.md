# Agent guidance

## Project intent

A solo take-home for a car-insurance onboarding flow, with two deliverables:

1. A stateless proxy for the supplied vehicle-info endpoint (this repository, deployed on
   Cloud Run).
2. An Insait Conversation Flow Agent that calls the proxy. It is built by hand in the Insait UI.

The proxy is shipped. Prefer small, explainable changes that protect its contract over new
features. Before changing behavior, read `ARCHITECTURE.md` (contract, seams, log events),
`CONTEXT.md` (vocabulary), and the ADRs under `docs/adr/`; an ADR wins on a disputed contract.

## Contract invariants

- Every lookup outcome, including a plate that breaks the rule, returns HTTP 200 with
  `success` and a stable `error_code`. Only structurally malformed requests get a framework
  400 ([ADR 0003](docs/adr/0003-invalid-plate-in-envelope.md)). A change to this split needs a
  new ADR.
- The plate rule is 7 or 8 ASCII digits after removing spaces, `-`, and `.`. It lives in
  `schemas.py` and applies to both the request and the upstream success body.
- One bounded upstream call per lookup, with a total timeout and no retries.
- One HTTP stack (`httpx`) and one stdlib JSON logging pipeline
  ([ADR 0002](docs/adr/0002-httpx-stdlib-logging-granian-env.md)). Log only the events in
  `ARCHITECTURE.md`; plates appear only masked, and bodies or contact details never appear.
- Out of scope: auth, caching, persistence, pricing, OpenTelemetry, and HTTP/3.

## Manual Insait boundary

The flow's design and test record live in `docs/insait-flow.md`. When a task touches the flow,
edit that document and describe the UI steps for a human. State platform actions as done only
when the user has confirmed them; repository code never configures the Insait platform.

## Checks

- App changes: `./scripts/check.sh` (ruff, ty, unit tests). Update tests with behavior changes,
  at the HTTP or `UpstreamPort` seam; unit tests never call the real upstream.
- Dockerfile or runtime environment changes: also `./scripts/check-image.sh` (needs Docker
  with buildx).
- Deploys follow `infra/README.md`.
- Create commits, branches, tags, remotes, or releases only when the user asks.
