# Domain docs

This is a single-context repository.

## Before domain work

When they exist, read:

- `CONTEXT.md` at the repository root
- relevant decisions under `docs/adr/`
- `ARCHITECTURE.md` for system boundaries and deployment intent

If a term is ambiguous or a decision is difficult to reverse, resolve it
explicitly and record the durable result in the appropriate domain document.
Do not create a glossary or ADR for routine implementation details.

## Layout

```text
/
├── CONTEXT.md
├── docs/
│   ├── adr/
│   └── agents/
└── src/
```

Use the vocabulary established in `CONTEXT.md` when it exists. If a change
conflicts with an existing ADR, call out the conflict before proceeding.
