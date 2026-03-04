# Copilot Recommendation Tracking

This document describes how the governance pipeline tracks, resolves, and audits Copilot review recommendations as part of the Phase 4 review cycle.

## Overview

When Copilot reviews a PR, it may produce recommendations of varying severity. The governance pipeline automatically creates tracked sub-issues for medium and higher severity recommendations, ensuring every significant recommendation has a clear disposition and audit trail.

This workflow is implemented as **Phase 4e-bis** in the startup sequence (`governance/prompts/startup.md`), executed between the CI & Copilot Review Loop (Phase 4e) and Pre-Merge Thread Verification (Phase 4f).

## Issue Creation Criteria

| Severity | Action | Tracked as Issue |
|----------|--------|:----------------:|
| Critical | Must fix | Yes |
| High | Must fix | Yes |
| Medium | Should fix | Yes |
| Low | Acknowledge in PR comment | No |
| Info | Acknowledge in PR comment | No |

**Rationale:** Tracking low/info recommendations as issues creates noise without governance value. These are acknowledged in PR comments for the record but do not require formal resolution tracking.

## Sub-Issue Format

Each tracked recommendation is created as a GitHub issue with the following structure:

```bash
gh issue create --title "copilot-rec: <summary> (PR #<pr-number>)" \
  --label "copilot-recommendation" --label "<severity>" \
  --body "## Copilot Recommendation

**PR:** #<pr-number>
**File:** <file>
**Line:** <line>
**Severity:** <severity>

### Recommendation
<body>

### Resolution
_Pending_"
```

**Labels:**
- `copilot-recommendation` — identifies the issue as a Copilot recommendation (applied to all)
- `<severity>` — one of `critical`, `high`, or `medium` (matches the classification from Phase 4e)

## Resolution Types

Every recommendation sub-issue must be resolved with one of three dispositions before the PR can merge.

### Implemented

The recommendation was accepted and a code change was made to address it.

```bash
gh issue close <rec-issue> --comment "Implemented in <sha>. Verified by Tester."
```

- Close as **completed**
- Reference the commit SHA that addresses the recommendation
- The Test Evaluator persona verifies the fix as part of Phase 4

### Dismissed

The recommendation was reviewed and intentionally not implemented.

```bash
gh issue close <rec-issue> --reason "not planned" --comment "Dismissed: <rationale>"
```

- Close as **not planned**
- A documented rationale is **required** — the DevOps Engineer will block merge if a dismissed recommendation lacks rationale
- Valid rationales include: false positive, not applicable to this codebase, conflicts with existing architecture decisions, addressed by other means

### Deferred

The recommendation is valid but will be addressed in a future iteration.

```bash
gh issue comment <rec-issue> --body "Deferred to #<follow-up-issue>. Will address in next iteration."
```

- Leave the issue **open**
- Link to a follow-up issue that will address the recommendation
- The follow-up issue must exist before the PR can merge

## Summary Table

After all recommendations are resolved, a summary table is posted as a comment on the PR:

```
## Copilot Recommendation Summary

| # | Recommendation | Severity | Disposition | Issue |
|---|---------------|----------|-------------|-------|
| 1 | <summary> | high | Implemented (abc1234) | #N |
| 2 | <summary> | medium | Dismissed (rationale) | #N |
| 3 | <summary> | critical | Deferred to #M | #N |
```

This table provides a single-glance view of how all recommendations were handled and serves as an audit record on the PR.

## DevOps Engineer Pre-Merge Verification

Before proceeding from Phase 4e-bis to Phase 4f (Pre-Merge Thread Verification), the DevOps Engineer verifies:

1. All medium+ recommendation sub-issues have a resolution (implemented, dismissed, or deferred)
2. No recommendation sub-issues remain in `_Pending_` state
3. Dismissed recommendations have documented rationale
4. Deferred recommendations are linked to existing follow-up issues
5. The summary table is posted on the PR

If any verification check fails, merge is blocked and resolution is assigned back to the Coder.

## Integration with Phase 4e

Phase 4e-bis is a direct continuation of Phase 4e (CI & Copilot Review Loop). The flow is:

1. **Phase 4e** — Poll CI, fetch Copilot recommendations, classify by severity, implement or dismiss, re-push
2. **Phase 4e-bis** — Create sub-issues for medium+ recommendations, track disposition, post summary table, DevOps Engineer verifies
3. **Phase 4f** — Pre-merge thread verification (GraphQL check for unresolved threads)

Phase 4e handles the _action_ (fixing or dismissing recommendations). Phase 4e-bis handles the _audit trail_ (ensuring every significant recommendation is formally tracked with a clear resolution record).

## When No Recommendations Exist

If Copilot produces no recommendations, or all recommendations are low/info severity, Phase 4e-bis is skipped entirely. The PR proceeds directly from Phase 4e to Phase 4f.
