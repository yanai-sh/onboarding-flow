# Agent guidance

## Project intent

This repository is a focused solo take-home assignment for a car-insurance
onboarding flow. Prefer a small, explainable implementation that demonstrates
production judgment over novelty or speculative infrastructure.

The system has two deliverables:

1. A resilient API proxy for the supplied vehicle-info endpoint.
2. A manually configured Insait Conversation Flow Agent using that API.

Keep the boundary between code the agent can change and actions that require
the Insait UI, account access, or a recorded submission explicit.

## Agent skills

### Issue tracker

Planning artifacts use local Markdown under `.scratch/<feature>/`. The
directory is intentionally git-ignored. See `docs/agents/issue-tracker.md`.

### Triage labels

Use `inbox`, `needs-clarification`, `ready-to-build`,
`manual-platform-step`, and `out-of-scope` in local planning notes. See
`docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository. Read `CONTEXT.md` and relevant decisions
under `docs/adr/` when they exist. See `docs/agents/domain.md`.

## Working agreements

- Read the assignment and relevant repository docs before changing behavior.
- Keep external failures inside typed, structured API responses.
- Add or update tests with behavior changes.
- Keep Insait-specific manual steps documented rather than pretending they are
  automated.
- Run the repository checks proportionally before handing work back:
  `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run ty check .`, and `uv run pytest`.
- Do not create remote labels, tags, branches, tickets, commits, or releases
  unless the user explicitly requests them.
