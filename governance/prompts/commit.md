# Commit

Generate a commit message and PR description for staged changes.

## Commit Message Format

```
<type>(<scope>): <subject>

<body>
```

### Types
- `feat` — new functionality
- `fix` — bug fix
- `refactor` — restructuring without behavior change
- `test` — adding or updating tests
- `docs` — documentation only
- `chore` — build, tooling, dependency updates
- `perf` — performance improvement

### Rules
- Subject line: imperative mood, lowercase, no period, under 72 characters
- Body: explain **why**, not what (the diff shows what)
- Reference ticket/issue numbers when applicable
- One logical change per commit

## PR Description Format

```
## Summary
<1-3 bullet points describing the change>

## Motivation
<why this change is needed>

## Changes
<list of notable changes, grouped by area>

## Testing
<how this was verified>
```

## When to Use
Before committing, to generate a well-structured message from the current diff.
