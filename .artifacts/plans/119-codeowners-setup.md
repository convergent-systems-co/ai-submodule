# Fix: CODEOWNERS Setup for Dark Forge and Consuming Repos

**Author:** Coder (agentic)
**Date:** 2026-02-23
**Status:** completed
**Issue:** #119
**Branch:** NETWORK_ID/fix/119/codeowners-setup

---

## 1. Objective

Populate the Dark Forge CODEOWNERS with meaningful ownership rules and improve init.sh CODEOWNERS generation for consuming repos to document governance workflow interaction.

## 2. Rationale

Empty CODEOWNERS makes `require_code_owner_review` a no-op. Consuming repos with populated CODEOWNERS are blocked by the governance workflow because `github-actions[bot]` approvals don't satisfy code owner review requirements.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Add bot to CODEOWNERS | Yes | GitHub CODEOWNERS doesn't support app/bot accounts as owners |
| Use PAT for governance workflow | Yes | Security concern — PATs have broad scope |
| Document the interaction | Yes — **chosen** | Pragmatic; provides clear guidance for each scenario |

## 3. Scope

### Files to Create

None.

### Files to Modify

| File | Change Description |
|------|-------------------|
| CODEOWNERS | Populate with rules matching config.yaml |
| init.sh | Improve CODEOWNERS generation with governance notes |
| governance/docs/repository-configuration.md | Document CODEOWNERS/governance interaction |

### Files to Delete

None.

## 4. Approach

1. Populate CODEOWNERS for the Dark Forge repo from config.yaml rules
2. Update init.sh generate_codeowners() to add governance interaction comment
3. Document the relationship in repository-configuration.md

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | CODEOWNERS | Verify GitHub recognizes ownership rules |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| CODEOWNERS blocks bot merges | Low | Medium | Document workarounds clearly |

## 7. Dependencies

N/A.

## 8. Backward Compatibility

Additive — existing consuming repos can re-run init.sh.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | CODEOWNERS affects access control |
| documentation-review | Yes | New documentation section |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Document rather than hack bot ownership | GitHub doesn't support bot accounts in CODEOWNERS |
