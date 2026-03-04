# Parallel Agent Session Protocol (Phase 5d)

**Author:** Team Lead (agentic)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/181
**Branch:** NETWORK_ID/feat/181/parallel-session-protocol

---

## 1. Objective

Define a governance specification (YAML) for spawning, coordinating, and reconciling multiple concurrent agent sessions. This completes Phase 5d governance artifact coverage alongside the conflict detection schema (PR #171) and merge sequencing policy (PR #174).

## 2. Rationale

The two existing 5d artifacts define *what conflicts look like* (schema) and *how to order merges* (policy). The missing piece is the session coordination protocol — *how* parallel sessions are spawned, assigned work, synchronized, and reconciled. This protocol sits between the orchestrator and the individual agents.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| JSON Schema (like conflict detection) | Yes | Protocol is more operational/procedural than structural; YAML policy format is a better fit |
| YAML policy (like merge sequencing) | Yes | Selected — matches the operational nature of the specification |
| Agentic workflow prompt (markdown) | Yes | Too informal; needs structured, machine-parseable rules |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/policy/parallel-session-protocol.yaml` | Parallel agent session protocol specification |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Check off "Parallel agent session protocol" in Phase 5d section |
| `CLAUDE.md` | Update Phase 5d status description if needed |
| `README.md` | Update Phase 5d status if the description mentions it |

### Files to Delete

None.

## 4. Approach

1. Create `governance/policy/parallel-session-protocol.yaml` defining:
   - Session lifecycle states (pending → active → blocked → completed → failed)
   - Work assignment rules (issue independence, file conflict avoidance)
   - Coordination points (governance gates, shared file detection)
   - Conflict resolution (references to conflict-detection.schema.json and merge-sequencing.yaml)
   - Session limits (max concurrent, per-session caps)
   - Handoff protocol (inter-session communication)
2. Update GOALS.md to check off the item
3. Review other docs for consistency

## 5. Testing Strategy

N/A — governance policy artifact. Validation is structural (valid YAML, references correct).

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Over-specification of runtime behavior | Medium | Low | Keep to declarative rules; avoid implementation details |
| Inconsistency with existing 5d artifacts | Low | Medium | Cross-reference existing schemas/policies explicitly |

## 7. Dependencies

- Conflict detection schema (`governance/schemas/conflict-detection.schema.json`) — referenced
- Merge sequencing policy (`governance/policy/merge-sequencing.yaml`) — referenced

## 8. Backward Compatibility

Fully additive. New file only. Single-session startup.md workflow is unaffected — the protocol applies only when a multi-agent orchestrator is present.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Standard review |
| security-review | Yes | Standard review |
| documentation-review | Yes | GOALS.md and doc updates |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Use YAML policy format | Consistent with merge-sequencing.yaml; operational protocol is better as policy than schema |
| 2026-02-24 | Reference existing 5d artifacts | The three artifacts form a cohesive Phase 5d governance package |
