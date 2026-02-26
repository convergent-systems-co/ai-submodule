# IaC Engineer Agentic Persona

**Author:** Code Manager (agentic)
**Date:** 2026-02-25
**Status:** in_progress
**Issue:** #308
**Branch:** itsfwcp/feat/308/iac-engineer-persona

---

## 1. Objective

Create a new agentic persona — IaC Engineer — that the Code Manager can delegate to when infrastructure-as-code work is required. The persona follows JM Paved Roads Bicep standards derived from the JM-Paved-Roads GitHub org, with Terraform support.

## 2. Rationale

Infrastructure changes require specialized knowledge: naming conventions, security defaults, environment handling, module registries, and compliance tagging (SNOW). A dedicated IaC Engineer persona provides this specialized context without bloating the general Coder persona.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Add IaC knowledge to Coder | Yes | Would bloat the Coder with domain-specific infrastructure patterns |
| External IaC tool integration | Yes | Doesn't leverage the agentic pipeline governance model |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/personas/agentic/iac-engineer.md` | Full IaC Engineer persona definition |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/personas/agentic/code-manager.md` | Add IaC routing decision and ASSIGN transitions |
| `governance/prompts/agent-protocol.md` | Add IaC Engineer to valid transition map |
| `governance/prompts/startup.md` | Reference IaC Engineer in Phase 3 dispatch |
| `CLAUDE.md` | Add IaC Engineer to agentic personas list |

### Files to Delete

None

## 4. Approach

1. Create `iac-engineer.md` persona with JM Bicep standards, naming conventions, security patterns, module registry references
2. Update Code Manager to detect and route IaC work
3. Update agent protocol transitions
4. Update CLAUDE.md documentation

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Persona completeness | Review against existing persona structure |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Persona too large for context tier | Low | Medium | Keep focused; reference external standards |

## 7. Dependencies

- [ ] None

## 8. Backward Compatibility

Additive change. No existing behavior affected.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | New persona and doc changes |
| ai-expert-review | Yes | Agentic persona design |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Bicep-first with Terraform support | JM standards are Bicep-based; Terraform for multi-cloud |
| 2026-02-25 | Derived standards from JM-Paved-Roads org and JM-Actions/bicep | Authoritative source for JM IaC conventions |
