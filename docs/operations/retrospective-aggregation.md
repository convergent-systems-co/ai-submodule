# Retrospective Aggregation

## Purpose

The retrospective aggregation schema (`governance/schemas/retrospective-aggregation.schema.json`) defines a structured format for collecting and analyzing governance run data over time. It aggregates the per-issue retrospective evaluations produced by the retrospective prompt (`governance/prompts/retrospective.md`) into a machine-readable format that enables data-driven governance improvements.

## Relationship to Other Schemas

| Schema | Relationship |
|--------|-------------|
| `run-manifest.schema.json` | Retrospective entries reference manifest IDs via `run_id`. Manifests are immutable audit records; retrospective data adds post-merge evaluation. |
| `autonomy-metrics.schema.json` | Autonomy metrics are period-based summaries of throughput, quality, efficiency, and safety. Retrospective aggregation provides the per-run detail that metrics summarize. |
| `panel-output.schema.json` | Panel outputs are real-time structured emissions. Retrospective data captures whether those emissions were accurate after the fact (post-merge outcomes). |

## Schema Structure

### Top Level

- **schema_version**: Always `"1.0.0"` for this schema version
- **report_id**: UUID identifying this aggregation report
- **period**: Start and end timestamps for the aggregation window
- **governance_version**: Git SHA of the `.ai` submodule at aggregation time
- **runs**: Array of per-run retrospective entries
- **aggregated**: Derived statistics computed across all runs

### Per-Run Entry (`runs[]`)

Each entry captures one governance run (one issue -> PR -> merge cycle):

- **Identification**: `run_id`, `timestamp`, `issue_number`, `pr_number`
- **Context**: `policy_profile` used
- **Planning**: `plan_accuracy` (accurate, minor_deviations, significant_deviations)
- **Review**: `review_cycles` count, `ci_failures` count
- **Panels**: Per-panel `verdict`, `confidence`, `was_overridden`, `post_merge_outcome`
- **Copilot**: `copilot_findings` with counts by severity and disposition
- **Overrides**: `human_overrides` count
- **Improvements**: `process_improvements` recommendations with categories

### Aggregated Metrics (`aggregated`)

Derived statistics across all runs in the period:

- **panel_accuracy**: Overall and per-panel accuracy rates, false positive/negative counts
- **false_positive_rate / false_negative_rate**: Overall signal quality
- **override_frequency**: Total overrides, override rate, breakdown by policy profile
- **review_cycle_distribution**: Mean, median, max, histogram
- **time_to_merge**: Mean, median, p90, max in minutes
- **plan_accuracy_distribution**: Counts by accuracy category

## Usage

### Data Collection

Retrospective data is collected during Step 7h of the startup sequence. Currently, retrospectives are posted as issue comments. To populate this schema:

1. Parse retrospective comments from closed issues
2. Cross-reference with run manifests for panel data
3. Check issue/PR timelines for time-to-merge calculations
4. Record post-merge outcomes when incidents or reverts occur

### Consumers

This schema is designed to support Phase 5b self-evolution capabilities:

1. **Threshold auto-tuning** — Uses `panel_accuracy.by_panel` and `false_positive_rate` to identify panels whose confidence thresholds should be adjusted
2. **Persona effectiveness scoring** — Uses per-panel accuracy and override data to score individual persona contributions
3. **Governance change proposals** — Uses `process_improvements` aggregation to identify recurring recommendations that warrant governance changes

### Storage

Aggregation reports should be stored in `governance/retrospectives/` (or a location specified by the consuming project). Reports are append-only — new periods generate new reports, they do not overwrite previous ones.
