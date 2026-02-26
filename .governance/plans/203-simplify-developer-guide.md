# Simplify Developer Guide — Extract Detail to Linked Pages

**Author:** Code Manager (agentic)
**Date:** 2026-02-24
**Status:** completed
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/203
**Branch:** `itsfwcp/docs/203/simplify-developer-guide`

---

## 1. Objective

Reduce DEVELOPER_GUIDE.md to its essential purpose: getting a developer running quickly. Move detailed framework explanations behind links to README.md and governance docs.

## 2. Rationale

The guide grew to 360+ lines with framework internals (governance layers, policy profile details, context tiers, file structure). Developers need setup steps and operational commands, not architecture knowledge.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Delete sections entirely | Yes | Information is valuable, just misplaced in the quick guide |
| Create separate deep-dive doc | Yes | Content already exists in README.md and governance/docs/ |
| Keep as-is with TOC | Yes | Length itself is the problem — developers won't read a 360-line quick guide |

## 3. Scope

### Files to Modify

| File | Change Description |
|------|-------------------|
| `DEVELOPER_GUIDE.md` | Replace verbose sections with 1-line summaries + links to existing docs |

## 4. Approach

1. Keep Quick Start (setup commands) — unchanged
2. Condense "Key Concepts" to a compact glossary linking to persona index
3. Replace "Four Policy Profiles" with 1-line + link
4. Replace "How a Change Flows Through Governance" with 1-line + link
5. Condense "Repository Configuration" to essential setup + link
6. Replace "Context Management" with the hard rule + link
7. Remove "File Structure" section (already in README)
8. Keep Recovery & Re-Entry, Diagnostic Commands, Troubleshooting — these are operational
9. Streamline Further Reading

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Link check | Cross-references | Verify all link targets exist |
| Line count | Target | Verify under 200 lines |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Developers miss moved content | Low | Low | Links are explicit and descriptive |

## 7. Dependencies

None.

## 8. Backward Compatibility

Additive (moving content behind links, not deleting it from the repo).

## 9. Governance

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
