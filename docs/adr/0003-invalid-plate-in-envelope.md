# ADR 0003: Invalid plates are a lookup outcome in the response envelope

## Status

Accepted. Supersedes ADR 0001.

## Context

ADR 0001 rejected invalid plates at the Litestar/Pydantic seam with a framework
4xx, and left `ErrorCode.INVALID_REQUEST` reserved and never emitted. Three
facts changed that trade-off:

- The upstream `/docs` define the plate rule: 7 or 8 digits (Israeli format).
  It answers 422 (and documents 400) for anything else. The proxy accepted any
  alphanumeric string, so a typo reached the upstream and its 422 fell through
  to `UPSTREAM_UNAVAILABLE`. The flow told the applicant the service was down.
- The consumer is an Insait API node that feeds an LLM. The node routes on
  success or error, and the error branch has to produce a sentence. A Litestar
  `{"status_code":400,"detail":"Validation failed…","extra":[…]}` body is not
  speakable, and it can't be told apart from an outage.
- The assignment lists "validation failed" next to "vehicle not found" and "API
  not responding" as cases the flow must handle. A plate that breaks the
  registry's rule is a business outcome, like a plate the registry doesn't know.

Once upstream 400/422 map to `INVALID_REQUEST`, keeping proxy-side rejection
on 4xx would give the same applicant mistake two different surfaces,
depending on which layer caught it.

## Decision

The plate rule: strip surrounding whitespace, remove spaces, `-`, and `.`,
then require `^[0-9]{7,8}$`. The digits-only result is the canonical plate
sent upstream. The same rule parses the plate in upstream success payloads.

- A well-formed JSON request whose `license_plate` string breaks the plate
  rule returns **HTTP 200**
  `{success: false, data: null, error_code: "INVALID_REQUEST", message, trace_id}`.
  The upstream is **not** called, and the completion log carries no plate mask.
- An upstream 400 or 422 also maps to `INVALID_REQUEST` on HTTP 200. It still
  logs `upstream_request_failed` at WARNING, because once the proxy validates
  first, an upstream rejection means the two rules have drifted apart.
- Structural faults stay framework **4xx** (Litestar returns 400): a body that
  isn't JSON, a missing `license_plate`, a non-string value, or a string
  longer than 32 characters. These are integration bugs, not applicant typos.

## Considered options

- **Keep ADR 0001 (4xx for every invalid plate).** This is correct REST
  semantics and costs no code. It was rejected because the flow can't speak a
  framework body, and because upstream 400/422 would still need an envelope
  code, which splits one user error across two surfaces.
- **Map all validation failures to HTTP 200 with a global exception handler.**
  Rejected: a malformed body or a wrong type means the Insait node is
  misconfigured. Reporting that as a business outcome would hide it.

## Consequences

- One routable, speakable surface for every applicant-facing outcome. The
  Insait node branches on `error_code`. `INVALID_REQUEST` and
  `VEHICLE_NOT_FOUND` both mean "re-ask the plate".
- HTTP 200 for bad input is less RESTful. A client bug that sends a
  well-formed but wrong plate string shows up as a business outcome, not a
  4xx. The structural 4xx path limits the blast radius.
- Letters, and plates with other lengths, are now rejected. Dashed, dotted,
  and spaced plates are now accepted. This follows the upstream rule rather
  than a country-neutral one.
