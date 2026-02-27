# Multi-Model Execution Backend

> Governance schema: `governance/schemas/execution-backend.schema.json`
> Cost policy: `governance/policy/cost-optimization.yaml`
> Panel output fields: `execution_context.token_count`, `execution_context.estimated_cost_usd`

## Overview

The multi-model execution backend abstraction allows the governance pipeline to route panel executions and persona tasks across different LLM providers and models. This enables:

- **Cost optimization** — Route lower-risk panels to cheaper models while reserving premium models for security-critical work.
- **Provider redundancy** — Define fallback backends so panel execution continues if a primary provider is unavailable.
- **Per-persona routing** — Assign different models to different personas based on capability requirements.
- **Budget enforcement** — Track token usage per panel and enforce spending limits at session, issue, and panel levels.

## Backend Configuration

Backends are defined in the `execution` section of a consuming project's `project.yaml`, validated against `governance/schemas/execution-backend.schema.json`.

### Example Configuration

```yaml
# project.yaml (consuming repo)
execution:
  default_backend: claude-opus

  backends:
    claude-opus:
      model_id: claude-opus-4-6
      provider: anthropic
      context_window: 200000
      cost_per_1k_input_tokens: 0.015
      cost_per_1k_output_tokens: 0.075
      capabilities:
        - reasoning
        - code-generation
        - vision
      max_output_tokens: 32000

    claude-sonnet:
      model_id: claude-sonnet-4-20250514
      provider: anthropic
      context_window: 200000
      cost_per_1k_input_tokens: 0.003
      cost_per_1k_output_tokens: 0.015
      capabilities:
        - reasoning
        - code-generation
      max_output_tokens: 16000

    gpt-4o:
      model_id: gpt-4o-2024-08-06
      provider: openai
      context_window: 128000
      cost_per_1k_input_tokens: 0.0025
      cost_per_1k_output_tokens: 0.010
      capabilities:
        - reasoning
        - code-generation
        - vision
      max_output_tokens: 16384

    copilot:
      model_id: copilot-chat
      provider: github-copilot
      context_window: 128000
      cost_per_1k_input_tokens: 0
      cost_per_1k_output_tokens: 0
      capabilities:
        - code-generation
      max_output_tokens: 4096

  model_assignment:
    code-manager:
      primary: claude-opus
      fallback: gpt-4o
    coder:
      primary: claude-sonnet
      fallback: copilot
    security-review:
      primary: claude-opus
      fallback: gpt-4o
    threat-modeling:
      primary: claude-opus
      fallback: gpt-4o
    code-review:
      primary: claude-sonnet
      fallback: copilot
    documentation-review:
      primary: claude-sonnet
      fallback: copilot
    cost-analysis:
      primary: claude-sonnet
      fallback: copilot
    data-governance-review:
      primary: claude-sonnet
      fallback: copilot
```

### Schema Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `backends` | object | Yes | Named backend definitions keyed by identifier |
| `backends.<id>.model_id` | string | Yes | Provider-specific model identifier |
| `backends.<id>.provider` | string | Yes | One of: `anthropic`, `openai`, `azure-openai`, `github-copilot` |
| `backends.<id>.context_window` | integer | Yes | Max context window in tokens (min 1024) |
| `backends.<id>.cost_per_1k_input_tokens` | number | No | USD per 1,000 input tokens |
| `backends.<id>.cost_per_1k_output_tokens` | number | No | USD per 1,000 output tokens |
| `backends.<id>.capabilities` | array | No | Model capabilities for task routing |
| `backends.<id>.max_output_tokens` | integer | No | Max output tokens per response |
| `default_backend` | string | Yes | Backend key used when no assignment exists |
| `model_assignment` | object | No | Per-persona routing with primary/fallback |

## Per-Persona Model Routing

The `model_assignment` section maps persona identifiers to backend keys. When a persona begins execution:

1. Look up the persona in `model_assignment`.
2. If found, use the `primary` backend.
3. If the primary is unavailable or budget-exceeded, use `fallback`.
4. If no assignment exists, use `default_backend`.

Protected personas (defined in `cost-optimization.yaml`) are never downgraded, even under budget pressure. Security-review and threat-modeling panels always use their assigned primary backend.

## Cost Tracking

### Panel Output Fields

Two optional fields in the `execution_context` of every panel emission track costs:

```json
{
  "execution_context": {
    "model_version": "claude-opus-4-6",
    "token_count": {
      "input": 45200,
      "output": 3800
    },
    "estimated_cost_usd": 0.963
  }
}
```

- `token_count.input` — Number of input tokens consumed by the panel execution.
- `token_count.output` — Number of output tokens generated.
- `estimated_cost_usd` — Calculated as: `(input / 1000 * cost_per_1k_input_tokens) + (output / 1000 * cost_per_1k_output_tokens)`.

These fields are optional and backward-compatible. Panels that do not report token counts continue to function; cost tracking is best-effort.

### Budget Enforcement

The `cost-optimization.yaml` policy defines three budget levels:

| Level | Default | Scope |
|-------|---------|-------|
| `per_session_usd` | $5.00 | Total spend across all panels in a single governance session |
| `per_issue_usd` | $1.00 | Total spend for all panels evaluating a single issue |
| `per_panel_usd` | $0.25 | Maximum spend for a single panel execution |

When thresholds are approached or exceeded:

- **75% of session budget** — Skip optional panels to conserve budget.
- **90% of session budget** — Switch all non-protected personas to fallback backends.
- **100% of session budget** — Block further panel executions; require human decision.
- **100% of issue budget** — Require human approval to continue work on the issue.
- **100% of panel budget** — Flag as anomaly (unusual token consumption).

### Cost Aggregation

When `cost_tracking.aggregate_in_manifest` is enabled, the run manifest includes a `total_cost_usd` field summing all panel `estimated_cost_usd` values.

## Adding a New Backend

To add a new LLM backend:

1. Add a new entry under `execution.backends` in `project.yaml` with the required fields (`model_id`, `provider`, `context_window`).
2. If the provider is not yet supported, add it to the `provider` enum in `governance/schemas/execution-backend.schema.json`.
3. Update `model_assignment` to route specific personas to the new backend if desired.
4. Set `cost_per_1k_input_tokens` and `cost_per_1k_output_tokens` for budget tracking.
5. Run schema validation to confirm the configuration is valid.

### Provider Support

| Provider | Description | Notes |
|----------|-------------|-------|
| `anthropic` | Anthropic Claude models | Primary recommended provider |
| `openai` | OpenAI GPT models | Direct API access |
| `azure-openai` | Azure-hosted OpenAI models | Enterprise deployments with Azure compliance |
| `github-copilot` | GitHub Copilot Chat | Zero marginal cost if included in GitHub plan |

## Relationship to Existing Configuration

- **`execution_context.model_version`** in panel output continues to record which model was actually used. The new `token_count` and `estimated_cost_usd` fields supplement this with usage data.
- **Policy profiles** (`default.yaml`, etc.) are unmodified. The `cost-optimization.yaml` policy operates alongside the active evaluation profile, not as a replacement.
- **Run manifests** may optionally include aggregated cost data when cost tracking is enabled.
