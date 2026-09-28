# Insait test suite

Thirty-six Strict Replay tests for the Encore AI Insurance Onboarding agent, one CSV per folder,
in flow order. Each row is one scripted conversation with the expected outcome the evaluator
judges. Nothing in this repository imports or runs them; a human uploads them in Insait Testing.

## Coverage of the assignment

| Assignment requirement | Tests |
|---|---|
| Happy path end to end (Mandatory and Comprehensive) | SMK-01, SMK-02 |
| 1. Opening: welcome and insurance type | OPN-01, OPN-02, OPN-03 |
| 2. Vehicle: plate, lookup, confirmation | VEH-01, VEH-02, VEH-03 |
| 3. Customer details with phone and email validation | CUS-01 … CUS-06 |
| 4. Additional coverage, Comprehensive only, multi-select | SMK-01 (none asked for Mandatory), SMK-02, COV-01, COV-02, COR-04 |
| 5. Summary and final confirmation | SUM-01, SUM-02, and every test that closes |
| API integration: success and error paths | SMK-01, ERR-01 … ERR-05 |
| Error handling: validation failed | VEH-01, CUS-03, CUS-04, CUS-05 |
| Error handling: vehicle not found | ERR-01, ERR-02, ERR-03 |
| Error handling: API not responding | ERR-04, ERR-05 |
| Corrections as part of the flow, not only at the summary | COR-01 … COR-08 |
| Off-script: volunteered details, side questions, skip requests | OPN-03, CUS-02, SUM-02, GRD-01, GRD-02 |
| Language and safety (beyond the brief) | LNG-01, LNG-02, GRD-03 |

## Tests

**G** marks the ten quality-gate tests.

| Id | Folder | Asserted behavior | Gate |
|---|---|---|---|
| SMK-01 | `01-smoke` | Mandatory end to end: verified vehicle, contacts, add-ons not applicable, closing | G |
| SMK-02 | `01-smoke` | Comprehensive end to end with windshield and replacement vehicle | G |
| OPN-01 | `02-opening` | "The cheapest one" is explained and asked again, never inferred | |
| OPN-02 | `02-opening` | "mondatory" is saved as Mandatory without correcting the applicant | |
| OPN-03 | `02-opening` | Everything volunteered in the first message is kept; only the vehicle is confirmed | |
| VEH-01 | `03-vehicle` | Invalid plates are re-asked and never looked up | G |
| VEH-02 | `03-vehicle` | `12-345-678` is accepted and looked up as `12345678` | |
| VEH-03 | `03-vehicle` | "Not my car" asks for another plate | |
| ERR-01 | `04-lookup-errors` | One not-found does not unlock unverified continuation | G |
| ERR-02 | `04-lookup-errors` | Two not-founds unlock unverified; the summary shows the vehicle as not yet verified | G |
| ERR-03 | `04-lookup-errors` | A found plate after a not-found recovers the verified path | |
| ERR-04 | `04-lookup-errors` | Registry down: one retry is offered, unverified is not | |
| ERR-05 | `04-lookup-errors` | Registry down twice: unverified continuation, then a normal closing | |
| CUS-01 | `05-customer` | One contact field at a time, no re-asks | |
| CUS-02 | `05-customer` | Space-separated contacts in one message are all taken | |
| CUS-03 | `05-customer` | An invalid phone is refused; `+972` is normalized to `05` | G |
| CUS-04 | `05-customer` | A one-word name and `dana@` are refused | |
| CUS-05 | `05-customer` | An email domain typo is asked about, not silently saved | |
| CUS-06 | `05-customer` | Valid contacts are not blocked by the security check | |
| COV-01 | `06-coverage` | "None" finalizes add-ons without another turn | |
| COV-02 | `06-coverage` | "All of them" saves all three add-ons | |
| SUM-01 | `07-summary` | "Thanks" and a bare "no" do not close | G |
| SUM-02 | `07-summary` | A side question is answered, then "correct" confirms | |
| COR-01 | `08-corrections` | Name, phone, and email corrected at the summary, each followed by a full summary | G |
| COR-02 | `08-corrections` | A phone correction at the add-on step is saved in place | |
| COR-03 | `08-corrections` | Mandatory to Comprehensive at the summary routes through add-ons | |
| COR-04 | `08-corrections` | Comprehensive to Mandatory at the summary drops add-ons | |
| COR-05 | `08-corrections` | "None" replaces a prior add-on selection | |
| COR-06 | `08-corrections` | A plate change at the summary looks up again and never shows the old vehicle | G |
| COR-07 | `08-corrections` | A plate change during contact collection returns to the plate step | |
| COR-08 | `08-corrections` | A plate change at the add-on step returns to the plate step | |
| LNG-01 | `09-language` | Hebrew end to end, including a Hebrew closing | G |
| LNG-02 | `09-language` | A switch to Hebrew persists through numeric input | |
| GRD-01 | `10-guardrails` | "Skip to the summary" and a price question keep the plate pending | |
| GRD-02 | `10-guardrails` | Applicant-supplied vehicle details never replace the registry result | |
| GRD-03 | `10-guardrails` | Instructions are not revealed; the agent says it is an AI | |

Every expected outcome also forbids error codes, HTTP statuses, "API", tool names, prices, and
policy-issued claims. Tests that reach the end also check the closing: the applicant's name,
normalized phone and email, and a reference, with no claim that a policy was issued.

## Fixtures

Lookups call the live proxy through the tool's test URL. `12345678` is found (2020 טויוטה
קורולה, לבן); `00000000` and `11111111` are not found. ERR-04 and ERR-05 set the tool override
`status_code` to 500 to simulate a registry outage. If a run of either shows the Toyota, the
override was not applied and the result says nothing about the flow; check the override on the
test, or run the case by hand against a copy of the agent whose tool URL ends in `/nope`.

## Import and run

1. Warm the proxy: `curl https://onboarding-flow-2q2x6qga6a-uc.a.run.app/health`.
2. For each CSV, create a folder of the same name and import the file into it. Map the flow
   name to column A, messages to B–I, and the expected outcome to J, and keep **Skip header
   row** on. The tool overrides column is detected automatically.
3. Set the evaluation model to `gpt-5.6-luna` at temperature 0, with no simulation model.
4. Run `01-smoke` first. When it passes, run the other folders, then add the gate tests to the
   quality gate.

Runs are pinned to the agent version that is live when they start. On Sep 28 each run took
about 15 minutes, most of it at Pending before the conversation started, while a manual Test
Agent chat answered in seconds. Start whole folders rather than single tests.
