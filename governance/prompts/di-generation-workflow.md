# DI Generation Workflow

**Purpose:** Agentic workflow for the Tech Lead to transform classified runtime signals into Design Intents (DIs) that the governance pipeline can process.

**Schema:** `governance/schemas/runtime-di.schema.json` (v1.0.0)
**Template:** `governance/templates/prompts/runtime-di-template.md`
**Architecture Reference:** `docs/architecture/runtime-feedback.md` Section 2

---

## Prerequisites

Before executing this workflow, verify:

1. The incoming signal conforms to `governance/schemas/runtime-signal.schema.json`
2. The signal has passed normalization (has `signal_id`, `fingerprint`, all required fields)
3. The signal has passed deduplication (is not suppressed by the deduplication window)
4. Access to the existing DI store for correlation checks
5. Access to `governance/policy/signal-panel-mapping.yaml` for panel routing

---

## Step 1: Signal Ingestion Validation

Validate the incoming signal before processing.

### Checks

1. **Schema conformance** — Signal must validate against `runtime-signal.schema.json`. Reject with error if invalid.
2. **Required fields present** — `signal_id`, `timestamp`, `source`, `severity`, `category`, `affected_component`, `message` must all be non-empty.
3. **Component registered** — `affected_component` must exist in `governance/policy/component-registry.yaml`. If unregistered, log a warning and proceed with default criticality (Standard = 0.5).
4. **Fingerprint computed** — If `fingerprint` is missing, compute it:
   ```
   fingerprint = SHA-256(category + affected_component + severity + normalize_whitespace(message)[0:256])
   ```
5. **Timestamp sanity** — `timestamp` must not be more than 24 hours in the future or more than 30 days in the past. Reject signals outside this window.

### On Validation Failure

- Log the failure with signal details and rejection reason.
- Do not generate a DI.
- If the failure is due to missing `fingerprint`, compute it and continue.
- If the failure is due to unregistered component, continue with default criticality.
- All other validation failures are terminal — stop processing this signal.

---

## Step 2: Deduplication Check

Determine whether this signal is a duplicate of a recently processed signal.

### Process

1. Look up the signal's `fingerprint` in the deduplication window (default: 15 minutes, configurable in `governance/policy/deduplication.yaml`).
2. **If fingerprint match found within window:**
   - Increment the suppression counter for the existing entry.
   - Update `last_seen` timestamp.
   - Check if suppression counter exceeds `escalation_threshold` (default: 10).
     - **If exceeded:** Forward the signal with severity escalated by one level. Continue to Step 3.
     - **If not exceeded:** Suppress the signal. Log suppression. Stop processing.
3. **If no fingerprint match:** Create a new deduplication entry. Continue to Step 3.
4. **If a duplicate arrives with higher severity than the original:** Reset the deduplication window and forward the signal. Continue to Step 3.

### Configuration Reference

```yaml
# governance/policy/deduplication.yaml
deduplication:
  window_duration_minutes: 15
  escalation_threshold: 10
  max_window_duration_minutes: 60
  window_reset_on_severity_change: true
```

---

## Step 3: Correlation with Existing DIs

Before generating a new DI, check whether an existing open DI already addresses the same issue.

### Correlation Rules (evaluated in order; first match wins)

| # | Criterion | Match Logic | Action |
|---|-----------|-------------|--------|
| 1 | Signal fingerprint match | New signal fingerprint matches a signal already attached to an open DI | Append signal to existing DI. Update `occurrence_count` and `last_detected`. |
| 2 | Component + category match | Same `affected_component` and `category` as an open DI created within the last 24 hours | Append signal to existing DI. Recalculate priority. |
| 3 | Correlation ID overlap | New signal shares a `correlation_id` with a signal attached to an open DI | Append signal to existing DI. Expand blast radius if needed. |
| 4 | Root cause similarity | Cosine similarity of root cause hypothesis text exceeds 0.85 against an open DI | Flag for human review. Do **not** auto-merge. Present both DIs to reviewer. |
| 5 | No match | None of the above criteria are satisfied | Generate new DI. Continue to Step 4. |

### State Transitions for Correlated DIs

**Open DI + same fingerprint signal:**
- Update `occurrence_count` and `last_detected`
- If severity increased → recalculate priority
- If priority increased AND priority >= P1 → trigger re-evaluation

**Open DI + different fingerprint, same component+category:**
- Append to `signal_ids`
- Expand `evidence`
- Recalculate priority with updated blast radius
- If new panel needed → add to `proposed_panels_secondary`

**Closed DI + same fingerprint signal (recurrence):**
- Generate NEW DI
- Set `recurrence_of` to the closed DI's `di_id`
- Escalate severity by one level (regression penalty)

### On Correlation Match (Rules 1-3)

Update the existing DI and stop. Do not generate a new DI.

### On Similarity Flag (Rule 4)

Set `requires_human_review: true` on the new DI. Continue to Step 4.

---

## Step 4: Priority Calculation

Compute the priority score deterministically from signal attributes.

### Formula

```
priority = (severity_weight * 0.35)
         + (blast_radius_weight * 0.25)
         + (sla_impact_weight * 0.20)
         + (recurrence_penalty * 0.10)
         + (time_decay_bonus * 0.10)
```

### Factor Definitions

| Factor | Calculation | Range |
|--------|-------------|-------|
| `severity_weight` | critical=100, high=75, medium=50, low=25, informational=10 | 10–100 |
| `blast_radius_weight` | `min(100, count(affected_components) * 20)` | 0–100 |
| `sla_impact_weight` | tier_1=100, tier_2=70, tier_3=40, no_sla=10 | 10–100 |
| `recurrence_penalty` | 0 if first occurrence; +20 per recurrence in last 30 days, max 100 | 0–100 |
| `time_decay_bonus` | Signals older than 1 hour lose 5 points per hour, floor 0 | 0–100 |

### Priority-to-Label Mapping

| Score Range | Label | Response Expectation |
|-------------|-------|---------------------|
| 80–100 | P0 | Immediate. Panel execution within 5 minutes. Human notification required. |
| 60–79 | P1 | Urgent. Panel execution within 30 minutes. |
| 40–59 | P2 | Standard. Panel execution within 4 hours. |
| 20–39 | P3 | Low. Panel execution within 24 hours. |
| 0–19 | P4 | Advisory. Queued for next scheduled review cycle. |

### Remediation Class Determination

Based on severity, category, and policy constraints:

- **`auto_remediate`** — Severity <= medium AND category in auto-remediable set (per `governance/policy/drift-remediation.yaml`) AND no active incident on component AND circuit breaker is CLOSED.
- **`panel_review`** — Severity > medium OR category not in auto-remediable set OR circuit breaker is HALF_OPEN.
- **`human_escalation`** — Category is `compliance_violation` OR severity is `critical` OR circuit breaker is OPEN OR component is in change freeze window.

### Human Review Requirements

Set `requires_human_review: true` when ANY of these conditions hold:
- Category is `compliance_violation`
- Severity is `critical`
- Correlation engine flagged root cause similarity (Rule 4)
- Component has `force_human_review: true` in signal-panel-mapping.yaml
- Recurrence of a DI closed within the last 7 days

---

## Step 5: Template Hydration

Generate the DI markdown document by hydrating the template.

### Process

1. Load `governance/templates/prompts/runtime-di-template.md`
2. Generate a new `di_id` (UUID v4)
3. Populate all template variables from the signal data, priority calculation, and correlation results
4. Generate the root cause hypothesis:
   - Combine signal category and metrics into a baseline hypothesis
   - If historical DIs exist for the same component+category, reference prior root causes
   - If upstream dependency signals are active, note potential upstream origin
   - Label the hypothesis as "machine-generated and provisional"
5. Compile evidence from:
   - The runtime signal(s) data
   - Metrics (current vs. threshold vs. baseline values)
   - Dependency graph traversal results
   - Historical pattern matches
6. Populate the structured emission block between `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers
7. Validate the structured emission JSON against `governance/schemas/runtime-di.schema.json`

### Validation

- All required fields in the schema must be present in the structured emission
- `signal_ids` must contain at least one valid UUID
- `priority` must be within 0-100 range
- `remediation_class` must be one of: `auto_remediate`, `panel_review`, `human_escalation`
- Structured emission block must be valid JSON

---

## Step 6: Panel Routing

Route the generated DI to the appropriate governance panels.

### Process

1. Look up the signal `category` in `governance/policy/signal-panel-mapping.yaml`
2. Set `proposed_panel` to the `primary` panel for that category
3. Set `proposed_panels_secondary` to the `secondary` panels
4. Verify all proposed panels exist as files in `governance/prompts/reviews/`
5. If a panel file does not exist, log a warning and fall back to `governance/prompts/reviews/code-review.md`

### Panel Execution Triggers

After DI generation, the DI enters the governance pipeline:

| Condition | Action |
|-----------|--------|
| Priority P0 | Trigger immediate panel execution. Notify on-call. |
| Priority P1 | Trigger panel execution within 30 minutes. |
| Priority P2-P4 | Queue for scheduled execution per priority SLA. |
| `requires_human_review: true` | Route to human review queue. Do not auto-execute remediation panels. |
| `remediation_class: auto_remediate` | After panel approval, proceed to `governance/prompts/remediation-workflow.md` |

### Output

The generated DI (markdown + structured emission) is:
1. Stored in the DI store for correlation by future signals
2. Submitted to the governance pipeline for panel execution
3. Recorded in the manifest system with provenance tracing back to the originating signal(s)

---

## Error Handling

| Error | Action |
|-------|--------|
| Signal fails schema validation | Reject signal. Log error with signal_id and validation details. |
| Component not in registry | Proceed with default criticality (0.5). Log warning. |
| Panel mapping not found for category | Fall back to `governance/prompts/reviews/code-review.md`. Log warning. |
| Template hydration produces invalid JSON | Abort DI generation. Log error. Signal remains in dead-letter queue. |
| DI store unavailable for correlation | Skip correlation (Step 3). Generate new DI. Log warning. |
| Priority calculation produces out-of-range value | Clamp to 0-100 range. Log warning. |

---

## Cross-References

| Artifact | Purpose |
|----------|---------|
| `governance/schemas/runtime-signal.schema.json` | Input signal schema |
| `governance/schemas/runtime-di.schema.json` | Output DI structured emission schema |
| `governance/schemas/baseline.schema.json` | Baseline data for drift comparison |
| `governance/schemas/panel-output.schema.json` | Panel execution output schema |
| `governance/schemas/remediation-action.schema.json` | Downstream remediation action records |
| `governance/schemas/remediation-verification.schema.json` | Post-remediation verification |
| `governance/policy/signal-panel-mapping.yaml` | Signal category to panel routing |
| `governance/policy/deduplication.yaml` | Deduplication window configuration |
| `governance/policy/severity-reclassification.yaml` | Severity reclassification rules |
| `governance/policy/drift-remediation.yaml` | Auto-remediation policy constraints |
| `governance/policy/circuit-breaker.yaml` | Circuit breaker state machine |
| `governance/policy/rate-limits.yaml` | Rate limiting configuration |
| `governance/prompts/remediation-workflow.md` | Downstream remediation execution workflow |
| `docs/architecture/runtime-feedback.md` | Architecture specification (Section 2) |
