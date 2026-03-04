# Hallucination Detection in Panel Emissions

**Author:** Coder (agentic)
**Date:** 2026-02-26
**Status:** completed
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/406
**Branch:** NETWORK_ID/fix/406/hallucination-detection

---

## 1. Objective

Mitigate the risk of LLM hallucination in panel emissions by requiring grounding evidence for findings and validating that evidence at the pipeline level.

## 2. Rationale

LLMs can hallucinate findings, confidence scores, and risk assessments. A security-review panel might report "no vulnerabilities found" with 0.90 confidence when critical vulnerabilities exist. Without ground-truth verification or confidence calibration, hallucinated findings can cause false approvals or false blocks. The execution_trace field (from #396) records what files were read, but doesn't verify that findings are actually grounded in those files. This change adds mandatory cross-referencing: every finding must cite a specific file and line, and "no findings" verdicts must still demonstrate that files were actually analyzed.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Independent SAST/DAST tool integration | Yes | Out of scope for this issue; requires external tooling and CI integration. Future enhancement. |
| Confidence calibration via historical data | Yes | Requires accumulated emission data not yet available. Future Phase 5 work. |
| Evidence-based grounding (this approach) | Yes | Selected — lightweight, backward-compatible, immediately enforceable via schema and prompts. |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.governance/plans/406-hallucination-detection.md` | This plan document |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/schemas/panel-output.schema.json` | Add optional `evidence` object to findings items with file, line_start, line_end, snippet |
| `governance/prompts/reviews/security-review.md` | Add Grounding Requirement section before Structured Emission |
| `governance/prompts/reviews/code-review.md` | Add Grounding Requirement section before Structured Emission Example |
| `governance/prompts/startup.md` | Add Hallucination Detection validation step to Phase 4c |

### Files to Delete

N/A — no files deleted.

## 4. Approach

1. Extend `panel-output.schema.json` findings items with an optional `evidence` object containing `file` (required), `line_start`, `line_end`, and `snippet` (max 200 chars). Optional for backward compatibility.
2. Add a Grounding Requirement section to `security-review.md` requiring evidence blocks for medium+ severity findings and grounding_references for zero-finding reviews.
3. Add the same Grounding Requirement section to `code-review.md`.
4. Add a Hallucination Detection validation step to `startup.md` Phase 4c that flags ungrounded findings and triggers re-review for emissions lacking evidence or execution_trace.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | `panel-output.schema.json` | Existing schema validation tooling will accept emissions with or without the evidence field (backward compatible) |
| Manual | Review prompts | Verify grounding requirement text is correctly placed in security-review.md and code-review.md |
| Manual | startup.md | Verify hallucination detection step is correctly placed in Phase 4c |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Backward compatibility break | Low | High | Evidence field is optional in schema; existing emissions remain valid |
| Over-flagging hallucinations | Medium | Medium | Only medium+ severity findings require evidence; low/info findings are exempt |
| Review prompt ignored by LLM | Medium | Medium | Schema enforcement provides a second layer; pipeline validation in Phase 4c catches gaps |

## 7. Dependencies

- [x] No blocking dependencies — all changes are additive to existing files

## 8. Backward Compatibility

All changes are backward compatible. The `evidence` field is optional in the schema. Existing panel emissions without evidence will continue to validate. The grounding requirement is a soft enforcement via prompts; the pipeline validation flags but does not hard-block.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Changes affect security review process |
| code-review | Yes | Changes affect code review process |
| documentation-review | Yes | Schema and prompt changes require doc review |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | Evidence field is optional in schema | Backward compatibility with existing emissions |
| 2026-02-26 | Only medium+ severity findings require evidence | Avoids over-burdening low/info findings with evidence requirements |
| 2026-02-26 | Hallucination detection triggers re-review, not hard-block | Allows gradual adoption; hard-block can be added in future policy update |
