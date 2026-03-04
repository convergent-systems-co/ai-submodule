# Plan: Segregate Phase 5 artifacts from production policy and schemas (#565)

## Objective

Move unimplemented Phase 5 policy files and schemas to `future/` subdirectories to reduce auditor surface area and cognitive load.

## Scope

### Policy files to move to `governance/policy/future/`

14 aspirational files:
- autonomy-thresholds.yaml, collision-domains.yaml, component-registry.yaml, cost-optimization.yaml
- deduplication.yaml, drift-policy.yaml, drift-remediation.yaml, integration-strategy.yaml
- merge-sequencing.yaml, parallel-session-protocol.yaml, rate-limits.yaml
- severity-reclassification.yaml, signal-panel-mapping.yaml, threshold-tuning.yaml

### Schema files to move to `governance/schemas/future/`

8 aspirational files:
- autonomy-metrics.schema.json, formal-spec.schema.json, persona-effectiveness.schema.json
- remediation-action.schema.json, remediation-verification.schema.json
- retrospective-aggregation.schema.json, runtime-di.schema.json, runtime-signal.schema.json

### Keep in place

Active policy: default.yaml, fast-track.yaml, fin_pii_high.yaml, infrastructure_critical.yaml, reduced_touchpoint.yaml, agent-containment.yaml, circuit-breaker.yaml, panel-timeout.yaml, canary-calibration.yaml
Active schemas: panel-output, run-manifest, checkpoint, agent-message, agent-log-entry, baseline, breaking-change, conflict-detection, cross-repo-escalation, execution-backend, governance-compliance, integration-manifest, orchestrator-config, panels.defaults, panels.schema, project.schema, prompt-catalog, session-state, test-governance, ado-*
