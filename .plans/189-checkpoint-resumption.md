# Automatic Checkpoint Resumption Schema and Workflow

**Author:** Code Manager (agentic)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/189
**Branch:** itsfwcp/feat/189/checkpoint-resumption

---

## 1. Objective

Formalize the checkpoint mechanism into proper governance artifacts: a JSON Schema for checkpoint files and a resumption workflow prompt, enabling reliable session recovery after context resets.

## 2. Rationale

The checkpoint structure is currently defined only as an informal JSON example in startup.md's shutdown protocol. Formalizing it ensures checkpoint files can be validated and the resumption process is explicit and repeatable.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Keep checkpoint format informal | Yes | No validation; format drift over time; hard for new agents to consume |
| Embed resumption steps in startup.md | Yes | Startup.md is already long; dedicated workflow prompt is cleaner |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/checkpoint.schema.json` | JSON Schema for `.checkpoints/` state files |
| `governance/prompts/checkpoint-resumption-workflow.md` | Workflow for resuming from a checkpoint |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Check off "Automatic checkpoint resumption" item in Phase 5c; add completed work entry |
| `README.md` | Add new schema and prompt to file listings |
| `DEVELOPER_GUIDE.md` | Update schema count (19 → 20) |

### Files to Delete

N/A

## 4. Approach

1. Create checkpoint schema matching the format in startup.md
2. Create resumption workflow with issue state validation
3. Update documentation

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | checkpoint.schema.json | Validate with python -m json.tool |
| Manual review | Workflow prompt | Verify resumption steps are complete |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Schema too strict for existing checkpoints | Low | Low | Match exactly what startup.md specifies |

## 7. Dependencies

- [x] #186 (Issue state validation) — resumption workflow references this rule

## 8. Backward Compatibility

Fully additive. New files only; no existing files changed structurally.

## 9. Governance

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Match existing checkpoint format exactly | Ensure existing checkpoints pass validation |
