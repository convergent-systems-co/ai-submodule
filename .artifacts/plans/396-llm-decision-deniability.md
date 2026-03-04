# LLM Decision Deniability — Execution Trace for Panel Emissions

**Author:** Team Lead (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** #396 — LLM Decision Deniability
**Branch:** NETWORK_ID/fix/396/panel-execution-trace

---

## 1. Objective

Add an `execution_trace` field to the panel output schema that records which files the LLM read and which specific code sections it analyzed during a panel review, providing evidence that the panel actually evaluated the code rather than producing a template response.

## 2. Rationale

Currently, confidence scores and findings are entirely self-assessed by the LLM. There is no proof that the model read the diff, analyzed the files, or grounded its findings in actual code. The `model_version` field is self-reported and unverifiable.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| External SAST/DAST alongside LLM | Yes | Good long-term, but requires CI integration beyond this repo's scope |
| Require file hashes in emissions | Yes | Adds complexity; hashes prove file identity but not that the model read them |
| execution_trace with files_read list | Yes | **Selected** — lightweight, verifiable against git diff, actionable |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/schemas/panel-output.schema.json` | Add optional `execution_trace` object with: `files_read` (array of file paths), `diff_lines_analyzed` (integer), `analysis_duration_ms` (integer), `grounding_references` (array of `{file, line, finding_id}` linking findings to specific code locations) |
| `governance/prompts/reviews/security-review.md` | Add instruction to populate `execution_trace` in the structured emission |
| `governance/prompts/reviews/code-review.md` | Add instruction to populate `execution_trace` in the structured emission |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Extend `panel-output.schema.json` with optional `execution_trace` object
2. The `files_read` array must list every file the panel agent actually read during review
3. The `grounding_references` array links each finding to a specific file and line number
4. Update the two highest-impact review prompts (security-review, code-review) to include `execution_trace` in their emission instructions
5. Other review prompts can adopt `execution_trace` incrementally

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema | panel-output.schema.json | Validate extended schema is well-formed |
| Unit | governance/engine/tests/ | Verify policy engine handles emissions with and without execution_trace |
| Manual | security-review.md | Verify emission instruction produces the expected trace structure |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM fabricates execution_trace | Medium | Medium | Cross-reference files_read against git diff; flag mismatches |
| Schema change breaks existing emissions | Low | High | Field is optional; existing emissions remain valid |

## 7. Dependencies

- [ ] None — backward-compatible schema extension

## 8. Backward Compatibility

Fully backward-compatible. `execution_trace` is optional. Existing emissions without it remain valid. Policy engine does not require it for merge decisions.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Changes to security review prompt |
| code-review | Yes | Schema and prompt changes |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | Optional field, not required | Allows incremental adoption across all 19 review prompts |
| 2026-02-26 | Start with security-review and code-review | Highest-impact panels first |
