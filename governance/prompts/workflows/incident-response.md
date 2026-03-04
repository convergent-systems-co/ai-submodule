# Workflow: Incident Response

Managing an active incident through mitigation, communication, root cause analysis, and post-mortem.

## Prerequisites

- An active or recently resolved incident (alert, user report, monitoring signal)
- Access to logs, monitoring dashboards, and the affected system
- Communication channel for stakeholders

## Phases

1. **Triage** → `[INC-1]` — **GATE**
2. **Mitigate** → `[INC-2]` — **GATE**
3. **Communicate** → `[INC-3]`
4. **Root Cause** → `[INC-4]` — **GATE**
5. **Post-Mortem** → `[INC-5]` — **GATE**
6. **Action Items** → `[INC-6]`

---

## Phase 1: Triage

> **Adopt persona:** `governance/personas/specialist/incident-commander.md`

### Input

- Alert or incident report
- Initial symptoms and affected systems
- Time of first detection

### Process

1. Assess severity (critical / major / minor)
2. Identify affected users, services, and data
3. Determine if the incident is ongoing or resolved
4. Assign initial roles (who is investigating, who is communicating)
5. Establish a timeline of known events

### Output

**Artifact `[INC-1]: Triage Assessment`**

```
## Severity
<Critical / Major / Minor>

## Impact
- **Users affected:** <scope>
- **Services affected:** <list>
- **Data impact:** <None / Read degraded / Write degraded / Data loss>

## Status
<Ongoing / Mitigated / Resolved>

## Timeline
- <timestamp> — <event>
- ...

## Initial Hypothesis
<Best current understanding of what's happening>

## Immediate Actions Needed
- <Action>
- ...
```

### GATE

**Stop.** Present `[INC-1]` for review.

**Approval criteria:** Severity is assessed. Impact scope is understood. Immediate actions are identified.

- **Approved** → proceed to Phase 2
- **Revise** → gather more information, re-present `[INC-1]`

---

## Phase 2: Mitigate

> **Adopt persona:** `governance/personas/specialist/incident-commander.md`
> **Secondary persona:** `governance/personas/operations/sre.md`

### Input

- `[INC-1]: Triage Assessment`

### Process

1. Identify the fastest path to reduce user impact (rollback, feature flag, scaling, failover)
2. Execute mitigation steps
3. Verify mitigation is effective (metrics returning to normal)
4. Document what was done and the result

### Output

**Artifact `[INC-2]: Mitigation Report`**

```
## Mitigation Strategy
<What was done to reduce impact>

## Steps Taken
1. <Step> — <result>
2. <Step> — <result>
...

## Current Status
<Mitigated / Partially mitigated / Mitigation failed>

## Metrics
- <metric> — <before> → <after>
- ...

## Residual Risk
<Any remaining exposure>
```

### GATE

**Stop.** Present `[INC-2]` for review.

**Approval criteria:** User impact is reduced or eliminated. Mitigation is verified with metrics. Residual risk is known.

- **Approved** → proceed to Phase 3
- **Mitigation insufficient** → try alternative mitigation, re-present `[INC-2]`

---

## Phase 3: Communicate

> **Adopt persona:** `governance/personas/specialist/incident-commander.md`

### Input

- `[INC-1]: Triage Assessment`
- `[INC-2]: Mitigation Report`

### Process

1. Draft stakeholder communication appropriate to severity
2. Include: what happened, current status, what's being done, next update time
3. Identify who needs to be notified (users, leadership, dependent teams)

### Output

**Artifact `[INC-3]: Stakeholder Communication`**

```
## Audience
<Who is being notified>

## Message

### What Happened
<Brief, non-technical summary>

### Current Status
<Mitigated / Investigating / Resolved>

### What We're Doing
<Next steps>

### Next Update
<When stakeholders will hear from us again>
```

---

## Phase 4: Root Cause

> **Adopt persona:** `governance/personas/engineering/debugger.md`
> **Invoke prompt:** `governance/prompts/debug.md`

### Input

- `[INC-1]: Triage Assessment`
- `[INC-2]: Mitigation Report`
- Logs, traces, metrics from the incident window

### Process

1. Build a detailed timeline from logs and monitoring
2. Identify the triggering event
3. Trace the chain of causation from trigger to impact
4. Distinguish root cause from contributing factors
5. Identify systemic factors (missing monitoring, inadequate testing, etc.)

### Output

**Artifact `[INC-4]: Root Cause Analysis`**

```
## Detailed Timeline
- <timestamp> — <event> — <source>
- ...

## Triggering Event
<What set off the incident>

## Causal Chain
1. <Cause> → <Effect>
2. <Effect> → <Further effect>
...

## Root Cause
<The fundamental issue>

## Contributing Factors
- <Factor>
- ...

## Systemic Factors
- <What allowed this to happen or go undetected>
- ...
```

### GATE

**Stop.** Present `[INC-4]` for review.

**Approval criteria:** Root cause is definitive, not speculative. Causal chain is traceable. Contributing and systemic factors are identified.

- **Approved** → proceed to Phase 5
- **Revise** → deepen investigation, re-present `[INC-4]`

---

## Phase 5: Post-Mortem

> **Invoke panel:** `governance/prompts/reviews/incident-post-mortem.md`

### Input

- `[INC-1]: Triage Assessment`
- `[INC-2]: Mitigation Report`
- `[INC-4]: Root Cause Analysis`

### Process

1. Review the incident end-to-end with the panel
2. Evaluate what went well (detection, response, communication)
3. Evaluate what went poorly
4. Identify lessons learned
5. Generate prioritized action items to prevent recurrence

### Output

**Artifact `[INC-5]: Post-Mortem Report`**

```
## Incident Summary
<One-paragraph summary>

## What Went Well
- <Item>
- ...

## What Went Poorly
- <Item>
- ...

## Lessons Learned
- <Lesson>
- ...

## Recommended Action Items
1. [P0] <Action> — <owner suggestion>
2. [P1] <Action> — <owner suggestion>
3. [P2] <Action> — <owner suggestion>
...
```

### GATE

**Stop.** Present `[INC-5]` for review.

**Approval criteria:** Post-mortem is blameless. Action items are concrete, prioritized, and address systemic factors. Lessons learned are actionable.

- **Approved** → proceed to Phase 6
- **Revise** → address feedback, re-present `[INC-5]`

---

## Phase 6: Action Items

> **Adopt persona:** `governance/personas/leadership/tech-lead.md`

### Input

- `[INC-5]: Post-Mortem Report`

### Process

1. Refine action items into trackable tasks
2. Assign owners and priorities
3. Identify quick wins vs. longer-term improvements
4. Document the post-mortem and action items in the project record

### Output

**Artifact `[INC-6]: Action Item Tracker`**

```
## Quick Wins (do this week)
- [ ] <Action> — @<owner>
- ...

## Short-Term (do this sprint/cycle)
- [ ] <Action> — @<owner>
- ...

## Long-Term (schedule for planning)
- [ ] <Action> — @<owner>
- ...

## Post-Mortem Document
<path or link to published post-mortem>
```
