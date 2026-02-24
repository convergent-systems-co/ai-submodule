# Phase 5e — Formal spec schema

**Author:** Code Manager (agentic)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/163
**Branch:** itsfwcp/feat/163/formal-spec-schema

---

## 1. Objective

Create a JSON Schema for formal specifications that are richer than GitHub issue templates — providing structured acceptance criteria, dependency declarations, risk pre-classification, and machine-verifiable completion conditions.

## 2. Rationale

GitHub issues use free-text descriptions that are ambiguous for automated validation. A formal spec schema lets agents verify whether an implementation satisfies acceptance criteria programmatically, enabling Phase 5e's reduced human touchpoint model.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Extend issue templates with more fields | Yes | GitHub issue templates are YAML metadata + markdown body; they can't enforce structured acceptance criteria or machine-verifiable conditions |
| Use existing runtime-di.schema.json | Yes | DIs are for runtime-detected anomalies; specs are for proactive intent declaration with acceptance criteria |
| Create formal spec schema | Yes | **Selected** — standalone enforcement artifact, follows existing schema conventions |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/formal-spec.schema.json` | The formal spec schema |
| `governance/schemas/examples/formal-spec.example.json` | Example instance |
| `governance/docs/formal-spec.md` | Documentation |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Check off "Formal spec schema" item in 5e |
| `README.md` | Add schema to repository structure listing |

### Files to Delete

N/A

## 4. Approach

1. Design schema with sections: metadata, acceptance criteria, dependencies, risk classification, completion conditions
2. Create example instance demonstrating all fields
3. Write documentation explaining schema purpose and integration
4. Update GOALS.md and README.md

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | formal-spec.schema.json | Example instance validates against the schema |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Schema too rigid for diverse project needs | Low | Medium | Use optional fields extensively; require only core metadata |

## 7. Dependencies

- [x] No dependencies

## 8. Backward Compatibility

Additive — new schema file, no existing behavior changed.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Default required |
| documentation-review | Yes | New documentation |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Schema follows runtime-di.schema.json conventions | Consistency with existing enforcement artifacts |
