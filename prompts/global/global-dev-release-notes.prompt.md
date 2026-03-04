---
name: global-dev-release-notes
description: "Generate release notes from git history between two refs"
status: production
tags: [dev, git, release, documentation]
model: null
---

# Generate Release Notes

Generate human-readable release notes from the git history between two references (tags, branches, or commits).

## Workflow

1. **Determine the range** -- identify the previous release tag and the current ref:
   ```bash
   git tag --sort=-v:refname | head -5       # Recent tags
   git log --oneline <previous>..HEAD        # Commits in range
   ```
2. **Collect all commits** in the range and parse their conventional commit types.
3. **Group by category** (see categories below).
4. **Summarize each change** -- one line per commit, focusing on user-visible impact.
5. **Identify breaking changes** from commits with `BREAKING CHANGE:` in the body or `!` after the type.
6. **List contributors** who authored commits in the range.

## Categories

Group changes in this order (omit empty categories):

### Breaking Changes
Changes that require users to modify their code, configuration, or workflow. Always list these first with clear migration instructions.

### New Features
New capabilities added in this release (`feat:` commits).

### Bug Fixes
Issues resolved in this release (`fix:` commits).

### Performance Improvements
Speed, memory, or efficiency improvements (`perf:` commits).

### Documentation
Documentation additions or updates (`docs:` commits).

### Other Changes
Refactoring, test improvements, CI changes, dependency updates (`refactor:`, `test:`, `ci:`, `chore:` commits). Keep this section brief.

## Formatting Rules

- Each entry is a single line: `- Brief description of the change (#PR or commit hash)`
- Use active voice and user-facing language ("Add export to CSV" not "Implemented CSV export functionality in the download module")
- Group related commits into a single entry when they represent one logical change
- Omit merge commits, revert-then-redo sequences (mention only the final state), and automated dependency bumps (unless security-relevant)
- Include PR numbers or commit hashes for traceability

## Output Format

```markdown
# Release vX.Y.Z

**Date:** YYYY-MM-DD

## Breaking Changes
- Description of breaking change with migration steps (#NNN)

## New Features
- Description of feature (#NNN)

## Bug Fixes
- Description of fix (#NNN)

## Performance
- Description of improvement (#NNN)

## Documentation
- Description of doc change (#NNN)

## Other
- Description of other change (#NNN)

## Contributors
@username1, @username2, @username3
```

## Guidelines

- Write for the audience who uses the software, not the developers who built it.
- Focus on outcomes ("Faster page load for dashboards with 1000+ widgets") not implementation details ("Replaced O(n^2) loop with hash map in widget renderer").
- If the release is large (> 30 entries), add a 2-3 sentence "Highlights" section at the top.
- If the release fixes security vulnerabilities, call them out explicitly with severity.
