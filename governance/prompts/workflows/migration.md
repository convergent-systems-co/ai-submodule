# Workflow: Migration

System, dependency, or data migrations with safety gates at every critical juncture.

## Prerequisites

- Migration need (system upgrade, dependency change, data migration, platform move)
- Access to source and target environments
- Understanding of what depends on the thing being migrated

## Phases

1. **Assessment** → `[MIG-1]` — **GATE**
2. **Strategy** → `[MIG-2]` — **GATE**
3. **Execution Plan** → `[MIG-3]` — **GATE**
4. **Execute** → `[MIG-4.N]` — **per-step GATE**
5. **Validation** → `[MIG-5]` — **GATE**
6. **Rollback Readiness** → `[MIG-6]` — **GATE**

---

## Phase 1: Assessment

> **Adopt persona:** `governance/personas/specialist/migration-specialist.md`
> **Invoke prompt:** `governance/prompts/migrate.md`

### Input

- Migration need (what is being migrated and why)
- Current system state
- Target state

### Process

1. Inventory everything affected by the migration
2. Identify breaking changes between current and target
3. Map all consumers/dependents that will be impacted
4. Assess data compatibility (schema changes, format changes)
5. Identify the risk level (low / medium / high / critical)

### Output

**Artifact `[MIG-1]: Migration Assessment`**

```
## Migration
<From what → to what>

## Motivation
<Why this migration is needed>

## Affected Components
- <Component> — <how it's affected>
- ...

## Breaking Changes
- <Breaking change> — <impact>
- ...

## Data Compatibility
<Compatible / Requires transformation — details>

## Risk Level
<Low / Medium / High / Critical>

## Risk Factors
- <Factor>
- ...
```

### GATE

**Stop.** Present `[MIG-1]` for review.

**Approval criteria:** All affected components are identified. Breaking changes are documented. Risk level is assessed.

- **Approved** → proceed to Phase 2
- **Revise** → deepen assessment, re-present `[MIG-1]`

---

## Phase 2: Strategy

> **Adopt persona:** `governance/personas/specialist/migration-specialist.md`
> **Invoke prompt:** `governance/prompts/plan.md`

### Input

- `[MIG-1]: Migration Assessment`

### Process

1. Choose a migration strategy (big bang, incremental, parallel run, blue-green, strangler fig)
2. Define the migration sequence
3. Identify feature flags or compatibility layers needed
4. Define the rollback strategy for each phase
5. Establish success criteria and health checks

### Output

**Artifact `[MIG-2]: Migration Strategy`**

```
## Strategy
<Big bang / Incremental / Parallel run / Blue-green / Strangler fig>

## Rationale
<Why this strategy was chosen>

## Sequence
1. <Phase/step>
2. <Phase/step>
...

## Compatibility Layers
- <Layer needed> — <purpose>
- ... (or "None needed")

## Rollback Strategy
- **Per-step:** <how to roll back individual steps>
- **Full rollback:** <how to abort and return to original state>

## Success Criteria
- <Criterion>
- ...

## Health Checks
- <Check> — <what it validates>
- ...
```

### GATE

**Stop.** Present `[MIG-2]` for review.

**Approval criteria:** Strategy matches the risk level. Rollback is defined. Success criteria are measurable.

- **Approved** → proceed to Phase 3
- **Revise** → adjust strategy, re-present `[MIG-2]`

---

## Phase 3: Execution Plan

> **Adopt persona:** `governance/personas/specialist/migration-specialist.md`
> **Secondary persona:** `governance/personas/operations/sre.md`

### Input

- `[MIG-1]: Migration Assessment`
- `[MIG-2]: Migration Strategy`

### Process

1. Break the strategy into concrete, executable steps
2. Define pre-conditions and verification for each step
3. Identify the point of no return (if any)
4. Plan for monitoring during migration
5. Define communication plan (who to notify, when)

### Output

**Artifact `[MIG-3]: Execution Plan`**

```
## Pre-Migration Checklist
- [ ] <Pre-condition>
- [ ] <Pre-condition>
- ...

## Steps

### Step 1: <Name>
- **Action:** <what to do>
- **Pre-condition:** <what must be true before starting>
- **Verification:** <how to confirm success>
- **Rollback:** <how to undo>
- **Duration estimate:** <expected time>

### Step 2: <Name>
...

## Point of No Return
<After step N / None — fully reversible>

## Monitoring Plan
- <What to watch during migration>
- ...

## Communication Plan
- **Before:** notify <who>
- **During:** update <who> at <frequency>
- **After:** confirm to <who>
```

### GATE

**Stop.** Present `[MIG-3]` for review.

**Approval criteria:** Steps are concrete and ordered. Each step has verification and rollback. Point of no return is identified. Monitoring plan exists.

- **Approved** → proceed to Phase 4
- **Revise** → adjust plan, re-present `[MIG-3]`

---

## Phase 4: Execute

> **Invoke prompt:** `governance/prompts/migrate.md`

### Input

- `[MIG-3]: Execution Plan`

### Process

For each step in the execution plan:

1. Verify pre-conditions are met
2. Execute the step
3. Run the verification defined for that step
4. Monitor health checks from `[MIG-2]`
5. Document the result

### Output (per step)

**Artifact `[MIG-4.N]: Step N Result`**

```
## Step N: <Name>

### Pre-conditions
<Met / Not met — details>

### Execution
<What was done>

### Verification Result
<Pass / Fail — details>

### Health Check Status
- <Check> — <status>
- ...

### Status
<Complete / Rolled back — reason>
```

### GATE (per step)

**Stop** after each step. Present `[MIG-4.N]` for review.

**Approval criteria:** Verification passes. Health checks are green.

- **Approved** → proceed to next step (or Phase 5 if all steps complete)
- **Rollback** → undo step, assess whether to continue or abort

---

## Phase 5: Validation

> **Invoke panel:** `governance/prompts/reviews/migration-review.md`

### Input

- `[MIG-1]: Migration Assessment`
- `[MIG-2]: Migration Strategy`
- All `[MIG-4.N]` artifacts
- Current system state

### Process

1. Verify all success criteria from `[MIG-2]` are met
2. Run comprehensive health checks
3. Verify all consumers/dependents are functioning correctly
4. Check data integrity (if data migration)
5. Compare pre-migration and post-migration behavior

### Output

**Artifact `[MIG-5]: Validation Report`**

```
## Success Criteria
- <Criterion> — <Met / Not met>
- ...

## Health Checks
- <Check> — <Pass / Fail>
- ...

## Consumer Status
- <Consumer> — <Functioning / Issues>
- ...

## Data Integrity
<Verified / Issues — details>

## Verdict
<Migration successful / Issues found>
```

### GATE

**Stop.** Present `[MIG-5]` for review.

**Approval criteria:** All success criteria met. Health checks pass. Consumers function correctly.

- **Approved** → proceed to Phase 6
- **Issues found** → address issues, re-validate, re-present `[MIG-5]`

---

## Phase 6: Rollback Readiness

> **Adopt persona:** `governance/personas/operations/failure-engineer.md`

### Input

- `[MIG-2]: Migration Strategy` (rollback strategy)
- `[MIG-5]: Validation Report`

### Process

1. Verify rollback mechanism is still functional (even though migration succeeded)
2. Define the window during which rollback remains possible
3. Identify conditions that would trigger a rollback
4. Document the rollback procedure for on-call/ops teams
5. Schedule cleanup of compatibility layers and old system (if applicable)

### Output

**Artifact `[MIG-6]: Rollback & Cleanup Plan`**

```
## Rollback Status
<Available / No longer possible — reason>

## Rollback Window
<Until when rollback is feasible>

## Rollback Triggers
- <Condition that would warrant rollback>
- ...

## Rollback Procedure
1. <Step>
2. <Step>
...

## Cleanup Tasks
- [ ] <Remove compatibility layer X> — <safe after date/condition>
- [ ] <Decommission old system> — <safe after date/condition>
- ...
```

### GATE

**Stop.** Present `[MIG-6]` for review.

**Approval criteria:** Rollback procedure is documented and tested (or confirmed feasible). Cleanup tasks are scheduled. Rollback triggers are defined.

- **Approved** → migration is complete
- **Revise** → address concerns, re-present `[MIG-6]`
