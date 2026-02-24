# Workflow Plans

Standardized multi-phase workflows that chain personas, prompts, and panels together into end-to-end processes. Each workflow produces named artifacts at every phase, with decision gates where human review is required before proceeding.

## How to Use

1. Pick the workflow that matches your task
2. Start at Phase 1 (or resume mid-workflow by providing a prior artifact)
3. At each **GATE**, review the artifact and approve or request revisions
4. The workflow chains the right personas and prompts automatically

## Workflows

| Workflow | Use When | Phases | File |
|----------|----------|--------|------|
| **Feature Implementation** | Building a new feature from scratch | 6 | `feature-implementation.md` |
| **Bug Fix** | Investigating and resolving a bug | 7 | `bug-fix.md` |
| **Documentation** | Creating or updating technical docs | 5 | `documentation.md` |
| **Refactoring** | Restructuring code without changing behavior | 5 | `refactoring.md` |
| **API Design** | Designing a new API or evolving an existing one | 5 | `api-design.md` |
| **Migration** | System, dependency, or data migrations | 6 | `migration.md` |
| **Architecture Decision** | Making and documenting an architectural choice | 5 | `architecture-decision.md` |
| **Incident Response** | Handling an active incident through post-mortem | 6 | `incident-response.md` |
| **Acceptance Verification** | Validating implementation against formal spec criteria | 5 | `acceptance-verification.md` |

## Artifact Prefixes

Each workflow uses a unique prefix for its artifacts, enabling cross-referencing:

| Prefix | Workflow |
|--------|----------|
| `FEAT` | Feature Implementation |
| `BUG` | Bug Fix |
| `DOC` | Documentation |
| `REF` | Refactoring |
| `API` | API Design |
| `MIG` | Migration |
| `ADR` | Architecture Decision |
| `INC` | Incident Response |
| `AV` | Acceptance Verification |

## Conventions

- **Artifacts** are named `[PREFIX-N]: Name` (e.g., `[FEAT-1]: Requirements Spec`)
- **Gates** require explicit approval before the workflow continues
- **Personas** are adopted at the start of each phase via `governance/personas/` paths
- **Prompts** are invoked where a specific task prompt applies via `governance/prompts/` paths
- **Panels** are invoked for multi-perspective review phases
- **Mid-workflow resume:** paste a prior artifact to pick up from that point
