# Fix Missing Panel Emissions in Governance CI

**Author:** Team Lead (agentic)
**Date:** 2026-02-21
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/49
**Branch:** NETWORK_ID/fix/49/missing-panel-emissions

---

## 1. Objective

Add baseline emission files for `security-review` and `ai-expert-review` panels so the governance CI workflow evaluates all expected panels instead of blocking on missing required panels.

## 2. Rationale

The governance CI reads static JSON emissions from `governance/emissions/`. Only `code-review.json` and `documentation-review.json` exist. The `default.yaml` policy profile lists `security-review` as a required panel and `ai-expert-review` as an optional panel (triggered on governance file changes). Since this repo IS a governance repo, `ai-expert-review` should always trigger. The policy engine blocks PRs because `security-review` is required but has no emission.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Remove security-review from required panels | Yes | Security review should be required — the policy is correct |
| Generate emissions dynamically in CI | Yes | Requires LLM API key in CI — not yet available (Phase 5) |
| Add static baseline emissions | Yes | Selected — matches existing pattern, fixes the immediate bug |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/emissions/security-review.json` | Baseline emission for the security review panel |
| `governance/emissions/ai-expert-review.json` | Baseline emission for the AI expert review panel |

### Files to Modify

None.

### Files to Delete

None.

## 4. Approach

1. Create `security-review.json` conforming to `panel-output.schema.json`, using personas from `security-review.md` panel definition
2. Create `ai-expert-review.json` conforming to `panel-output.schema.json`, using personas from `ai-expert-review.md` panel definition
3. Validate both files against the schema locally
4. Commit and push

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | Both new files | Run policy engine locally to validate emissions parse correctly |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Static emissions don't reflect actual change risk | Medium | Low | This matches the existing pattern; real per-PR panels are a Phase 5 feature |

## 7. Dependencies

None.

## 8. Backward Compatibility

Additive only. Existing emissions unchanged.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| Code Review | Yes | Changes governance enforcement artifacts |
| AI Expert Review | No | Changes affect governance pipeline behavior (optional per policy) |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Use static baselines matching existing pattern | Dynamic generation requires LLM in CI (Phase 5) |
