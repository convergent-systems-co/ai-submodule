# Add Issue Templates for Consuming Repositories

**Author:** Coder (agentic)
**Date:** 2026-02-21
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/35
**Branch:** NETWORK_ID/feat/35/issue-templates

---

## 1. Objective

Create GitHub issue templates that ensure users provide structured intent when filing issues, and update `init.sh` to install these templates in consuming repositories.

## 2. Rationale

The agentic startup sequence requires clear acceptance criteria to determine if an issue is actionable. Without structured templates, users file free-form issues that frequently need the `refine` label, adding friction and delay.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| No templates, rely on refine label | Yes | Creates unnecessary back-and-forth |
| Single generic template | Yes | Different issue types need different fields |
| GitHub issue forms (YAML) | **Selected** | Structured fields, dropdowns, validation — better for AI parsing |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.github/ISSUE_TEMPLATE/feature-request.yml` | Feature/enhancement request form |
| `.github/ISSUE_TEMPLATE/bug-report.yml` | Bug report form |
| `.github/ISSUE_TEMPLATE/config.yml` | Template chooser configuration |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `init.sh` | Add step to copy issue templates to consuming repo's `.github/ISSUE_TEMPLATE/` |
| `config.yaml` | Not needed — templates are auto-discovered by GitHub from `.github/ISSUE_TEMPLATE/` |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Create issue form templates using GitHub's YAML-based issue forms:
   - **Feature request**: Title, description, acceptance criteria, risk level, priority
   - **Bug report**: Title, description, steps to reproduce, expected vs actual, severity
   - **Config**: Links to blank issue for anything that doesn't fit

2. Update `init.sh` to copy templates to consuming repo when running outside the `.ai` repo itself

3. Update `config.yaml` to document the new template paths

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Template syntax | YAML | Verify templates parse as valid GitHub issue forms |
| PR test | Full | Templates visible in this repo's "New Issue" page after merge |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Templates too restrictive for users | Medium | Low | Include blank issue option in config.yml |
| init.sh breaks on existing repos | Low | Medium | Idempotent copy with directory creation |

## 7. Dependencies

- [x] GitHub supports YAML-based issue forms (available since 2021)

## 8. Backward Compatibility

Additive change. Existing repos without templates are unaffected until they re-run `init.sh`.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Shell script changes |
| documentation-review | Yes | User-facing templates |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Use YAML issue forms over markdown templates | Structured fields enable better AI parsing |
| 2026-02-21 | Include blank issue option | Avoid blocking users who need free-form issues |
