# Governance Review CI Workflow

**Author:** Team Lead (agentic)
**Date:** 2026-02-20
**Status:** approved
**Branch:** NETWORK_ID/governance-review-workflow

---

## 1. Objective

Create a GitHub Actions workflow that validates panel structured emissions on PRs and posts an approving review, enabling the governance framework to satisfy the enterprise review requirement programmatically.

## 2. Rationale

Enterprise rulesets on SET-Apps require 1 approving review before merge. The agentic loop runs panels locally but has no way to post reviews as a distinct identity. A CI workflow bridges this gap — it validates emissions committed to the PR branch and posts a review as either a GitHub App ("Dark Forge Manager") or `github-actions[bot]`.

## 3. How It Works

```
Agentic loop (local)                     CI (GitHub Actions)
─────────────────────                     ───────────────────
1. Run panel review
2. Produce structured emission JSON
3. Commit to .ai/emissions/ on PR branch
4. Push                                   5. Workflow triggers on PR
                                          6. Validate emissions against schema
                                          7. Evaluate against policy thresholds
                                          8. Post approving review (or block/comment)
```

### Two identity modes:

| Mode | Identity | Setup Required |
|------|----------|---------------|
| Default | `github-actions[bot]` | None — uses GITHUB_TOKEN |
| GitHub App | "Dark Forge Manager" | Create app, add GOVERNANCE_APP_ID + GOVERNANCE_APP_PRIVATE_KEY secrets |

## 4. Scope

### Files Created

| File | Purpose |
|------|---------|
| `.github/workflows/governance-review.yml` | CI workflow |
| `emissions/.gitkeep` | Directory for structured emissions on PR branches |

## 5. Policy Evaluation Logic

Thresholds from `policy/default.yaml`:

| Decision | Condition |
|----------|-----------|
| **approve** | All valid, all approve, confidence >= 0.85, risk low/negligible |
| **human_review_required** | Confidence < 0.70, not all approve, high risk, or panel requests human review |
| **block** | Invalid emissions, confidence < 0.40, critical/high policy flags |

## 6. GitHub App Setup (for "Dark Forge Manager" identity)

1. Org admin creates GitHub App named "Dark Forge Manager"
2. Permissions: `pull_requests: write`, `contents: read`
3. Install on SET-Apps org (or specific repos)
4. Add `GOVERNANCE_APP_ID` as a repository variable
5. Add `GOVERNANCE_APP_PRIVATE_KEY` as a repository secret
6. Workflow automatically detects and uses the app token

Without the app, the workflow falls back to `github-actions[bot]`.
