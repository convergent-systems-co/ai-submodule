# Plan: PM Topology Enforcement at Orchestrator Dispatch Time

**Issue:** #759
**Branch:** `itsfwcp/fix/759/pm-topology-enforcement`
**Type:** fix

## Problem

The PM mode agent topology (PM -> DevOps Engineer -> Tech Leads -> Coders) is defined in personas and documentation but has zero runtime enforcement at dispatch time. The orchestrator validates phase transition gates but not who spawns whom. The PM can register agents without actually following the spawn DAG, and there is no `dispatch` command to validate parent-child relationships.

## Solution

### 1. Add `governance/policy/agent-topology.yaml`

Define the spawn DAG as a policy file:

```yaml
topology:
  project_manager:
    can_spawn: [devops_engineer, tech_lead]
    cannot_spawn: [coder, iac_engineer, test_evaluator, document_writer, documentation_reviewer]
    max_concurrent:
      devops_engineer: 1
      tech_lead: ${governance.parallel_tech_leads}
  tech_lead:
    can_spawn: [coder, iac_engineer, test_evaluator, document_writer, documentation_reviewer]
    cannot_spawn: [devops_engineer, tech_lead, project_manager]
    max_concurrent:
      coder: ${governance.parallel_coders}
  devops_engineer:
    can_spawn: []
    cannot_spawn: ["*"]
  coder:
    can_spawn: []
    cannot_spawn: ["*"]
  iac_engineer:
    can_spawn: []
    cannot_spawn: ["*"]
  test_evaluator:
    can_spawn: []
    cannot_spawn: ["*"]
  document_writer:
    can_spawn: []
    cannot_spawn: ["*"]
  documentation_reviewer:
    can_spawn: []
    cannot_spawn: ["*"]
```

### 2. Add `orchestrator dispatch` CLI Command

New subcommand in `__main__.py`:

```
orchestrator dispatch --persona <persona> --parent <parent_task_id> \
  --session-id <id> --assign '<json>' [--config project.yaml]
```

Behavior:
1. Load topology policy from `governance/policy/agent-topology.yaml`
2. Look up parent agent in registry to determine parent persona
3. Validate parent persona is allowed to spawn target persona (transition map)
4. Check max_concurrent limits against current registry counts
5. Generate a dispatch descriptor (envelope) with:
   - `dispatch_id`: UUID
   - `persona`: target persona path
   - `assign`: structured ASSIGN message
   - `session_id`: current session
   - `task_id`: generated task ID
   - `self_register_required`: true
6. Return the envelope as JSON to stdout

Rejection case:
```json
{"error": "topology_violation", "detail": "project_manager cannot spawn coder. Valid targets: [devops_engineer, tech_lead]"}
```

### 3. Add Phase-Persona Binding to `step --complete`

Extend `step --complete` to accept an optional `--agent <task_id>` parameter. When provided (and PM mode is active), validate that the completing agent's persona matches the expected executor for that phase.

Phase-persona bindings (PM mode):
- Phase 1: `devops_engineer`
- Phase 2: `tech_lead`
- Phase 3: `tech_lead`
- Phase 4: `devops_engineer`
- Phase 5: `devops_engineer`

In standard mode (PM off), this validation is skipped.

### 4. Implementation Files

| File | Change |
|------|--------|
| `governance/policy/agent-topology.yaml` | New: spawn DAG policy |
| `governance/engine/orchestrator/topology.py` | New: topology loader + validator |
| `governance/engine/orchestrator/__main__.py` | Add `dispatch` subcommand, add `--agent` to `step` |
| `governance/engine/orchestrator/step_runner.py` | Add `dispatch_agent()` method, add persona binding check in `step()` |
| `governance/engine/orchestrator/agent_registry.py` | No changes needed (already has `get_agent`, `get_agents_by_persona`) |
| `governance/engine/tests/test_topology.py` | New: unit tests for topology validator |
| `governance/engine/tests/test_agent_registry.py` | Add dispatch + persona binding integration tests |

### 5. Test Plan

- Unit: TopologyPolicy loads and validates spawn rules
- Unit: dispatch rejects invalid parent->child (PM spawns coder)
- Unit: dispatch accepts valid parent->child (PM spawns tech_lead)
- Unit: max_concurrent limits enforced
- Unit: phase-persona binding rejects wrong persona completing phase
- Unit: standard mode (PM off) skips all topology checks
- Integration: CLI `dispatch` command returns envelope JSON
- Integration: CLI `step --complete --agent` validates persona binding

### 6. Out of Scope (Future)

- Envelope-based dispatch transport (#751)
- Self-registration from envelope (#751)
- Timeout for unregistered agents
- External state storage (#757)
