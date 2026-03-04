---
name: global-dev-git-review
description: "Review staged changes and suggest a conventional commit message"
status: production
tags: [dev, git, commit, review]
model: null
---

# Git Review and Commit Message

Review the currently staged changes and generate an appropriate conventional commit message.

## Workflow

1. **Inspect staged changes** by running `git diff --cached` (or `git diff --staged`).
2. **Identify the change type** from the diff:
   - `feat` -- new functionality or capability
   - `fix` -- bug fix or error correction
   - `refactor` -- code restructuring without behavior change
   - `test` -- adding or updating tests
   - `docs` -- documentation-only changes
   - `chore` -- build system, tooling, dependency updates
   - `perf` -- performance improvements
   - `ci` -- CI/CD configuration changes
   - `style` -- formatting, whitespace, linting (no logic change)
3. **Determine the scope** from the primary area of change (e.g., `auth`, `api`, `ui`, `config`). Omit scope if the change spans many areas.
4. **Write the subject line**:
   - Imperative mood ("add", not "added" or "adds")
   - Lowercase first word after the colon
   - No trailing period
   - Under 72 characters total
5. **Write the body** (if needed):
   - Explain **why** the change was made, not what (the diff shows what)
   - Wrap lines at 72 characters
   - Reference issue or ticket numbers with `#NNN` or `Closes #NNN`
6. **Check for problems** before suggesting the message:
   - Are unrelated changes mixed together? Recommend splitting if so.
   - Are there secrets, credentials, or large binaries staged? Warn immediately.
   - Is there a `.env`, `.pem`, or credentials file? Flag it and do not include in the commit.

## Output Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Provide the full commit message in a fenced code block. If the change is simple enough, the body and footer may be omitted. If issues should be closed, include `Closes #NNN` in the footer.

## Example

```
feat(auth): add OAuth2 token refresh flow

Implement automatic token refresh when access tokens expire within
5 minutes of a request. Refresh tokens are stored in the existing
session store with a 30-day TTL.

Closes #142
```
