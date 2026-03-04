# Topology Enforcement in Python Engine

**Author:** Claude Code
**Date:** 2026-03-03
**Status:** draft
**Issue:** [#775 - enforce: Topology validation must reject phase transitions when agent hierarchy is violated](https://github.com/convergent-systems-co/dark-forge/issues/775)
**Branch:** itsfwcp/enforce/775/topology-enforcement

---

## 1. Objective

Convert PM mode topology validation from advisory warnings to hard-blocking errors. The orchestrator must reject phase transitions when agent hierarchy invariants are violated, preventing malformed agent trees from completing the pipeline. Specifically:

1. Convert `TopologyWarning` to `TopologyError` with blocking behavior in `step --complete`
2. Add `parent_task_id` validation requiring every Coder to reference its parent Tech Lead
3. Enforce persona-phase binding so `step --complete N` validates the caller's persona matches expected actors
4. Hard-gate Phase 3→4 transitions when PM mode is active and no Coder agents exist under any Tech Lead
5. Add enforcement in the Go binary via new `validate-topology` subcommand for CI/pre-merge gates

---

## 2. Rationale

The issue documents that topology rules are currently treated as recommendations (warnings), not requirements. This creates a critical governance gap:

- Tech Leads can code directly without spawning Coders — orchestrator warns but allows it
- PM can perform implementation work directly — no enforcement at all
- Phase 4 proceeds without registered Coder agents — only a metadata field, not a gate

This violates the PM mode contract, which requires strict agent hierarchy for auditability and role separation. The acceptance criteria explicitly demand blocking behavior, not warnings.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Keep warnings, add logging | Yes | Governance audits require hard gates; warnings are insufficient for enforcement |
| Reject at agent registration time | Yes | Validation must also consider cross-agent relationships (Coder→TL, TL→PM); deferred to phase transitions is cleaner |
| Make parent_task_id optional in standard mode | Yes | Explicit linkage is better; standard mode can set empty string, PM mode validates non-empty |
| Defer Go binary changes to Phase 2 | Yes | Users need CI/pre-merge validation now; Python enforcement alone is incomplete |

---

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/engine/orchestrator/topology_error.py` | New exception class `TopologyError` replacing warnings; hard-blocking enforcement |
| `governance/engine/tests/test_topology_enforcement.py` | Unit tests for all topology enforcement rules (Phase 1→2, 3→4, persona-phase binding, parent linkage) |
| `src/cmd/dark-governance/validate-topology.go` | Go subcommand for standalone topology validation with exit codes |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/engine/orchestrator/agent_registry.py` | Replace `validate_topology()` soft warnings with `validate_topology_hard()` that raises `TopologyError` instead of returning strings; add `validate_parent_linkage()` method for Coder→TL parent validation |
| `governance/engine/orchestrator/step_runner.py` | (1) Import and catch `TopologyError` in `step()` method, convert to RuntimeError with clear error message; (2) Add persona validation on `step --complete` using `_validate_caller_persona()` helper; (3) Call `validate_topology_hard()` before phase transitions when PM mode is active (Phase 1→2, 3→4) |
| `governance/engine/orchestrator/__init__.py` | Export `TopologyError` in public API |
| `governance/engine/orchestrator/session.py` | No change needed (parent_task_id already in RegisteredAgent) |
| `src/cmd/dark-governance/main.go` | Add subcommand routing for `validate-topology` |
| `src/cmd/dark-governance/validate/topology.go` | New file; load session state and check topology invariants |
| `.ai/CLAUDE.md` | Update command reference to include `validate-topology` subcommand usage |

### Files to Delete

None — `TopologyWarning` remains for backward compatibility but is no longer used in enforcement paths.

---

## 4. Approach

### Step 1: Create TopologyError Exception Class

Create `/Users/itsfwcp/.ai/governance/engine/orchestrator/topology_error.py`:

- Define `TopologyError(RuntimeError)` with phase, rule, and detail fields
- Provide `to_dict()` for serialization
- Provide clear `__str__()` for user-facing error messages

### Step 2: Update Agent Registry

Modify `/Users/itsfwcp/.ai/governance/engine/orchestrator/agent_registry.py`:

- Rename `validate_topology_hard()` to raise `TopologyError` instead of returning error strings
- Add `validate_parent_linkage(use_project_manager: bool)` method:
  - In PM mode: every Coder must have non-empty `parent_task_id`
  - In PM mode: every Tech Lead must have non-empty `parent_task_id` (optional, or always empty)
  - Return list of `TopologyError` objects, one per violation
- Add `validate_phase_4_coder_coverage()` method:
  - At Phase 3→4, every Tech Lead registered must have at least one Coder under it
  - Return `TopologyError` if any Tech Lead has zero Coders

### Step 3: Update StepRunner

Modify `/Users/itsfwcp/.ai/governance/engine/orchestrator/step_runner.py`:

1. **Import and export** `TopologyError` from topology module
2. **Add `_validate_caller_persona()` helper**:
   - Takes (agent_task_id, completed_phase)
   - Loads topology policy (from `governance/policy/agent-topology.yaml` or hardcoded rules)
   - Checks that agent's persona matches expected actor for phase
   - Raises `TopologyError` if mismatch
3. **Update `step()` method**:
   - After ensuring session, call `_validate_caller_persona(agent_task_id, completed_phase)` if `agent_task_id` is provided
   - Wrap in try-except, convert `TopologyError` to RuntimeError with clear message
4. **Add hard topology enforcement before phase transitions**:
   - In `_advance_to()` or after `_next_phase()`, if PM mode is active:
     - Before entering Phase 2: call `self._registry.validate_topology_hard(2, True)` — must have DevOps Engineer
     - Before entering Phase 4: call `self._registry.validate_topology_hard(4, True)` and `validate_phase_4_coder_coverage()` — must have Tech Leads and Coders under each TL
   - Wrap in try-except, convert `TopologyError` to RuntimeError with formatted message

### Step 4: Write Tests

Create `/Users/itsfwcp/.ai/governance/engine/tests/test_topology_enforcement.py`:

**Unit tests for TopologyError**:
- Construction and serialization
- Clear string representation

**Unit tests for Agent Registry topology enforcement**:
- `validate_parent_linkage()` passes when all Coders have parent_task_id in PM mode
- `validate_parent_linkage()` fails when Coder has empty parent_task_id in PM mode
- `validate_parent_linkage()` skips validation in standard mode
- `validate_phase_4_coder_coverage()` passes when all Tech Leads have ≥1 Coder
- `validate_phase_4_coder_coverage()` fails when Tech Lead has zero Coders
- `validate_topology_hard()` raises TopologyError for missing DevOps Engineer at Phase 2
- `validate_topology_hard()` raises TopologyError for missing Tech Lead at Phase 4

**Integration tests for StepRunner**:
- `step(1, {"issues_selected": ["#42"]}, agent_task_id="pm-1")` succeeds with correct persona
- `step(1, ...)` with wrong persona raises RuntimeError with topology error message
- `step(2, ...)` in PM mode fails if no DevOps Engineer registered
- `step(4, ...)` in PM mode fails if no Tech Leads registered
- `step(4, ...)` in PM mode fails if Tech Lead has no Coders
- Session persistence: restored registry preserves parent_task_id links

**E2E scenario test**:
- Register PM agent, DevOps Engineer → advance to Phase 2 ✓
- Register Tech Lead without Coders → attempt Phase 3→4 fails ✗
- Register Coder under Tech Lead with correct parent_task_id → Phase 3→4 succeeds ✓

### Step 5: Create Go `validate-topology` Subcommand

Create `/Users/itsfwcp/.ai/src/cmd/dark-governance/validate/topology.go`:

1. **Load current session** from `.artifacts/state/sessions/{latest}.json`
2. **Check topology invariants**:
   - If PM mode: DevOps Engineer exists
   - If PM mode: All Tech Leads have ≥1 Coder under them
   - All Coders have non-empty parent_task_id
3. **Output results**:
   - JSON format with violations array
   - Human-readable format with clear error messages
4. **Exit codes**:
   - 0 if valid
   - 1 if topology violations found
   - 2 if cannot load session or config

Update `/Users/itsfwcp/.ai/src/cmd/dark-governance/main.go` to route `validate-topology` subcommand.

### Step 6: Update Documentation

Update `/Users/itsfwcp/.ai/.ai/CLAUDE.md`:

Add command reference:
```bash
# Validate topology without state change
python3 -m governance.engine.orchestrator status --validate-topology

# Go binary (when available)
dark-governance validate-topology [--session-id <id>] [--format json|text]
```

Update governance docs to document the enforcement model.

---

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `TopologyError`, `AgentRegistry.validate_parent_linkage()`, `AgentRegistry.validate_topology_hard()`, `AgentRegistry.validate_phase_4_coder_coverage()` | Test each validation rule in isolation with mocked registry state |
| Integration | `StepRunner.step()` with topology violations, `_validate_caller_persona()` with mismatched personas | Test StepRunner integration with registry; verify RuntimeError conversion; test session persistence |
| E2E | Full PM mode workflow: PM→DevOps→Tech Leads→Coders | Test complete agent hierarchy setup and phase transitions with proper topology |
| Go | `validate-topology` subcommand with various session states | Test exit codes, JSON output, missing sessions, invalid configs |

**Acceptance test checklist**:
- [ ] `step --complete 3` returns error if PM mode + no Coders registered
- [ ] `step --complete N` validates persona of the caller
- [ ] Agent registry enforces parent linkage in PM mode
- [ ] `topology_errors` returned (not just warnings) for violations
- [ ] Go binary `validate-topology` returns exit code 1 on violation, 0 on pass
- [ ] All existing orchestrator tests pass
- [ ] New topology enforcement tests added

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking change for existing PM mode workflows | Medium | High | Provide clear error messages; update docs with setup checklist; add migration guide for failed workflows |
| Go binary not available during Phase 1 | High | Low | Go command is optional for CI; Python enforcement is sufficient for now |
| Phase transitions block unexpectedly | Medium | High | Add extensive debug logging; provide `--force` override for manual recovery (with audit trail) |
| Persona validation too strict | Low | Medium | Load topology policy from file; allow overrides via config.yaml |
| Test coverage gaps in complex scenarios | Medium | Medium | Write parameterized tests; test with multiple Tech Leads and Coders |

---

## 7. Dependencies

- [ ] Non-blocking: `governance/policy/agent-topology.yaml` must exist (currently hardcoded in code; no blocking dependency)
- [ ] Non-blocking: Go build tools available (Go subcommand is optional; Python enforcement is primary)
- [ ] Blocking: Python 3.10+ with dataclasses (already required)

---

## 8. Backward Compatibility

**Breaking change**: PM mode workflows will now fail if topology invariants are violated (previously warnings only).

**Migration path**:
1. Update orchestrator code
2. On first workflow failure, read error message — shows which agent persona is missing
3. Update dispatch code to register correct agents before phase transitions
4. Retry workflow

Non-PM mode (standard) workflows are unaffected — `validate_topology_hard()` returns empty list when `use_project_manager=False`.

---

## 9. Governance

Expected panel reviews and policy profile:

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Changes to core orchestrator control plane; high risk |
| security-review | Yes | Enforcement logic directly impacts pipeline execution |
| threat-modeling | Yes | Topology violations could indicate injection attacks or agent misconfiguration |
| documentation-review | Yes | New enforcement rules must be clearly documented |

**Policy Profile:** `infrastructure_critical`
**Expected Risk Level:** `high` (control plane changes; blocking enforcement)

---

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-03 | Convert warnings to hard errors using TopologyError exception | Clear, explicit exception handling provides better error reporting and audit trails than error strings |
| 2026-03-03 | Add `validate_parent_linkage()` as separate method from `validate_topology_hard()` | Separates concerns: hierarchy validation (parent linkage) from role validation (who's registered) |
| 2026-03-03 | Phase 4 gating checks *all* Tech Leads have ≥1 Coder | Prevents partial dispatches; ensures every Tech Lead can delegate to at least one Coder |
| 2026-03-03 | Keep `TopologyWarning` in codebase for backward compatibility | Allows gradual migration; old code referencing warnings won't break immediately |
| 2026-03-03 | Make parent_task_id validation PM-mode-only | Standard mode doesn't enforce hierarchy; skips extra validation cost |
