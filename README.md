# Car-insurance onboarding

[![CI](https://github.com/yanai-sh/onboarding-flow/actions/workflows/ci.yml/badge.svg)](https://github.com/yanai-sh/onboarding-flow/actions/workflows/ci.yml)

This is my Encore AI Forward Deployed Engineer take-home:

1. I built a stateless vehicle-lookup proxy and deployed it to Cloud Run.
2. I built and tested an Insait Conversation Flow Agent that calls the proxy during onboarding.

I built and tested the Insait flow manually in its platform UI; the repository contains its
design and test record. I do not redistribute the assignment PDF here.

## Reviewer start

- [Proxy architecture, live service, and design decisions](docs/architecture.md)
- [Insait flow design and manual test record](docs/insait-flow.md)
- [Submission links and handoff checklist](docs/submission.md)

## Quick check

```bash
uv sync
./scripts/check.sh
```

## AI-assisted development

I used Cursor agents for implementation and review. `AGENTS.md` and `.cursor/rules/` show the
constraints I gave them for architecture, privacy, testing, and deployment. I reviewed and
validated changes with automated checks and manual verification.
