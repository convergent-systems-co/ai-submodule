# Design Intent: ${di_title}

## Metadata
- **DI ID:** ${di_id}
- **Generated:** ${generated_at}
- **Origin:** runtime-signal
- **Signal ID(s):** ${signal_ids}
- **Priority:** ${priority_label} (score: ${priority})
- **Status:** pending_review
- **Generator Version:** ${generator_version}

## Affected Component
- **Primary:** ${affected_component}
- **Secondary:** ${affected_components_secondary}
- **Component Owner:** ${component_owner}

## Signal Summary
- **Category:** ${category}
- **Severity:** ${severity}
- **First Detected:** ${first_detected}
- **Last Detected:** ${last_detected}
- **Occurrence Count:** ${occurrence_count}
- **Duration:** ${duration_seconds}s

## Impact Assessment
- **Blast Radius:** ${blast_radius}
- **User Impact:** ${user_impact}
- **SLA Impact:** ${sla_impact}
- **Revenue Impact:** ${revenue_impact_estimate}

## Root Cause Hypothesis

> **Note:** This hypothesis is machine-generated and provisional. It exists to give the reviewing panel a starting point, not a conclusion.

${root_cause_hypothesis}

## Evidence

${evidence_summary}

## Proposed Panel
- **Primary:** ${proposed_panel}
- **Secondary:** ${proposed_panels_secondary}
- **Personas Required:** ${personas_required}

## Proposed Remediation Class
- **Class:** ${remediation_class}
  - `auto_remediate` — System can fix without human intervention.
  - `panel_review` — Panel must evaluate before action.
  - `human_escalation` — Requires human decision-maker.

## Priority Calculation Breakdown

| Factor | Value | Weight |
|--------|-------|--------|
| Severity | ${severity_weight} | 0.35 |
| Blast Radius | ${blast_radius_weight} | 0.25 |
| SLA Impact | ${sla_impact_weight} | 0.20 |
| Recurrence Penalty | ${recurrence_penalty} | 0.10 |
| Time Decay Bonus | ${time_decay_bonus} | 0.10 |
| **Total** | **${priority}** | |

## Correlation
- **Method:** ${correlation_method}
- **Correlated DI:** ${correlated_di_id}
- **Recurrence Of:** ${recurrence_of}
- **Group ID:** ${correlation_group_id}

## Constraints

${constraints}

<!-- STRUCTURED_EMISSION_START -->
```json
{
  "di_id": "${di_id}",
  "di_version": "1.0.0",
  "origin": "runtime-signal",
  "signal_ids": ${signal_ids_json},
  "affected_component": "${affected_component}",
  "severity": "${severity}",
  "category": "${category}",
  "priority": ${priority},
  "priority_label": "${priority_label}",
  "proposed_panel": "${proposed_panel}",
  "remediation_class": "${remediation_class}",
  "correlation_group_id": ${correlation_group_id_json},
  "recurrence_of": ${recurrence_of_json},
  "requires_human_review": ${requires_human_review},
  "generated_at": "${generated_at}",
  "generator_version": "${generator_version}"
}
```
<!-- STRUCTURED_EMISSION_END -->
