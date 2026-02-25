# Dark Factory Governance: Autonomy Metrics and Index

**Version:** 1.0.0
**Status:** Active
**Last Updated:** 2026-02-20
**Classification:** Internal -- Governance Engineering

---

## Purpose

This document defines the metrics framework and composite Autonomy Index used to measure, track, and govern the progression of the Dark Factory system toward full autonomous operation. Each metric is designed to be computed deterministically from structured data already produced by the system -- panel emissions, policy engine decisions, version manifests, and CI logs.

These metrics serve three functions:

1. **Operational visibility** into the health and consistency of autonomous governance.
2. **Defensibility evidence** for auditors and compliance reviewers who require quantitative proof that autonomous decisions meet or exceed human-equivalent quality.
3. **Phase gating criteria** that determine when the system is ready to advance from supervised autonomy to full dark-factory operation.

All metrics are defined with explicit measurement methods, data sources, and action thresholds so that no ambiguity exists in their computation or interpretation.

---

## Metric Definitions

### 1. Human Touchpoints per Feature (HT/F)

| Attribute | Detail |
|---|---|
| **Definition** | The number of discrete human interventions required for a single feature to progress from Design Intent (DI) through final merge. |
| **Unit** | Count (integer) per feature |
| **Measurement Method** | For each feature branch, count the number of gates where the policy engine returned `human_review_required` and a human actor subsequently provided input. Gates include: architecture review, security panel, code review panel, compliance panel, and merge decision. A gate counts as a touchpoint only if a human action was recorded (approval, rejection, comment that altered the pipeline). |
| **Data Sources** | Policy engine decision log, GitHub review events, panel emission records with `decision: "human_review_required"` |
| **Target** | Monotonically decreasing trend over rolling 30-day windows. No absolute target -- the goal is directional improvement. |
| **Baseline** | Established during Phase 3 initial deployment by measuring the first 50 features processed. |

**Breakdown Dimensions:**

| Dimension | Purpose |
|---|---|
| Feature Type | Distinguish net-new features, bug fixes, refactors, dependency updates, and configuration changes. Each type has different expected touchpoint profiles. |
| Risk Level | As assigned by the policy engine (`low`, `medium`, `high`, `critical`). Higher risk features are expected to require more touchpoints; the metric tracks whether that expectation holds. |
| Team | Per-team tracking identifies whether specific teams produce work that consistently requires more human intervention, indicating a training or tooling gap. |

**Interpretation Guidelines:**

- A sustained increase in HT/F for low-risk features indicates policy regression or confidence miscalibration.
- HT/F for `critical` risk features is expected to remain elevated and is not a primary optimization target.
- Week-over-week delta greater than +0.5 for any single feature type triggers investigation.

---

### 2. Auto-merge Rate (AMR)

| Attribute | Detail |
|---|---|
| **Definition** | The percentage of pull requests that reach a final merge decision of `auto_merge` without any human intervention in the decision chain. |
| **Unit** | Percentage (0.00% -- 100.00%) |
| **Formula** | `AMR = (count of PRs with decision = "auto_merge") / (total PRs with any terminal decision) * 100` |
| **Measurement Method** | Query the policy engine decision log for all terminal merge decisions (`auto_merge`, `auto_remediate`, `human_review_required`, `block`) within the reporting window. PRs still in flight are excluded. |
| **Data Sources** | Policy engine decision log, merge event records in version manifests |

**Segmentation:**

| Segment | Expected Range | Notes |
|---|---|---|
| Low risk | 85% -- 98% | Dependency bumps, documentation, config changes |
| Medium risk | 50% -- 80% | Standard feature work, moderate refactors |
| High risk | 15% -- 45% | Security-sensitive changes, API surface changes |
| Critical risk | 0% -- 10% | Infrastructure changes, auth/authz modifications |

**Threshold Alerts:**

| Condition | Severity | Action |
|---|---|---|
| AMR drops more than 10 percentage points below 30-day rolling average for any risk segment | Warning | Investigate policy engine changes, recent panel updates, or shifts in PR composition |
| AMR for low-risk PRs falls below 70% | Critical | Halt auto-merge for the affected policy profile; conduct root cause analysis on recent panel emissions |
| AMR for any segment exceeds upper bound by more than 5 points | Warning | Verify panels are not producing false confidence; audit a random sample of auto-merged PRs |

---

### 3. Panel Disagreement Rate (PDR)

| Attribute | Detail |
|---|---|
| **Definition** | The frequency at which two or more panels within the same review cycle produce conflicting or opposing recommendations for the same PR. |
| **Unit** | Percentage (0.00% -- 100.00%) |
| **Formula** | `PDR = (review cycles with at least one opposing verdict pair) / (total review cycles with multi-panel invocation) * 100` |
| **Measurement Method** | For each PR review cycle, extract the terminal verdict from every invoked panel's structured JSON emission. A disagreement is recorded when one panel returns `approve` or `auto_merge` while another returns `block` or `human_review_required` for the same PR. Panels returning `auto_remediate` are treated as conditional approvals and do not count as disagreements against `approve` verdicts. |
| **Data Sources** | Panel structured emissions (JSON), panel invocation registry |

**Disagreement Classification:**

| Type | Definition | Weight |
|---|---|---|
| Hard Disagreement | One panel returns `approve`, another returns `block` | 1.0 |
| Soft Disagreement | One panel returns `approve`, another returns `human_review_required` | 0.5 |
| Remediation Conflict | One panel returns `auto_remediate`, another returns `block` | 0.75 |

**Action Triggers:**

| PDR Threshold | Action |
|---|---|
| < 5% | Normal operation. No action required. |
| 5% -- 10% | Flag for weekly review. Examine disagreement patterns for systematic persona conflicts. |
| 10% -- 20% | Initiate policy reconciliation review. Audit persona prompt configurations for contradictory directives. |
| > 20% | Escalate to governance owner. Suspend auto-merge for affected policy profiles until disagreement root cause is resolved. |

**Significance:** Persistent disagreement is not inherently negative -- it may reflect genuinely ambiguous situations. However, rising PDR trends indicate that either (a) policy boundaries are unclear, (b) persona configurations have drifted, or (c) the change types being submitted do not fit existing panel competencies.

---

### 4. Defect Escape Rate (DER)

| Attribute | Detail |
|---|---|
| **Definition** | The rate at which bugs, vulnerabilities, or regressions reach production that should have been caught by one or more panels during the review cycle. |
| **Unit** | Percentage (0.0000% -- 100.0000%), reported to four decimal places due to expected low values |
| **Formula** | `DER = (post-merge incidents attributable to panel oversight) / (total merges in the same period) * 100` |
| **Measurement Method** | Post-merge incidents are identified from production monitoring, bug reports, and security advisories. Each incident undergoes root cause analysis to determine whether it falls within the detection scope of any panel that reviewed the originating PR. Only incidents where a panel had the capability and data to detect the issue are counted. |
| **Data Sources** | Incident management system, production monitoring alerts, version manifests (to trace incidents to originating PRs), panel capability registry |
| **Lookback Window** | 14 days from merge to capture latent defects that surface after deployment |

**Root Cause Categories:**

| Category | Definition | Remediation Path |
|---|---|---|
| Panel Gap | No panel exists with the competency to detect this class of defect | Add new panel or expand existing panel scope |
| Confidence Miscalibration | A panel reviewed the change and returned a high confidence approval despite the defect being present | Retrain or recalibrate the panel; adjust confidence thresholds in policy engine |
| Policy Gap | The policy engine received a low-confidence or conditional panel result but the policy rules did not escalate to human review | Update policy rules; lower auto-merge confidence threshold for the affected change type |
| Data Insufficiency | The panel lacked sufficient context (e.g., missing test coverage data, incomplete dependency graph) to detect the issue | Improve data pipeline feeding panel inputs |

**Feedback Loop:** Every confirmed defect escape generates a structured remediation ticket that includes:

1. The originating PR and merge SHA.
2. The panels that reviewed it and their emissions.
3. The root cause category.
4. A proposed policy or panel adjustment.
5. A regression test case to be added to the panel validation suite.

---

### 5. Remediation Loop Count (RLC)

| Attribute | Detail |
|---|---|
| **Definition** | The number of review-fix-resubmit cycles a PR undergoes before all invoked panels return passing verdicts. |
| **Unit** | Count (integer) per PR; reported as a distribution and as a mean |
| **Formula (mean)** | `RLC_mean = sum(iteration counts for all PRs) / count(PRs)` |
| **Measurement Method** | Each time a panel returns `auto_remediate` or `human_review_required` and the PR is subsequently updated and re-reviewed, one iteration is counted. The count starts at 0 (first-pass approval) and increments with each cycle. |
| **Data Sources** | Panel emission records (sequential emissions for the same PR), Git push events to PR branches, policy engine re-evaluation logs |

**Distribution Targets:**

| RLC Value | Target Distribution | Interpretation |
|---|---|---|
| 0 (first-pass approval) | > 60% of PRs | Healthy: coder persona and intent spec are producing review-ready code |
| 1 | 20% -- 30% of PRs | Acceptable: minor issues caught and resolved quickly |
| 2 | 5% -- 10% of PRs | Elevated: review criteria may be unclear to the coder persona |
| 3+ | < 5% of PRs | Problematic: investigate intent clarity, coder persona calibration, or panel threshold strictness |

**Correlation Analysis:**

| Correlated Factor | Expected Relationship |
|---|---|
| Coder Persona Effectiveness | Inverse -- better coder personas produce lower RLC |
| Intent Specification Clarity | Inverse -- clearer DI specs reduce ambiguity and rework |
| Panel Strictness Level | Direct -- stricter panels increase RLC but may also reduce DER |
| Change Complexity | Direct -- more complex changes naturally require more iterations |

**Target:** RLC_mean should trend downward over rolling 30-day windows. A sustained increase of more than 0.3 in the rolling mean triggers a review of recent coder persona changes and intent specification templates.

---

### 6. Confidence Variance Trend (CVT)

| Attribute | Detail |
|---|---|
| **Definition** | The standard deviation of confidence scores produced by panels across review cycles, measured over a rolling time window. |
| **Unit** | Standard deviation (decimal, 0.00 -- 1.00, assuming confidence scores are normalized to 0.0 -- 1.0) |
| **Formula** | `CVT = stddev(confidence_scores) over rolling window W` |
| **Measurement Method** | Extract the `confidence` field from every panel structured emission within the rolling window. Compute standard deviation across all emissions, then segment by panel type. |
| **Data Sources** | Panel structured emissions (JSON), specifically the `confidence` field |
| **Rolling Window** | Default: 7 days. Secondary window: 30 days for trend analysis. |

**Interpretation:**

| CVT Range | Interpretation | Action |
|---|---|---|
| 0.00 -- 0.05 | Highly stable panel behavior. Panels are producing consistent confidence levels. | None. This is the target state. |
| 0.05 -- 0.10 | Normal variance. Expected in systems processing diverse change types. | Monitor for trend direction. |
| 0.10 -- 0.15 | Elevated variance. Panels may be encountering edge cases or receiving inconsistent inputs. | Review panel input data quality. Audit recent prompt changes. |
| 0.15 -- 0.20 | High variance. Panel behavior is inconsistent. | Investigate per-panel CVT to isolate the unstable panel. Freeze panel configuration changes until stabilized. |
| > 0.20 | Critical instability. Confidence scores are unreliable for policy decisions. | Escalate. Consider temporarily raising human review thresholds until root cause is resolved. |

**Per-Panel Tracking:** CVT must be computed both in aggregate (all panels) and per individual panel. A single unstable panel can inflate aggregate CVT while other panels remain stable. Per-panel tracking isolates the source.

**Significance:** CVT is the primary indicator of governance maturity. A system with low CVT demonstrates that its panels behave predictably across varied inputs, which is a prerequisite for trusting auto-merge decisions at scale.

---

### 7. Autonomy Index (Composite Score)

The Autonomy Index (AI-X) is a single composite score from 0 to 100 that represents the overall autonomous capability and trustworthiness of the Dark Factory governance system.

#### Formula

```
AI-X = (w1 * S_htf) + (w2 * S_amr) + (w3 * S_pdr) + (w4 * S_der) + (w5 * S_rlc) + (w6 * S_cvt)
```

Where `S_*` are normalized sub-scores (0 -- 100) for each metric, and `w_*` are weights summing to 1.0.

#### Component Normalization

Each metric is converted to a 0 -- 100 sub-score where 100 represents optimal autonomous operation.

| Metric | Sub-score Formula | Rationale |
|---|---|---|
| HT/F | `S_htf = max(0, 100 - (HT_F_mean * 20))` | 0 touchpoints = 100; 5+ touchpoints = 0 |
| AMR | `S_amr = AMR` (direct percentage) | Higher auto-merge rate = higher score |
| PDR | `S_pdr = max(0, 100 - (PDR * 5))` | 0% disagreement = 100; 20%+ = 0 |
| DER | `S_der = max(0, 100 - (DER * 1000))` | 0% escapes = 100; 0.1%+ = 0 |
| RLC | `S_rlc = max(0, 100 - (RLC_mean * 25))` | 0 iterations = 100; 4+ iterations = 0 |
| CVT | `S_cvt = max(0, 100 - (CVT * 500))` | 0.00 variance = 100; 0.20+ = 0 |

#### Weighting Model

| Component | Weight | Justification |
|---|---|---|
| S_der (Defect Escape Rate) | 0.30 | Quality is the primary constraint. A system that ships defects cannot be trusted with autonomy regardless of speed. |
| S_amr (Auto-merge Rate) | 0.20 | Direct measure of autonomous throughput. |
| S_htf (Human Touchpoints) | 0.15 | Measures reduction in human dependency. |
| S_pdr (Panel Disagreement) | 0.15 | Internal consistency is a prerequisite for reliable decisions. |
| S_cvt (Confidence Variance) | 0.10 | Stability indicator; ensures consistency over time. |
| S_rlc (Remediation Loops) | 0.10 | Efficiency of the generation-review loop. |
| **Total** | **1.00** | |

#### Phase Classification Thresholds

| AI-X Range | Phase | Description | Governance Posture |
|---|---|---|---|
| 0 -- 29 | Phase 3 | Supervised Autonomy | Human review required on all high/critical PRs. Auto-merge limited to low-risk only. All panel decisions logged for human audit. |
| 30 -- 54 | Phase 4a | Conditional Autonomy | Auto-merge enabled for low and medium risk. Human review on high/critical. Weekly metric review by governance owner. |
| 55 -- 74 | Phase 4b | Managed Autonomy | Auto-merge enabled for low, medium, and high risk. Human review on critical only. Bi-weekly metric review. |
| 75 -- 100 | Phase 5 | Full Autonomy (Dark Factory) | Auto-merge enabled for all risk levels including critical, with policy-defined exceptions. Monthly metric review. Anomaly-based alerting replaces scheduled review. |

#### Phase Transition Rules

1. **Advancement:** AI-X must remain at or above the threshold for the target phase for a minimum of 4 consecutive weeks before phase advancement is approved.
2. **Regression:** If AI-X drops below the current phase threshold for 2 consecutive weeks, the system automatically regresses to the lower phase and restores the corresponding governance posture.
3. **Manual Override:** The governance owner may override phase classification in either direction with a documented justification that is recorded in the governance log.

#### Trend Visualization Specification

| Report Cadence | Chart Type | Content |
|---|---|---|
| Weekly | Line chart | AI-X composite score, 12-week trailing window, with phase threshold bands overlaid as horizontal reference lines |
| Weekly | Stacked bar chart | Sub-score contributions (weighted) showing which components are driving the composite |
| Monthly | Multi-line chart | All six sub-scores on a single chart, 6-month trailing window, for trend comparison |
| Monthly | Heat map | Per-team AI-X by feature type, identifying pockets of low autonomy |

---

## Weekly Report Generation

### Data Sources

| Source | Data Extracted | Collection Method |
|---|---|---|
| Version Manifests | Merge SHAs, timestamps, policy decisions, risk levels | Query manifest store via API; filter by reporting window |
| Panel Structured Emissions | Confidence scores, verdicts, panel identifiers, disagreement data | Query emissions database; parse JSON payloads |
| Policy Engine Decision Log | Terminal decisions (auto_merge, auto_remediate, human_review_required, block), decision timestamps, policy profile applied | Query policy engine audit log |
| CI/CD Logs | Build results, test pass rates, deployment timestamps | Query CI system API (GitHub Actions, etc.) |
| Incident Management System | Post-merge incidents, root cause classifications, originating PRs | Query incident tracker; join on merge SHA from version manifests |
| Git Event Stream | PR creation, push events, review events, merge events | GitHub webhook payloads or API queries |

### Report Format

The weekly report is generated as a Markdown document with embedded tables, suitable for rendering in GitHub Issues, internal wikis, or email clients.

**Report Structure:**

```
# Dark Factory Governance -- Weekly Autonomy Report
## Reporting Period: [START_DATE] -- [END_DATE]
## Generated: [TIMESTAMP]

### Executive Summary
- Autonomy Index: [AI-X] ([PHASE])
- Week-over-week delta: [+/- CHANGE]
- Alert count: [COUNT] ([SEVERITY BREAKDOWN])

### Metric Summary Table
| Metric | Current Value | Prior Week | Delta | Sub-score | Status |
|--------|--------------|------------|-------|-----------|--------|
| HT/F   | ...          | ...        | ...   | ...       | ...    |
| AMR    | ...          | ...        | ...   | ...       | ...    |
| PDR    | ...          | ...        | ...   | ...       | ...    |
| DER    | ...          | ...        | ...   | ...       | ...    |
| RLC    | ...          | ...        | ...   | ...       | ...    |
| CVT    | ...          | ...        | ...   | ...       | ...    |

### Autonomy Index Detail
- Composite Score: [AI-X]
- Phase: [PHASE]
- Phase Stability: [WEEKS AT CURRENT PHASE]
- Nearest Threshold: [NEXT PHASE] at [THRESHOLD] (delta: [POINTS NEEDED])

### Segment Breakdowns
#### Auto-merge Rate by Risk Level
| Risk Level | AMR   | PR Count | Prior Week | Delta |
|------------|-------|----------|------------|-------|
| Low        | ...   | ...      | ...        | ...   |
| Medium     | ...   | ...      | ...        | ...   |
| High       | ...   | ...      | ...        | ...   |
| Critical   | ...   | ...      | ...        | ...   |

#### Human Touchpoints by Feature Type
| Feature Type         | Mean HT/F | Median | P90  | PR Count |
|----------------------|-----------|--------|------|----------|
| New Feature          | ...       | ...    | ...  | ...      |
| Bug Fix              | ...       | ...    | ...  | ...      |
| Refactor             | ...       | ...    | ...  | ...      |
| Dependency Update    | ...       | ...    | ...  | ...      |
| Configuration Change | ...       | ...    | ...  | ...      |

#### Panel Disagreement Detail
| Panel Pair              | Disagreement Count | Type           |
|-------------------------|--------------------|----------------|
| Security vs. Code Review | ...               | Hard / Soft    |
| Architecture vs. Security | ...              | Hard / Soft    |
| ...                      | ...               | ...            |

### Defect Escapes (if any)
| Incident ID | Originating PR | Root Cause Category | Panel(s) Involved | Remediation Status |
|-------------|---------------|--------------------|--------------------|-------------------|
| ...         | ...           | ...                | ...                | ...               |

### Alerts Triggered
| Alert | Severity | Metric | Threshold | Actual | Resolved |
|-------|----------|--------|-----------|--------|----------|
| ...   | ...      | ...    | ...       | ...    | ...      |

### Recommendations
- [Auto-generated based on metric trends and threshold proximity]
```

### Distribution

| Channel | Audience | Format | Cadence |
|---|---|---|---|
| GitHub Issue | Engineering team, governance owner | Markdown (rendered) | Weekly, posted to dedicated governance repository |
| Email Digest | Engineering leadership, compliance | HTML (converted from Markdown) | Weekly, sent Monday 08:00 UTC |
| Dashboard | All stakeholders | Interactive web dashboard with drill-down | Real-time, with weekly snapshot archival |
| Governance Log | Audit trail | Structured JSON appended to immutable log | Per-report, retained for minimum 24 months |

### Alerting Thresholds for Metric Degradation

Alerts are evaluated continuously (not just at report generation time) and are triggered when any of the following conditions are met.

| Alert ID | Metric | Condition | Severity | Notification |
|---|---|---|---|---|
| ALT-001 | AI-X | Drops below current phase threshold | Critical | Immediate: Slack, email to governance owner |
| ALT-002 | AI-X | Week-over-week decrease exceeding 10 points | Warning | Next business day: email to governance owner |
| ALT-003 | AMR | Drops more than 10pp below 30-day rolling average for any risk segment | Warning | Next business day: email digest |
| ALT-004 | AMR | Low-risk AMR falls below 70% | Critical | Immediate: Slack, auto-merge suspension for affected profile |
| ALT-005 | DER | Any defect escape confirmed | Warning | Immediate: incident channel notification |
| ALT-006 | DER | DER exceeds 0.05% in any rolling 30-day window | Critical | Immediate: Slack, email to governance owner, auto-phase regression evaluation |
| ALT-007 | PDR | Exceeds 20% in any 7-day window | Critical | Immediate: auto-merge suspension for affected policy profiles |
| ALT-008 | PDR | Exceeds 10% in any 7-day window | Warning | Next business day: email to governance owner |
| ALT-009 | CVT | Any individual panel CVT exceeds 0.15 | Warning | Next business day: panel freeze recommendation |
| ALT-010 | CVT | Aggregate CVT exceeds 0.20 | Critical | Immediate: escalation to governance owner, human review threshold increase |
| ALT-011 | RLC | RLC_mean increases by more than 0.3 over 30-day rolling average | Warning | Next business day: coder persona review recommendation |
| ALT-012 | HT/F | Week-over-week increase exceeding 0.5 for any feature type | Warning | Next business day: email digest |

### Alert Lifecycle

1. **Triggered:** Condition met, notification dispatched.
2. **Acknowledged:** Governance owner or designated responder acknowledges receipt.
3. **Investigating:** Root cause analysis in progress.
4. **Resolved:** Root cause addressed, metric returned to acceptable range.
5. **Closed:** Resolution verified over subsequent reporting period.

All alert state transitions are recorded in the governance log with timestamps and actor identifiers.

---

## Appendix A: Data Schema References

### Panel Structured Emission (Relevant Fields)

```json
{
  "panel_id": "string",
  "pr_number": "integer",
  "run_id": "string",
  "timestamp": "ISO-8601",
  "verdict": "approve | auto_merge | auto_remediate | human_review_required | block",
  "confidence": "float (0.0 - 1.0)",
  "risk_level": "low | medium | high | critical",
  "findings": [],
  "metadata": {}
}
```

### Policy Engine Decision Record (Relevant Fields)

```json
{
  "pr_number": "integer",
  "decision": "auto_merge | auto_remediate | human_review_required | block",
  "policy_profile": "string",
  "risk_level": "low | medium | high | critical",
  "panel_inputs": [],
  "timestamp": "ISO-8601",
  "decision_rationale": "string"
}
```

### Version Manifest Entry (Relevant Fields)

```json
{
  "merge_sha": "string",
  "pr_number": "integer",
  "merge_timestamp": "ISO-8601",
  "policy_decision": "string",
  "risk_level": "string",
  "panel_run_ids": [],
  "human_interventions": "integer",
  "remediation_iterations": "integer"
}
```

---

## Appendix B: Calculation Examples

### Example: Autonomy Index Calculation

Given the following metric values for a reporting period:

| Metric | Raw Value |
|---|---|
| HT/F (mean) | 1.2 |
| AMR | 72% |
| PDR | 6% |
| DER | 0.02% |
| RLC (mean) | 0.8 |
| CVT | 0.07 |

**Sub-score calculations:**

| Metric | Formula | Sub-score |
|---|---|---|
| S_htf | max(0, 100 - (1.2 * 20)) | 76.0 |
| S_amr | 72 | 72.0 |
| S_pdr | max(0, 100 - (6 * 5)) | 70.0 |
| S_der | max(0, 100 - (0.02 * 1000)) | 80.0 |
| S_rlc | max(0, 100 - (0.8 * 25)) | 80.0 |
| S_cvt | max(0, 100 - (0.07 * 500)) | 65.0 |

**Composite calculation:**

```
AI-X = (0.15 * 76.0) + (0.20 * 72.0) + (0.15 * 70.0) + (0.30 * 80.0) + (0.10 * 80.0) + (0.10 * 65.0)
     = 11.4 + 14.4 + 10.5 + 24.0 + 8.0 + 6.5
     = 74.8
```

**Result:** AI-X = 74.8, classified as **Phase 4b (Managed Autonomy)**.

This system is 0.2 points below the Phase 5 threshold of 75. It would need to sustain 75+ for 4 consecutive weeks to qualify for Phase 5 advancement.

---

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0.0 | 2026-02-20 | Governance Engineering | Initial definition of all metrics, Autonomy Index formula, weekly report specification, and alerting thresholds |
