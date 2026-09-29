# Submission handoff

I implemented, tested, and deployed the proxy. I also built the Insait agent and ran its 36
configured platform tests. Only the final email remains.

These are the final handoff details:

| Item | Value |
|---|---|
| Repository | <https://github.com/yanai-sh/onboarding-flow> |
| Live API | <https://onboarding-flow-2q2x6qga6a-uc.a.run.app> |
| Swagger | <https://onboarding-flow-2q2x6qga6a-uc.a.run.app/schema/swagger> |
| Insait workspace | `Yanai Klugman Workspace` |
| Agent | `Encore AI Insurance Onboarding` |
| Flow link | [Open in Insait](https://platform.gainencore.ai/agent-builder/9cd6b40b-330b-4300-abe0-95f18d43dea4?panel=flow-builder) |
| Flow export | `encore_ai_insurance_onboarding_2026-09-28.json` (email attachment, not committed) |
| Video (about 3 minutes) | `encore_ai_insurance_onboarding_demo.mp4` (email attachment) |

## Agent UUID

`9cd6b40b-330b-4300-abe0-95f18d43dea4`

The direct link requires an authenticated Encore account with access to the workspace. The
workspace and agent names above provide a fallback for reviewers who need to locate it manually.

## Before sending

- [ ] Attach the video showing the graph explanation and Comprehensive happy path.
- [ ] Attach the exported flow JSON to the email.
- [x] Run `./scripts/check.sh` and confirm CI is green for the submitted commit.
- [x] Run the configured Insait test suites.
- [x] Confirm the live service and Swagger links in the
  [architecture guide](architecture.md#live-service) still respond.
