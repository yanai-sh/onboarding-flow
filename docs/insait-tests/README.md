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
| `new-<folder>.*.csv` | Same six, split by destination folder |
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
