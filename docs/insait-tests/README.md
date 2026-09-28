# Insait strict-replay suite

[`suite.csv`](suite.csv) is the full test suite for the live Insait agent: 30 Strict Replay tests
in 8 folders, 10 of them in the quality gate. The design and per-test intent are in
[`../insait-flow.md`](../insait-flow.md#test-suite). Nothing in this repository imports it; a
human uploads it in the Insait Testing UI.

## Rules

- **Strict Replay only.** Each row is a scripted conversation (`flow_questions`). Do not import
  it as Simulate, and do not set a simulation model on the run.
- **Evaluation model** `gpt-5.6-luna`, temperature 0.
- **No tool overrides.** Lookup uses the agent tool's live URL. Fixtures: `12345678` is found
  (2020 טויוטה קורולה, לבן); `00000000` and `11111111` are not found.

## Columns

| Column | Meaning |
|---|---|
| `name` | Stage id and asserted behavior, e.g. `REC-02 Two not-founds unlock unverified` |
| `folder_name` | `01-smoke` … `08-guardrails`, in flow order |
| `expected_outcome` | What the evaluator checks |
| `flow_questions` | Applicant turns, separated by ` \| ` |
| `channel` | `chat` |
| `quality_gate_mode` | `included` for gate tests, otherwise `excluded` |
| `evaluation_model`, `evaluation_temperature` | `gpt-5.6-luna`, `0` |

If the import dialog uses its own template, map these columns to it. If it wants one column per
turn, split `flow_questions` on ` | `.

## Rollout

1. Delete all existing tests and folders in Insait.
2. Create folder `01-smoke` and hand-create `SMK-01 Mandatory end to end` as a Strict Replay
   (eval model `gpt-5.6-luna`, no simulation model). Run it.
3. If SMK-01 shows an execution error, the problem is the agent or runner, not this file: publish
   the agent, warm `https://onboarding-flow-2q2x6qga6a-uc.a.run.app/health`, check the Lookup
   tool URL, and stop there.
4. If SMK-01 passes, import `suite.csv` (skip the duplicate SMK-01 row or delete the hand-made one).
5. Run the suite and confirm the 10 gate tests are included in the quality gate.
