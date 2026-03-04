# Panel Catalog

Searchable catalog of all governance review panels. Each panel implements
Anthropic's Parallelization (Voting) pattern with multiple independent
perspectives producing structured emissions.

> **Auto-generated** by `governance/bin/generate-catalog.py`.
> Do not edit manually -- regenerate with `python governance/bin/generate-catalog.py`.

## Architecture

| Panel | Required In | Perspectives | Status |
|-------|------------|--------------|--------|
| [api-design-review](../../governance/prompts/reviews/api-design-review.md) | conditional | 5 | Optional |
| [architecture-review](../../governance/prompts/reviews/architecture-review.md) | infrastructure_critical | 5 | Required |
| [migration-review](../../governance/prompts/reviews/migration-review.md) | conditional | 5 | Optional |

## Code Quality

| Panel | Required In | Perspectives | Status |
|-------|------------|--------------|--------|
| [ai-expert-review](../../governance/prompts/reviews/ai-expert-review.md) | conditional | 3 | Optional |
| [code-review](../../governance/prompts/reviews/code-review.md) | default, fin_pii_high, infrastructure_critical, reduced_touchpoint | 5 | Required |
| [technical-debt-review](../../governance/prompts/reviews/technical-debt-review.md) | conditional | 5 | Optional |

## Cost

| Panel | Required In | Perspectives | Status |
|-------|------------|--------------|--------|
| [cost-analysis](../../governance/prompts/reviews/cost-analysis.md) | default, fin_pii_high, infrastructure_critical, reduced_touchpoint | 6 | Required |

## Data

| Panel | Required In | Perspectives | Status |
|-------|------------|--------------|--------|
| [data-design-review](../../governance/prompts/reviews/data-design-review.md) | fin_pii_high | 5 | Required |
| [data-governance-review](../../governance/prompts/reviews/data-governance-review.md) | default, fin_pii_high, reduced_touchpoint | 4 | Required |

## Documentation

| Panel | Required In | Perspectives | Status |
|-------|------------|--------------|--------|
| [documentation-review](../../governance/prompts/reviews/documentation-review.md) | default, fin_pii_high, infrastructure_critical, reduced_touchpoint | 6 | Required |

## Operations

| Panel | Required In | Perspectives | Status |
|-------|------------|--------------|--------|
| [copilot-review](../../governance/prompts/reviews/copilot-review.md) | conditional | 1 | Optional |
| [governance-compliance-review](../../governance/prompts/reviews/governance-compliance-review.md) | conditional | 3 | Optional |
| [incident-post-mortem](../../governance/prompts/reviews/incident-post-mortem.md) | conditional | 5 | Optional |
| [performance-review](../../governance/prompts/reviews/performance-review.md) | conditional | 5 | Optional |
| [production-readiness-review](../../governance/prompts/reviews/production-readiness-review.md) | conditional | 5 | Optional |

## Security

| Panel | Required In | Perspectives | Status |
|-------|------------|--------------|--------|
| [security-review](../../governance/prompts/reviews/security-review.md) | default, fin_pii_high, infrastructure_critical, reduced_touchpoint | 5 | Required |
| [threat-model-system](../../governance/prompts/reviews/threat-model-system.md) | conditional | 5 | Optional |
| [threat-modeling](../../governance/prompts/reviews/threat-modeling.md) | default, fin_pii_high, infrastructure_critical, reduced_touchpoint | 5 | Required |

## Testing

| Panel | Required In | Perspectives | Status |
|-------|------------|--------------|--------|
| [test-generation-review](../../governance/prompts/reviews/test-generation-review.md) | conditional | 3 | Optional |
| [testing-review](../../governance/prompts/reviews/testing-review.md) | fin_pii_high | 5 | Required |

## Summary

- **Total panels:** 20
- **Categories:** 8
  - Architecture: 3
  - Code Quality: 3
  - Cost: 1
  - Data: 2
  - Documentation: 1
  - Operations: 5
  - Security: 3
  - Testing: 2

## All Panels

| Panel | Category | Required In | Perspectives | Purpose |
|-------|----------|------------|--------------|---------|
| [ai-expert-review](../../governance/prompts/reviews/ai-expert-review.md) | code-quality | conditional | 3 | Evaluate changes to AI governance artifacts for impact on agent behavior, prompt engineering quality, governance pipe... |
| [api-design-review](../../governance/prompts/reviews/api-design-review.md) | architecture | conditional | 5 | Evaluate API design from both provider and consumer perspectives. This panel assesses REST correctness, contract stab... |
| [architecture-review](../../governance/prompts/reviews/architecture-review.md) | architecture | infrastructure_critical | 5 | Evaluate system design decisions from multiple architectural perspectives. This panel assesses scalability, security ... |
| [code-review](../../governance/prompts/reviews/code-review.md) | code-quality | default, fin_pii_high, infrastructure_critical, reduced_touchpoint | 5 | Comprehensive code evaluation from multiple engineering perspectives. This panel examines correctness, security, perf... |
| [copilot-review](../../governance/prompts/reviews/copilot-review.md) | operations | conditional | 1 | Integrates GitHub Copilot as a formal review panel within the Dark Forge governance pipeline. Copilot feedback is p... |
| [cost-analysis](../../governance/prompts/reviews/cost-analysis.md) | cost | default, fin_pii_high, infrastructure_critical, reduced_touchpoint | 6 | Evaluate the cost implications of proposed changes, including estimated implementation cost (AI token usage), infrast... |
| [data-design-review](../../governance/prompts/reviews/data-design-review.md) | data | fin_pii_high | 5 | Evaluate data architecture, schema design, and data management practices for proposed changes. This panel assesses st... |
| [data-governance-review](../../governance/prompts/reviews/data-governance-review.md) | data | default, fin_pii_high, reduced_touchpoint | 4 | Enforce enterprise canonical data model standards from the [dach-canonical-models](https://github.com/SET-Apps/dach-c... |
| [documentation-review](../../governance/prompts/reviews/documentation-review.md) | documentation | default, fin_pii_high, infrastructure_critical, reduced_touchpoint | 6 | Evaluate documentation completeness, accuracy, and usability for proposed changes. This panel ensures that documentat... |
| [governance-compliance-review](../../governance/prompts/reviews/governance-compliance-review.md) | operations | conditional | 3 | Evaluate whether a pull request followed the required governance steps defined in the startup and governance pipeline... |
| [incident-post-mortem](../../governance/prompts/reviews/incident-post-mortem.md) | operations | conditional | 5 | Analyze a production incident to identify root causes, contributing factors, and systemic improvements. This panel re... |
| [migration-review](../../governance/prompts/reviews/migration-review.md) | architecture | conditional | 5 | Evaluate a migration plan for safety, completeness, and risk mitigation. This panel assesses data integrity preservat... |
| [performance-review](../../governance/prompts/reviews/performance-review.md) | operations | conditional | 5 | Comprehensive performance analysis from multiple perspectives. This panel evaluates algorithmic efficiency, infrastru... |
| [production-readiness-review](../../governance/prompts/reviews/production-readiness-review.md) | operations | conditional | 5 | Assess whether a system is ready for production deployment. This panel evaluates operational maturity across reliabil... |
| [security-review](../../governance/prompts/reviews/security-review.md) | security | default, fin_pii_high, infrastructure_critical, reduced_touchpoint | 5 | Comprehensive security assessment from multiple threat perspectives. This panel evaluates code changes for vulnerabil... |
| [technical-debt-review](../../governance/prompts/reviews/technical-debt-review.md) | code-quality | conditional | 5 | Assess and prioritize technical debt for strategic remediation. This panel inventories existing and newly introduced ... |
| [test-generation-review](../../governance/prompts/reviews/test-generation-review.md) | testing | conditional | 3 | Evaluate test coverage, verification requirements, and proof-of-correctness criteria for code changes. Emits structur... |
| [testing-review](../../governance/prompts/reviews/testing-review.md) | testing | fin_pii_high | 5 | Evaluate test coverage, quality, and testing approach comprehensively. This panel assesses the adequacy of the test p... |
| [threat-model-system](../../governance/prompts/reviews/threat-model-system.md) | security | conditional | 5 | Comprehensive system-level threat model producing a structured security assessment of the entire platform or applicat... |
| [threat-modeling](../../governance/prompts/reviews/threat-modeling.md) | security | default, fin_pii_high, infrastructure_critical, reduced_touchpoint | 5 | Systematic PR-level threat analysis mapping the attack surface introduced or modified by a pull request to MITRE ATT&... |
