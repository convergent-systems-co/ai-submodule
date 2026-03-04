# Fix Persona Count in Documentation

**Author:** Code Manager (Claude)
**Date:** 2026-03-02
**Status:** approved
**Issue:** #15
**Branch:** itsfwcp/fix/15/persona-count-docs

---

## 1. Objective

Update all documentation that claims "6 agentic personas" to correctly state "7 agentic personas" and include the Document Writer persona in all persona lists.

## 2. Rationale

The `governance/personas/agentic/` directory contains 7 personas (Project Manager, DevOps Engineer, Code Manager, Coder, IaC Engineer, Tester, Document Writer). The Document Writer was added but 11 documentation files still reference "6 agentic personas" and omit it from lists.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Remove Document Writer persona | No | It's actively used in Phase 4 of the agentic loop |
| Update all docs | Yes | Selected — accurate documentation is mandatory |

## 3. Scope

### Files to Create

None.

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Update "6 agentic personas" to "7 agentic personas", add Document Writer |
| `docs/architecture/agent-architecture.md` | Update "6-agent" to "7-agent", add Document Writer to persona list |
| `docs/onboarding/team-starter.html` | Update "6 agentic personas" to "7" |
| `docs/onboarding/developer-guide.md` | Update persona count and list |
| `docs/tutorials/end-to-end-walkthrough.md` | Update persona count and list |
| `docs/contributing.md` | Update persona count and list |
| `docs/compliance/iso-42001-mapping.md` | Update "Six" to "Seven" |
| `docs/decisions/README.md` | Update "6 agentic personas" to "7" |
| `docs/research/README.md` | Update "6 agentic personas" to "7" |
| `docs/research/technique-comparison.md` | Update "6 agentic personas" to "7" |
| `governance/prompts/init.md` | Update persona count and list |

### Files to Delete

None.

## 4. Approach

1. Grep for "6 agentic" and "six agentic" across all files
2. Update each occurrence to "7 agentic personas" with Document Writer included
3. Where persona lists appear, add ", Document Writer" to the list
4. Verify no remaining incorrect counts

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Grep | All files | Verify no remaining "6 agentic" references |
| Existing test | test_persona_structure.py | Already expects 7 personas |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Missing a reference | Low | Low | Comprehensive grep search |
| Breaking HTML formatting | Low | Low | Careful edit of team-starter.html |

## 7. Dependencies

None.

## 8. Backward Compatibility

Documentation-only change. No behavior impact.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Doc accuracy fix |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Update all 11 files | Comprehensive fix for consistency |
