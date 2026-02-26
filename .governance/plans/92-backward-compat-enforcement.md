# Backward Compatibility Enforcement Workflow and Schema

**Author:** Code Manager (agentic)
**Date:** 2026-02-22
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/92
**Branch:** itsfwcp/feat/92/backward-compat-enforcement

---

## 1. Objective

Create governance artifacts that enable the Code Manager to systematically check for breaking changes before merging. This converts the existing documented convention ("All changes must be additive") into an enforceable workflow with structured audit records.

## 2. Rationale

CLAUDE.md states that changes must be additive and breaking changes require migration plans and version bumps. However, this is only documented — there's no enforcement mechanism, no structured record format, and no workflow for the Code Manager to follow. Phase 5 requires backward compatibility enforcement; creating the governance artifacts now prepares for that.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Add breaking change detection to CI | Yes | Requires runtime code; this repo is configuration-only |
| Only document the convention | Yes | Already done — no enforcement |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/breaking-change.schema.json` | JSON Schema for recording breaking changes |
| `governance/prompts/backward-compatibility-workflow.md` | Agentic workflow for checking backward compatibility |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Check off "Backward compatibility enforcement" in Phase 5 |

### Files to Delete

None.

## 4. Approach

1. Create `breaking-change.schema.json` with fields for: change identification, affected artifact, change classification, version tracking, migration path, consumer impact, rollback strategy
2. Create `backward-compatibility-workflow.md` with steps for: artifact type detection, version comparison, contract compatibility check, migration plan requirement, consumer impact assessment
3. Update `GOALS.md`

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | `breaking-change.schema.json` | Valid JSON Schema Draft 2020-12 |
| Manual review | All files | Cross-reference with existing schema patterns |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Over-engineering the schema | Low | Low | Follow existing schema patterns; keep fields practical |

## 7. Dependencies

- [x] Existing enforcement artifacts for pattern reference
- [x] CLAUDE.md backward compatibility convention

## 8. Backward Compatibility

Purely additive. No breaking changes.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Mandatory per all policy profiles |
| threat-modeling | Yes | Mandatory per all policy profiles |
| cost-analysis | Yes | Mandatory per all policy profiles |
| documentation-review | Yes | Mandatory per all policy profiles |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
