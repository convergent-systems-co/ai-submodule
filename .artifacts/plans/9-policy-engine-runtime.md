# Policy Engine Runtime (Phase 4b)

**Author:** Coder (agentic)
**Date:** 2026-02-21
**Status:** completed
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/9
**Branch:** NETWORK_ID/9-policy-engine-runtime

---

## 1. Objective

Build a standalone Python CLI tool that evaluates YAML policy profiles against structured panel emissions to produce deterministic merge decisions, rule-by-rule audit logs, and run manifests conforming to `schemas/run-manifest.schema.json`.

## 2. Rationale

The existing `governance-review.yml` has inline Python that handles basic evaluation against `default.yaml` only. Issue #9 requires a proper reusable engine that supports all three profiles, produces audit-quality logs, and generates run manifests. Python is chosen because the existing workflow already uses Python with `jsonschema` and `pyyaml`.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Node.js (per CI blueprint) | Yes | Blueprint is aspirational (issue #10); existing workflow is Python; no npm infrastructure in repo |
| Inline expansion of governance-review.yml | Yes | Not reusable, not testable, doesn't produce manifests |
| GitHub Action (composite) | Yes | More complexity than needed; a CLI script invokable from workflows is simpler and more portable |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.governance/policy-engine.py` | Main CLI tool — reads emissions + profile, evaluates rules, outputs decision + manifest |
| `.governance/README.md` | Usage documentation for the policy engine |

### Files to Modify

| File | Change Description |
|------|-------------------|
| None | The governance-review.yml update is issue #10's scope |

### Files to Delete

| File | Reason |
|------|--------|
| None | No deletions |

## 4. Approach

### Step 1: Build the Policy Engine CLI

Single Python file `.governance/policy-engine.py` with:

**CLI interface:**
```
python .governance/policy-engine.py \
  --emissions-dir emissions/ \
  --profile policy/default.yaml \
  --output manifest.json \
  --log-file evaluation.log
```

**Flags:**
- `--emissions-dir` — Directory containing panel emission JSON files
- `--profile` — Path to YAML policy profile
- `--output` — Path to write the run manifest JSON
- `--log-file` — Optional path to write rule-by-rule evaluation log (defaults to stderr)
- `--ci-checks-passed` — Boolean flag for CI check status (default: true)
- `--commit-sha` — Git commit SHA for manifest
- `--pr-number` — PR number for manifest context
- `--repo` — Repository name for manifest context

**Exit codes:**
- 0: `auto_merge`
- 1: `block`
- 2: `human_review_required`
- 3: `auto_remediate`

**Evaluation sequence (deterministic):**
1. Load and validate all emissions against `schemas/panel-output.schema.json`
2. Load and parse policy profile YAML
3. Check required panels present
4. Compute weighted aggregate confidence (with redistribution for missing optional panels)
5. Compute aggregate risk level via risk aggregation rules
6. Collect all policy flags across emissions
7. Evaluate block conditions
8. Evaluate escalation rules
9. Evaluate auto-merge conditions
10. Evaluate auto-remediate conditions
11. Default to `human_review_required`
12. Generate run manifest
13. Write output and exit

Each step logs its evaluation with pass/fail/skip and the specific values that led to the result.

### Step 2: Write README

Brief usage docs in `.governance/README.md`.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual validation | All 3 profiles | Run engine against existing emissions with each profile |
| Determinism check | Same inputs | Run engine twice, verify identical output |
| Schema validation | Manifest output | Validate manifest against run-manifest.schema.json |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Policy rule DSL is complex to parse | Medium | Medium | Implement the specific rule patterns used in the three profiles, not a general DSL parser |
| Run manifest generation fails schema validation | Low | High | Validate output against schema before writing |

## 7. Dependencies

- [x] Python 3.12+ (available in CI)
- [x] `jsonschema` pip package (already in CI)
- [x] `pyyaml` pip package (already in CI)
- [x] Schemas exist: `panel-output.schema.json`, `run-manifest.schema.json`
- [x] Policy profiles exist: all three YAML files

## 8. Backward Compatibility

New files only. No existing behavior changed. The existing governance-review.yml inline Python continues working. Issue #10 will update the workflow to invoke this engine.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | First application code in repo |
| security-review | Yes | Policy engine makes security-relevant decisions |
| ai-expert-review | Yes | Changes governance pipeline integrity |

**Policy Profile:** default
**Expected Risk Level:** medium (first code in a config-only repo)

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Python over Node.js | Matches existing inline code, no npm infra needed, simpler for deterministic evaluation |
| 2026-02-21 | Single file over package | Keep it simple — one file with stdlib + 2 pip deps |
| 2026-02-21 | Profile-specific rule patterns, not general DSL | The three profiles use specific patterns; a general DSL parser is over-engineering for Phase 4b |
