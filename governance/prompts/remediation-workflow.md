# Remediation Workflow: Autonomous Drift Remediation

This workflow is executed by the Tech Lead when a drift signal triggers remediation. It is invoked from the startup sequence (startup.md) or from the runtime feedback pipeline when drift is detected.

<!-- ANCHOR: Must survive context resets -->

## Prerequisites

Before entering this workflow, ensure:

1. A drift signal has been received and normalized (conforming to `governance/schemas/runtime-signal.schema.json`)
2. The drift has been classified by type and severity (per `docs/architecture/runtime-feedback.md` Section 4)
3. A baseline exists for the affected component (conforming to `governance/schemas/baseline.schema.json`)

**Policy files referenced by this workflow:**

- `governance/policy/drift-remediation.yaml` — Allowed actions, prohibited actions, verification config
- `governance/policy/drift-policy.yaml` — Drift-specific policy rules
- `governance/policy/circuit-breaker.yaml` — Circuit breaker state machine
- `governance/policy/component-registry.yaml` — Component criticality
- `governance/policy/rate-limits.yaml` — Rate limiting configuration

**Schemas produced by this workflow:**

- `governance/schemas/remediation-action.schema.json` — Remediation action record
- `governance/schemas/remediation-verification.schema.json` — Verification result record

<!-- /ANCHOR -->

## Workflow Steps

### Step 1: Receive and Validate Drift Signal

1. Confirm the drift signal conforms to `runtime-signal.schema.json`
2. Extract: `signal_id`, `category`, `affected_component`, `severity`, `metrics`
3. Confirm the signal category is drift-related (`configuration_drift` or a category that produced a drift detection result)
4. Assign a `drift_id` (UUID) for tracking this remediation lifecycle

### Step 2: Classify Drift Severity

Apply the severity calculation from the architecture doc:

```
drift_severity = deviation_magnitude × dimension_criticality
```

1. Compute `deviation_magnitude` (0.0–1.0) from signal metrics:
   - Configuration: magnitude of config difference
   - Behavior: standard deviations from baseline
   - Performance: percent degradation from baseline
   - Compliance: control gap severity

2. Look up `dimension_criticality` from `governance/policy/component-registry.yaml`:
   - Critical: 1.0
   - High: 0.75
   - Standard: 0.5
   - Low: 0.25

3. Map the resulting score to severity:
   - 0.0–0.1: informational
   - 0.1–0.3: low
   - 0.3–0.5: medium
   - 0.5–0.7: high
   - 0.7–1.0: critical

### Step 3: Check Policy Constraints

Evaluate the following rules **in order**. If any rule blocks remediation, stop and escalate.

#### 3a: Active Incident Check

```
Rule: drift_policy.active_incident_rule
If: component has an active incident DI
Then: ESCALATE to human — do not auto-remediate
Rationale: Drift during an active incident may indicate ongoing attack or cascading failure
```

#### 3b: Regression Check

```
Rule: drift_policy.regression_rule
If: drift fingerprint matches a remediated drift within 7 days
Then: Escalate severity by one level, tag as "regression"
Then: Re-evaluate against ceiling (may now exceed ceiling)
```

#### 3c: Change Freeze Check

```
Rule: drift_policy.change_freeze_rule
If: component is in a change_freeze window
Then: BLOCK auto-remediation, escalate to immediate human review
```

#### 3d: Compliance Drift Check

```
Rule: drift_policy.compliance_audit_rule
If: drift_type == compliance
Then: BLOCK auto-remediation — compliance drift always requires human review
Action: Generate compliance audit entry, require compliance-officer persona review
```

#### 3e: Severity Ceiling Check

```
Rule: drift_remediation.ceiling_severity
If: drift_severity > ceiling_severity ("medium" by default)
Then: ESCALATE to human — severity exceeds auto-remediation ceiling
```

#### 3f: Circuit Breaker Check

```
Rule: circuit-breaker.yaml
If: circuit breaker for this component is OPEN
Then: ESCALATE to human — system has failed too many consecutive remediation attempts
If: circuit breaker is HALF_OPEN
Then: Allow one probe remediation attempt
```

### Step 4: Select Remediation Action

If all Step 3 checks pass, select the appropriate action:

1. Look up `drift_type` in `drift-remediation.yaml` → `allowed_drift_types`
2. Select the most appropriate action for the specific drift:
   - **Configuration drift:**
     - Environment variable changed → `environment_variable_rollback`
     - Feature flag modified → `feature_flag_restore`
     - Replica count changed → `replica_count_restore`
     - Config file modified → `config_file_restore_from_manifest`
   - **Behavior drift:**
     - Instance unhealthy → `restart_unhealthy_instance`
     - Load spike within bounds → `scale_horizontal_within_bounds`
   - **Performance drift:**
     - Cache degradation → `cache_flush`
     - Connection pool exhaustion → `connection_pool_reset`

3. Verify the selected action is NOT in `drift-remediation.yaml` → `prohibited_actions`:
   - `data_deletion` — NEVER auto-remediate
   - `schema_migration` — NEVER auto-remediate
   - `secret_rotation` — NEVER auto-remediate
   - `network_rule_modification` — NEVER auto-remediate
   - `iam_policy_change` — NEVER auto-remediate

4. If no allowed action matches the drift, escalate to human review

### Step 5: Execute Remediation

1. Create a remediation action record (conforming to `remediation-action.schema.json`):
   - Set `outcome.status` to `verification_pending`
   - Record all policy rules evaluated in `authorization.policy_rules_evaluated`
   - Set `authorization.mode` to `auto`

2. Execute the selected action through the remediation executor:
   - The executor is a privilege-scoped component with write access ONLY to the specific action type
   - Log the action with all parameters

3. If execution fails:
   - Set `outcome.status` to `failed`
   - Record `outcome.error_message`
   - Update circuit breaker failure count
   - Escalate to human if circuit breaker trips
   - **Stop here** — do not proceed to verification

4. If execution succeeds, proceed to Step 6

### Step 6: Verify Remediation

1. Start the verification window (`drift-remediation.yaml` → `verification.verification_window_minutes`, default 15)

2. Create a verification record (conforming to `remediation-verification.schema.json`):
   - Set `verification_window.started_at` to now
   - Set `verification_window.duration_minutes` from config

3. During the verification window, collect metric samples:
   - Compare each relevant metric against the baseline
   - For each metric, record: `baseline_value`, `pre_remediation_value`, `post_remediation_value`, `threshold`, `result`

4. Determine early termination conditions:
   - If drift worsens significantly during verification → terminate early, mark as `fail`
   - If new drift signals arrive for the same component → terminate early, mark as `fail`

5. At window end, compute the verdict:
   - All checks pass → `pass`
   - Any critical check fails → `fail`
   - Non-critical checks inconclusive, critical checks pass → `partial`
   - Insufficient data → `inconclusive`

### Step 7: Post-Verification Decision

Based on the verification verdict:

#### Verdict: PASS

1. Update remediation action record: `outcome.status` = `success`
2. Capture new baseline:
   - Create a new baseline snapshot (conforming to `baseline.schema.json`)
   - Set `validity.valid_until` to 30 days from now
   - Set `superseded_by` on the old baseline
3. Record `new_baseline.baseline_id` in the verification record
4. Reset circuit breaker success counter
5. Log audit entry: "Auto-remediation executed, drift resolved"

#### Verdict: FAIL

1. Check `drift-remediation.yaml` → `verification.revert_on_verification_failure`
2. If revert is required (default: true):
   - Execute the inverse of the remediation action
   - Record revert in verification record's `revert` section
   - If revert succeeds: escalate to human with context "auto-remediation attempted and reverted"
   - If revert fails: escalate to human as P0 with context "auto-remediation failed and revert failed"
3. Update remediation action record: `outcome.status` = `reverted`
4. Update circuit breaker failure count
5. If circuit breaker trips → escalate to human, set circuit breaker to OPEN

#### Verdict: PARTIAL or INCONCLUSIVE

1. Do NOT revert — the remediation may have partially worked
2. Escalate to human with full verification details
3. Update remediation action record: `outcome.status` = `escalated_to_human`
4. Provide the human reviewer with:
   - Original drift signal
   - Remediation action taken
   - Verification results (which checks passed, which were inconclusive)
   - Recommendation: re-evaluate after more data is collected

### Step 8: Audit and Record

Regardless of outcome:

1. Finalize the remediation action record with all timestamps and outcome
2. Finalize the verification record (if verification was reached)
3. Store both records as immutable audit artifacts
4. Log the following audit entries (per architecture doc cross-cutting concerns):
   - `drift_detected`: drift_id, component, drift_type, severity, baseline_id
   - `auto_remediation_executed`: drift_id, remediation_action, result
   - `human_escalation_triggered` (if applicable): drift_id, reason, escalation_target

### Step 9: Return to Caller

Return the remediation outcome to the invoking workflow:

- If invoked from the startup sequence: continue to the next issue or checkpoint
- If invoked from the runtime feedback pipeline: return outcome for pipeline processing
- If the circuit breaker is now OPEN: flag the component for human attention in the next status report

## Escalation Summary

| Condition | Action | Severity |
|-----------|--------|----------|
| Active incident on component | Immediate human escalation | Original + context |
| Regression (fingerprint match within 7 days) | Severity +1, re-evaluate | Escalated severity |
| Change freeze active | Block, immediate human review | Original |
| Compliance drift (any severity) | Block, compliance-officer review | Original |
| Severity above ceiling | Human escalation | Original |
| Circuit breaker OPEN | Human escalation | Original |
| No matching allowed action | Human escalation | Original |
| Prohibited action required | Human escalation | Original |
| Execution failure | Human escalation, circuit breaker update | Original |
| Verification failure (revert succeeds) | Human escalation with context | Original |
| Verification failure (revert fails) | P0 human escalation | Critical |
| Partial/inconclusive verification | Human escalation with data | Original |

## Constraints

- **Never perform a prohibited action** — the prohibited list in `drift-remediation.yaml` is absolute
- **Never auto-remediate compliance drift** — always requires human review
- **Never exceed the severity ceiling** — auto-remediation is bounded
- **Always verify** — the verification step is not optional when `verification.required` is true
- **Always revert on failure** — when `revert_on_verification_failure` is true
- **Always audit** — every action, success or failure, produces an immutable record
- **Maximum 3 consecutive auto-remediation attempts** — circuit breaker enforces this
- **Respect rate limits** — do not exceed per-DI, per-component, or global rate limits from `rate-limits.yaml`
