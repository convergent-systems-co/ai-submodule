# ADR-002: Panel-Based Review System

**Status:** Accepted
**Date:** 2024-06-01 (retroactive)
**Author:** Dark Factory Governance Team

---

## Context

The governance platform needed a review architecture that could evaluate code changes across multiple dimensions -- security, cost, architecture, testing, documentation, data governance -- without relying on a single monolithic prompt or requiring separate AI agent instances for each concern.

Two competing pressures shaped this decision. First, research from Anthropic, Google DeepMind, and arXiv consistently shows that frontier models perform best with consolidated, self-contained prompts rather than decomposed multi-agent pipelines (arXiv:2512.08296 reports 39-70% degradation in sequential reasoning tasks with multi-agent setups; arXiv:2602.04853 finds diminishing returns from prompt decomposition on frontier models). Second, governance reviews require genuine diversity of perspective -- a security auditor and a cost analyst evaluate the same diff through fundamentally different lenses.

Anthropic's Parallelization (Voting) pattern provided the resolution: "You can use voting when reviewing a piece of code for vulnerabilities, where several different prompts review and flag the code if they find a problem." Each review panel runs as a single prompt containing multiple inlined perspectives that vote on findings.

## Decision

The review system uses 21 self-contained review prompts in `governance/prompts/reviews/`, each implementing Anthropic's Parallelization (Voting) pattern. Each prompt file contains:

1. **Purpose and scope** -- what the panel evaluates
2. **Inlined perspective definitions** -- each participant's role, evaluation criteria, and anti-patterns
3. **Scoring formula** -- deterministic confidence calculation with severity deductions
4. **Pass/fail criteria** -- minimum confidence threshold and maximum finding counts
5. **Structured emission example** -- valid JSON matching `governance/schemas/panel-output.schema.json`

Perspectives appearing in two or more panels are canonically defined in `governance/prompts/shared-perspectives.md` for authoring-time DRY. At runtime, each panel is fully self-contained -- no cross-file loading required.

Six panels are mandatory on every PR regardless of files changed: code-review, security-review, threat-modeling, cost-analysis, documentation-review, and data-governance-review. Four of the five policy profiles enforce this full set; the fast-track profile requires only code-review and security-review. See `governance/policy/` for all 5 policy profiles and 18 supporting policy configurations.

## Consequences

### Positive

- Each panel is a single file load -- no multi-file assembly, no cross-reference resolution at runtime
- Perspective diversity is preserved within a single-agent execution model
- The Voting pattern produces naturally varied findings: security perspectives flag different issues than performance perspectives, even on the same code
- Mandatory panels ensure security-critical changes cannot bypass threat modeling via file-pattern gaps
- Structured emissions enable deterministic policy evaluation (see `docs/decisions/001-deterministic-policy-engine.md`)

### Negative

- 21 review prompts produce significant token volume per PR review cycle
- Perspective definitions are duplicated across panels (authoring-time DRY via `shared-perspectives.md`, but runtime copies are inlined)
- Adding a new perspective to multiple panels requires updating each panel file individually

### Neutral

- The 24 shared perspectives in `governance/prompts/shared-perspectives.md` serve as the canonical source of truth but are never loaded at runtime -- this is a deliberate design choice documented in the file header
- Panel pass/fail scoring currently lives in cognitive artifacts (the prompts themselves) rather than the policy engine -- this boundary is an open design question

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| Monolithic review prompt (one prompt covers all concerns) | Exceeds effective prompt length; perspectives compete for attention; no modular panel selection |
| Multi-agent panel execution (one agent per perspective) | Research shows 39-70% sequential degradation; 17.2x error amplification; 3.2x less token-efficient (arXiv:2512.08296) |
| MCP Skills as panel executors | Tool count degradation (49% accuracy at 23-28 tools per Anthropic benchmarks); no MCP infrastructure exists (ADR-003 in README.md); premature optimization for a runtime that does not yet exist |
| Separate persona files loaded per panel | 30-42 tool calls per review (60-84% of budget); cross-file indirection violates Locality of Behaviour; composability was theoretical with zero real usage |

## References

- `governance/prompts/reviews/` -- 21 self-contained review prompts
- `governance/prompts/shared-perspectives.md` -- canonical definitions for 24 cross-panel perspectives
- `governance/schemas/panel-output.schema.json` -- structured emission schema
- `governance/policy/default.yaml` -- mandatory panel list and confidence weighting
- `docs/decisions/README.md` (ADR-006: Mandatory Panels) -- why six panels are always required
- `docs/decisions/README.md` (ADR-010: Self-Contained Prompts over MCP Skills) -- full research evaluation
- `docs/decisions/README.md` (ADR-011: Persona Consolidation) -- implementation details
- `docs/research/README.md` -- 51-source research informing the consolidation decision
