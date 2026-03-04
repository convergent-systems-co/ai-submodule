# Threshold Auto-Tuning Policy

**Author:** Team Lead (agentic)
**Date:** 2026-02-23
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/117
**Branch:** NETWORK_ID/feat/117/threshold-auto-tuning-policy

---

## 1. Objective

Create a YAML policy configuration that defines the rules for adjusting governance confidence thresholds based on retrospective aggregation data. This policy specifies when, how, and by how much thresholds can be adjusted — with safety bounds to prevent runaway tuning.

## 2. Rationale

The governance pipeline uses static confidence thresholds (e.g., 0.85 for auto-merge, 0.70 for escalation). These values were chosen as reasonable defaults but may not be optimal for all repositories or over time. A threshold auto-tuning policy allows the system to self-adjust based on empirical data while maintaining human oversight for significant changes.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Modify thresholds directly in default.yaml | Yes | Mixes static policy with dynamic tuning rules; harder to audit and revert |
| Python-based tuning script | Yes | This is a config-only repo; YAML policy is consistent with the artifact model |
| Per-profile tuning rules | Yes (future) | Start with a single tuning policy; per-profile variants can extend later |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/policy/threshold-tuning.yaml` | Auto-tuning policy rules |
| `governance/docs/threshold-tuning.md` | Documentation for the auto-tuning mechanism |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Check off the threshold auto-tuning item in Phase 5b |
| `README.md` | Add policy file to repository structure listing |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

1. Create `threshold-tuning.yaml` with tuning rules, safety bounds, and approval gates
2. Create documentation explaining the mechanism
3. Update GOALS.md and README.md

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Policy file | Verify YAML syntax and logical consistency |
| Manual | Documentation | Verify accuracy of mechanism description |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Tuning rules are too aggressive | Low | Medium | Conservative safety bounds, human approval gate for large changes |
| Policy doesn't cover edge cases | Medium | Low | Extensible design with explicit fallback to human review |

## 7. Dependencies

- [x] Retrospective aggregation schema (PR #115, merged)
- [x] No other blocking dependencies

## 8. Backward Compatibility

Fully backward compatible. New policy file, no existing behavior changed.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New policy file |
| documentation-review | Yes | New docs + GOALS/README updates |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Standalone tuning policy file | Clean separation from static policy profiles |
| 2026-02-23 | Conservative safety bounds | Prevent runaway tuning; can be relaxed once proven |
