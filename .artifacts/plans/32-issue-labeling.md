# Add Best-Practice Labels to Issues

**Author:** Coder (agentic)
**Date:** 2026-02-21
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/32
**Branch:** NETWORK_ID/chore/32/issue-labeling

---

## 1. Objective

Establish a best-practice labeling scheme across all repository issues. Create missing governance-critical labels (`refine`, priority tiers, `blocked`) and retroactively label all existing issues (open and closed).

## 2. Rationale

The startup sequence (`prompts/startup.md`) depends on labels for filtering and prioritization (`refine`, `blocked`, `wontfix`, `duplicate`, `P0`–`P4`, `bug`, `enhancement`). None of the 13 issues have any labels, making autonomous triage impossible.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Only label open issues | Yes | Closed issues benefit from labels for historical context |
| Create labels via config file | Yes | GitHub Labels API is the standard; no config-as-code tool exists in repo |
| Minimal labels only | Yes | Issue explicitly asks for "best-practice" model |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.plans/32-issue-labeling.md` | This plan file; no implementation files are created beyond this |

### Files to Modify

| File | Change Description |
|------|-------------------|
| N/A | No file modifications |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Create missing labels via `gh label create`:
   - `refine` — AI-only label meaning "needs human clarification before work begins"
   - `blocked` — Work cannot proceed due to external dependency
   - `P0` through `P4` — Priority tiers (P0 = critical, P4 = backlog)
   - `chore` — Maintenance/housekeeping tasks
   - `refactor` — Code restructuring without behavior change
   - `ci` — CI/CD related changes

2. Apply labels to all 13 issues (open + closed) based on their content:
   - Type labels: `bug`, `enhancement`, `documentation`, `chore`, `refactor`, `ci`
   - Priority labels where determinable from content

3. Commit the plan file

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual verification | All issues | Confirm labels appear correctly via `gh issue list --state all` |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Incorrect label assignment on closed issues | Low | Low | Labels can be updated retroactively |
| Missing a label the startup sequence needs | Low | Medium | Cross-reference startup.md filter criteria |

## 7. Dependencies

- [x] GitHub CLI authenticated with label management permissions

## 8. Backward Compatibility

No backward compatibility concerns. Adding labels is purely additive.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | No | No code changes |
| documentation-review | No | No doc changes |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Audit Record

### Labels Created

| Label | Color | Description |
|-------|-------|-------------|
| `refine` | `#fbca04` | Needs human clarification before AI can work on it |
| `blocked` | `#b60205` | Cannot proceed due to external dependency |
| `P0` | `#d93f0b` | Critical priority — immediate action required |
| `P1` | `#e99695` | High priority — address this sprint |
| `P2` | `#f9d0c4` | Medium priority — address soon |
| `P3` | `#c2e0c6` | Low priority — address when possible |
| `P4` | `#bfdadc` | Backlog — nice to have |
| `chore` | `#ededed` | Maintenance and housekeeping tasks |
| `refactor` | `#d4c5f9` | Code restructuring without behavior change |
| `ci` | `#0e8a16` | CI/CD pipeline changes |

### Labels Applied to Issues

| Issue | Title | Labels Applied |
|-------|-------|---------------|
| #5 | Create a Agile Coach Persona | `enhancement` |
| #6 | Create a FinOps Group | `enhancement` |
| #7 | MITRE Specialist | `enhancement` |
| #8 | AD MCP server for Entra | `enhancement` |
| #9 | Implement policy engine runtime | `enhancement` |
| #10 | Add dark-factory-governance.yml | `ci`, `enhancement` |
| #11 | Implement instruction decomposition | `enhancement`, `refactor` |
| #12 | Add auto-propagation workflow | `ci`, `enhancement` |
| #21 | AI Expert Persona review | `enhancement` |
| #22 | Fix agentic loop | `bug` |
| #26 | Branching Naming is incorrect | `bug` |
| #27 | Clean up all unused branches | `chore` |
| #32 | No labels on issues | `chore` |

## 11. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Include closed issues in labeling | Historical context aids future triage |
| 2026-02-21 | Use GitHub API directly, no config file | No label-as-code tooling exists in this repo |
