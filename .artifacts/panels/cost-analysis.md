# Cost Analysis — PR #587 (`feat/retire-prompt-chaining`)

**Panel:** cost-analysis v1.0.0
**Date:** 2026-03-02
**Branch:** `feat/retire-prompt-chaining`
**Commit:** `f3c7d18b6d6af376cce384598ac37e905d5a5b9d`
**Repository:** convergent-systems-co/dark-forge

---

## Change Summary

Three modifications to `governance/engine/pyproject.toml`:

1. **Lower Python version floor** from `>=3.12` to `>=3.9` — widens runtime compatibility.
2. **Add `pytest-html>=4.0.0`** to `[project.optional-dependencies] dev` — new dev-only dependency for HTML test reports.
3. **Add pytest `addopts`** — `--html=tests/naming-report.html --self-contained-html` — produces a self-contained HTML report on every test run.

No cloud infrastructure, IaC, API endpoints, or production runtime changes are introduced.

---

## Per-Perspective Findings

### FinOps Analyst

**Risk Level:** info

**Findings:**
- No showback/chargeback impact. Changes are confined to dev tooling in a governance submodule — no production workload billing is affected.
- No unit cost metric changes. No new cloud resources provisioned.
- Budget-to-actual variance: negligible. The only incremental cost is CI compute time for generating HTML test reports, which adds single-digit seconds per pipeline run.

**Suggested Optimizations:** None required.

---

### FinOps Engineer

**Risk Level:** info

**Findings:**
- No new cloud resources to tag or budget against.
- The `pytest-html` dependency is dev-only (`[project.optional-dependencies] dev`), so it does not enter production dependency trees or container images.
- No commitment coverage or reservation implications.

**Suggested Optimizations:** None required.

---

### Cost Optimizer

**Risk Level:** info

**Findings:**
- Lowering Python from 3.12 to 3.9 has no direct cost impact. It may avoid forcing CI runners to upgrade Python images prematurely, which preserves existing cached images and avoids rebuild costs.
- The self-contained HTML report (`--self-contained-html`) embeds all assets into a single file. This increases disk I/O per test run by the size of the report (typically 30-100 KB). At governance submodule test frequency, this is negligible.
- No idle or orphaned resource concerns.

**Suggested Optimizations:**
- Consider gating HTML report generation behind a CI-only flag or environment variable to avoid producing reports during rapid local iteration. This is a minor convenience optimization, not a cost concern.

---

### Cloud Cost Analyst

**Risk Level:** info

**Findings:**
- No IaC files (Bicep, Terraform, CloudFormation) are modified.
- No new Azure or AWS resources are provisioned.
- No egress, data transfer, or licensing implications.
- Multi-environment projection: $0 incremental cost across dev, staging, and production.

**Suggested Optimizations:** None required.

---

### LLM Cost Analyst

**Risk Level:** low

**Findings:**
- **Token budget impact:** The addition of `pytest-html` and HTML report generation does not affect LLM token consumption directly. However, the generated HTML report file (`tests/naming-report.html`) will appear in the working tree. If an agentic session reads this file (e.g., during a broad file scan), it could consume tokens unnecessarily.
  - Estimated token cost per accidental read: 500-2,000 tokens (HTML reports range 30-100 KB; partial reads likely).
  - Mitigation: the file is in `tests/` which agents typically do not scan broadly. Risk is low.
- **Compute cost of CLI invocations:** `pytest-html` adds approximately 1-3 seconds of compute per test suite invocation for report serialization. At ~$0.0001/second on standard CI runners, this is negligible ($0.01-0.05/month at typical PR frequency).
- **Session persistence / disk I/O:** The self-contained HTML report adds 30-100 KB of disk writes per test run. No session persistence mechanism is altered.

**Suggested Optimizations:**
- Add `tests/naming-report.html` to `.gitignore` if not already present, to prevent accidental commits of generated artifacts and avoid inflating repo size over time.

---

### Infrastructure Engineer

**Risk Level:** info

**Findings:**
- No infrastructure topology changes.
- No scaling parameter modifications.
- Lowering the Python floor to 3.9 is backward-compatible and does not require infrastructure changes (CI runners, containers, etc.).
- The `pytest-html` package is lightweight (~50 KB installed) with no native extensions or system-level dependencies.

**Suggested Optimizations:** None required.

---

## Consolidated Assessment

### Implementation Cost Estimate

| Category | Estimate |
|----------|----------|
| AI tokens (this review) | 5,000-10,000 tokens |
| Developer time | < 15 minutes |
| CI compute (one-time) | < $0.01 |

### Infrastructure Cost Estimate (Initial)

| Category | Estimate |
|----------|----------|
| New cloud resources | $0 |
| Image rebuilds | $0 (no image changes required) |

### Runtime Cost Estimate (Monthly)

| Category | Estimate | Assumptions |
|----------|----------|-------------|
| CI compute (incremental) | $0.01-0.05/month | ~20 PR test runs/month, 1-3s overhead each |
| Disk I/O (reports) | negligible | 30-100 KB per run |
| LLM token overhead | $0.00-0.02/month | Only if agent accidentally reads HTML report |

**Total incremental monthly cost:** $0.01-0.07/month

### Cost Optimization Opportunities

1. Gate HTML report generation behind `CI=true` environment variable to skip during local development (saves ~1-3s per local test run).
2. Add `tests/naming-report.html` to `.gitignore` to prevent repo size growth from committed generated artifacts.

### Cost Risk Factors

- **Risk:** Generated HTML report files accumulating in version control if not gitignored. **Likelihood:** Low (dev-only workflow). **Impact:** Minimal repo bloat.
- No other cost risk factors identified.

### Final Recommendation

**APPROVE** — This change has negligible cost impact. All modifications are confined to dev-only tooling in a governance submodule. No cloud resources, production workloads, or meaningful CI compute costs are introduced. The total incremental monthly cost is estimated at $0.01-0.07.

---

<!-- STRUCTURED_EMISSION_START -->
See `cost-analysis.json` for structured emission.
<!-- STRUCTURED_EMISSION_END -->
