# Add Agile Coach Persona

**Author:** Code Manager (agentic)
**Date:** 2026-02-20
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/5
**Branch:** itsfwcp/5-agile-coach-persona

---

## 1. Objective

Add an Agile Coach persona to the leadership category that evaluates work through the lens of agile practices: user story quality, definition of done, acceptance criteria completeness, sprint health, and continuous improvement.

## 2. Rationale

The existing Product Manager persona focuses on requirements clarity and user value. The Agile Coach fills a distinct gap — evaluating process adherence, story decomposition, and delivery cadence rather than product direction.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Extend Product Manager | Yes | Overloads PM scope; agile coaching is a distinct discipline |
| Create under specialist/ | Yes | Leadership is the correct semantic category for coaching roles |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `personas/leadership/agile-coach.md` | Agile Coach persona definition |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `personas/index.md` | Add Agile Coach to the Leadership table |

### Files to Delete

None.

## 4. Approach

1. Create `personas/leadership/agile-coach.md` following the standard persona format (Role, Evaluate For, Output Format, Principles, Anti-patterns)
2. Update `personas/index.md` Leadership table with the new entry
3. Commit, push, create PR

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Persona file | Verify format matches existing personas |
| Manual | Index | Verify index table is consistent |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Overlap with Product Manager | Low | Low | Clearly differentiate scope in Role section |

## 7. Dependencies

None.

## 8. Backward Compatibility

Additive change only. No existing files are modified in a breaking way.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| Documentation Review | No | Low-risk additive persona |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-20 | Place in leadership/ category | Coaching is a leadership function, consistent with Tech Lead, Mentor, PM |
