# Agent Containment

## Overview

The agent containment policy enforces least-privilege boundaries across the Dark Forge agentic pipeline. Each persona operates within a defined sandbox that restricts which files it can modify, which git operations it can perform, and how large its changes can be.

The policy is defined in `governance/policy/agent-containment.yaml` and referenced by each persona definition in `governance/personas/agentic/`. It is an enforcement artifact: deterministic rules evaluated programmatically, never by AI interpretation.

---

## Design Principles

1. **Least privilege** -- each persona receives only the permissions required for its role. Worker agents (Coder, IaC Engineer, Tester) have the tightest restrictions; the orchestrator (Tech Lead) has elevated but still bounded permissions.

2. **Defense in depth** -- containment rules complement (not replace) existing guardrails such as the Test Evaluator approval gate, the policy engine merge decision, and the agent protocol's separation of concerns.

3. **Blast radius limitation** -- resource limits (max files per PR, max lines per commit) prevent any single agent action from producing outsized changes that are difficult to review.

4. **Governance infrastructure protection** -- policy files, schemas, personas, and review prompts are denied to all worker agents. These artifacts are managed by humans or the governance framework itself.

5. **Advisory-first rollout** -- the policy starts in `advisory` mode (log and warn) to allow calibration before switching to `enforced` mode (block and escalate).

---

## Per-Persona Boundaries

### Path Restrictions

| Persona | Allowed Paths | Denied Paths |
|---------|--------------|--------------|
| **Coder** | All except denied | `governance/policy/**`, `governance/schemas/**`, `governance/personas/**`, `governance/prompts/reviews/**`, `jm-compliance.yml`, `.github/workflows/dark-factory-governance.yml` |
| **IaC Engineer** | `infra/**`, `bicep/**`, `terraform/**`, IaC file types, `.artifacts/plans/**`, `docs/**` | Same as Coder |
| **Tester** | Write: `tests/**`, `test/**`, test file patterns, `.artifacts/panels/**` | Same as Coder |
| **Tech Lead** | Orchestration scope (no implementation files) | `governance/policy/**`, `governance/schemas/**` |
| **DevOps Engineer** | Session lifecycle scope | `governance/policy/**`, `governance/schemas/**`, `src/**`, `lib/**`, `app/**` |

### Operation Restrictions

| Persona | Allowed Operations | Denied Operations |
|---------|-------------------|-------------------|
| **Coder** | Implementation within plan scope | `git_push`, `git_merge`, `approve_pr`, `modify_policy`, `modify_schema` |
| **IaC Engineer** | IaC implementation within plan scope | `git_push`, `git_merge`, `approve_pr`, `modify_policy`, `modify_schema`, `modify_application_code` |
| **Tester** | Test execution, evaluation, panel reports | `git_push`, `git_merge`, `approve_own_pr`, `modify_source_code`, `modify_policy`, `modify_schema`, `create_branch` |
| **Tech Lead** | `git_push`, `create_pr`, `merge_pr`, `assign_work`, `invoke_panels`, `create_issues` | `approve_own_pr`, `write_implementation_code`, `modify_policy`, `modify_schema` |
| **DevOps Engineer** | `update_submodule`, `triage_issues`, `create_issues`, `run_preflight`, `manage_session_lifecycle`, `emit_cancel` | `implement_code`, `review_code`, `merge_pr`, `approve_pr`, `invoke_panels`, `modify_policy`, `modify_schema` |

### Resource Limits

| Persona | Max Files/PR | Max Lines/Commit | Max New Files/PR | Max Commits/PR |
|---------|-------------|------------------|-----------------|----------------|
| **Coder** | 30 | 1,000 | 15 | 20 |
| **IaC Engineer** | 20 | 800 | 10 | 15 |
| **Tester** | 10 | 500 | -- | -- |
| **Tech Lead** | -- | -- | -- | -- (max 10 PRs/session) |
| **DevOps Engineer** | -- | -- | -- | -- (max 20 issues/triage) |

**Global ceilings** (override per-persona limits if higher): 50 files/PR, 2,000 lines/commit, 25 new files/PR, 30 commits/PR.

---

## Enforcement Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `advisory` | Log violation, warn, continue execution | Initial rollout, calibration period |
| `enforced` | Block operation, log violation, escalate to human review | Production steady-state |

The current default is `advisory`. To switch to enforced mode, update the `enforcement.mode` field in `governance/policy/agent-containment.yaml`.

---

## Violation Handling

When a containment rule is violated:

1. **Advisory mode**: The violation is logged to `.artifacts/state/containment-violations.jsonl`, the Tech Lead is notified, and the violation is included in the next panel emission. Execution continues.

2. **Enforced mode**: The operation is blocked. The violation is logged, both the Tech Lead and DevOps Engineer are notified, and the incident is escalated to human review. Execution halts for the violating action.

All violations (in both modes) are included in panel emissions so the policy engine can factor them into merge decisions.

### Violation Log Format

Violations are appended as JSON lines to `.artifacts/state/containment-violations.jsonl`:

```json
{
  "timestamp": "2026-02-27T14:30:00Z",
  "persona": "coder",
  "rule_type": "denied_path",
  "rule_value": "governance/policy/**",
  "attempted_action": "modify",
  "target": "governance/policy/default.yaml",
  "enforcement_mode": "advisory",
  "outcome": "logged_and_continued",
  "correlation_id": "issue-428"
}
```

---

## Extension Guide

Consuming repositories can customize containment rules via `project.yaml`:

### Adding Denied Paths

```yaml
# project.yaml
governance:
  containment:
    additional_denied_paths:
      coder:
        - "config/production/**"
        - "secrets/**"
      iac-engineer:
        - "legacy-infra/**"
```

Additional denied paths are **merged** with the base policy. Paths cannot be removed.

### Tightening Resource Limits

```yaml
# project.yaml
governance:
  containment:
    resource_limits:
      coder:
        max_files_per_pr: 15       # Stricter than default 30
        max_lines_per_commit: 500  # Stricter than default 1000
```

Limits can be **lowered** but never raised above the values in the base policy.

### What Cannot Be Extended

- Denied paths cannot be removed from any persona
- Resource limits cannot be raised above base policy values
- Enforcement mode cannot be relaxed (consuming repos cannot set `advisory` if the base policy is `enforced`)
- Denied operations cannot be removed from any persona

---

## Relationship to Other Governance Controls

The containment policy works alongside -- not in place of -- existing governance mechanisms:

| Control | Scope | Containment Role |
|---------|-------|-----------------|
| Agent protocol (ASSIGN/RESULT/APPROVE) | Inter-agent communication | Containment restricts *what* each agent can do; protocol restricts *how* they communicate |
| Tester approval gate | Push authorization | Containment denies `git_push` for Coder; Tester gate is the mechanism that grants it |
| Policy engine merge decision | PR merge | Containment denies `merge_pr` for workers; policy engine governs when Tech Lead may merge |
| Panel emissions | Review quality | Containment violations are surfaced in emissions for policy engine evaluation |
| Context capacity protocol | Session lifecycle | Containment resource limits are per-PR/commit; context capacity is per-session |

---

## Future Work

- **Phase transition to `enforced`**: After calibration with `advisory` mode data, switch the default enforcement mode.
- **Runtime enforcement integration**: Hook containment checks into the policy engine for automated pre-commit validation.
- **Telemetry dashboard**: Aggregate containment violation logs for trend analysis and threshold tuning.
- **Dynamic limits**: Adjust resource limits based on risk classification of the change (e.g., tighter limits for high-risk PRs).
