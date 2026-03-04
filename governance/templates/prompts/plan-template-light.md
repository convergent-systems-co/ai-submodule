# Lightweight Plan Template

Use this template for fast-track changes: documentation updates, typo fixes, chores, and test-only changes. For non-trivial changes, use the full `plan-template.md` instead.

Plans must be saved to `governance/plans/` (dark-forge) or `.artifacts/plans/` (consuming repos).

---

## Instructions

Copy the template below into a new file. Fill in every section. If a section is not applicable, state "N/A".

---

```markdown
# [Plan Title]

**Author:** [agent name or human author]
**Date:** [YYYY-MM-DD]
**Status:** [draft | approved | completed | abandoned]
**Issue:** [link to GitHub issue, if applicable]
**Change Type:** [docs_only | chore | typo_fix | test_only]

---

## 1. Objective

What does this change accomplish? One or two sentences.

## 2. Scope

### Files Changed

| File | Change |
|------|--------|
| [path] | [what changes] |

## 3. Approach

Brief description of how the change will be made. Numbered steps if more than one action is required.

1. [Step 1]
2. [Step 2]
```

---

## When to Use This Template

- Documentation-only changes (README, guides, inline comments)
- Typo and formatting fixes
- Chore tasks (dependency bumps, config cleanup, CI tweaks)
- Test-only additions or fixes

If the change touches application source code, infrastructure, APIs, or security-sensitive paths, use the full `plan-template.md`.

## Governance

Fast-track changes use the `fast-track` policy profile with reduced panel requirements. Security-review is always required regardless of change type.
