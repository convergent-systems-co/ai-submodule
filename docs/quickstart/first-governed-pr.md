# Quickstart: Your First Governed PR

**Time:** 5 minutes | **Prerequisites:** Governance installed ([setup guide](add-governance.md))

---

## Step 1: Create a Branch

```bash
git checkout -b my-first-governed-pr
```

## Step 2: Make a Change

Any change will trigger governance. For this quickstart, add a simple file:

```bash
echo "# Hello Governance" > HELLO.md
git add HELLO.md
git commit -m "docs: add hello file to test governance"
```

## Step 3: Push and Open a PR

```bash
git push -u origin my-first-governed-pr
gh pr create --title "docs: test governance review" --body "Testing automated governance reviews."
```

Or create the PR through the GitHub web UI.

## Step 4: Watch Governance Run

Within 1-2 minutes:

1. The `dark-factory-governance.yml` GitHub Action starts
2. Governance panels analyze your changes
3. Results appear as PR review comments

## Step 5: Read the Results

Panel findings look like this:

```
## Code Review

Severity: info
Finding: New markdown file adds documentation. No issues detected.
Action: None required.
```

### Severity Guide

| Severity | What to Do |
|----------|-----------|
| **Critical** | Must fix. PR cannot merge. |
| **High** | Must fix. PR cannot merge. |
| **Medium** | Should fix. Explain if skipping. |
| **Low** | Nice to have. |
| **Info** | For your awareness only. |

## Step 6: Merge

Once all critical and high findings are addressed:
1. `github-actions[bot]` approves your PR
2. Merge using your preferred method (squash recommended)

## What Just Happened

Your PR went through automated governance:
- **Code review panel** checked code quality
- **Security review panel** scanned for vulnerabilities
- **Documentation review panel** verified doc completeness
- **Policy engine** evaluated findings against your policy profile

All without any manual reviewer involvement.

## Clean Up

```bash
git checkout main
git branch -d my-first-governed-pr
```

---

## Next Steps

- [Customize policy profiles](customize-policy.md) - Different rules for different projects
- [Run the agentic loop](run-agentic-loop.md) - Let AI handle issues end-to-end
