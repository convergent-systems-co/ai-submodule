# Conflict Detection Schema — Phase 5d Governance Artifact

**Author:** Code Manager (agentic)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/170
**Branch:** itsfwcp/feat/170/conflict-detection-schema

---

## 1. Objective

Create a JSON Schema that defines the structure for detecting when multiple agents modify overlapping files or governance state, enabling future multi-agent coordination. This is the first Phase 5d governance artifact.

## 2. Rationale

Multi-agent coordination requires a structured way to declare and detect conflicts before they occur. The schema defines the data contract — runtime implementations in consuming repos can use it once multi-agent tooling exists.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| YAML-based conflict rules only | Yes | Schemas provide validation; rules are complementary but not sufficient alone |
| Wait for runtime tooling to exist | Yes | Governance artifacts can be defined now per Phase 5d assessment |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/conflict-detection.schema.json` | Conflict detection data contract |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Check off "Conflict detection schema" in Phase 5d |
| `CLAUDE.md` | Update schema listing |
| `README.md` | Add schema to file structure listing |

### Files to Delete

None.

## 4. Approach

1. Create the JSON Schema following existing conventions (draft-2020-12, UUID IDs, descriptive properties)
2. Define agent session identification, file modification sets, overlap detection, severity classification, and resolution strategies
3. Update documentation

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | JSON Schema | Valid JSON Schema structure |

No automated tests — config-only repo.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Schema design insufficient for future runtime needs | Low | Low | Schema is versioned and can evolve; additive changes only |

## 7. Dependencies

None.

## 8. Backward Compatibility

Fully backward compatible — new file, no modifications to existing schemas.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Standard requirement |
| security-review | Yes | Schema defines agent coordination boundaries |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Include resolution strategy declarations in schema | Future coordination needs to know what resolution approach each agent supports |
