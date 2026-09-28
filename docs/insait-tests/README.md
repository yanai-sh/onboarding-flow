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

The header follows Insait's Strict Replay template exactly:

```text
name,message_1,…,message_8,expected_outcome,tool_overrides,chunk_1,chunk_2,tool_assertions,metric_thresholds,session_data
```

Each row is one conversation: `name` is the flow name, and `message_1`…`message_8` are the
applicant turns in order (empty cells are skipped). Every row sets `tool_overrides` to
`{"lookup_vehicle_info":{"mode":"test_url"}}`, so Lookup calls the tool's configured test URL
(the live proxy); every Sep 23 lookup test that completed had an override, and runs without one
stalled. Fixtures: `12345678` is found; `00000000` and `11111111` are not found. `chunk_*`,
`tool_assertions`, `metric_thresholds`, and `session_data` are left empty. The CSV has no folder
column; the folder is whichever one you import into.

In the import dialog: flow name column A (`name`), messages B–I (`message_1`…`message_8`),
expected outcome column J (`expected_outcome`), and keep **Skip header row** on.

Set on each folder or run: evaluation model `gpt-5.6-luna` at temperature 0 and no simulation
model.

## Expected run times

Completed Sep 23 runs took 3–48 s per test (about 25 s for the Mandatory happy path), so a
folder finishes in a few minutes. A run pins the agent version that was live when it started
(shown as Agent version in the run config). If tests sit at Pending or Running for several
minutes with no transcript, check that version first: runs started on a broken version stay
stuck even after a rollback. Cancel them and start new runs.

## Rollout

1. Delete all existing tests and folders.
2. Create folder `00-diagnostic`, import `00-diagnostic.csv`, and run it. DIAG-01 has no lookup
   (about 3 s on Sep 23); DIAG-02 runs one lookup with the `test_url` override. If DIAG-01 hangs,
   the runner itself is stuck; if only DIAG-02 hangs, the Lookup path is.
3. Create folder `01-smoke`, import `01-smoke.csv` into it, and run it.
4. If SMK-01 shows an execution error, the cause is the agent or runner: publish the agent, run
   one live Test Agent chat, check the Lookup tool URL and the tool schema's `required` field,
   and stop there.
5. If it passes, create the other nine folders and import each CSV into its own folder.
6. Add the gate tests above to the quality gate and run.
