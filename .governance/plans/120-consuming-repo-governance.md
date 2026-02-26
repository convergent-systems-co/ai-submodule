# Fix: Consuming Repos Don't Replicate Governance Review Flow

**Author:** Coder (agentic)
**Date:** 2026-02-23
**Status:** completed
**Issue:** #120
**Branch:** itsfwcp/fix/120/consuming-repo-governance

---

## 1. Objective

Make the Dark Factory governance workflow function identically in consuming repos (where files are under `.ai/`) and in the ai-submodule repo itself (where files are at the root). Fix SSH URL issue for CI compatibility.

## 2. Rationale

The governance workflow has hard-coded root-relative paths (`governance/emissions/`, `.governance/policy-engine.py`). When symlinked into consuming repos, these paths don't resolve because the files are under `.ai/`. This means consuming repos never find emissions, never run the policy engine, and get no governance review.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Separate workflow file for consuming repos | Yes | Maintenance burden — two files to keep in sync |
| Environment variable for prefix | Yes | Fragile; still a single workflow with conditional paths is cleaner |
| Auto-detect prefix in workflow | Yes — **chosen** | Single workflow works in both contexts |

## 3. Scope

### Files to Create

None.

### Files to Modify

| File | Change Description |
|------|-------------------|
| `.github/workflows/dark-factory-governance.yml` | Auto-detect `.ai/` prefix; check both emission paths; adjust policy engine paths |
| `init.sh` | Add SSH→HTTPS URL conversion for `.gitmodules` |
| `governance/docs/copilot-auto-fix.md` | N/A — not related |

### Files to Delete

None.

## 4. Approach

1. Modify governance workflow to auto-detect context (root vs `.ai/` prefix)
2. Add SSH→HTTPS URL conversion to init.sh
3. Add a documentation section explaining consuming repo governance setup

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Workflow YAML | Verify find commands resolve both paths |
| Manual | init.sh | Verify SSH URL conversion logic |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Workflow change breaks ai-submodule CI | Low | High | Test root-relative paths still work |
| SSH conversion matches too broadly | Low | Low | Only target `.gitmodules` entries for .ai |

## 7. Dependencies

N/A.

## 8. Backward Compatibility

Fully backward compatible — existing root-relative paths still work; new `.ai/` paths are additive.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Workflow changes affect CI/CD pipeline |
| documentation-review | Yes | New documentation for consuming repos |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Auto-detect prefix rather than env var | Simpler, no configuration needed |
