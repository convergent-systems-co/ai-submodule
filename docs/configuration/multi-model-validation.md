# Multi-Model Validation Configuration

Multi-model validation runs review panels across multiple LLM models and aggregates their verdicts using a configurable consensus strategy. This provides higher assurance by requiring cross-model agreement before merge decisions.

## Quick Start

Set the policy profile to `multi-model` in your `project.yaml`:

```yaml
governance:
  policy_profile: "multi-model"
```

This enables multi-model validation with the default configuration: two models (`claude-opus-4-6` and `claude-sonnet-4-6`), majority consensus, applied to all required panels.

## Custom Configuration

You can configure multi-model validation in your policy profile YAML:

```yaml
multi_model:
  enabled: true
  models:
    - "claude-opus-4-6"
    - "claude-sonnet-4-6"
    - "gpt-5.3-codex"
  consensus: majority          # majority | supermajority | unanimous
  min_models: 2                # Minimum models required for valid consensus
  panels: []                   # Empty = all panels; or list specific panels
```

Or configure via `project.yaml` for per-repo overrides:

```yaml
governance:
  multi_model_validation:
    enabled: true
    models: ["claude-opus-4-6", "claude-sonnet-4-6"]
    consensus_threshold: 0.75
    consensus_mode: "majority"
```

## Consensus Strategies

| Strategy | Threshold | Description |
|----------|-----------|-------------|
| `majority` | > 50% | More than half the models must agree. Default. |
| `supermajority` | >= 75% | At least three-quarters must agree. Recommended for security-critical repos. |
| `unanimous` | 100% | All models must agree. Strictest; any dissent triggers human review. |

## Confidence Adjustment

Multi-model consensus strength affects confidence scoring:

| Consensus Result | Confidence Multiplier | Effect |
|-----------------|----------------------|--------|
| Unanimous agreement | 1.0 | No penalty |
| Supermajority agreement | 0.95 | Slight reduction |
| Majority agreement | 0.90 | Moderate reduction |
| No consensus reached | Cap at 0.70 | Triggers human review |
| Insufficient models | Cap at 0.65 | Triggers human review |

## Fallback Behavior

When a model API is unavailable during multi-model validation:

1. If remaining models meet `min_models`, validation proceeds with reduced model count
2. If remaining models are below `min_models`, the verdict is `insufficient_models` and confidence is capped at 0.65
3. This triggers the `human_review_required` escalation rule

## Panel Filtering

To run multi-model validation only on specific panels:

```yaml
multi_model:
  enabled: true
  models: ["claude-opus-4-6", "claude-sonnet-4-6"]
  consensus: supermajority
  min_models: 2
  panels:
    - security-review
    - threat-modeling
```

Panels not in the list continue to use single-model evaluation.

## Emissions

Each model produces a separate emission file:

```
.governance/panels/security-review.claude-opus-4-6.json
.governance/panels/security-review.claude-sonnet-4-6.json
```

The policy engine aggregates these into a single consensus verdict. The aggregated result includes per-model detail in the `multi_model` field of the synthesized emission.
