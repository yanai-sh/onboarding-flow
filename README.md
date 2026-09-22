# FDE: Encore AI Car Insurance Onboarding Flow

Small production-shaped vertical slice for the Encore AI home assignment:

1. a resilient API proxy for the supplied vehicle-info endpoint; and
2. a manually configured Insait Conversation Flow Agent that uses the proxy.

## Assignment references

- [`docs/FDE_Home_Assignment.pdf`](docs/FDE_Home_Assignment.pdf) — local source
  material (ignored by Git).
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — service boundary, contracts, failure
  mapping, and deployment shape.
- [`ROADMAP.md`](ROADMAP.md) — implementation sequence and acceptance gates.
- [`TODO.md`](TODO.md) — actionable checklist (proxy done; Insait handoff open).
- [`CONTEXT.md`](CONTEXT.md) — domain vocabulary and scope.

## Service

Litestar on Granian exposes `POST /vehicle-info` (and `/health`). The proxy
normalizes and validates alphanumeric plates, calls the upstream JSON endpoint
via an injected `niquests.AsyncSession`, and returns typed Pydantic success and
error envelopes. Logs include a trace ID and masked plate only. Configuration at deploy time: `UPSTREAM_URL` and optional
`UPSTREAM_TIMEOUT_SECONDS` (`onboarding_flow.config.Settings`).
OpenAPI: `/schema/openapi.json` (Swagger UI at `/schema/swagger` when enabled).

The image targets unprivileged Cloud Run on port 8080.

## GCP deploy (Terraform)

Declarative Terraform under [`infra/`](infra/README.md). Install native **aarch64**
`gcloud` in WSL (official `google-cloud-cli-linux-arm.tar.gz` on Fedora 44; see
infra README), configure `terraform.tfvars`, then follow the deploy steps there.

## Development

Requires [uv](https://docs.astral.sh/uv/) and Python 3.14 (see `.python-version`).
Full WSL/Fedora container setup: [`docs/runbook-dev-environment.md`](docs/runbook-dev-environment.md).

```bash
uv sync
./scripts/check.sh          # unit tests only (fast; no Docker)
./scripts/check-image.sh    # optional: build image + /health smoke
```

| Script | What it runs |
|--------|----------------|
| `scripts/check.sh` | ruff, ty, **tests/unit** (default CI job `unit`) |
| `scripts/check-image.sh` | **tests/integration** (Docker + BuildKit; CI job `image-smoke`) |

Image smoke flags: `--container-force-build`, `--container-image onboarding-flow:test`.
See [`docs/runbook-dev-environment.md`](docs/runbook-dev-environment.md) for Docker on Fedora WSL.

## Manual Insait boundary

The Insait Conversation Flow Agent cannot be created from this repository. A
human with platform access creates the flow, connects the deployed endpoint,
tests debug paths, and records the submission video. Node behavior and the
handoff checklist are in [`ARCHITECTURE.md`](ARCHITECTURE.md) and
[`TODO.md`](TODO.md).
