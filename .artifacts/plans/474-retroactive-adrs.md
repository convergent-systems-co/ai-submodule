# Retroactive ADRs for Key Architectural Decisions

**Author:** coder (agent)
**Date:** 2026-02-27
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/474
**Branch:** NETWORK_ID/docs/474/retroactive-adrs

---

## 1. Objective

Create an ADR template and 5 retroactive Architecture Decision Records documenting the key architectural decisions that shaped the Dark Forge. These complement the existing inline ADRs in `docs/decisions/README.md` by covering foundational decisions that predate the repository's ADR practice.

## 2. Rationale

The existing `docs/decisions/README.md` contains 11 ADRs documenting decisions from 2026-02-21 onward. However, five foundational architectural decisions were made earlier (retroactively dated 2024-06-01) and lack formal documentation: the deterministic policy engine, the panel-based review system, the agent persona model, the submodule distribution model, and the JIT context management strategy.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Append to README.md | Yes | Inline ADRs are harder to reference individually and the README is already 477 lines |
| Standalone files only | Yes | Selected approach — each ADR gets its own file for independent linking |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `docs/decisions/000-template.md` | Reusable ADR template |
| `docs/decisions/001-deterministic-policy-engine.md` | ADR for deterministic policy evaluation |
| `docs/decisions/002-panel-based-review-system.md` | ADR for 21 consolidated review prompts |
| `docs/decisions/003-agent-persona-model.md` | ADR for 6-agent architecture |
| `docs/decisions/004-submodule-distribution.md` | ADR for git submodule distribution |
| `docs/decisions/005-jit-context-management.md` | ADR for 4-tier JIT context |
| `.governance/plans/474-retroactive-adrs.md` | This plan |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `docs/decisions/README.md` | Add links to new standalone ADR files in the Table of Contents |

### Files to Delete

N/A — no files are deleted.

## 4. Approach

1. Create `.governance/plans/474-retroactive-adrs.md` (this plan)
2. Create `docs/decisions/000-template.md` with standard ADR sections
3. Create ADR-001 through ADR-005 as standalone files, each ~80 lines
4. Update `docs/decisions/README.md` TOC to reference standalone files
5. Commit and push branch, create PR

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | All 7 new files | Verify markdown renders correctly, file references are valid |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Numbering collision with existing README ADRs | Low | Low | Use separate numbering namespace (000-005 for standalone files) |
| Inaccurate historical context | Low | Medium | Cross-reference existing documentation and codebase |

## 7. Dependencies

- None — documentation-only change

## 8. Backward Compatibility

N/A — additive documentation change only.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Primary deliverable is documentation |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Use standalone files numbered 000-005 | Issue spec requests standalone files; existing README uses 001-011 inline |
