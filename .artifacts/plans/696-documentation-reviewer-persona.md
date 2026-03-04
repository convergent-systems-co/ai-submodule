# Add Documentation Reviewer Agentic Persona

**Author:** Project Manager (agentic)
**Date:** 2026-03-02
**Status:** approved
**Issue:** #696
**Branch:** itsfwcp/feat/696/documentation-reviewer-persona

---

## 1. Objective

Add a documentation reviewer agentic persona that validates all affected documentation has been updated when code changes are made. Runs in parallel with the Tester during Phase 4.

## 2. Rationale

Documentation staleness is caught late or not at all. A dedicated reviewer that runs alongside Tester catches doc gaps before PRs are created.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Extend Tester with doc checks | Yes | Tester already has too many responsibilities; separation of concerns |
| New persona in parallel | Yes — chosen | Clean separation, runs concurrently for no added latency |
| Rely on Document Writer only | Yes | Writer creates docs but nobody verifies them |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/personas/agentic/documentation-reviewer.md` | New persona definition following ASSIGN/RESULT/FEEDBACK protocol |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/policy/agent-containment.yaml` | Add documentation_reviewer containment rules |
| `governance/engine/tests/test_persona_structure.py` | Add documentation-reviewer to expected persona list |
| `CLAUDE.md` | Update persona count (7 → 8 agentic personas) |

## 4. Approach

1. Create `documentation-reviewer.md` persona following existing patterns (tester.md as reference)
2. Define responsibilities: run `bin/check-doc-staleness.py`, verify CLAUDE.md counts, README.md features, GOALS.md items, inline comments
3. Define the ASSIGN/RESULT/FEEDBACK protocol messages
4. Add containment rules — documentation-reviewer can read all files but only modify docs
5. Update test expectations for persona count
6. Update CLAUDE.md persona count

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | test_persona_structure.py | Verify documentation-reviewer.md exists with required sections |
| Manual | Persona content | Verify protocol compliance with agent-protocol.md |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Persona overlap with Tester doc checks | Medium | Low | Clear scope: Tester checks test coverage, doc-reviewer checks doc freshness |

## 7. Dependencies

- [ ] None

## 8. Backward Compatibility

Additive only — existing personas and workflows unaffected. Code Manager dispatching documentation-reviewer is opt-in until integrated into startup.md.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New persona file and test changes |
| documentation-review | Yes | New persona documentation |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Separate persona over extending Tester | Separation of concerns, parallel execution |
