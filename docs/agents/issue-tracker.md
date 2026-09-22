# Issue tracker: Local Markdown

This is a small solo assignment, so planning stays in the repository instead
of using a remote issue tracker.

## Conventions

- One feature or milestone per directory:
  `.scratch/<feature-slug>/`
- The feature spec is `.scratch/<feature-slug>/spec.md`.
- Implementation tickets are separate files under
  `.scratch/<feature-slug>/issues/`, numbered from `01`.
- Each ticket has a `Status:` line near the top.
- Use `Blocked by:` only when a ticket genuinely depends on another ticket.
- Append discussion under a `## Comments` heading.

`.scratch/` is git-ignored because it contains working plans and disposable
agent coordination state. Durable decisions belong in tracked documentation,
such as `CONTEXT.md`, `ARCHITECTURE.md`, or `docs/adr/`.

## Workflow

When a skill asks to publish an issue, create the relevant Markdown file
locally. Do not create GitHub/GitLab issues, labels, tags, branches, or
commits unless the user explicitly asks for them.
