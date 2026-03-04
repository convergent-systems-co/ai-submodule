# fix: Context Capacity Shutdown Protocol Enforcement

**Author:** Team Lead (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** #505
**Branch:** itsfwcp/fix/505/context-capacity-shutdown-protocol

---

## 1. Objective

Make the context capacity shutdown protocol enforceable by ensuring checkpoints conform to the official schema, adding a `context_capacity` extension to the schema, adding milestone-based checkpoint instructions to the Team Lead persona, and ensuring the commit-PR-merge cycle is never handed back for manual prompting.

## 2. Rationale

The shutdown protocol is documented in `startup.md` but checkpoints written in practice don't conform to `checkpoint.schema.json`. Phase 0 recovery works but expects schema-compliant data. Milestone checkpoints are missing — the Team Lead only checkpoints at shutdown, not at pipeline milestones.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Add runtime code (Python) to enforce checkpoints | Yes | This repo is cognitive artifacts, not application code. Enforcement is via persona instructions + schema. |
| Keep freeform checkpoint format | Yes | Non-deterministic recovery; schema exists but isn't used |
| Add context tracking tooling | Yes | AI agents cannot programmatically measure their own context usage; heuristic signals in persona instructions are the correct mechanism |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files needed |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/schemas/checkpoint.schema.json` | Add optional `context_capacity` object and `context_gates_passed` array (already written in practice, not yet in schema). Add `session_id` field. |
| `governance/personas/agentic/team-lead.md` | Add "Milestone Checkpoint Protocol" section with checkpoint-at-milestone instructions and schema-compliant format. Add CANCEL handling that checkpoints remaining steps. |
| `governance/personas/agentic/devops-engineer.md` | Strengthen context gate enforcement instructions. Add explicit checkpoint-writing format that matches schema. |
| `CLAUDE.md` | Update checkpoint schema reference to note `context_capacity` extension |
| `docs/architecture/context-management.md` | Update to reference milestone checkpoints (if file exists) |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. **Update `checkpoint.schema.json`** — Add `context_capacity` object (tier, tool_calls, turn_count, issues_completed_count, platform, trigger), `context_gates_passed` array, and `session_id` string. All optional to maintain backward compatibility with existing checkpoints.

2. **Update Team Lead persona** — Add a "Milestone Checkpoint Protocol" section that instructs the Team Lead to write schema-compliant checkpoints at these milestones:
   - After all plans created (Phase 2 complete)
   - After PR creation (Phase 4d complete)
   - On CANCEL receipt: commit partial work, checkpoint remaining steps, do NOT hand control back

3. **Update DevOps Engineer persona** — Strengthen the context gate instructions to explicitly output the checkpoint JSON format matching the schema. Ensure the shutdown protocol section references `checkpoint.schema.json` field names.

4. **Update CLAUDE.md** — Reference the `context_capacity` extension in the checkpoint schema description.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | `checkpoint.schema.json` | Validate that the updated schema accepts both old-format and new-format checkpoints (backward compat via optional fields) |
| Manual | Persona instructions | Verify instructions reference correct field names |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Existing checkpoints fail new schema | Low | Low | All new fields are optional; old checkpoints remain valid |
| Persona instructions ignored by agent | Med | Med | Instructions are clear, schema-backed, and referenced from startup.md |

## 7. Dependencies

- [x] `checkpoint.schema.json` exists (already present)
- [x] Phase 0 recovery exists in `startup.md` (already implemented)
- [ ] No blocking dependencies

## 8. Backward Compatibility

All schema changes are additive (optional fields). Existing checkpoints remain valid. No migration needed.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Schema changes affect enforcement artifacts |
| documentation-review | Yes | Persona and docs changes |
| code-review | Yes | Schema validation |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Schema extension (not replacement) | Backward compatibility with existing checkpoints |
| 2026-02-27 | Milestone checkpoints in Team Lead only | DevOps Engineer already handles shutdown; Team Lead needs milestones |
