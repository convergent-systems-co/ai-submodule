# MCP Security Guidelines and Tool Access Controls

**Author:** Team Lead (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/437
**Branch:** NETWORK_ID/feat/437/mcp-security-guidelines

---

## 1. Objective

Create comprehensive security guidelines for MCP server deployment, including tool classification (read-only vs. action), rate limiting recommendations, and confused deputy attack mitigations.

## 2. Rationale

The MCP server (#425) exposes governance tools to IDEs. Without documented security guidelines, the distribution layer could become a governance bypass vector. OWASP and MCP spec security requirements apply.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Embed security in mcp-server-usage.md | Yes | Too important — deserves dedicated guide |
| Code-level enforcement only | Yes | Guidelines needed for operators deploying the server |
| Dedicated security guide | Yes | **Selected** — comprehensive, referenceable |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `docs/guides/mcp-security-guidelines.md` | Comprehensive MCP security guidance |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `docs/guides/mcp-server-usage.md` | Add cross-reference to security guidelines |

### Files to Delete

None.

## 4. Approach

1. Create `docs/guides/mcp-security-guidelines.md` with sections:
   - Tool classification table (read-only: list_panels, list_policy_profiles, get_schema; action: check_policy)
   - Token scoping guidance (per-tool authorization)
   - Confused deputy attack mitigations
   - Rate limiting recommendations per tool type
   - Input validation requirements
   - Logging and audit requirements
2. Update `docs/guides/mcp-server-usage.md` to reference the security guide

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Documentation | Review for completeness and accuracy |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Guidelines become stale | Medium | Low | Reference OWASP and MCP spec versions |
| Incomplete coverage | Low | Medium | Follow OWASP MCP checklist systematically |

## 7. Dependencies

- MCP server (#425) — already merged

## 8. Backward Compatibility

Documentation only — no backward compatibility concerns.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Security documentation needs review |
| documentation-review | Yes | New documentation |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Dedicated guide rather than inline | Importance warrants standalone document |
