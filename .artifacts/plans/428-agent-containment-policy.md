# Agent Containment Policy for Sandboxing and Least-Privilege

**Author:** Team Lead (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/428
**Branch:** NETWORK_ID/feat/428/agent-containment-policy

---

## 1. Objective

Create a per-persona containment policy defining tool allowlists, denied paths, denied operations, and resource limits for each agentic persona, preventing lateral escalation and unintended modifications.

## 2. Rationale

Coder agents operate in worktrees (filesystem isolation) but have no documented containment boundaries. The 2025 AI Agent Index found only 9/30 agents documented sandboxing.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Code-level enforcement | Yes | Requires runtime changes — too invasive for initial implementation |
| Policy file + documentation | Yes | **Selected** — declarative, auditable, enforceable by Team Lead |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/policy/agent-containment.yaml` | Per-persona containment rules |
| `docs/architecture/agent-containment.md` | Architecture documentation |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/personas/agentic/coder.md` | Add containment policy reference |
| `governance/personas/agentic/iac-engineer.md` | Add containment policy reference |
| `governance/personas/agentic/tester.md` | Add containment policy reference |

### Files to Delete

None.

## 4. Approach

1. Create `governance/policy/agent-containment.yaml` with per-persona rules:
   - Coder: allowed_tools, denied_paths (governance/, policy/, schemas/), max_files_per_pr, max_lines_per_commit
   - IaC Engineer: allowed_tools, allowed_paths (infra/, bicep/, terraform/), denied_paths
   - Tester: read-only access to implementation, write access to test files only
2. Add containment reference to each persona .md file
3. Create architecture documentation

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Policy review | Verify containment rules are complete |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Over-restrictive rules | Medium | Medium | Start permissive, tighten iteratively |

## 7. Dependencies

None.

## 8. Backward Compatibility

Additive — new policy file and documentation references.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Security policy changes |
| documentation-review | Yes | New architecture docs |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Declarative policy over code enforcement | Auditable, simpler first step |
