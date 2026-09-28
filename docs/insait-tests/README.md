# Insait strict-replay CSV import packs

These CSVs are built from the live agent export fields (`name`, `folder_*`,
`expected_outcome`, `flow_questions`, `tool_overrides`) plus the new Part B drafts
in [`../insait-flow.md`](../insait-flow.md). Nothing in this repository imports them
into Insait; a human uploads them in the Testing UI.

Insait has no public CSV schema, so two layouts are provided. Use whichever matches
the import dialog; remap columns if the UI template differs.

## Layouts

| Suffix | Columns | When to use |
|---|---|---|
| `.json.csv` | `flow_questions_json` as a JSON array string | Prefer if the importer accepts one multi-turn field |
| `.wide.csv` | `user_turn_1` … `user_turn_N` | Prefer if the importer wants one column per user turn |

Shared columns: `name`, `folder_name`, `channel` (`chat`), `quality_gate_mode`
(`excluded` by default), `expected_outcome`, `tool_overrides_json`, `notes`.

`tool_overrides_json` mirrors the platform shape, e.g.
`{"lookup_vehicle_info":{"mode":"test_url","status_code":200,"delay_ms":0,"test_url":null}}`.
Leave empty when the existing test had no override. Set `test_url` in the UI to the
live proxy if the importer does not accept null.

## Files

| File | Contents |
|---|---|
| `new-strict-replays.*.csv` | The six new tests (VEHICLE-05/06/07, SECURITY-01, CORRECTION-07/08) |
| `new-07-unverified-security-backtrack.*.csv` | Same six, all in folder `07-unverified-security-backtrack` |
| `existing-strict-replays.*.csv` | The current 27 stricts (re-export / backup) |
| `all-strict-replays.*.csv` | Existing 27 + six new |

## Import order

1. Broaden the single Vehicle → Customer exit and publish (see HITL checklist).
2. Ensure folders exist: `01-input-routing` … `06-vehicle-recovery-offscript`.
3. Import `new-strict-replays.json.csv` (or the per-folder files).
4. For **VEHICLE-06**, confirm the Lookup tool override actually forces a technical
   failure twice; adjust in the UI if needed.
5. Run the new cases, then decide which to include in the quality gate.

## Platform constraint

Confirmed and unverified completion share **one** Vehicle → Customer exit. New
VEHICLE expected outcomes refer to that shared exit, not a second edge.

## If import/run shows "execution error"

Likely causes from the first pack:

1. `tool_overrides` had `"test_url": null` while `mode` was `test_url` — Lookup then has no URL.
2. Column names did not match the Insait import template, so turns/overrides were empty or invalid.
3. **VEHICLE-06** forces HTTP 500; some runners treat that as a harness execution error.

Use these fixed files instead (also copied to `~/Downloads`):

| File | Purpose |
|---|---|
| `new-strict-replays.minimal.csv` | Simplest: `Name`, `Folder`, `Expected Outcome`, newline-separated `Flow Questions`; **no** tool overrides |
| `new-strict-replays.fixed.json.csv` | API-shaped fields with a **real** proxy `test_url` |
| `new-strict-replays.fixed.wide.csv` | `Question 1`…`Question N`; no overrides |
| `new-strict-replays.no-vehicl06.minimal.csv` | Same as minimal but skips VEHICLE-06 |

Preferred retry order: import `new-strict-replays.minimal.csv` (or the no-VEHICLE-06 variant), map columns in the UI if prompted, then run. Set Lookup test URL in each test to the live proxy only if the importer does not inherit the tool default.

