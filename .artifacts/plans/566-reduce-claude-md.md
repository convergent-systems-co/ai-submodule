# Reduce CLAUDE.md to 2K Tokens (#566)

**Author:** Claude (Coder)
**Date:** 2026-03-01
**Status:** approved
**Issue:** #566
**Branch:** NETWORK_ID/refactor/566/reduce-claude-md

---

## 1. Objective

Reduce `.ai/CLAUDE.md` from ~5,500 tokens to under 2,000 tokens by moving architecture detail to `docs/` and keeping only navigation + conventions.

## 2. Rationale

CLAUDE.md is loaded as system context on every interaction. Architecture detail that exists in `docs/` was duplicated here, wasting ~3,500 tokens per session.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Remove CLAUDE.md entirely | Yes | Still needed for repo navigation and conventions |
| Split into sections | Yes | Adds complexity; single concise file is better |
| Directory-of-directories format | Yes | Selected — minimal identity + key directories + references |

## 3. Scope

### Files to Modify

| File | Change Description |
|------|-------------------|
| CLAUDE.md | Rewrite to ~900 tokens: identity, commands, conventions, directory table, startup summary |

## 4. Approach

1. Remove: full architecture sections (Five Governance Layers, Three Artifact Types, Persona descriptions, Compliance Coverage, ADO Integration, CI Workflows, Policy Engine details, Regulatory Compliance, Structured Emissions, Checkpoint Schema, Instruction Delivery, Resource Locations table)
2. Keep: repo identity, commands, key conventions, directory table, agentic startup summary
3. Add: references to source docs for removed content

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Token count | CLAUDE.md | Verify under 2K tokens |
| Reference check | All refs | Verify docs/ references are valid |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Agent loses architecture context | Low | Low | Architecture detail is in docs/ and loaded on-demand (Tier 3) |

## 7. Dependencies

None.

## 8. Backward Compatibility

No breaking changes. Content moved to docs/, not deleted.

## 9. Governance

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-01 | Target ~900 tokens (below 2K goal) | Aggressive compression is safe because all detail exists in docs/ |
