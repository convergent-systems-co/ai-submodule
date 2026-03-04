# Your First Governed PR

A step-by-step guide from zero to your first governance-reviewed pull request. No prior knowledge required.

**Time:** ~5 minutes

---

## Prerequisites

- A GitHub repository with AI-Submodule installed (see [cheat sheet](cheat-sheet.md) step 1)
- A branch with at least one commit

## Step 1: Create a Branch

```bash
git checkout -b my-first-governed-pr
```

## Step 2: Make a Change

Edit any file in your repo. For this guide, we will add a comment to an existing file:

```bash
echo "# Governance test" >> README.md
git add README.md
git commit -m "docs: test governance review"
```

## Step 3: Push and Open a PR

```bash
git push -u origin my-first-governed-pr
gh pr create --title "docs: test governance review" --body "Testing governance panel reviews."
```

Or open a PR through the GitHub web interface.

## Step 4: Watch Governance Run

Within a few minutes, you will see:

1. **GitHub Actions workflow** — `dark-factory-governance.yml` runs automatically
2. **Panel comments** — governance panels post findings as PR review comments
3. **Approval or feedback** — `github-actions[bot]` approves if all panels pass, or requests changes if findings need attention

## Step 5: Read the Findings

Panel comments follow this format:

```
## Security Review

**Finding:** No hardcoded secrets detected.
**Severity:** info
**Action:** None required.
```

### What the Severities Mean

| Severity | Action Required |
|----------|----------------|
| Critical | Must fix before merge |
| High | Must fix before merge |
| Medium | Should fix; explain if you skip |
| Low | Nice to have |
| Info | Informational only |

## Step 6: Fix or Acknowledge

- **Critical/High:** Push a fix commit. Governance re-runs automatically.
- **Medium:** Fix it or add a comment explaining why you're skipping.
- **Low/Info:** No action needed.

## Step 7: Merge

Once all critical/high findings are resolved:
1. The governance workflow approves the PR
2. Merge via GitHub (squash merge recommended)

## What Just Happened

Your PR was automatically reviewed by governance panels that checked for:
- Security vulnerabilities
- Code quality issues
- Documentation completeness
- Policy compliance

All of this happened without any configuration beyond the initial `init.sh` install.

---

## Next Steps

- [Check governance status](cheat-sheet.md) — `bash .ai/bin/governance-status.sh`
- [Customize your policy](progressive-disclosure.md#tier-2-customization) — when you need different review rules
- [Learn about panels](progressive-disclosure.md#tier-1-your-first-pr) — understand what each panel reviews
