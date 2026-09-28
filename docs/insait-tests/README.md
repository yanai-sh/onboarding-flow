# Insait strict-replay suite

Thirty Strict Replay tests, one CSV per test group. Each file is imported into its own dedicated
folder of the same name. The design and per-test intent are in
[`../insait-flow.md`](../insait-flow.md#test-suite). Nothing in this repository imports them; a
human uploads them in the Insait Testing UI.

| File / folder | Tests | Quality gate |
|---|---|---|
| `01-smoke` | SMK-01, SMK-02 | both |
| `02-opening` | OPN-01 … OPN-03 | OPN-03 |
| `03-vehicle` | VEH-01, VEH-02 | VEH-01 |
| `04-lookup-recovery` | REC-01 … REC-03 | REC-01, REC-02 |
| `05-contact` | CON-01 … CON-05 | CON-05 |
| `06-coverage` | COV-01 | — |
| `07-summary` | SUM-01, SUM-02 | SUM-01 |
| `08-corrections` | COR-01 … COR-07 | COR-04 |
| `09-language` | LNG-01, LNG-02 | LNG-01 |
| `10-guardrails` | GRD-01 … GRD-03 | — |

## Columns

Only fields present on every existing platform test: `name`, `expected_outcome`, and
`flow_questions` (a JSON array of applicant turns). Folder, channel, evaluation model, and
quality-gate membership are set in the UI, not in the file. Insait publishes no import template,
so if its **Download template** header differs, map these three columns onto it.

Set on each folder or run: Strict Replay, chat, evaluation model `gpt-5.6-luna` at temperature 0,
no simulation model, no tool overrides. Lookup calls the live proxy: `12345678` is found;
`00000000` and `11111111` are not found.

## Rollout

1. Delete all existing tests and folders.
2. Create folder `01-smoke` and hand-create `SMK-01 Mandatory end to end` as a Strict Replay
   with the turns from `01-smoke.csv`. Run it.
3. If the hand-made SMK-01 shows an execution error, the cause is the agent or runner, not the
   CSV: publish the agent, run one live Test Agent chat, check the Lookup tool URL and the tool
   schema's `required` field, and stop there.
4. If it passes, create the remaining folders and import each CSV into its folder.
5. Add the gate tests above to the quality gate and run.
