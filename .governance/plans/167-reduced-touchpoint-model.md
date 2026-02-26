# Reduced Human Touchpoint Model — Phase 5e Policy Profile

**Author:** Code Manager (agentic)
**Date:** 2026-02-24
**Status:** completed
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/167
**Branch:** itsfwcp/feat/167/reduced-touchpoint-model

---

## 1. Objective

Create a policy profile that maximizes autonomous operation by requiring human approval only when policy overrides are invoked, security-critical findings are dismissed, or aggregate confidence drops below threshold. This completes Phase 5e (Spec-Driven Interface).

## 2. Rationale

The existing profiles represent three points on a spectrum:
- `fin_pii_high` — maximum human oversight (auto-merge disabled)
- `infrastructure_critical` — high automation with strict conditions
- `default` — balanced automation with human escalation

The reduced touchpoint model extends this spectrum to near-full autonomy, serving repos that have mature governance pipelines and want minimal human intervention during routine development.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Modify `default.yaml` to be more permissive | Yes | Would change behavior for all existing consumers; additive profile is safer |
| Create a "fully autonomous" profile with no human gates | Yes | Zero human oversight on policy overrides violates governance principles |
| Add a flag to `default.yaml` instead of a new profile | Yes | Profile-level separation matches the existing pattern and is cleaner for consumers |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/policy/reduced_touchpoint.yaml` | New policy profile with minimal human intervention requirements |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Check off "Reduced human touchpoint model" item in Phase 5e; update Phase 5 status if all 5e items are complete |
| `CLAUDE.md` (root `.ai/CLAUDE.md`) | Update Phase 5e status and policy profile listing |
| `README.md` | Update Phase 5e status in architecture/phase sections |

### Files to Delete

None.

## 4. Approach

1. Create `governance/policy/reduced_touchpoint.yaml` following the same structure as existing profiles:
   - Lower confidence threshold for auto-merge (0.75 vs 0.85 in default)
   - Fewer escalation rules — only trigger human review for:
     - Policy override requests
     - Dismissed critical/high security findings
     - Confidence below minimum floor (0.50)
   - Auto-merge enabled with broader conditions (accepts medium risk if all panels approve)
   - Auto-remediate with more allowed actions
   - Same required panels as default (governance coverage unchanged)
   - Override requires only 1 approval (vs 2 in default) but still requires justification
2. Update GOALS.md to check off the item
3. Update CLAUDE.md with new profile reference
4. Update README.md with Phase 5e completion status

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | Profile YAML | Verify YAML structure matches existing profile patterns |
| Manual review | Policy logic | Ensure escalation rules are internally consistent and don't create impossible merge states |

No automated tests — this is a configuration-only repo.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Profile allows merges that should have human review | Low | Medium | Security-critical dismissals still require human review; policy override always requires human approval |
| Consumers adopt profile without understanding implications | Low | Medium | Profile description clearly documents what is automated and what requires human intervention |
| Breaking change if consumers reference profile names | Low | Low | Additive — no existing profiles are modified |

## 7. Dependencies

- [x] Default policy profile structure (exists)
- [x] Phase 5e formal spec schema (PR #163)
- [x] Phase 5e acceptance verification workflow (PR #165)

## 8. Backward Compatibility

Fully backward compatible. This adds a new profile without modifying existing ones. Consumers must explicitly opt in by setting `profile: reduced_touchpoint` in their project configuration.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Standard governance requirement |
| security-review | Yes | Policy file changes require security review |
| documentation-review | Yes | Documentation updates included |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Set auto-merge confidence threshold at 0.75 | Lower than default (0.85) but still requires majority panel confidence; matches the "reduced touchpoint" intent |
| 2026-02-24 | Keep all required panels from default profile | Governance coverage should not decrease; only human escalation frequency decreases |
| 2026-02-24 | Accept medium risk for auto-merge when all panels approve | Key differentiator from default — medium risk with unanimous panel approval is safe for mature repos |
