# Fix Persona Count Documentation

**Author:** Project Manager (agentic)
**Date:** 2026-03-02
**Status:** approved
**Issue:** #15
**Branch:** itsfwcp/fix/15/persona-count-docs

---

## 1. Objective

Correct all documentation references from "6 agentic personas" to "7 agentic personas" (Document Writer was added but docs not updated). Clarify that the historical "57 personas" were consolidated into 21 review prompts and then removed.

## 2. Rationale

The Document Writer persona was added after the initial documentation was written. Multiple docs still reference "6 agentic personas" when 7 exist: Project Manager, DevOps Engineer, Code Manager, Coder, IaC Engineer, Tester, Document Writer.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Update only CLAUDE.md | Yes | Other docs also have stale counts |
| Comprehensive docs update | Yes — chosen | Prevents recurring confusion |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Fix persona count references, clarify consolidation history |
| `CLAUDE.md` | Verify persona count (may already say 7) |
| `docs/architecture/agent-architecture.md` | Update persona count |
| `docs/onboarding/developer-guide.md` | Update persona count |
| `docs/tutorials/end-to-end-walkthrough.md` | Update persona count |
| `docs/contributing.md` | Update persona count |
| Other docs with "6 agentic" references | Grep and fix all |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. List files in `governance/personas/agentic/` to confirm count is 7
2. Grep for "6 agentic", "six agentic", "6 personas" across all docs
3. Update each reference to "7 agentic personas"
4. Add Document Writer to any persona lists that omit it
5. Clarify GOALS.md historical narrative

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Documentation files | Grep verification of no stale "6 agentic" references |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Missing a reference | Low | Low | Comprehensive grep |

## 7. Dependencies

- [ ] None

## 8. Backward Compatibility

Documentation-only change. No code impact.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Documentation accuracy fix |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Update all docs comprehensively | Prevents recurring "stale count" issues |
