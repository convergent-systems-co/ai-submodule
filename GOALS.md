# Goals and Status — Dark Factory Governance Platform

This document tracks the maturity phases, completed work, and open enhancements for the governance platform. Updated as part of the implementation commit (Step 6.4) and verified during the post-merge retrospective.

## Phase Status

| Phase | Name | Description | Status | Key Deliverables |
|-------|------|-------------|--------|------------------|
| 3 | Agentic Orchestration | Personas, panels, workflows with human gates | **Implemented** | Governance personas and panels, agentic workflows, Code Manager + Coder personas |
| 4a | Policy-Bound Autonomy | Deterministic merge decisions, structured emissions | **Implemented** | Governance CI workflow, structured emissions, run manifests, policy profiles |
| 4b | Autonomous Remediation | Auto-fix, drift detection, remediation loops | **Implemented** | Policy engine runtime; drift detection schemas and policy config (PR #69); auto-remediation schemas and workflow (PR #81); incident-to-DI generation schemas and workflow (PR #87) |
| 5 | Dark Factory | Full automation with runtime feedback and self-evolution | **Phase 5a-5e defined** | Sub-phases decomposed with achievability assessment; see Phase 5 section below |

## Completed Work

### Phase 4a — Policy-Bound Autonomy

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #9 | #28 | Policy engine runtime | Deterministic evaluation engine in Python, integrated into governance CI |
| #10 | #31 | Governance CI workflow | `dark-factory-governance.yml` — detect, evaluate, review |
| #11 | #17 | Instruction decomposition | Composable context units per JIT loading strategy |
| #12 | #18 | Auto-propagation workflow | Submodule update propagation to consuming repos |
| #21 | #24 | AI Expert Review panel | Governance-aware panel triggers |
| #22 | #23 | Fix agentic loop | Full PR monitoring, Copilot review handling, merge lifecycle |

### Agentic Infrastructure

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #34 | #37 | Plan tracking best practices | Plan archival to GitHub Releases, retrospective prompt |
| #35 | #39 | Issue templates | Structured feature request and bug report forms |
| #43 | #44 | Context management enforcement | 3-issue cap, mandatory checkpoints, two-tier capacity thresholds |
| #26 | #29 | Branch naming convention | `itsfwcp/{type}/{number}/{name}` standard |
| #32 | #33 | Issue labeling | Governance labels (refine, blocked, P0-P4, chore, refactor, ci) |
| #48 | #55 | Agentic loop goals fallback | Startup sequence falls back to GOALS.md when no actionable issues remain |

### Documentation & Structure

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #40 | #45 | README and Goals status update | Comprehensive README rewrite, GOALS.md creation |
| #38 | #46 | Filesystem structure collapse | Consolidated 7 top-level directories under `governance/` |
| #36 | #47 | Dark Factory Next Steps | Goals section in README, Developer Quick Guide, GOALS.md cleanup |
| #49 | #52 | Missing panel emissions | Added security-review and ai-expert-review baseline emissions |
| #50 | #57 | Fix persona/panel counts | Corrected counts in CLAUDE.md and governance model doc |
| #56 | #62 | Root-level convenience files | Added startup.md and init.md at repo root for discoverability |
| #59 | #66 | Windows support | PowerShell bootstrap (init.ps1) with dependency checks and symlink/copy fallback |

### Personas and Panels

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #51 | #60 | Panel pass/fail criteria | Standardized scoring, schema, and local override system for all 15 panels |
| #53 | #64 | Evaluate personas and panels | 11 language, 2 platform, 1 LLM personas + Cost Analysis panel (42→57 personas, 15→16 panels) |
| #5 | #13 | Agile Coach persona | Sprint planning, velocity, retrospective guidance |
| #6 | #15 | FinOps group | FinOps Engineer and FinOps Analyst personas |
| #7 | #16 | MITRE Specialist | Threat modeling panel and MITRE ATT&CK mapping |

### Governance Infrastructure

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #68 | #69 | Drift detection schemas and policy config | 2 JSON schemas + 8 YAML policy files for Phase 4b drift detection |
| #71 | #72 | Simplify install with single-command setup | Streamlined bootstrap with venv support |
| #73 | #74 | Issue monitor (local scripts + GitHub Actions) | GitHub Actions workflow + local shell/PowerShell scripts for autonomous issue dispatch |
| #81 | #83 | Auto-remediation loops | 2 JSON schemas (remediation action + verification) + agentic workflow prompt for Phase 4b autonomous remediation |
| #87 | #89 | Incident-to-DI generation | Runtime DI schema, template, and 6-step agentic workflow for Phase 4b |
| #92 | #93 | Backward compatibility enforcement | Breaking change schema + 6-step backward compatibility workflow for Phase 5 |
| #90 | #91 | Template consolidation | Moved plan-template into templates/, updated all references, fixed stale architecture doc paths |
| #80 | #94 | Copilot context management parity | Expanded Copilot detection strategies, Tier 1 instruction module, refine label re-evaluation in startup |

## Open Work

### Needs Refinement

| Issue | Title | Labels | What's Unclear |
|-------|-------|--------|----------------|
| #41 | Agentic Speedup (parallelization) | `enhancement`, `refine` | Platform constraints for parallel agent execution |
| #42 | Agentic Monitor (always-on orchestrator) | `enhancement`, `refine` | Daemon vs. scheduled vs. event-driven architecture |

## Phase 4b — Remaining Work

The following Phase 4b capabilities are designed but not yet implemented:

- [x] **Drift detection** — Schemas and policy configuration files created (PR #69); runtime implementation pending
- [x] **Auto-remediation loops** — Governance artifacts for autonomous drift remediation (PR #81): remediation action schema, verification schema, and agentic workflow prompt
- [x] **Incident-to-DI generation** — Runtime anomalies automatically create Design Intents (PR #87)

## Phase 5 — Dark Factory (Future)

Architecture is documented in `governance/docs/runtime-feedback-architecture.md`.

### Industry Context

The Phase 5 roadmap is informed by industry maturity models for autonomous software delivery — primarily [Dan Shapiro's 5 Levels of Agentic Coding](https://www.linkedin.com/pulse/5-levels-agentic-coding-dan-shapiro/) and the [Mars Shot MSV-CMM](https://www.mars-shot.dev/) capability maturity model. These frameworks describe a progression from AI-assisted coding (Level 1-2) through autonomous orchestration (Level 3-4) to fully self-evolving systems (Level 5). Dark Factory currently operates at Level 3-4 for governance: autonomous issue-to-merge with policy gates, but without runtime self-evolution or multi-agent coordination. The gap between L3-4 and L5 includes capabilities that require runtime infrastructure beyond what a config-only governance repo can provide.

### Completed Phase 5 Prerequisites

- [x] Runtime feedback loop (anomaly → signal → DI → implementation → deploy) — All governance artifacts implemented: schemas (PR #69), policies (PR #69), templates (PR #89), workflows (PR #83, #89), signal adapters (PR #98)
- [x] Backward compatibility enforcement for governance changes (PR #92)
- [x] Autonomy metrics and weekly reporting dashboard — Metrics schema, health thresholds, and weekly report template (PR #100)

### Sub-Phase Decomposition

| Sub-Phase | Name | Achievable Now? | Rationale |
|-----------|------|-----------------|-----------|
| 5a | Self-Proving Systems | Partially | Can create test governance schemas, test-generation panel definition, proof-of-correctness policy. Cannot build runtime test execution — requires consuming repo integration. |
| 5b | Self-Evolution | Yes (governance artifacts) | Retrospective aggregation schema, threshold auto-tuning policy, persona effectiveness scoring schema, governance change proposal workflow. All are config/schema artifacts. |
| 5c | Always-On Orchestration | Partially | GitHub Actions scheduled trigger exists (#74). Cross-session state via checkpoints exists. Missing: event-driven webhook trigger, automatic session resumption from checkpoints. Blocked by Claude Code/Copilot being session-based tools. |
| 5d | Multi-Agent Coordination | Blocked | Requires runtime capable of spawning parallel agent sessions. Current AI tools (Claude Code, Copilot) are single-session. Can define conflict detection schemas and merge sequencing policies, but cannot implement parallel execution. |
| 5e | Spec-Driven Interface | Yes (governance artifacts) | Formal spec schema (richer than GitHub issues), acceptance verification workflow, reduced human touchpoint model. All are config artifacts. |

### 5a — Self-Proving Systems (Partially Achievable)

- [ ] Test governance schema — JSON Schema defining test coverage expectations, mutation testing thresholds, and proof-of-correctness criteria per policy profile
- [ ] Test-generation panel definition — Panel that emits test requirements as structured JSON; consuming repos execute tests via their own CI
- [ ] Proof-of-correctness policy — Policy rules that gate merge on formal verification artifacts (type proofs, property tests, contract checks)

### 5b — Self-Evolution (Achievable — Governance Artifacts)

- [ ] Retrospective aggregation schema — JSON Schema for collecting panel accuracy, false positive rates, and override frequency across runs
- [ ] Threshold auto-tuning policy — Policy that adjusts confidence thresholds based on retrospective data (e.g., lower security threshold after repeated false positives)
- [ ] Persona effectiveness scoring schema — Schema tracking per-persona signal-to-noise ratio, enabling automated persona weight adjustment
- [ ] Governance change proposal workflow — Agentic workflow where the system proposes governance config changes (new thresholds, persona adjustments) for human approval

### 5c — Always-On Orchestration (Partially Achievable)

- [ ] Event-driven webhook trigger — GitHub webhook listener that triggers governance sessions on issue creation, PR events, and deployment status changes
- [ ] Automatic checkpoint resumption — Mechanism to resume agentic sessions from `.checkpoints/` state files after context resets or tool restarts
- [ ] Cross-session state persistence — Schema and storage strategy for maintaining governance context across multiple agentic sessions

> **Blocked by:** Claude Code and GitHub Copilot are session-based tools without persistent daemon capabilities. Scheduled triggers via GitHub Actions (#74) partially address this, but true always-on orchestration requires runtime infrastructure.

### 5d — Multi-Agent Coordination (Blocked)

- [ ] Conflict detection schema — JSON Schema for detecting when multiple agents modify overlapping files or governance state
- [ ] Merge sequencing policy — Policy rules for ordering concurrent agent PRs to avoid conflicts and maintain governance consistency
- [ ] Parallel agent session protocol — Specification for spawning, coordinating, and reconciling multiple concurrent agent sessions

> **Blocked by:** Current AI coding tools (Claude Code, GitHub Copilot) operate as single-session agents. Multi-agent coordination requires a runtime orchestrator capable of spawning parallel sessions, which does not exist in current tooling. Governance schemas can be defined now, but execution is blocked.

### 5e — Spec-Driven Interface (Achievable — Governance Artifacts)

- [ ] Formal spec schema — JSON Schema richer than GitHub issue templates: structured acceptance criteria, dependency declarations, risk pre-classification, and machine-verifiable completion conditions
- [ ] Acceptance verification workflow — Agentic workflow that validates implementation against spec-defined acceptance criteria before triggering review panels
- [ ] Reduced human touchpoint model — Policy profile variant that requires human approval only for policy-override scenarios, with all other decisions fully automated

### Sources

- [Dan Shapiro — 5 Levels of Agentic Coding](https://www.linkedin.com/pulse/5-levels-agentic-coding-dan-shapiro/) — Framework defining progression from AI-assisted to fully autonomous coding
- [Mars Shot — MSV-CMM](https://www.mars-shot.dev/) — Capability maturity model for machine-speed software verification
- [Bessemer Venture Partners — Roadmap to AI Coding Agents](https://www.bvp.com/atlas/roadmap-to-ai-coding-agents) — Autonomy scale for AI coding from autocomplete to full agency
- [Addy Osmani — The 70% Problem: Hard Truths About AI-Assisted Coding](https://addyo.substack.com/p/the-70-problem-hard-truths-about) — Analysis of where AI coding agents stall and what's needed to reach full autonomy
