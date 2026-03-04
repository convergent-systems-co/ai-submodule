# Weekly Autonomy Report: ${period_start} – ${period_end}

**Report ID:** ${report_id}
**Generated:** ${generated_at}
**Schema Version:** 1.0.0

---

## Executive Summary

| Category | Status | Key Metric |
|----------|--------|------------|
| Throughput | ${throughput_status} | ${issues_completed} issues completed, ${prs_merged} PRs merged |
| Quality | ${quality_status} | ${merge_success_rate}% merge success, ${human_intervention_rate}% human intervention |
| Efficiency | ${efficiency_status} | ${avg_issues_per_session} issues/session, ${avg_context_usage}% avg context |
| Safety | ${safety_status} | ${dirty_compactions} dirty compactions, ${merge_without_verification} unverified merges |

Status values: **Healthy** / **Degraded** / **Critical** (per `governance/policy/autonomy-thresholds.yaml`)

---

## Throughput

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Issues processed | ${issues_processed} | — | — |
| Issues completed | ${issues_completed} | ≥ 5/week healthy | ${status} |
| Issues escalated | ${issues_escalated} | — | — |
| Issues skipped | ${issues_skipped} | — | — |
| PRs created | ${prs_created} | — | — |
| PRs merged | ${prs_merged} | — | — |
| PRs abandoned | ${prs_abandoned} | — | — |
| Merge success rate | ${merge_success_rate}% | ≥ 80% healthy | ${status} |
| Sessions run | ${sessions_run} | — | — |

## Quality

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Governance approval rate | ${governance_approval_rate}% | ≥ 70% healthy | ${status} |
| Human intervention rate | ${human_intervention_rate}% | ≤ 20% healthy | ${status} |
| Avg review cycles/PR | ${avg_review_cycles} | ≤ 1.5 healthy | ${status} |
| Copilot findings (total) | ${copilot_total} | — | — |
| — Critical | ${copilot_critical} | — | — |
| — High | ${copilot_high} | — | — |
| — Medium | ${copilot_medium} | — | — |
| — Low/Info | ${copilot_low_info} | — | — |
| Findings implemented | ${findings_implemented} | — | — |
| Findings dismissed | ${findings_dismissed} | — | — |
| Filter mismatch events | ${filter_mismatches} | 0 healthy | ${status} |

## Efficiency

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Avg context usage | ${avg_context_usage}% | ≤ 60% healthy | ${status} |
| Context shutdowns (80%) | ${context_shutdowns} | — | — |
| Context compactions | ${context_compactions} | — | — |
| Avg issues/session | ${avg_issues_per_session} | ≥ 2.0 healthy | ${status} |
| Avg review cycles before merge | ${avg_cycles_before_merge} | — | — |
| Checkpoints written | ${checkpoints_written} | — | — |

## Safety

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Unresolved threads caught (7f-bis) | ${threads_caught} | — | — |
| Max review cycles hit (3-cycle limit) | ${max_cycles_hit} | 0 healthy | ${status} |
| Dirty context compactions | ${dirty_compactions} | **Must be 0** | ${status} |
| Merge without thread verification | ${merge_without_verification} | **Must be 0** | ${status} |
| Escalations to human | ${escalations} | ≤ 2 healthy | ${status} |
| Governance blocks | ${governance_blocks} | — | — |

---

## Flagged Metrics

List any metrics in **Degraded** or **Critical** status with analysis and recommended actions:

${flagged_metrics_analysis}

## Week-over-Week Trends

| Metric | Previous | Current | Δ | Trend |
|--------|----------|---------|---|-------|
| Merge success rate | ${prev_merge_rate}% | ${curr_merge_rate}% | ${delta}% | ${trend} |
| Issues completed | ${prev_completed} | ${curr_completed} | ${delta} | ${trend} |
| Avg review cycles | ${prev_cycles} | ${curr_cycles} | ${delta} | ${trend} |
| Human intervention rate | ${prev_human}% | ${curr_human}% | ${delta}% | ${trend} |

## Notes

${notes}

---

**Data sources:** Run manifests (`governance/schemas/run-manifest.schema.json`), session checkpoints (`.artifacts/checkpoints/`), GitHub issue/PR API.
**Thresholds:** `governance/policy/autonomy-thresholds.yaml`
**Schema:** `governance/schemas/autonomy-metrics.schema.json`
