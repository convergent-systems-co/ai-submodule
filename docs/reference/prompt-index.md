# Prompt Index

Complete index of all governance prompts organized by type.

> **Auto-generated** by `governance/bin/generate-catalog.py`.
> Do not edit manually -- regenerate with `python governance/bin/generate-catalog.py`.

## Review Panels

| Name | File | Purpose |
|------|------|---------|
| ai-expert-review | `governance/prompts/reviews/ai-expert-review.md` | Evaluate changes to AI governance artifacts for impact on agent behavior, prompt engineering quality, governance pipe... |
| api-design-review | `governance/prompts/reviews/api-design-review.md` | Evaluate API design from both provider and consumer perspectives. This panel assesses REST correctness, contract stab... |
| architecture-review | `governance/prompts/reviews/architecture-review.md` | Evaluate system design decisions from multiple architectural perspectives. This panel assesses scalability, security ... |
| code-review | `governance/prompts/reviews/code-review.md` | Comprehensive code evaluation from multiple engineering perspectives. This panel examines correctness, security, perf... |
| copilot-review | `governance/prompts/reviews/copilot-review.md` | Integrates GitHub Copilot as a formal review panel within the Dark Forge governance pipeline. Copilot feedback is p... |
| cost-analysis | `governance/prompts/reviews/cost-analysis.md` | Evaluate the cost implications of proposed changes, including estimated implementation cost (AI token usage), infrast... |
| data-design-review | `governance/prompts/reviews/data-design-review.md` | Evaluate data architecture, schema design, and data management practices for proposed changes. This panel assesses st... |
| data-governance-review | `governance/prompts/reviews/data-governance-review.md` | Enforce enterprise canonical data model standards from the [dach-canonical-models](https://github.com/SET-Apps/dach-c... |
| documentation-review | `governance/prompts/reviews/documentation-review.md` | Evaluate documentation completeness, accuracy, and usability for proposed changes. This panel ensures that documentat... |
| governance-compliance-review | `governance/prompts/reviews/governance-compliance-review.md` | Evaluate whether a pull request followed the required governance steps defined in the startup and governance pipeline... |
| incident-post-mortem | `governance/prompts/reviews/incident-post-mortem.md` | Analyze a production incident to identify root causes, contributing factors, and systemic improvements. This panel re... |
| migration-review | `governance/prompts/reviews/migration-review.md` | Evaluate a migration plan for safety, completeness, and risk mitigation. This panel assesses data integrity preservat... |
| performance-review | `governance/prompts/reviews/performance-review.md` | Comprehensive performance analysis from multiple perspectives. This panel evaluates algorithmic efficiency, infrastru... |
| production-readiness-review | `governance/prompts/reviews/production-readiness-review.md` | Assess whether a system is ready for production deployment. This panel evaluates operational maturity across reliabil... |
| security-review | `governance/prompts/reviews/security-review.md` | Comprehensive security assessment from multiple threat perspectives. This panel evaluates code changes for vulnerabil... |
| technical-debt-review | `governance/prompts/reviews/technical-debt-review.md` | Assess and prioritize technical debt for strategic remediation. This panel inventories existing and newly introduced ... |
| test-generation-review | `governance/prompts/reviews/test-generation-review.md` | Evaluate test coverage, verification requirements, and proof-of-correctness criteria for code changes. Emits structur... |
| testing-review | `governance/prompts/reviews/testing-review.md` | Evaluate test coverage, quality, and testing approach comprehensively. This panel assesses the adequacy of the test p... |
| threat-model-system | `governance/prompts/reviews/threat-model-system.md` | Comprehensive system-level threat model producing a structured security assessment of the entire platform or applicat... |
| threat-modeling | `governance/prompts/reviews/threat-modeling.md` | Systematic PR-level threat analysis mapping the attack surface introduced or modified by a pull request to MITRE ATT&... |

## Workflow Prompts

| Name | File | Purpose |
|------|------|---------|
| Acceptance Verification | `governance/prompts/workflows/acceptance-verification.md` | N/A |
| Api Design | `governance/prompts/workflows/api-design.md` | <What this API enables> |
| Architecture Decision | `governance/prompts/workflows/architecture-decision.md` | N/A |
| Bug Fix | `governance/prompts/workflows/bug-fix.md` | N/A |
| Documentation | `governance/prompts/workflows/documentation.md` | N/A |
| Feature Implementation | `governance/prompts/workflows/feature-implementation.md` | N/A |
| Incident Response | `governance/prompts/workflows/incident-response.md` | N/A |
| Migration | `governance/prompts/workflows/migration.md` | N/A |
| Refactoring | `governance/prompts/workflows/refactoring.md` | N/A |

## Templates

| Name | File |
|------|------|
| Plan Template Light | `governance/templates/prompts/plan-template-light.md` |
| Plan Template | `governance/templates/prompts/plan-template.md` |
| Runtime Di Template | `governance/templates/prompts/runtime-di-template.md` |
| Weekly Report Template | `governance/templates/prompts/weekly-report-template.md` |

## Other Prompts

| Name | File |
|------|------|
| Agent Protocol | `governance/prompts/agent-protocol.md` |
| Backward Compatibility Workflow | `governance/prompts/backward-compatibility-workflow.md` |
| Checkpoint Resumption Workflow | `governance/prompts/checkpoint-resumption-workflow.md` |
| Code Review | `governance/prompts/code-review.md` |
| Commit | `governance/prompts/commit.md` |
| Cross Repo Escalation Workflow | `governance/prompts/cross-repo-escalation-workflow.md` |
| Data Governance Workflow | `governance/prompts/data-governance-workflow.md` |
| Debug | `governance/prompts/debug.md` |
| Di Generation Workflow | `governance/prompts/di-generation-workflow.md` |
| Docx Generation | `governance/prompts/docx-generation.md` |
| Explain | `governance/prompts/explain.md` |
| Github Pages Setup | `governance/prompts/github-pages-setup.md` |
| Governance Change Proposal | `governance/prompts/governance-change-proposal.md` |
| Governance Compliance Checklist | `governance/prompts/governance-compliance-checklist.md` |
| Init | `governance/prompts/init.md` |
| Migrate | `governance/prompts/migrate.md` |
| Plan | `governance/prompts/plan.md` |
| Refactor | `governance/prompts/refactor.md` |
| Remediation Workflow | `governance/prompts/remediation-workflow.md` |
| Retrospective | `governance/prompts/retrospective.md` |
| Startup | `governance/prompts/startup.md` |
| Test Coverage Gate | `governance/prompts/test-coverage-gate.md` |
| Write Tests | `governance/prompts/write-tests.md` |

## Global Developer Prompts

12 production-ready prompts for common development tasks. See [Prompt Library Guide](../guides/prompt-library.md) for usage details.

| Name | File | Description | Tags | Status |
|------|------|-------------|------|--------|
| global-dev-code-review | `prompts/global/global-dev-code-review.prompt.md` | Review code for quality, security, performance | dev, review, security, quality | production |
| global-dev-context-summary | `prompts/global/global-dev-context-summary.prompt.md` | Generate brief code context summary | dev, summary, context | production |
| global-dev-debug | `prompts/global/global-dev-debug.prompt.md` | Debug issues and troubleshoot errors | dev, debug, troubleshooting | production |
| global-dev-explain | `prompts/global/global-dev-explain.prompt.md` | Explain code sections and design patterns | dev, explain, documentation | production |
| global-dev-git-review | `prompts/global/global-dev-git-review.prompt.md` | Review git history and commit changes | dev, review, git, history | production |
| global-dev-plan-create | `prompts/global/global-dev-plan-create.prompt.md` | Create implementation plans | dev, planning, strategy | production |
| global-dev-plan-execute | `prompts/global/global-dev-plan-execute.prompt.md` | Execute plans and track progress | dev, execution, tracking | production |
| global-dev-pr-create | `prompts/global/global-dev-pr-create.prompt.md` | Create pull requests with structured summaries | dev, pr, review | production |
| global-dev-pr-review | `prompts/global/global-dev-pr-review.prompt.md` | Review pull requests | dev, pr, review, quality | production |
| global-dev-refactor | `prompts/global/global-dev-refactor.prompt.md` | Refactor code for clarity and performance | dev, refactor, improvement | production |
| global-dev-release-notes | `prompts/global/global-dev-release-notes.prompt.md` | Generate release notes and changelogs | dev, docs, release | production |
| global-dev-write-tests | `prompts/global/global-dev-write-tests.prompt.md` | Write comprehensive tests | dev, testing, quality | production |

## Shared Perspectives

Canonical definitions for perspectives appearing in 2+ review prompts.
Serves as the authoring-time DRY mechanism; compiled prompts have
full locality at runtime.

- [`governance/prompts/shared-perspectives.md`](../../governance/prompts/shared-perspectives.md)
