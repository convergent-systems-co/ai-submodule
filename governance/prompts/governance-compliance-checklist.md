# Governance Compliance Checklist

This checklist defines the required governance steps for every PR in the Dark Factory pipeline, and how to verify each step was completed. The governance-compliance-review panel evaluates PRs against this checklist.

## Required Steps

### 1. Plan Created (Step 5 of startup.md)

**Requirement:** Every PR must have an implementation plan in `.plans/` created before implementation began.

**Verification:**
- Check if a file matching `.plans/{issue-number}-*.md` exists in the PR diff or on the branch
- The plan should have a status field (draft, in_review, approved, in_progress, completed)
- The plan should reference the issue number

**Severity if missing:** `high` — Plans are the audit trail for architectural decisions. Working without a plan violates the plan-first governance principle.

**Exceptions:**
- Trivial documentation-only changes (pure typo fixes) may use a minimal plan
- Plans are always required for code changes, schema changes, and policy changes

---

### 2. Panel Evaluation (Step 7 of startup.md)

**Requirement:** All required panels defined in the active policy profile must produce emissions for the PR.

**Verification:**
- Check `governance/emissions/` for JSON files matching required panel names
- Required panels (default profile): code-review, security-review, threat-modeling, cost-analysis, documentation-review, data-governance-review
- Each emission must conform to `governance/schemas/panel-output.schema.json`
- Each emission must contain valid structured JSON between `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers

**Severity if missing:** `critical` — Missing panels mean the PR has not been reviewed by the governance pipeline. Merge decisions without panel input are not governance-approved.

**Exceptions:**
- Policy profiles with `missing_panel_behavior: redistribute` allow missing optional panels
- Projects with `governance.skip_panel_validation: true` in project.yaml opt out

---

### 3. Copilot Review (Step 7b-7d of startup.md)

**Requirement:** Copilot recommendations must be fetched, classified, and addressed (implemented or dismissed with rationale).

**Verification:**
- Check PR comments for evidence of Copilot polling (agent status comments)
- If Copilot comments exist on the PR, verify each has a reply (fix confirmation or dismissal rationale)
- Minimum 2 polling attempts with 2-minute separation must have occurred
- Unaddressed Copilot recommendations of severity `critical` or `high` must block merge

**Severity if skipped:** `high` — Copilot is a formal review panel. Ignoring its output bypasses a governance gate.

**Exceptions:**
- If Copilot is not enabled for the repository, this step is `not_applicable`
- After 2+ polls with 2-minute gaps and no Copilot comments, the step passes

---

### 4. Documentation Updated (Step 6.4 of startup.md)

**Requirement:** Every PR must update affected documentation in the same commit(s) as the code change.

**Verification:**
- Check PR diff for changes to documentation files:
  - `GOALS.md` — if the change completes a goals item
  - `CLAUDE.md` (root and .ai/) — if personas, panels, phases, or conventions changed
  - `README.md` — if bootstrap, architecture, or policy descriptions changed
  - `DEVELOPER_GUIDE.md` — if onboarding information changed
  - `docs/**/*.md` — if governance layers, definitions, or logic changed
- If the change affects user-facing or governance-facing behavior, at least one documentation file should be modified
- If no documentation is needed, the commit message body should state: `Docs: no documentation updates required — [reason]`

**Severity if missing:** `medium` — Documentation gaps are recoverable but create knowledge debt. The retrospective (Step 7h) should catch this, but catching it at PR time is better.

**Exceptions:**
- Pure refactors with no user-facing changes may skip documentation if the commit message explains why
- Test-only PRs do not require documentation updates

---

### 5. Issue Tracking (Startup.md constraint)

**Requirement:** Every PR must be linked to a GitHub issue. Work without a corresponding issue violates the audit trail requirement.

**Verification:**
- Check PR body for `Closes #N`, `Fixes #N`, or `Resolves #N` references
- Check that the referenced issue exists and is open (or was closed by this PR)
- Check that the issue has been commented with PR status updates

**Severity if missing:** `medium` — Untracked work cannot be audited. The issue is the single source of truth for intent and decisions.

**Exceptions:**
- Automated PRs (submodule updates, dependency bumps) may reference the automation trigger instead of an issue

---

### 6. Review Thread Resolution (Step 7f-bis of startup.md)

**Requirement:** All review threads must be resolved or outdated before merge.

**Verification:**
- GraphQL `reviewThreads` query returns zero active unresolved threads
- Both Copilot-specific jq filter and author-agnostic GraphQL check must agree

**Severity if unresolved:** `critical` — Merging with unresolved feedback means reviewer concerns were ignored.

**Exceptions:**
- Outdated threads (on code that was subsequently changed) do not count as unresolved

---

### 7. CI Checks Passed (Step 7a of startup.md)

**Requirement:** All CI checks must pass before merge.

**Verification:**
- `gh pr checks` shows all checks passed or skipped (no failures)
- The governance workflow itself must have run and produced a decision

**Severity if failing:** `critical` — Merging with failed CI is never acceptable.

**Exceptions:**
- Checks in `skipping` state are acceptable (conditional checks that don't apply)

---

## Compliance Levels

| Level | Definition | Action |
|-------|-----------|--------|
| **Compliant** | All required steps passed or not_applicable | Proceed with merge |
| **Partially compliant** | Only `low` or `medium` violations | Proceed with warnings; create follow-up issues for gaps |
| **Non-compliant** | Any `critical` or `high` violation | Block merge; require remediation |

## Severity Mapping

| Severity | Steps | Merge Impact |
|----------|-------|-------------|
| `critical` | Panel evaluation missing, review threads unresolved, CI failed | **Block merge** |
| `high` | Plan missing, Copilot review skipped | **Block merge** |
| `medium` | Documentation not updated, issue not tracked | **Warning** — create follow-up |
| `low` | Minor documentation gaps, optional panel missing | **Info only** |
