# Workflow: Architecture Decision

Making and documenting an architectural choice using an Architecture Decision Record (ADR) format.

## Prerequisites

- A technical decision that needs to be made (technology choice, pattern selection, system design)
- Context on the system or project affected
- Stakeholder concerns or constraints (if known)

## Phases

1. **Context** → `[ADR-1]`
2. **Options** → `[ADR-2]`
3. **Trade-offs** → `[ADR-3]` — **GATE**
4. **Decision** → `[ADR-4]` — **GATE**
5. **Documentation** → `[ADR-5]`

---

## Phase 1: Context

> **Adopt persona:** `governance/personas/architecture/architect.md`
> **Invoke prompt:** `governance/prompts/explain.md`

### Input

- The decision to be made (question or problem statement)
- Current system context and constraints
- Any prior art or existing patterns in the codebase

### Process

1. Articulate the exact decision that needs to be made
2. Document the current state of the system relevant to this decision
3. Identify the forces at play (requirements, constraints, quality attributes)
4. List stakeholders and their primary concerns
5. Note any deadlines or irreversibility factors

### Output

**Artifact `[ADR-1]: Decision Context`**

```
## Decision Required
<What specifically needs to be decided>

## Current State
<Relevant aspects of the current system>

## Forces
- <Force 1> — <description>
- <Force 2> — <description>
- ...

## Stakeholders & Concerns
- <Stakeholder> — <primary concern>
- ...

## Constraints
- <Constraint>
- ...

## Reversibility
<How reversible is this decision? What's the cost of changing later?>
```

---

## Phase 2: Options

> **Adopt persona:** `governance/personas/architecture/systems-architect.md`

### Input

- `[ADR-1]: Decision Context`

### Process

1. Enumerate all viable options (minimum 2, typically 3-4)
2. For each option, describe what it entails concretely
3. Include the "do nothing" option if applicable
4. Identify proof-of-concept or spike needs for any option

### Output

**Artifact `[ADR-2]: Options Catalog`**

```
## Option A: <Name>
**Description:** <What this option entails>
**Proof needed:** <Any spike/PoC required, or "None">

## Option B: <Name>
**Description:** <What this option entails>
**Proof needed:** <Any spike/PoC required, or "None">

## Option C: <Name>
...
```

---

## Phase 3: Trade-offs

> **Invoke panel:** `governance/prompts/reviews/architecture-review.md`

### Input

- `[ADR-1]: Decision Context`
- `[ADR-2]: Options Catalog`

### Process

1. Evaluate each option against the forces from `[ADR-1]`
2. Identify pros and cons for each option
3. Assess each option on key quality attributes (performance, maintainability, scalability, complexity, cost)
4. Identify risks unique to each option
5. Produce a comparison matrix

### Output

**Artifact `[ADR-3]: Trade-off Analysis`**

```
## Comparison Matrix

| Criterion        | Option A | Option B | Option C |
|------------------|----------|----------|----------|
| <Criterion 1>   | <rating> | <rating> | <rating> |
| <Criterion 2>   | <rating> | <rating> | <rating> |
| ...              | ...      | ...      | ...      |

## Option A: Pros & Cons
**Pros:** <list>
**Cons:** <list>
**Risks:** <list>

## Option B: Pros & Cons
**Pros:** <list>
**Cons:** <list>
**Risks:** <list>

## Option C: Pros & Cons
...

## Panel Perspectives
- <Persona>: <key insight or concern>
- ...
```

### GATE

**Stop.** Present `[ADR-3]` for review.

**Approval criteria:** All options have been fairly evaluated. Trade-offs are concrete, not vague. No viable option has been overlooked.

- **Approved** → proceed to Phase 4
- **Revise** → add missing options or deepen analysis, re-present `[ADR-3]`

---

## Phase 4: Decision

> **Adopt persona:** `governance/personas/leadership/tech-lead.md`

### Input

- `[ADR-1]: Decision Context`
- `[ADR-2]: Options Catalog`
- `[ADR-3]: Trade-off Analysis`

### Process

1. Weigh the trade-offs against the forces and constraints
2. Select the option that best satisfies the key forces
3. Articulate the rationale clearly
4. Acknowledge what is being traded away
5. Define success criteria — how will you know this was the right choice?

### Output

**Artifact `[ADR-4]: Decision`**

```
## Chosen Option
<Option name>

## Rationale
<Why this option was selected over the others>

## What We're Trading Away
<Honest acknowledgment of downsides accepted>

## Success Criteria
- <How to measure if this decision was correct>
- ...

## Review Trigger
<Conditions under which this decision should be revisited>
```

### GATE

**Stop.** Present `[ADR-4]` for review.

**Approval criteria:** Rationale is sound and traces back to the forces in `[ADR-1]`. Trade-offs are acknowledged honestly.

- **Approved** → proceed to Phase 5
- **Revise** → revisit rationale or reconsider decision, re-present `[ADR-4]`

---

## Phase 5: Documentation

> **Adopt persona:** `governance/personas/documentation/documentation-writer.md`
> **Invoke prompt:** `governance/prompts/commit.md`

### Input

- `[ADR-1]: Decision Context`
- `[ADR-2]: Options Catalog`
- `[ADR-3]: Trade-off Analysis`
- `[ADR-4]: Decision`

### Process

1. Compile all artifacts into a single ADR document
2. Use the standard ADR format: Title, Status, Context, Decision, Consequences
3. Place the ADR in the project's decision record location
4. Commit the ADR

### Output

**Artifact `[ADR-5]: Published ADR`**

```
## ADR File
<path/to/adr-NNN-title.md>

## Status
Accepted

## Content Summary
<One-line summary of the decision>

## Commit
<hash> — <commit message>
```
