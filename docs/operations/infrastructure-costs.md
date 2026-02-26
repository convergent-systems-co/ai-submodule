# Infrastructure Costs

What consuming repositories pay when adopting the Dark Factory Governance Platform.

This document covers **infrastructure costs only** — GitHub Actions minutes, runner pricing, and related CI/CD resources. For LLM token costs (the other major cost category), see [Token Costs](token-costs.md).

!!! note "Scope"
    Only resources that the consuming repository uses directly are counted here. Shared resources — such as the `ai-submodule` repository itself and its documentation site — are maintained centrally and do not cost consuming repos anything. The workflows listed below run in the **consuming repo's** GitHub Actions quota when installed via `init.sh`.

## GitHub Actions Minutes (Primary Cost)

The governance platform ships several GitHub Actions workflows. Each runs on `ubuntu-latest` (Linux) runners.

### Workflow Resource Consumption

| Workflow | Trigger | Approx Duration | Jobs | Notes |
|----------|---------|-----------------|------|-------|
| `dark-factory-governance.yml` | Every PR (open/sync) | ~3-5 min | 3 (detect, test, review) | Concurrency group cancels in-progress runs on same branch |
| `issue-monitor.yml` | Manual dispatch | ~5-10 min | 2 (evaluate, dispatch) | One run per issue; concurrency group prevents duplicates |
| `deploy-docs.yml` | Push to main (path-filtered) | ~3-5 min | 2 (build, deploy) | Only triggers on `docs/**`, `mkdocs.yml`, or workflow changes |
| `plan-archival.yml` | PR merge | <1 min | 1 (archive) | Archives plan files to GitHub Releases; skips bot PRs |
| `propagate-submodule.yml` | Push to main | ~2-3 min per consuming repo | Matrix job (1 per consumer) | Disabled by default; opt-in via matrix config |
| `event-trigger.yml` | Repository events | ~1-2 min | 1 (dispatch) | Event-driven governance session dispatch (Phase 5c) |

### Monthly Estimates by Team Size

These estimates assume typical usage patterns. Actual minutes depend on PR frequency, issue monitoring cadence, and documentation change rate. Workflows marked *(optional)* are not installed by default — they must be manually added or enabled. Only `dark-factory-governance.yml`, `issue-monitor.yml`, and `plan-archival.yml` are installed by `init.sh`.

| Metric | Small (10 PRs/mo) | Medium (50 PRs/mo) | Large (100+ PRs/mo) |
|--------|-------------------|---------------------|---------------------|
| Governance workflow (`dark-factory-governance.yml`) | ~40 min | ~200 min | ~400 min |
| Issue monitoring (`issue-monitor.yml`) | ~20 min | ~60 min | ~120 min |
| Doc deployment (`deploy-docs.yml`) *(optional)* | ~16 min | ~40 min | ~80 min |
| Plan archival (`plan-archival.yml`) | ~5 min | ~25 min | ~50 min |
| Event trigger (`event-trigger.yml`) *(optional)* | ~10 min | ~30 min | ~60 min |
| Submodule propagation (`propagate-submodule.yml`) *(optional)* | ~0 min (disabled) | ~0 min (disabled) | ~0 min (disabled) |
| **Total (required only)** | **~65 min** | **~285 min** | **~570 min** |
| **Total (all optional enabled)** | **~91 min** | **~355 min** | **~710 min** |

!!! tip "Free tier headroom"
    GitHub Free includes **2,000 minutes/month** for private repos. GitHub Team includes **3,000 minutes/month**. GitHub Enterprise includes **50,000 minutes/month**. Even at high PR volume, the governance platform uses a fraction of available minutes.

### Monthly Cost Estimates

| Team Size | Minutes | Est. Monthly Cost (Linux) |
|-----------|---------|---------------------------|
| Small (10 PRs/mo) | ~65-91 min | ~$0.52-$0.73 |
| Medium (50 PRs/mo) | ~285-355 min | ~$2.28-$2.84 |
| Large (100+ PRs/mo) | ~570-710 min | ~$4.56-$5.68 |

> Ranges reflect required-only vs all-optional-enabled. Cost calculated at $0.008/min for Linux runners. Public repositories get unlimited free minutes.

## GitHub Actions Pricing Reference

| Runner OS | Per-Minute Rate | Multiplier |
|-----------|----------------|------------|
| Linux (ubuntu-latest) | $0.008 | 1x |
| Windows | $0.016 | 2x |
| macOS | $0.08 | 10x |

All governance workflows use Linux runners exclusively.

For current pricing, see [About billing for GitHub Actions](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions).

## Cloud Resources

The Dark Factory Governance Platform **does not provision any cloud infrastructure**. There are no Azure, AWS, or GCP resources created by the platform itself.

If your consuming repository deploys application infrastructure, those costs are application-specific and unrelated to the governance platform. For estimating application infrastructure costs:

- [Azure Pricing Calculator](https://azure.microsoft.com/en-us/pricing/calculator/)
- [AWS Pricing Calculator](https://calculator.aws/)
- [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator)

## LLM Token Costs

LLM token consumption is a separate cost category from infrastructure. The governance platform uses AI models during panel reviews, implementation, and evaluation phases.

See [Token Costs](token-costs.md) for detailed per-PR token estimates, model pricing, and optimization tips.

## Optimization Tips

### 1. Workflow Concurrency Groups

All governance workflows already include concurrency groups that cancel in-progress runs when a new commit is pushed to the same branch. This prevents wasted minutes from stale runs:

```yaml
concurrency:
  group: governance-${{ github.head_ref || github.ref }}
  cancel-in-progress: true
```

### 2. Path Filters

The `deploy-docs.yml` workflow only triggers on documentation changes (`docs/**`, `mkdocs.yml`). Consider adding path filters to other workflows if your repository has areas that do not require governance review.

### 3. GitHub Actions Caching

Cache Python dependencies and other build artifacts to reduce setup time in each workflow run:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: 'pip'
```

### 4. Conditional Panel Execution

The `reduced_touchpoint.yaml` policy profile minimizes human checkpoints. For low-risk documentation changes, fewer panels are required, reducing both token costs and workflow duration.

### 5. Submodule Propagation

The `propagate-submodule.yml` workflow is disabled by default. Only enable it when you have consuming repos that should auto-update. Each consumer in the matrix adds ~2-3 minutes per push to main.

## Related Documentation

- [Token Costs](token-costs.md) -- LLM token consumption and per-PR cost estimates
- [Autonomy Metrics](autonomy-metrics.md) -- Tracking autonomy index and health thresholds
- [CI Gating](../configuration/ci-gating.md) -- CI checks, branch protection, and auto-merge configuration
