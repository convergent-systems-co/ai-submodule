# Plan: Multi-Agent Prompt-Chained Architecture (#228)

**Status:** completed
**Issue:** #228
**Branch:** `NETWORK_ID/refactor/228/multi-agent-architecture`

## Objective

Redesign the monolithic agentic startup loop into a multi-agent prompt-chained architecture implementing Anthropic's orchestration patterns (Routing, Orchestrator-Workers, Evaluator-Optimizer).

## Rationale

The startup loop was a 577-line monolithic prompt where a single Team Lead handled all responsibilities. This created cognitive overload and made it impossible to swap individual agent responsibilities. The multi-agent architecture:
- Separates concerns across four specialized personas
- Enables the Evaluator-Optimizer pattern (Coder→Tester feedback loop)
- Adds independent evaluation before push (Tester must approve)
- Adds mandatory Security Review gate after Tester approval
- Enables dynamic panel selection based on codebase type
- Establishes a structured inter-agent protocol for auditability

## Scope

### New Files
- `governance/prompts/agent-protocol.md` — Inter-agent communication contract
- `governance/personas/agentic/devops-engineer.md` — Session entry point (Routing pattern)
- `governance/personas/agentic/tester.md` — Independent evaluator (Evaluator-Optimizer pattern)

### Modified Files
- `governance/personas/agentic/team-lead.md` — Orchestrator-Workers pattern, Tester integration, security review gate, dynamic panel selection
- `governance/personas/agentic/coder.md` — Structured RESULT output, cannot-self-approve constraint
- `governance/prompts/startup.md` — 5-phase prompt-chained orchestrator (577→404 lines)
- `governance/personas/index.md` — Added DevOps Engineer and Tester entries
- `governance/templates/project.yaml` — Added `governance.ai_submodule_pin` config
- `CLAUDE.md` — Updated agentic persona descriptions and startup sequence
- `GOALS.md` — Updated Phase 5d status
- `CHANGELOG.md` — Added multi-agent architecture entry
- `docs/onboarding/developer-guide.md` — Updated agentic loop description

## Approach

1. Create agent protocol (inter-agent communication contract)
2. Create DevOps Engineer persona (session entry, triage, routing)
3. Create Tester persona (independent evaluation)
4. Update Team Lead (Orchestrator-Workers, Tester integration, security review, dynamic panels)
5. Update Coder (structured RESULT, cannot-self-approve)
6. Rewrite startup.md as 5-phase orchestrator
7. Update all documentation

## Testing Strategy

Configuration-only repo — no runtime tests. Verification by inspection of:
- All governance gates preserved in startup.md
- ANCHOR block content preserved
- No gate removal or weakening
- Mermaid diagrams render correctly
- Cross-references between files are consistent

## Risk Assessment

- **ANCHOR block mutation** — mitigated by preserving content, only updating cross-references
- **Gate removal** — mitigated by explicit preservation of all gates in the 5-phase rewrite
- **Breaking consuming repos** — mitigated by additive changes only (new files + compatible edits)
