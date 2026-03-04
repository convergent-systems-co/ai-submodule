# Enforce: Go Binary Must Encode PM Topology Rules as Compile-Time and Runtime Constraints

**Author:** Claude (Coder)
**Date:** 2026-03-03
**Status:** draft
**Issue:** [#776](https://github.com/convergent-systems-co/dark-forge/issues/776)
**Branch:** SET-Apps/itsfwcp/feat/776-go-binary-topology-enforcement

---

## 1. Objective

Add compile-time and runtime topology validation to the `dark-governance` Go binary to enforce PM mode topology rules (persona hierarchy, parent-child relationships, action allowlists). This ensures the binary can serve as the primary entry point for consuming repos while maintaining governance integrity without external orchestrator involvement.

The binary will detect and fail-fast on topology violations, preventing invalid agent configurations from progressing through phases.

## 2. Rationale

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Topology validation only in Python orchestrator | Yes | Python orchestrator is not available in consuming repos that run the binary directly; topology violations would only be caught after the fact via CI logs |
| Implicit type safety via structs | Yes | Implicit safety allows invalid states at runtime; exhaustive action allowlists with explicit validation prevent logical errors earlier in the pipeline |
| Runtime-only validation | Yes | Compile-time type constraints (Go enums, required fields) catch invalid configurations before any runtime logic executes; combined with runtime checks, this provides defense in depth |
| External topology schema in JSON | Partial | JSON schema is useful but Go types provide type-safe enforcement; topology rules derived from project.yaml and embedded at build time reduce runtime parsing overhead |

**Chosen approach:** Layered validation with compile-time Go types (PersonaRole enum, AgentRegistration struct with ParentTaskID requirement in PM mode) plus runtime validators (PhaseTransition function, validate-topology CLI command) and pre-phase hooks.

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `src/internal/topology/persona.go` | PersonaRole type with exhaustive action allowlists (Spawn, Review, Implement, Commit, etc.) |
| `src/internal/topology/validation.go` | PhaseTransition validator function and tree validators (CheckParentChild, CheckCodersHaveLeads, etc.) |
| `src/internal/topology/errors.go` | Typed error definitions (TopologyViolation, InvalidPhaseTransition, etc.) |
| `src/internal/topology/rules.go` | Topology rules loader from project.yaml; topology-rules.json schema definition |
| `src/cmd/dark-governance/validate_topology_cmd.go` | validate-topology CLI command with --strict flag |
| `src/internal/topology/topology_test.go` | Unit tests for PersonaRole, PhaseTransition, action validators |
| `src/cmd/dark-governance/validate_topology_cmd_test.go` | Integration tests for CLI command with session state |
| `.artifacts/schemas/topology-rules.schema.json` | JSON schema for topology-rules.json (required fields per phase) |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `src/cmd/dark-governance/root.go` | Add `validateTopologyCmd` to rootCmd in init() |
| `src/cmd/dark-governance/verify_environment_cmd.go` | Add `--check-topology` flag; call topology validator before drift checks |
| `src/cmd/dark-governance/engine_cmd.go` | Add `--strict` flag to engine run; integrate PhaseTransition validation (pre-merge check) |
| `src/internal/deliveryintent/types.go` | Add `topology_valid: bool` field to session state struct |
| `src/internal/home/session.go` | Add TopologyState field to session; load/persist topology_valid flag |
| `src/cmd/dark-governance/init_cmd.go` | Emit topology-rules.json from project.yaml governance config on init |
| `governance/prompts/agent-protocol.md` | Document topology constraints in agent persona definitions (reference) |
| `docs/architecture/agent-architecture.md` | Add topology enforcement section with exit codes and validation flow |

### Files to Delete

None.

## 4. Approach

### Step 1: Define PersonaRole Type with Action Allowlists (Day 1)

Create `src/internal/topology/persona.go`:
- Define `PersonaRole` enum: PM, TechLead, Coder, DevOps (iota-based const)
- Define `Action` enum: Spawn, Review, Implement, Test, Commit, Push, Wait, Merge, Edit, Write
- Create `AllowedActions(role PersonaRole) []Action` function returning the exhaustive allowlist per role:
  - PM: Spawn, Wait, Review, Advance
  - TechLead: Plan, Spawn, Review
  - Coder: Implement, Test, Commit
  - DevOps: Merge, Rebase, Push
- Create `CanExecute(role PersonaRole, action Action) bool` validator
- Add `String()` method for human-readable output

**Test:** Unit tests in `persona_test.go` verify:
- PM cannot execute Implement, Commit, Edit
- TechLead cannot execute Implement directly (must spawn Coders)
- Coder cannot execute Spawn
- DevOps cannot execute Implement

### Step 2: Define AgentRegistration Struct with ParentTaskID Requirement (Day 1)

In `src/internal/topology/validation.go`:
- Create `AgentRegistration` struct with fields:
  - `AgentID string`
  - `PersonaRole PersonaRole`
  - `ParentTaskID string` (required in PM mode; optional otherwise)
  - `ChildTaskIDs []string`
  - `Phase int`
- Add validation function `ValidateRegistration(reg AgentRegistration, pmModeEnabled bool) error`:
  - If pmModeEnabled && ParentTaskID == "" → return TopologyViolation("ParentTaskID required in PM mode")
  - If PersonaRole == PM && ParentTaskID != "" → return error (PM has no parent)

### Step 3: Implement PhaseTransition Validator (Day 2)

In `src/internal/topology/validation.go`:
- Create `PhaseTransition(currentPhase, targetPhase int, registry []AgentRegistration, pmModeEnabled bool) error`:
  - Validate target phase is currentPhase + 1 (no skipping)
  - Check tree constraints before advancing:
    - If pmModeEnabled: Every TechLead must have ≥1 Coder child
    - Every Coder must have a TechLead parent
    - DevOps must exist if PM mode active
  - Return `InvalidPhaseTransition` error with constraint name if violated
- Implement helper functions:
  - `CheckParentChildRelationships(registry []AgentRegistration) error`
  - `CheckCodersHaveTechLeads(registry []AgentRegistration) error`
  - `CheckTechLeadsHaveCoders(registry []AgentRegistration) error`
  - `CheckDevOpsExists(registry []AgentRegistration) error`

**Test:** Table-driven tests in `validation_test.go`:
- Valid tree: PM → TechLead → Coder passes
- Missing TechLead parent → error
- TechLead with no Coders → warning (allowed but degraded)
- Coder as direct PM child → error
- No DevOps in PM mode → error

### Step 4: Create validate-topology CLI Command (Day 2)

Create `src/cmd/dark-governance/validate_topology_cmd.go`:
- Command signature: `dark-governance validate-topology`
- Flags:
  - `--session-dir` (default: `.artifacts/state/sessions/`)
  - `--strict` (fail on any violation including warnings)
  - `--output` (human | json)
- Load session state from .artifacts/state/sessions/latest.json
- Extract agent registry from session
- Call PhaseTransition validator for each phase boundary traversed
- Exit codes:
  - 0: topology valid
  - 1: warnings (degraded but functional) — only if --strict not set
  - 2: violation (hard block)
- Output format:
  - Human: "Topology Validation Report" with agent tree, violations, warnings, summary
  - JSON: { "status": "valid|warning|violation", "phase": N, "violations": [...], "agents": [...] }

### Step 5: Add --strict Flag to verify-environment (Day 2)

In `src/cmd/dark-governance/verify_environment_cmd.go`:
- Add flag: `verifyEnvCheckTopology bool`
- After loading delivery intent, call topology validator
- If topology invalid and --strict set, fail with exit code 2
- Integrate topology_valid into verification report
- Update docstring to document --check-topology flag and exit codes

### Step 6: Add --strict Flag to engine run (Day 2)

In `src/cmd/dark-governance/engine_cmd.go`:
- Add flag: `engineStrict bool`
- Before running policy evaluation, validate PhaseTransition for the phase boundary
- If validation fails and strict mode enabled, return error (exit code 2)
- Allows merges only if topology is valid

### Step 7: Load Topology Rules from project.yaml on init (Day 3)

In `src/cmd/dark-governance/init_cmd.go`:
- After loading project.yaml, extract governance.use_project_manager flag
- Create topology-rules.json with structure:
  ```json
  {
    "pm_mode_enabled": bool,
    "parallel_team_leads": int,
    "parallel_coders": int,
    "required_personas": ["PM", "TechLead", "Coder", "DevOps"],
    "constraints": {
      "every_techLead_must_have_coders": true,
      "every_coder_must_have_parent": true,
      "devops_required_in_pm_mode": true
    }
  }
  ```
- Write to `.artifacts/state/topology-rules.json`
- Validate against `governance/schemas/topology-rules.schema.json`

### Step 8: Update Session State to Track Topology (Day 3)

In `src/internal/home/session.go`:
- Add field: `TopologyValid bool` to session struct
- Add method: `ValidateAndRecord(registry []AgentRegistration, pmModeEnabled bool)`
  - Calls PhaseTransition validator
  - Sets TopologyValid field
  - Persists to disk

### Step 9: Write Comprehensive Tests (Day 4)

Create `src/internal/topology/topology_test.go`:
- Table-driven tests for PersonaRole.CanExecute
- PhaseTransition validator tests:
  - Valid trees (PM → TL → Coder)
  - Missing parent relationships
  - TechLead with no children (warning vs error)
  - DevOps missing in PM mode
  - Phase sequence violations (skip phases)
- Tests for all helper validators

Create `src/cmd/dark-governance/validate_topology_cmd_test.go`:
- Mock session state with valid/invalid trees
- Verify exit codes (0, 1, 2)
- Verify JSON and human output formatting
- Test --strict flag behavior

### Step 10: Update Documentation (Day 4)

- Add topology enforcement section to `docs/architecture/agent-architecture.md`:
  - Describe PersonaRole enum and action allowlists
  - Show valid tree structure diagrams (ASCII)
  - Document PhaseTransition constraints with examples
  - Show validate-topology CLI usage and exit codes
- Update `governance/prompts/agent-protocol.md` with topology rules reference
- Add topology-rules.json schema to `.artifacts/schemas/topology-rules.schema.json`

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | PersonaRole enum; CanExecute logic; all validators (CheckParentChild, CheckTechLeads, etc.) | Exhaustive table-driven tests for action allowlists; constraint validation per function |
| Integration | validate-topology CLI; verify-environment --check-topology; engine run --strict | Load session state from disk; call full validation pipeline; verify exit codes and output formats |
| E2E | Multi-phase traversal with topology changes | Simulate 3+ phases with agent registration changes; validate topology at each boundary |

**Test framework:** Go's stdlib `testing` package; table-driven pattern for maintainability.

**Coverage target:** 85% on new topology package; 80% overall on modified commands.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking change to session state struct (topology_valid field) | Low | High — consuming repos with old session files will fail | Add migration logic in session loader; default topology_valid=true for legacy sessions until first validation |
| Topology rules in project.yaml are missing or malformed | Medium | Medium — init will fail or emit incomplete rules | Validate project.yaml structure in init; provide helpful error message listing required topology fields |
| PhaseTransition validator is too strict; blocks valid workflows | Medium | High — legitimate PM workflows fail | Document all constraints explicitly; include --strict flag to make degraded mode opt-in; add warnings vs errors tier |
| Circular dependencies in agent tree aren't detected | Low | High — infinite loop in traversal | Add visited set in CheckParentChildRelationships; fail on cycles |
| Performance regression on large agent registries (100+ agents) | Low | Low | Use efficient data structures (maps by AgentID); add optional caching in session state |

**Mitigation summary:** Make topology enforcement backwards-compatible; provide clear error messages; use phased rollout (warnings first, --strict for enforcement).

## 7. Dependencies

- [x] Issue #745 (Go build release pipeline) — must be merged before this implementation; provides build infrastructure for embedding topology rules
- [ ] Session state persistence (existing in home/session.go) — no new work needed; add TopologyValid field only
- [ ] project.yaml parsing (existing in engine) — reuse existing config loading; add governance.use_project_manager extraction

**Blocking:** None. Non-blocking: #745 simplifies embedding but not strictly required.

## 8. Backward Compatibility

**Breaking change:** Yes, adds TopologyValid field to session state.

**Migration path:**
1. Add TopologyValid field with default value `true` in session struct tag
2. In session loader, if field is missing in persisted JSON, set to `true` (assume valid until proven otherwise)
3. After first `validate-topology` run, field is populated from actual validation result
4. Document in CHANGELOG.md: "Added topology state tracking to sessions; legacy sessions default to valid=true"

**For consuming repos:** No impact unless they explicitly enable PM mode (use_project_manager: true). Non-PM repos remain unaffected; topology checks are bypassed if PM mode disabled.

## 9. Governance

Expected panel reviews and policy profile:

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New Go types and functions; architectural patterns must align with existing codebase |
| security-review | No | No authentication, secrets, or external communication involved |
| threat-modeling | No | Not applicable; internal control flow |
| cost-analysis | No | No infrastructure changes |
| documentation-review | Yes | New types and validators must be clearly documented with examples |
| data-governance-review | Yes | Session state gains topology_valid field; persistence logic must be audited |
| architecture-review | Yes | New subsystem (topology) affects agent protocol and phase transitions; cross-cutting concern |

**Policy Profile:** default
**Expected Risk Level:** medium (new type system + state persistence; moderate scope; well-isolated package)

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-03 | Use iota-based const for PersonaRole instead of strings | Type safety; compile-time exhaustiveness checking in switch statements; prevents invalid string values at runtime |
| 2026-03-03 | Separate validation.go and persona.go instead of single file | Separation of concerns; persona is data model, validation is business logic; easier to test and maintain |
| 2026-03-03 | Make --strict flag opt-in, not default | Backward compatibility; allow consuming repos to adopt topology enforcement gradually; degraded mode is functional |
| 2026-03-03 | Embed topology rules from project.yaml at init time instead of runtime parsing | Simpler Go binary; rules are immutable once session starts; reduces coupling to project.yaml format changes |
| 2026-03-03 | Use phase sequence (0, 1, 2, ...) instead of named phases | Alignment with existing orchestrator state representation; simpler validation logic; less coupling to phase name semantics |

---

## Implementation Order

1. **Day 1:** persona.go (PersonaRole enum, action allowlists) + validation.go (AgentRegistration, ValidateRegistration)
2. **Day 2:** PhaseTransition validator + validate_topology_cmd.go + --check-topology flag on verify-environment
3. **Day 3:** init_cmd.go updates + session state topology field + --strict flag on engine run
4. **Day 4:** Comprehensive test suite + documentation updates

**Estimated effort:** 16–20 dev hours (including tests and docs)
