# Hallucination Detection — Cross-Reference Requirements for Panel Emissions

**Author:** Code Manager (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** #406 — LLM-1: Hallucination in Panel Emissions
**Branch:** itsfwcp/fix/406/hallucination-detection

---

## 1. Objective

Add cross-referencing requirements to review prompts and the panel output schema that force panel agents to ground their findings in verifiable evidence, reducing the risk of hallucinated findings or fabricated confidence scores.

## 2. Rationale

LLMs can hallucinate findings and confidence scores. The execution_trace field (from #396) records what files were read, but doesn't verify that findings are actually grounded in those files. This change adds mandatory cross-referencing: every finding must cite a specific file and line, and "no findings" verdicts must still demonstrate that files were actually analyzed.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| External SAST/DAST as ground truth | Yes | Requires CI integration beyond repo scope; good future addition |
| Confidence calibration via historical data | Yes | Requires historical dataset; Phase 5 concern |
| Mandatory cross-references in findings | Yes | **Selected** — verifiable now, builds on execution_trace |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/schemas/panel-output.schema.json` | Add `evidence` field to findings items: `file`, `line_range`, `snippet` (first 200 chars of relevant code) |
| `governance/prompts/reviews/security-review.md` | Add cross-reference requirement: every finding must include file, line, and code snippet |
| `governance/prompts/reviews/code-review.md` | Same cross-reference requirement |
| `governance/prompts/startup.md` | Add cross-reference validation in Phase 4c: findings without evidence are flagged as potentially hallucinated |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Extend panel-output.schema.json findings items:
   - Add optional `evidence` object: `{ "file": "string", "line_start": "integer", "line_end": "integer", "snippet": "string (maxLength 200)" }`
   - Findings with severity >= "medium" should include evidence (enforced by prompts, not schema)
2. Update security-review.md and code-review.md:
   - Instruction: "Every finding with severity medium or above MUST include an `evidence` block with the file path, line range, and a code snippet (first 200 chars). Findings without evidence may be treated as hallucinated."
   - Instruction: "If the review produces zero findings, include at least one `evidence` block in execution_trace.grounding_references demonstrating files were actually analyzed."
3. Update startup.md Phase 4c:
   - Add validation: if a panel emission has medium+ findings without evidence, flag as potentially hallucinated and request re-review

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema | panel-output.schema.json | Validate extended schema is well-formed |
| Unit | governance/engine/tests/ | Verify policy engine handles findings with/without evidence |
| Manual | Review prompts | Verify cross-reference instructions are clear |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM fabricates evidence | Medium | Medium | Code Manager can cross-reference snippets against actual file content |
| Additional prompt overhead | Low | Low | Evidence field is optional in schema; enforced by prompt for medium+ |

## 7. Dependencies

- [ ] #396 execution_trace (merged) — builds on the execution_trace framework

## 8. Backward Compatibility

Fully backward-compatible. `evidence` field is optional in schema. Existing emissions remain valid.

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
| 2026-02-26 | Evidence optional in schema, required by prompt for medium+ | Allows incremental adoption while pushing toward full evidence |
| 2026-02-26 | 200 char snippet limit | Prevents evidence from bloating emissions while providing enough context |
