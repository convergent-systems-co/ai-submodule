# Per-PR Token Costs and Cost Estimation

This document covers **LLM token costs for AI-assisted governance** -- the tokens consumed by Claude models during panel reviews, implementation, and evaluation. For GitHub Actions minutes and infrastructure costs, see [Infrastructure Costs](infrastructure-costs.md).

Estimated token consumption and cost for each governance phase during a single PR lifecycle.

## Token Budget by Phase

| Phase | Description | Estimated Tokens | Notes |
|-------|-------------|-----------------|-------|
| 1 — Triage | Pre-flight, issue scanning, routing | 5K-10K | DevOps Engineer persona; scales with issue count |
| 2 — Planning | Intent validation, panel selection, plan creation | 10K-20K per issue | Tech Lead persona; one plan per issue |
| 3 — Implementation | Code generation, tests, documentation | 50K-100K per Coder | Coder persona in isolated worktree; largest phase |
| 4 — Review | Panel emissions, CI monitoring, Test Evaluator evaluation | 20K-50K | 6 required panels + security re-review |
| 5 — Merge | Merge decision, retrospective | ~5K | Policy engine is deterministic (zero LLM tokens); cost is manifest write + log |

### Total Per-PR Estimate

| Scenario | Tokens (input + output) | Typical Cost (Sonnet) |
|----------|------------------------|-----------------------|
| Small fix (1 file, low risk) | ~70K | ~$0.21-$1.05 |
| Medium feature (3-5 files) | ~120K | ~$0.36-$1.80 |
| Large feature (10+ files, high risk) | ~200K | ~$0.60-$3.00 |

> Phase 3 dominates. A parallel session with 5 Coder agents can consume 250K-500K tokens for the implementation phase alone.

## Model Pricing Reference

Pricing per 1M tokens (as of 2026-02):

| Model | Input | Output | Best For |
|-------|-------|--------|----------|
| Claude Opus 4 | $15.00 | $75.00 | Complex reasoning, architecture decisions |
| Claude Sonnet 4 | $3.00 | $15.00 | Default for most governance work |
| Claude Haiku 3.5 | $0.80 | $4.00 | Lightweight triage, formatting |

### Cost Per PR by Model

Assuming a medium-complexity PR (~120K tokens, 80/20 input/output split):

| Model | Input Cost | Output Cost | Total |
|-------|-----------|-------------|-------|
| Opus 4 | $1.44 | $1.80 | ~$3.24 |
| Sonnet 4 | $0.29 | $0.36 | ~$0.65 |
| Haiku 3.5 | $0.08 | $0.10 | ~$0.18 |

## Cost Optimization Tips

1. **Use the `--dry-run` flag** on the policy engine to preview decisions without writing manifests:
   ```bash
   python governance/bin/policy-engine.py \
       --emissions-dir governance/emissions/ \
       --profile governance/policy/default.yaml \
       --output /dev/null \
       --dry-run
   ```

2. **Pin to Sonnet for routine work.** Opus is only needed for complex architectural reasoning or high-risk reviews. Most governance panels produce equivalent results on Sonnet.

3. **Leverage context tiers.** The JIT context management system (see [Context Management](../architecture/context-management.md)) keeps per-phase token use bounded. Avoid loading Tier 3 context (policies, schemas) unless the current phase requires it.

4. **Reduce panel count for low-risk changes.** The `reduced_touchpoint.yaml` profile requires fewer human checkpoints. For documentation-only PRs, optional panels can be skipped.

5. **Parallel Coder agents are context-efficient.** Each Coder runs in its own context window. Five parallel agents cost the same total tokens as five sequential agents, but finish faster.

6. **Monitor with `--dry-run`.** Before running a full evaluation, use dry-run mode to confirm emissions are valid and see the estimated decision without writing a manifest.

## Dry-Run Mode

The policy engine supports a `--dry-run` flag that loads emissions and the policy profile, computes confidence and risk scores, and prints a summary without writing a manifest or producing a non-zero exit code.

```bash
python governance/bin/policy-engine.py \
    --emissions-dir governance/emissions/ \
    --profile governance/policy/default.yaml \
    --output /dev/null \
    --dry-run
```

Example output:
```
=== DRY RUN SUMMARY ===
  Profile:    default (v1.0.0)
  Panels:     6 loaded
  Confidence: 0.9200
  Risk:       low
  Estimated:  auto_merge
  (No manifest written — dry-run mode)
========================
```

Dry-run always exits 0 regardless of what the decision would be.

## Related Documentation

- [Context Management](../architecture/context-management.md) — JIT loading tiers and token budgets
- [Autonomy Metrics](autonomy-metrics.md) — Tracking autonomy index and health thresholds
- [Threshold Tuning](threshold-tuning.md) — Auto-tuning confidence thresholds
