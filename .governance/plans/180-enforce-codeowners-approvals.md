# Enforce CODEOWNERS Approvals

**Author:** Code Manager (agentic)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/180
**Branch:** itsfwcp/fix/180/enforce-codeowners-approvals

---

## 1. Objective

Update the governance framework so that `init.sh` merges `@github-actions[bot]` into consuming repos' CODEOWNERS files, enabling the governance workflow's approvals to satisfy code owner review requirements (when combined with appropriate ruleset configuration).

## 2. Rationale

Currently, `config.yaml` CODEOWNERS rules do not include `@github-actions[bot]`, and `init.sh` only generates CODEOWNERS when the file is empty or missing. Consuming repos that already have a CODEOWNERS file get no governance entries merged in. This means the agentic loop's approvals cannot satisfy `require_code_owner_review` rulesets.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Only update config.yaml (no merge logic) | Yes | Repos with existing CODEOWNERS would still not get the entries |
| Full CODEOWNERS overwrite on every init | Yes | Destructive — would lose project-specific rules |
| Merge governance entries into existing CODEOWNERS | Yes (chosen) | Additive, non-destructive, respects existing rules |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `config.yaml` | Add `@github-actions[bot]` to all CODEOWNERS owner entries |
| `init.sh` | Update `configure_codeowners()` to merge governance entries into existing CODEOWNERS; update `generate_codeowners()` header comment |
| `governance/docs/repository-configuration.md` | Update to reflect merge behavior and `@github-actions[bot]` inclusion |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. **Update `config.yaml`** — Add `@github-actions[bot]` to `codeowners.default_owner` and each rule's `owners` list
2. **Update `generate_codeowners()`** — Remove the "Bot approvals do NOT satisfy" warning since the bot is now explicitly included
3. **Update `configure_codeowners()`** — Replace the "skip if exists" logic with merge logic that:
   - Reads existing CODEOWNERS content
   - For each governance-required pattern: check if the pattern exists; if so, ensure required owners are present; if not, append the rule
   - Preserves all existing rules and comments
   - Adds a managed-section marker so subsequent runs can identify and update governance entries
4. **Update `repository-configuration.md`** — Document the new merge behavior
5. **Address bot renaming** — Document that `github-actions[bot]` cannot be renamed (it's a GitHub system account); custom GitHub App creation would be needed for a different bot identity

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | init.sh | Run init.sh in a test context to verify CODEOWNERS generation |
| Review | config.yaml | Verify all entries include @github-actions[bot] |

This is a configuration-only repo with no test runner.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Merge logic corrupts existing CODEOWNERS | Low | Medium | Use marker-based managed section; only modify between markers |
| `@github-actions[bot]` still doesn't satisfy code owner review | Medium | Low | Document that bypass actor configuration is also needed |

## 7. Dependencies

- None — self-contained changes

## 8. Backward Compatibility

Fully backward compatible. The merge logic is additive — existing CODEOWNERS entries are preserved. Repos without CODEOWNERS get the full generated file as before.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Script logic changes |
| security-review | Yes | CODEOWNERS affects access control |
| documentation-review | Yes | Doc updates included |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Use managed-section markers in CODEOWNERS | Allows init.sh to update governance entries on subsequent runs without touching user-added rules |
| 2026-02-24 | Bot renaming not possible | `github-actions[bot]` is a GitHub system account; would require custom GitHub App |
