# Add Structured Emission Examples to Panel Definitions

**Author:** Team Lead (agentic)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/196
**Branch:** `NETWORK_ID/feat/196/emission-examples`

---

## 1. Objective

Add a concrete JSON emission example and explicit schema reference to each of the 19 panel definition files, so AI agents produce schema-compliant output without needing to read the raw JSON Schema.

## 2. Rationale

Agents infer output structure from panel descriptions, resulting in schema validation failures (wrong field names, incorrect enum values, nested structures instead of flat). A concrete example in each panel file eliminates guesswork.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Add example only to panel-output.schema.json | Yes | Agents load panel files, not schema files, during execution |
| Create a separate examples/ directory | Yes | Separating from the panel file creates a drift risk |
| Add a schema validation step in workflow | Yes | Good complement but doesn't prevent malformed output at source |

## 3. Scope

### Files to Modify

All 19 panel definitions in `governance/personas/panels/*.md`:
- ai-expert-review, api-design-review, architecture-review, code-review
- cost-analysis, copilot-review, data-design-review, data-governance-review
- documentation-review, governance-compliance-review, incident-post-mortem
- migration-review, performance-review, production-readiness-review
- security-review, technical-debt-review, test-generation-review
- testing-review, threat-modeling

### Change per file

1. Add schema reference line after `## Output Format` heading
2. Add `### Structured Emission Example` subsection with a minimal valid JSON block after the Consolidated subsection

## 4. Approach

1. For each panel, read the participants list and panel name
2. Insert schema reference: `> Emissions must conform to governance/schemas/panel-output.schema.json`
3. Insert a JSON example with correct `panel_name`, persona findings matching participants, and all required fields
4. Commit all 19 files in a single commit

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | All 19 examples | Validate each example against panel-output.schema.json |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Example drifts from schema | Low | Medium | Example is minimal, using only required fields |
| Panels have varying structures | Medium | Low | Examples follow the same schema, only persona names vary |

## 7. Dependencies

None.

## 8. Backward Compatibility

Additive change only.

## 9. Governance

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
