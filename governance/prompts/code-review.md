# Code Review

Quick, focused review of a changeset (PR, diff, or snippet).

## Scope
Review only the **changed code** for:

1. **Correctness** - Does the change do what it claims?
2. **Edge cases** - What inputs or states could break it?
3. **Regressions** - Could this break existing behavior?
4. **Conventions** - Does it follow project patterns and style?

## Format
- Reference specific lines
- Classify each finding: must-fix, should-fix, or nit
- Suggest concrete fixes, not just problems

## When to Use
Use this prompt for PR-level reviews of bounded changesets. For deeper analysis, use the **Reviewer** or **Code Reviewer** personas. For adversarial stress-testing, use the **Adversarial Reviewer** persona.
