# chore: remove 77 deprecated persona and panel files with migration plan

**Author:** Team Lead (agent)
**Date:** 2026-02-25
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/257
**Branch:** NETWORK_ID/chore/257/remove-deprecated-personas

---

## 1. Objective

Remove 78 deprecated persona and panel files (59 persona files across 13 categories + 19 panel files + index.md), update all codebase references to point to the replacement `governance/prompts/reviews/` location, and update template `project.yaml` files.

## 2. Rationale

These files were superseded by consolidated review prompts in `governance/prompts/reviews/` (Issue #220). They consume ~85KB of context when agents scan directories and create confusion about the authoring-time vs runtime boundary.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Archive to separate branch | Yes | Adds complexity; git history preserves files anyway |
| Move to `deprecated/` directory | Yes | Still consumes disk; no value over deletion since replacements exist |
| Delete with migration plan (chosen) | Yes | Clean removal with version-tagged release |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `CLAUDE.md` (root .ai/) | Update persona/panel descriptions to reference only `governance/prompts/reviews/` |
| `README.md` | Remove references to deprecated persona/panel directories |
| `CHANGELOG.md` | Add removal entry |
| `docs/architecture/governance-model.md` | Update panel/persona path references |
| `docs/architecture/context-management.md` | Update panel definition references |
| `docs/architecture/runtime-feedback.md` | Update panel references |
| `docs/architecture/mass-parallelization.md` | Update persona/panel references |
| `docs/governance/artifact-classification.md` | Update panel listing |
| `docs/tutorials/end-to-end-walkthrough.md` | Update panel references |
| `docs/onboarding/developer-guide.md` | Remove persona index reference |
| `governance/prompts/di-generation-workflow.md` | Update panel path verification |
| `tests/test_governance_artifacts.py` | Update test expectations for removed directories |
| Template `project.yaml` files in `governance/templates/` | Remove deprecated persona path references |

### Files to Delete

| File | Reason |
|------|--------|
| `governance/personas/architecture/*.md` (3) | Deprecated — replaced by consolidated reviews |
| `governance/personas/compliance/*.md` (4) | Deprecated |
| `governance/personas/documentation/*.md` (2) | Deprecated |
| `governance/personas/domain/*.md` (6) | Deprecated |
| `governance/personas/engineering/*.md` (6) | Deprecated |
| `governance/personas/finops/*.md` (4) | Deprecated |
| `governance/personas/governance/*.md` (2) | Deprecated |
| `governance/personas/language/*.md` (11) | Deprecated |
| `governance/personas/leadership/*.md` (5) | Deprecated |
| `governance/personas/operations/*.md` (6) | Deprecated |
| `governance/personas/platform/*.md` (2) | Deprecated |
| `governance/personas/quality/*.md` (3) | Deprecated |
| `governance/personas/specialist/*.md` (4) | Deprecated |
| `governance/personas/panels/*.md` (19) | Deprecated — replaced by `governance/prompts/reviews/` |
| `governance/personas/index.md` (1) | Reference grid for deprecated personas |

**Total: 78 files across 14 directories**

## 4. Approach

1. Delete all files in the 13 persona category directories and `governance/personas/panels/`
2. Remove empty directories
3. Delete `governance/personas/index.md`
4. Update documentation files to replace deprecated path references with `governance/prompts/reviews/`
5. Update test expectations in `tests/test_governance_artifacts.py`
6. Update template `project.yaml` files to reference current artifacts
7. Update CHANGELOG.md with removal entry
8. Verify `governance/personas/agentic/` is untouched (5 active personas remain)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `tests/test_governance_artifacts.py` | Verify tests pass after removing deprecated file expectations |
| Manual | All modified docs | Verify no broken links or stale references |
| Grep verification | Entire codebase | Confirm no remaining references to deleted paths |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Consuming repos reference old paths | Medium | Low | Consuming repos use `governance/prompts/reviews/`; old paths weren't exposed via init.sh |
| Missing reference update | Medium | Low | Post-deletion grep for all old paths |

## 7. Dependencies

- [x] No blocking dependencies — replacement files already exist in `governance/prompts/reviews/`

## 8. Backward Compatibility

This is a breaking change for any tooling that reads deprecated persona/panel files directly. However, the deprecation was announced in CLAUDE.md and CHANGELOG.md, the replacement locations exist, and no consuming repo init path references these files. Git history preserves the files for reference.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | File deletion at scale |
| documentation-review | Yes | Major documentation update |
| threat-modeling | Yes | Required by default profile |
| cost-analysis | Yes | Required by default profile |
| data-governance-review | Yes | Required by default profile |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Delete rather than archive | Git history preserves files; archive branch adds maintenance burden |
