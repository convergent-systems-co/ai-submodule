# ADR-005: Just-In-Time Context Management

**Status:** Accepted
**Date:** 2024-06-01 (retroactive)
**Author:** Dark Forge Team

---

## Context

AI agents operating within the Dark Forge have finite context windows. The platform contains over 15,000 lines of Markdown across personas, review prompts, workflows, policies, schemas, and documentation. Loading all governance artifacts simultaneously would exhaust the context window, degrade reasoning quality, and risk context resets that lose critical guidance.

The problem has two dimensions. First, different workflow phases need different artifacts: pre-flight triage does not need panel review prompts; code implementation does not need policy profiles; merge decisions do not need persona definitions. Loading everything wastes the most constrained resource an AI agent has. Second, context compaction (when the window fills) can silently drop instructions, causing the agent to lose governance rules, skip mandatory panels, or forget session state -- all of which are governance failures.

The platform needed a strategy that loads the minimum context required for each phase, prevents context overflow, and ensures critical instructions survive context resets.

## Decision

Context is managed in four tiers with a hard stop at 80% capacity:

### Tier 0: Persistent Context (~400 tokens, survives resets)

| Content | Source |
|---------|--------|
| Base instructions | `instructions.md` |
| Project identity | `project.yaml` (name, language, framework only) |
| Active governance profile | Profile name + decision thresholds only |
| Current task reference | Issue/DI ID + objective statement |

Design rule: if `instructions.md` exceeds 500 tokens, decompose it. The base file contains only universal principles.

### Tier 1: Session Context (~2,000 tokens, loaded at session start)

| Content | Source |
|---------|--------|
| Language conventions | `governance/templates/{language}/instructions.md` |
| Active persona set | Persona files from `project.yaml` |
| Current plan | `.artifacts/plans/{active-plan}.md` |

Design rule: if the persona set exceeds budget, load only persona headers (Role + Evaluate For). Full content moves to Tier 2.

### Tier 2: Phase Context (~3,000 tokens, loaded per workflow phase)

| Content | Source |
|---------|--------|
| Workflow phase definition | `governance/prompts/workflows/{workflow}.md` (single phase) |
| Phase-specific prompt | `governance/prompts/{prompt}.md` |
| Panel definition | `governance/prompts/reviews/{panel}.md` |

Design rule: workflow files must be decomposable by phase. Each phase section works independently.

### Tier 3: Reference Context (0 tokens pre-loaded, queried on-demand)

Policies, schemas, full documentation, and historical emissions. Never pre-loaded. Queried via file reads only when a specific decision requires the data.

### 80% Hard Stop Protocol

When approaching 80% context capacity: stop all work immediately, ensure git working tree is clean (commit, stash, or abort), write a checkpoint to `.artifacts/checkpoints/` with current task, completed work, remaining work, and branch state, then request a context reset. No exceptions. A dirty compaction loses instructions and context that cannot be recovered.

## Consequences

### Positive

- Context usage is predictable: each tier has a token budget, and total pre-loaded context is approximately 5,400 tokens -- leaving the majority of the window for reasoning
- Critical instructions (Tier 0) survive context resets, preventing governance amnesia
- Phase-based loading means agents carry only what they need: a Coder in implementation phase does not carry triage context
- The 80% hard stop prevents silent instruction loss from compaction, which is the most dangerous failure mode for governance agents
- Checkpoint-based recovery enables session continuity across context resets

### Negative

- Tier budgets are estimates based on current model context windows; they require recalibration as models evolve
- The 80% threshold is conservative -- it sacrifices approximately 20% of available context to avoid compaction risk
- Phase transitions require explicit context management: loading new tier content and releasing previous phase context adds orchestration complexity
- Tier 3 on-demand queries add latency compared to pre-loading (file read tool calls for each policy or schema access)

### Neutral

- The tiering strategy implicitly prioritizes breadth (many small artifacts) over depth (few large artifacts) in governance design -- this shapes how new governance artifacts should be authored
- Parallel Coder execution (via `Task` tool with `isolation: "worktree"`) sidesteps the context problem entirely: each Coder subagent has its own context window, so the orchestrating Tech Lead does not carry Coder execution context

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| Load everything at session start | 15,000+ lines exceeds practical context budgets; degrades reasoning quality; no headroom for actual work |
| No tiering (ad-hoc loading) | Unpredictable context usage; no budget enforcement; risk of silent overflow |
| Aggressive summarization (compress all artifacts) | Lossy; governance rules require precise wording; summarized policy is interpreted policy, violating the deterministic-engine principle |
| External memory / RAG | Adds infrastructure dependency; retrieval accuracy is imperfect; governance rules need guaranteed presence, not probabilistic retrieval |

## References

- `docs/architecture/context-management.md` -- full context management specification
- `governance/prompts/startup.md` -- agentic startup sequence implementing tier loading
- `governance/personas/agentic/devops-engineer.md` -- session lifecycle management including 80% enforcement
- `governance/personas/agentic/tech-lead.md` -- phase-based context loading during orchestration
- `.artifacts/checkpoints/` -- checkpoint directory for 80% hard stop recovery
- `instructions.md` -- Tier 0 base instructions
