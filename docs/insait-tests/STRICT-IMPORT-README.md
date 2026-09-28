# Fix "execution error" on Insait test runs

## What your run screen shows

- **No configuration snapshot was captured for this run** → the harness failed before a normal
  scored conversation, not a soft eval miss.
- **Simulation model: claude-haiku-4.5** → this run was treated as a **simulate/persona** run.
  Our CSV packs are **strict scripted** turns (`flow_questions`), not simulate personas.

## Do this in order

1. In Testing, open folder `07-unverified-security-backtrack` and **delete** the broken imported tests from prior attempts.
2. Confirm you are creating/importing **Strict Replay** tests (same type as CORE-01), **not**
   Simulate Replay.
3. First import and run only:
   `strict-07.smoke-core-clone.csv`
   (one Mandatory happy-path clone).
4. If that smoke test also shows execution error:
   - Run an **existing** UI-created test such as CORE-01 (never imported).
   - If CORE-01 also execution-errors → agent/publish/platform issue (publish agent, warm proxy,
     check Lookup tool test URL). Not a CSV problem.
   - If CORE-01 passes but smoke fails → import column mapping is wrong; download Insait's
     official Strict CSV template from the UI and map our columns into it.
5. If smoke passes, import `strict-07.pipe.csv` (preferred) or `strict-07.minimal.csv`.
6. Run them as **Strict Replay** / QA flow eval — do **not** enable a simulation model.

## Files (also in ~/Downloads)

| File | Use |
|---|---|
| `strict-07.smoke-core-clone.csv` | One known-good path to validate import+runner |
| `strict-07.pipe.csv` | Five new tests; turns separated by ` \| ` |
| `strict-07.minimal.csv` | Same five; newline-separated Flow Questions |
| `strict-07.json-questions.csv` | Same five; JSON array in flow_questions |
| `strict-07.with-tool-override.csv` | Same five + Lookup override with real proxy URL |

VEHICLE-06 (forced HTTP 500) is omitted until the Strict path is green.
