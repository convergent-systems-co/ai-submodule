# Architecture — Visual Overview

How a developer request becomes governed, tested, merged code.

---

## Pipeline Flow

```mermaid
flowchart TD
    DEV["You (Developer)\n'Build me X' · 'Fix Y' · 'Add Z feature'"]
    DEV --> DEVOPS["DevOps Engineer\nSession entry — pre-flight, triage, routing"]
    DEVOPS --> CM["Tech Lead\nOrchestrator — validates intent, selects panels, assigns work"]
    CM -->|"Plan written to\n.artifacts/plans/"| CODER["Coder\nWorker — implements plan, writes tests"]
    CODER --> TESTER["Tester\nIndependent evaluator — must approve before push"]
    TESTER --> PANELS["Review Panels (run in parallel)\nSecurity · Architecture · Data/PII · Quality · +15 more"]
    PANELS -->|"Each emits structured JSON\nwith confidence score & risk level"| ENGINE["Policy Engine\nDeterministic Python — reads emissions\nproduces: merge · remediate · block"]
    ENGINE -->|Pass| GITHUB["GitHub\nPR created · auto-merged\nIssues closed · Plans archived"]
    ENGINE -->|Fail| FIX["Coder Fixes\nRe-implements based on panel feedback"]
    FIX -->|"Loops back through panels"| PANELS
```

---

## Agent Roles

| Agent | Role | Pattern |
|-------|------|---------|
| **You (Developer)** | Initiates requests via natural language or `/startup` | Human in the loop |
| **DevOps Engineer** | Session entry — pre-flight checks, submodule freshness, issue triage, routing | Anthropic's Routing pattern |
| **Tech Lead** | Orchestrator — validates intent, selects review panels, assigns Coder agents, coordinates merge | Orchestrator-Workers pattern |
| **Coder** | Worker — implements plan, writes tests, produces structured output. Runs in isolated git worktrees for parallel execution | Worker pattern |
| **IaC Engineer** | Worker — infrastructure execution (Bicep/Terraform), security-first defaults. Dispatched only for infrastructure changes | Worker pattern |
| **Tester** | Independent evaluator — test coverage gate, documentation verification, structured feedback | Evaluator-Optimizer pattern |

---

## Review Panels

21 consolidated review prompts execute in parallel on every change. Each panel emits structured JSON validated against `panel-output.schema.json`:

| Panel Category | What It Reviews |
|---------------|----------------|
| **Security** | Vulnerabilities, OWASP top 10, dependency risks, secrets exposure |
| **Architecture** | Design patterns, separation of concerns, backward compatibility |
| **Data / PII** | PII exposure, data classification, GDPR/HIPAA compliance |
| **Quality** | Code quality, test coverage, documentation completeness |
| **Cost** | Cloud resource costs, performance implications |
| **Threat Modeling** | Attack surface analysis, trust boundaries |

---

## Policy Engine Decision Flow

The policy engine is **deterministic Python** — no AI interprets policy rules. It reads panel emissions and produces one of four outcomes:

```mermaid
flowchart LR
    EMISSIONS["Panel Emissions\n(structured JSON)"] --> ENGINE["Policy Engine"]
    ENGINE -->|"All panels pass\nconfidence ≥ threshold"| MERGE["auto_merge"]
    ENGINE -->|"Fixable issues\nfound"| REMEDIATE["auto_remediate"]
    ENGINE -->|"Requires human\njudgment"| REVIEW["human_review_required"]
    ENGINE -->|"Critical issues\nor policy violation"| BLOCK["block"]
```

---

## Audit Trail

Every decision is recorded:

| Artifact | Location | Mutability |
|----------|----------|------------|
| **Plans** | `.artifacts/plans/` | Written before implementation, archived to GitHub Releases on merge |
| **Panel Emissions** | `.artifacts/panels/` | Latest per panel type (overwrite strategy) |
| **Run Manifests** | `governance/manifests/` | Immutable — complete audit trail for replay and compliance |
| **Checkpoints** | `.artifacts/checkpoints/` | Session state for resumption across context resets |

---

## Legend

| Color | Meaning |
|-------|---------|
| **Blue** | DevOps Engineer (session entry) / Developer |
| **Purple** | Tech Lead (orchestrator) |
| **Green** | Tester (evaluator) / GitHub (remote mode) |
| **Orange** | Review Panels (21 total, dynamically selected) |
| **Yellow** | Policy Engine (deterministic) |
| **Dashed** | Audit trail artifacts |

---

*See the [Windows Onboarding](windows-onboarding.md) guide for step-by-step setup, or the [Governance Model](../architecture/governance-model.md) for the full five-layer architecture.*
