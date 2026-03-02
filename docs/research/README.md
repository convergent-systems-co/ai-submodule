# Research: Persona Consolidation & Architecture Decisions

**Issue:** #220 — Migrate personas to prompts and agentic updates
**Date:** 2026-02-25
**Status:** Active research — informs all persona/panel architectural decisions

---

## Table of Contents

1. [Research Sources](#1-research-sources)
2. [Terminology Corrections](#2-terminology-corrections)
3. [Anthropic Agent Patterns Applied](#3-anthropic-agent-patterns-applied)
4. [Consolidation vs. Status Quo Analysis](#4-consolidation-vs-status-quo-analysis)
5. [MCP Skills vs. Self-Contained Prompts](#5-mcp-skills-vs-self-contained-prompts)
6. [Multi-Agent Performance Research](#6-multi-agent-performance-research)
7. [Tool Count Scaling Research](#7-tool-count-scaling-research)
8. [Sub-Prompt Decomposition Research](#8-sub-prompt-decomposition-research)
9. [Ralph Wiggum Loop Pattern](#9-ralph-wiggum-loop-pattern)
10. [Decision Matrix](#10-decision-matrix)
11. [Recommended Architecture](#11-recommended-architecture)
12. [Complete Source Index](#12-complete-source-index)

---

## 1. Research Sources

All claims in this document are grounded in peer-reviewed research, official vendor documentation, or recognized industry practitioners. Sources are categorized by authority level.

### Tier 1: Primary Research (Vendor Labs, Peer-Reviewed)

| Source | Author/Org | URL | Key Finding |
|--------|-----------|-----|-------------|
| Building Effective Agents | Anthropic (Schluntz, Zhang) | [anthropic.com](https://www.anthropic.com/research/building-effective-agents) | Voting pattern for code review; "start simple, add complexity only when it demonstrably improves outcomes" |
| Advanced Tool Use | Anthropic Engineering | [anthropic.com](https://www.anthropic.com/engineering/advanced-tool-use) | Opus 4 tool accuracy: 49% without Tool Search, 74% with; tool definitions consume 134K tokens in real deployments |
| Towards a Science of Scaling Agent Systems | Google DeepMind / MIT | [arXiv:2512.08296](https://arxiv.org/abs/2512.08296) | Multi-agent degrades sequential performance by 39-70%; single agents 3.2x more token-efficient; 17.2x error amplification |
| Decomposed Prompting Does Not Fix Knowledge Gaps | arXiv (Feb 2025) | [arxiv.org](https://arxiv.org/html/2602.04853) | Frontier models show diminishing/negative returns from prompt decomposition; consistency only 59.7% on multi-hop |
| Single-Task vs. Multitask Prompts | MDPI Electronics (2024) | [mdpi.com](https://www.mdpi.com/2079-9292/13/23/4712) | No definitive rule favoring decomposition over consolidated prompts; model- and task-dependent |
| Prompt Repetition Improves Accuracy | Google Research | [analyticsvidhya.com](https://www.analyticsvidhya.com/blog/2026/02/prompt-repetition/) | Across 70 comparisons, repetition improved accuracy 47 times, never significantly reduced performance |
| Tool-Space Interference in the MCP Era | Microsoft Research (Nov 2025) | [microsoft.com](https://www.microsoft.com/en-us/research/blog/tool-space-interference-in-the-mcp-era-designing-for-agent-compatibility-at-scale/) | Tool name collisions, semantic overlap degrade agent accuracy; recommendation: "expose as few tools as possible" |
| Effective Harnesses for Long-Running Agents | Anthropic | [anthropic.com](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | Progress should live in files/git, not context; harness decides completion, not the model |
| Writing Tools for Agents | Anthropic | [anthropic.com](https://www.anthropic.com/engineering/writing-tools-for-agents) | Tool design principles for agentic systems |
| Anthropic Cookbook — Agent Patterns | Anthropic | [github.com](https://github.com/anthropics/anthropic-cookbook/tree/main/patterns/agents) | Reference implementations of Voting, Orchestrator-Workers, Evaluator-Optimizer |
| Claude 4 Best Practices | Anthropic | [docs.anthropic.com](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices) | Current-generation prompt engineering guidance |
| Claude Code Security Review | Anthropic | [github.com](https://github.com/anthropics/claude-code-security-review) | Security review patterns for Claude Code |

### Tier 2: Industry Practitioners & Technical Analysis

| Source | Author/Org | URL | Key Finding |
|--------|-----------|-----|-------------|
| Ralph Wiggum Technique | Geoffrey Huntley | [ghuntley.com/ralph](https://ghuntley.com/ralph/) | External validation loop: harness decides completion, not model; stateless resampling |
| Everything is a Ralph Loop | Geoffrey Huntley | [ghuntley.com/loop](https://ghuntley.com/loop/) | All effective agentic patterns reduce to external validation loops |
| Context Engineering | Simon Willison | [simonwillison.net](https://simonwillison.net/2025/jun/27/context-engineering/) | Fill context with the right information for the next step; locality over indirection |
| Locality of Behaviour | Carson Gross (htmx) | [htmx.org](https://htmx.org/essays/locality-of-behaviour/) | Code behavior should be obvious from the unit itself; cross-file references are worst-case LoB violation |
| Skills vs Dynamic MCP Loadouts | Armin Ronacher (Flask creator) | [lucumr.pocoo.org](https://lucumr.pocoo.org/2025/12/13/skills-vs-mcp/) | Skills don't load tool definitions; they provide tips for how to use existing tools more effectively |
| Skills vs MCP Tools for Agents | LlamaIndex | [llamaindex.ai](https://www.llamaindex.ai/blog/skills-vs-mcp-tools-for-agents-when-to-use-what) | Skills = packaged expertise shaping reasoning; tools = external integrations with schema-driven I/O |
| Claude Skills — Token-Efficient Architecture | DEV Community | [dev.to](https://dev.to/jimquote/claude-skills-vs-mcp-complete-guide-to-token-efficient-ai-agent-architecture-4mkf) | Skills report ~50% lower token usage vs MCP tool calling for equivalent domain-expertise tasks |
| Skills Explained | Claude Blog | [claude.com/blog/skills-explained](https://claude.com/blog/skills-explained) | Official explanation of Claude Code skills architecture |
| LLM Powered Autonomous Agents | Lilian Weng | [lilianweng.github.io](https://lilianweng.github.io/posts/2023-06-23-agent/) | Foundational survey of agent architectures |
| Supervising Ralph: Principal Skinner Pattern | Secure Trajectories | [securetrajectories.substack.com](https://securetrajectories.substack.com/p/ralph-wiggum-principal-skinner-agent-reliability) | Without governance constraints, Ralph loops enter sycophancy loops or overbake on impossible tasks |
| Why Your Multi-Agent System is Failing | Towards Data Science | [towardsdatascience.com](https://towardsdatascience.com/why-your-multi-agent-system-is-failing-escaping-the-17x-error-trap-of-the-bag-of-agents/) | 17.2x error amplification in bag-of-agents architectures |
| Stacklok vs Anthropic Tool Search Comparison | DEV Community | [dev.to](https://dev.to/stacklok/stackloks-mcp-optimizer-vs-anthropics-tool-search-tool-a-head-to-head-comparison-2f32) | Tool Search achieved 34% accuracy with 2,792 tools (contradicts Anthropic's optimistic benchmarks) |
| AI Tool Overload: More Tools Mean Worse Performance | Jenova.ai | [jenova.ai](https://www.jenova.ai/en/resources/mcp-tool-scalability-problem) | OpenAI recommends fewer than 20 functions; tools exceeding 20 cause accuracy degradation |
| The MCP Tool Trap | Jentic | [jentic.com](https://jentic.com/blog/the-mcp-tool-trap) | More tools ≠ more capable agents; diminishing returns past tool-count thresholds |
| Optimizing Tool Calling | Paragon | [useparagon.com](https://www.useparagon.com/learn/rag-best-practices-optimizing-tool-calling/) | Tool correctness is model-specific and fragile across Claude model updates |
| How to Scale MCP to 100+ Tools | apxml | [apxml.com](https://apxml.com/posts/scaling-mcp-with-tool-rag) | Strategies for large tool sets, confirming degradation baseline |

### Tier 3: Standards & Compliance

| Source | Author/Org | URL | Key Finding |
|--------|-----------|-----|-------------|
| LLM01:2025 Prompt Injection | OWASP | [genai.owasp.org](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) | Prompt injection is #1 vulnerability; "prompt injection loop" is security terminology, not workflow |
| Prompt Injection Attacks Review | MDPI/Information | [mdpi.com](https://www.mdpi.com/2078-2489/17/1/54) | Comprehensive review of injection attack vectors |
| NIST AI RMF 2025 | NIST/IS Partners | [ispartnersllc.com](https://www.ispartnersllc.com/blog/nist-ai-rmf-2025-updates-what-you-need-to-know-about-the-latest-framework-changes/) | AI risk management framework; audit requirements for AI decisions |
| NIST SP 800-53 R5 | NIST | [csrc.nist.gov](https://csrc.nist.gov/news/2025) | Security and privacy controls; requires decision rationale, not file-level traceability |
| EU AI Act Compliance | Label Studio, THRON | [labelstud.io](https://labelstud.io/blog/operationalizing-compliance-with-the-eu-ai-act-s-high-risk-requirements/) | EU AI Act requirements for high-risk AI systems |

### Tier 4: Supplementary & Commentary

| Source | Author/Org | URL |
|--------|-----------|-----|
| Prompt Chaining Guide | Prompt Engineering Guide | [promptingguide.ai](https://www.promptingguide.ai/techniques/prompt_chaining) |
| Role Prompting Research | PromptHub | [prompthub.us](https://www.prompthub.us/blog/role-prompting-does-adding-personas-to-your-prompts-really-make-a-difference) |
| AI Agent Persona via LLM Prompts | The New Stack | [thenewstack.io](https://thenewstack.io/how-to-define-an-ai-agent-persona-by-tweaking-llm-prompts/) |
| System Prompt Best Practices | The Agent Architect | [theagentarchitect.substack.com](https://theagentarchitect.substack.com/p/4-tips-writing-system-prompts-ai-agents-work) |
| Prompt Chaining for AI Agents | NivaLabs AI | [medium.com](https://medium.com/@nivalabs.ai/prompt-chaining-for-the-ai-agents-modular-reliable-and-scalable-workflows-a22d15fd5d33) |
| Ralph Wiggum Loop Costs | Towards AI | [pub.towardsai.net](https://pub.towardsai.net/the-ralph-wiggum-loop-how-developers-are-cutting-ai-costs-by-99-aad1109874d9) |
| Mastering Ralph Loops | LinearB | [linearb.io](https://linearb.io/blog/ralph-loop-agentic-engineering-geoffrey-huntley) |
| 2026 — Year of the Ralph Loop Agent | DEV Community | [dev.to](https://dev.to/alexandergekov/2026-the-year-of-the-ralph-loop-agent-1gkj) |
| Inventing the Ralph Wiggum Loop | Dev Interrupted | [devinterrupted.substack.com](https://devinterrupted.substack.com/p/inventing-the-ralph-wiggum-loop-creator) |
| Building Effective Agents (summary) | Simon Willison | [simonwillison.net](https://simonwillison.net/2024/Dec/20/building-effective-agents/) |
| Design Patterns for Agentic Workflows | HuggingFace | [huggingface.co](https://huggingface.co/blog/dcarpintero/design-patterns-for-building-agentic-workflows) |
| Practical Guide to Building Agents | OpenAI | [openai.com](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/) |
| MCP Specification | Model Context Protocol | [modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-11-25) |
| Google Explores Scaling Principles | InfoQ | [infoq.com](https://www.infoq.com/news/2026/02/google-agent-scaling-principles/) |
| Chain Complex Prompts | Anthropic Docs | [docs.anthropic.com](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-prompts) |
| Unleashing Prompt Engineering Potential | ScienceDirect | [sciencedirect.com](https://www.sciencedirect.com/science/article/pii/S2666389925001084) |

---

## 2. Terminology Corrections

Issue #220 originally stated: *"The Governance workflow transitions to a prompt injection loop."*

**"Prompt injection" is a security vulnerability (OWASP #1 for LLM Applications), not a workflow pattern.** The correct terms:

| Issue Term | Correct Term | Definition | Source |
|-----------|-------------|------------|--------|
| "Prompt injection loop" | **Prompt chaining** | Sequential subtasks where output feeds the next | Anthropic, Prompt Engineering Guide |
| "Prompt injection loop" | **Ralph Wiggum Loop** | External validation loop with stateless resampling | Geoffrey Huntley |
| "Prompt injection loop" | **Evaluator-Optimizer** | Generate → evaluate → iterate until criteria met | Anthropic Cookbook |

**Resolution:** Term corrected to "prompt chaining loop" in the issue body.

---

## 3. Anthropic Agent Patterns Applied

Anthropic identifies five workflow patterns. Mapping to the governance pipeline:

| Pattern | Definition | Governance Equivalent | Status |
|---------|-----------|----------------------|--------|
| **Prompt Chaining** | Sequential subtasks, output feeds next | Workflow phases (FEAT-1 → FEAT-2 → ...) | Already used |
| **Routing** | Classify input, route to specialist | Policy profile selection (default, fin_pii_high, etc.) | Already used |
| **Parallelization (Voting)** | Same task, multiple prompts, aggregate | Panels with persona perspectives | **Key pattern for consolidation** |
| **Parallelization (Sectioning)** | Independent subtasks in parallel | Running code-review + security-review simultaneously | Should adopt |
| **Orchestrator-Workers** | Central LLM delegates dynamically | Code Manager → Coder delegation | Already used |
| **Evaluator-Optimizer** | Generate → evaluate → loop | PR review cycles | Already used |

Anthropic explicitly endorses the governance use case:

> *"You can use voting when reviewing a piece of code for vulnerabilities, where several different prompts review and flag the code if they find a problem."* — Building Effective Agents

The consolidated review prompts implement this Voting pattern directly.

---

## 4. Consolidation vs. Status Quo Analysis

### Counter-arguments evaluated

| Claim | Assessment | Verdict |
|-------|-----------|---------|
| **Single source of truth prevents drift** | Valid risk, but `shared-perspectives.md` addresses it. Locality of Behaviour (Carson Gross) favors inline definitions. | Consolidate with shared-perspectives.md |
| **Audit traceability from emissions** | NIST/SOC2/PCI-DSS require decision traceability, not file-path traceability. `findings[].persona` uses string labels, not file paths. | Not blocked by consolidation |
| **Consuming repo composability** | Theoretical — no mechanism exists for custom panel compositions. 19 personas appear in only 1 panel. | Not exercised; consolidation doesn't prevent future composability |
| **Phase 5 multi-agent justifies current architecture** | Contradicted by Anthropic ("add complexity only when it demonstrably improves outcomes") and Google DeepMind (multi-agent degrades sequential performance by 39-70%). | Premature abstraction |
| **Context cost solved by JIT loading** | Partially true, but 30-42 tool calls per PR review consumes 60-84% of the tool call budget. | Self-contained prompts eliminate tool call overhead |
| **File count is misleading** | Valid for frequently-changed files, but governance artifacts change as a unit, not individually. | Consolidated files match change patterns |
| **Per-persona emission fidelity** | **Strongest counter-argument.** Per-persona findings enable weighted aggregation and effectiveness tracking. | Constraint on consolidation: must preserve per-persona emission structure |

### Decision matrix

| Aspect | Status Quo (60 files) | Consolidation (19 prompts) | Winner |
|--------|----------------------|---------------------------|--------|
| Context efficiency | 30-42 tool calls/PR | 6 file reads/PR | **Consolidation** |
| Duplication risk | None (single source) | Managed via shared-perspectives.md | **Consolidation** |
| Audit traceability | File path → emission | Section header → emission | **Equivalent** |
| Phase 5 readiness | Persona fragments | Full agent system prompts | **Consolidation** |
| Anthropic alignment | Contradicts "start simple" | Matches Voting pattern | **Consolidation** |
| Ralph Loop compatibility | Requires file-chasing | Self-contained per iteration | **Consolidation** |
| Schema compliance | Preserved | Preserved | **Equivalent** |

---

## 5. MCP Skills vs. Self-Contained Prompts

An external review report (2026-02-25) proposed converting high-reuse personas into MCP Skills registered as tools like `skill_security_auditor`, with panels becoming orchestrator+sub-prompt trees distributed via the awesome-dach-copilot MCP server.

### Research verdict: Self-contained prompts are superior for this use case.

| Criterion | MCP Skills / Tools | Self-Contained Prompts | Research Winner |
|-----------|-------------------|----------------------|-----------------|
| Token efficiency | 400-500 tokens/tool definition + discovery overhead | Zero tool overhead | **Self-contained** |
| Accuracy at scale | Degrades past 20 tools (Anthropic, Microsoft, OpenAI) | No tool-count dependency | **Self-contained** |
| Frontier model performance | Decomposition shows diminishing/negative returns (arXiv 2025) | Single-prompt Voting matches Anthropic recommendation | **Self-contained** |
| Multi-agent overhead | 3.2x less efficient per token (Google DeepMind) | Single-agent baseline efficiency | **Self-contained** |
| Sequential task degradation | 39-70% degradation (Google DeepMind) | No degradation (single context) | **Self-contained** |
| Error propagation | 17.2x amplification with independent agents | Single context, no propagation | **Self-contained** |
| Audit traceability | Unchanged (`findings[].persona`) | Unchanged (`findings[].persona`) | **Equivalent** |
| Phase 5 readiness | Must be re-architected | Prompts become agent system prompts directly | **Self-contained** |

### Why MCP Skills don't fit

1. **Skills ≠ Tools.** Anthropic defines Skills as "the recipe" — markdown instructions an agent reads and follows. Skills don't execute anything. Self-contained review prompts already ARE skills in Anthropic's terminology. Registering them as MCP tools adds infrastructure without benefit.

2. **Tool count budget exceeded.** 15-20 persona-skills + Claude Code's existing tools = 23-28 total tools. Anthropic's Opus 4 drops to 49% accuracy with large tool libraries (recovers to only 74% with Tool Search). Microsoft Research recommends "expose as few tools as possible."

3. **No infrastructure exists.** Dark Factory Governance deliberately removed MCP server code (commit b636ebd) with rationale "MCP configs belong in consuming repos." Zero skill files, zero awesome-dach-copilot references exist in the codebase.

4. **Two-repo coordination cost.** Splitting cognitive (dach-copilot) and enforcement (Dark Factory Governance) layers creates version drift risk. Breaking changes to `panel-output.schema.json` require coordinated releases across repos.

### When MCP Skills would make sense

If governance personas need to be invoked by **external agents or third-party MCP clients** without filesystem access to the governance repo. This is a legitimate Phase 5 requirement but is not the current operating model.

---

## 6. Multi-Agent Performance Research

### Google DeepMind / MIT: "Towards a Science of Scaling Agent Systems" (Dec 2025)

180 agent configurations tested across multiple benchmarks. Key findings:

| Metric | Single Agent | Centralized Multi-Agent | Ratio |
|--------|-------------|------------------------|-------|
| Tasks per 1,000 tokens | 67 | 21 | **3.2x single-agent advantage** |
| Sequential task performance | Baseline | -39% to -70% degradation | Multi-agent hurts |
| Error amplification | Baseline | 17.2x | Independent agents amplify errors |

**The "45% Rule":** If a single agent solves more than 45% of a task correctly, multi-agent systems are usually not worth it. Current single-prompt panels already exceed this threshold.

**Implication for governance:** Panel reviews are sequential reasoning tasks — evaluating code against criteria, checking for vulnerabilities, assessing performance. This is precisely the category where multi-agent showed the worst degradation.

### Anthropic's guidance

> *"Start with simple prompts, optimize them with comprehensive evaluation, and add multi-step agentic systems only when simpler solutions fall short."*

> *"Consider adding complexity only when it demonstrably improves outcomes."*

---

## 7. Tool Count Scaling Research

### Documented thresholds

| Source | Finding |
|--------|---------|
| **OpenAI** | Recommends "fewer than 20 functions at any one time" |
| **Anthropic** | Opus 4: 49% accuracy with large tool library → 74% with Tool Search mitigation |
| **Anthropic** | Opus 4.5: 79.5% → 88.1% with Tool Search (still 12% failure) |
| **Microsoft Research** | Tool name collisions and semantic overlap degrade accuracy; "expose as few tools as possible" |
| **Stacklok (independent)** | Tool Search achieved only 34% accuracy with 2,792 tools (contradicts Anthropic's optimistic benchmarks) |

### Token overhead

At ~400-500 tokens per tool definition, 25 tools consume 10,000-12,500 tokens before any conversation begins. In a governance session with 80% context hard-stop, this is a meaningful fraction of available context.

### Implication

Adding 15-20 persona-skills on top of Claude Code's existing tools (Bash, Read, Write, Edit, Grep, Glob, WebSearch, etc.) pushes total tool count past the documented 20-tool degradation threshold.

---

## 8. Sub-Prompt Decomposition Research

### Frontier model findings

arXiv (Feb 2025) — "Decomposed Prompting Does Not Fix Knowledge Gaps":
- Smaller models (≤70B) benefit from decomposition
- **Frontier models show diminishing or negative returns**
- Consistency on multi-hop benchmarks reached only 59.7%

### Error propagation risk

ScienceDirect (2025): *"Errors in early-stage subtasks can propagate downstream, compounding inaccuracies and complicating root-cause analysis."*

### Implication for orchestrator → sub-prompt pattern

The proposed orchestrator → 5 sub-prompts → consolidation pattern creates:
- 7 files per panel instead of 1
- 5 inter-step boundaries where errors can propagate
- Loss of shared evaluation context (each sub-prompt runs independently)
- No benefit on frontier models where the governance pipeline operates

---

## 9. Ralph Wiggum Loop Pattern

### What it is

The Ralph Wiggum Loop (Geoffrey Huntley, mid-2025) is an iterative pattern:
1. Agent runs against a task
2. External checks (tests, linters, schema validators) determine success/failure
3. On failure, agent receives task again with **fresh context**
4. Progress lives in **files and git**, not in the context window
5. The harness (not the model) decides when work is complete

### How it applies to governance

The current governance loop (startup.md) partially implements this:
- External checks: CI, Copilot recommendations, panel emissions
- Iteration: Max 3 review cycles per PR
- Progress in git: Branch commits, plan files, emissions on disk

**What's missing:** The current loop relies on agent self-assessment. The Ralph pattern would have the harness (Stop hook) reinject governance tasks until all external validators pass.

### Integration opportunity (separate from consolidation)

Wrap governance review in a Ralph loop using Claude Code Stop hooks:
1. **Task:** Review PR against required panels
2. **External validators:** Schema validation, policy engine, CI checks
3. **Loop condition:** All validators pass OR max iterations reached
4. **Fresh context per iteration:** Self-contained review prompts make this possible

This is a **separate follow-up issue**, independent of the consolidation work.

---

## 10. Decision Matrix

| Decision | Choice | Research Basis |
|----------|--------|---------------|
| Consolidate personas into review prompts? | **Yes** | Anthropic Voting pattern, Google DeepMind efficiency data, Locality of Behaviour |
| Use MCP Skills instead of markdown prompts? | **No** | Tool count degradation (Anthropic, Microsoft, OpenAI), Skills ≠ Tools distinction, no infrastructure exists |
| Build orchestrator → sub-prompt decomposition? | **No** | Frontier model decomposition research (arXiv), error propagation risk, no accuracy benefit |
| Build multi-agent runtime now? | **No** | Google DeepMind 39-70% degradation, Anthropic "add complexity only when it improves outcomes" |
| Preserve per-persona emission structure? | **Yes** | Strongest counter-argument; enables weighted aggregation and effectiveness tracking |
| Use shared-perspectives.md for DRY? | **Yes** | Addresses duplication drift; authoring-time DRY with runtime locality |
| Integrate Ralph Wiggum Loop? | **Separate issue** | Independent of consolidation; requires Stop hook implementation |
| Select framework (LangGraph/CrewAI/AutoGen)? | **Defer** | Anthropic: "Frameworks obscure prompts and add unnecessary complexity" |

---

## 11. Recommended Architecture

### Implemented (Issue #220)

1. **19 self-contained review prompts** in `governance/prompts/reviews/` — Anthropic's Voting pattern with inline perspective sections
2. **`shared-perspectives.md`** — Canonical definitions for 19 perspectives appearing in 2+ panels (authoring-time DRY)
3. **Per-persona emission structure preserved** — `findings[].persona` labels unchanged
4. **Workflow references updated** — All 7 workflow files + startup.md point to new prompts
5. **Deprecation notices** — 77 files (58 personas + 19 panels) marked deprecated; agentic personas excluded (4 at the time of #220; now 6 after Project Manager #464 and IaC Engineer additions)

### Deferred

- **Ralph Wiggum Loop integration** — Separate follow-up issue (requires Stop hook implementation)
- **True multi-agent runtime** — Deferred per Google DeepMind/Anthropic research
- **MCP Skills conversion** — Not justified for current use case (personas are reasoning roles, not external integrations)
- **Framework selection** — Deferred per Anthropic guidance against premature framework adoption

---

## 12. Complete Source Index

All research sources cited in this document, alphabetically by organization:

| # | Organization | Title | URL |
|---|-------------|-------|-----|
| 1 | Anthropic | Building Effective Agents | [Link](https://www.anthropic.com/research/building-effective-agents) |
| 2 | Anthropic | Advanced Tool Use | [Link](https://www.anthropic.com/engineering/advanced-tool-use) |
| 3 | Anthropic | Effective Harnesses for Long-Running Agents | [Link](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) |
| 4 | Anthropic | Writing Tools for Agents | [Link](https://www.anthropic.com/engineering/writing-tools-for-agents) |
| 5 | Anthropic | Agent Patterns Cookbook | [Link](https://github.com/anthropics/anthropic-cookbook/tree/main/patterns/agents) |
| 6 | Anthropic | Claude 4 Best Practices | [Link](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices) |
| 7 | Anthropic | Claude Code Security Review | [Link](https://github.com/anthropics/claude-code-security-review) |
| 8 | Anthropic | Chain Complex Prompts | [Link](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-prompts) |
| 9 | Anthropic | Code Execution with MCP | [Link](https://www.anthropic.com/engineering/code-execution-with-mcp) |
| 10 | apxml | How to Scale MCP to 100+ Tools | [Link](https://apxml.com/posts/scaling-mcp-with-tool-rag) |
| 11 | arXiv | Decomposed Prompting Does Not Fix Knowledge Gaps | [Link](https://arxiv.org/html/2602.04853) |
| 12 | Carson Gross | Locality of Behaviour | [Link](https://htmx.org/essays/locality-of-behaviour/) |
| 13 | Claude Blog | Skills Explained | [Link](https://claude.com/blog/skills-explained) |
| 14 | DEV Community | Claude Skills vs MCP (Token Efficiency) | [Link](https://dev.to/jimquote/claude-skills-vs-mcp-complete-guide-to-token-efficient-ai-agent-architecture-4mkf) |
| 15 | DEV Community | 2026 — Year of the Ralph Loop Agent | [Link](https://dev.to/alexandergekov/2026-the-year-of-the-ralph-loop-agent-1gkj) |
| 16 | Dev Interrupted | Inventing the Ralph Wiggum Loop | [Link](https://devinterrupted.substack.com/p/inventing-the-ralph-wiggum-loop-creator) |
| 17 | Geoffrey Huntley | Ralph Wiggum Technique | [Link](https://ghuntley.com/ralph/) |
| 18 | Geoffrey Huntley | Everything is a Ralph Loop | [Link](https://ghuntley.com/loop/) |
| 19 | Google DeepMind / MIT | Towards a Science of Scaling Agent Systems | [Link](https://arxiv.org/abs/2512.08296) |
| 20 | Google Research | Prompt Repetition Improves Accuracy | [Link](https://www.analyticsvidhya.com/blog/2026/02/prompt-repetition/) |
| 21 | Google Research Blog | Scaling Agent Systems (Blog) | [Link](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/) |
| 22 | HuggingFace | Design Patterns for Agentic Workflows | [Link](https://huggingface.co/blog/dcarpintero/design-patterns-for-building-agentic-workflows) |
| 23 | InfoQ | Google Explores Scaling Principles | [Link](https://www.infoq.com/news/2026/02/google-agent-scaling-principles/) |
| 24 | Jenova.ai | AI Tool Overload | [Link](https://www.jenova.ai/en/resources/mcp-tool-scalability-problem) |
| 25 | Jentic | The MCP Tool Trap | [Link](https://jentic.com/blog/the-mcp-tool-trap) |
| 26 | Label Studio | EU AI Act Compliance | [Link](https://labelstud.io/blog/operationalizing-compliance-with-the-eu-ai-act-s-high-risk-requirements/) |
| 27 | Lilian Weng | LLM Powered Autonomous Agents | [Link](https://lilianweng.github.io/posts/2023-06-23-agent/) |
| 28 | LinearB | Mastering Ralph Loops | [Link](https://linearb.io/blog/ralph-loop-agentic-engineering-geoffrey-huntley) |
| 29 | LlamaIndex | Skills vs MCP Tools for Agents | [Link](https://www.llamaindex.ai/blog/skills-vs-mcp-tools-for-agents-when-to-use-what) |
| 30 | Lucumr (Armin Ronacher) | Skills vs Dynamic MCP Loadouts | [Link](https://lucumr.pocoo.org/2025/12/13/skills-vs-mcp/) |
| 31 | MCP Specification | Model Context Protocol v2025-11-25 | [Link](https://modelcontextprotocol.io/specification/2025-11-25) |
| 32 | MDPI Electronics | Single-Task vs. Multitask Prompts | [Link](https://www.mdpi.com/2079-9292/13/23/4712) |
| 33 | MDPI Information | Prompt Injection Attacks Review | [Link](https://www.mdpi.com/2078-2489/17/1/54) |
| 34 | Microsoft Research | Tool-Space Interference in the MCP Era | [Link](https://www.microsoft.com/en-us/research/blog/tool-space-interference-in-the-mcp-era-designing-for-agent-compatibility-at-scale/) |
| 35 | NIST | AI RMF 2025 Updates | [Link](https://www.ispartnersllc.com/blog/nist-ai-rmf-2025-updates-what-you-need-to-know-about-the-latest-framework-changes/) |
| 36 | NIST | SP 800-53 R5 | [Link](https://csrc.nist.gov/news/2025) |
| 37 | NivaLabs AI | Prompt Chaining for AI Agents | [Link](https://medium.com/@nivalabs.ai/prompt-chaining-for-the-ai-agents-modular-reliable-and-scalable-workflows-a22d15fd5d33) |
| 38 | OpenAI | Practical Guide to Building Agents | [Link](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/) |
| 39 | OWASP | LLM01:2025 Prompt Injection | [Link](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) |
| 40 | Paragon | Optimizing Tool Calling | [Link](https://www.useparagon.com/learn/rag-best-practices-optimizing-tool-calling/) |
| 41 | Prompt Engineering Guide | Prompt Chaining | [Link](https://www.promptingguide.ai/techniques/prompt_chaining) |
| 42 | PromptHub | Role Prompting Research | [Link](https://www.prompthub.us/blog/role-prompting-does-adding-personas-to-your-prompts-really-make-a-difference) |
| 43 | ScienceDirect | Unleashing Prompt Engineering Potential | [Link](https://www.sciencedirect.com/science/article/pii/S2666389925001084) |
| 44 | Secure Trajectories | Supervising Ralph: Principal Skinner Pattern | [Link](https://securetrajectories.substack.com/p/ralph-wiggum-principal-skinner-agent-reliability) |
| 45 | Simon Willison | Context Engineering | [Link](https://simonwillison.net/2025/jun/27/context-engineering/) |
| 46 | Simon Willison | Building Effective Agents (summary) | [Link](https://simonwillison.net/2024/Dec/20/building-effective-agents/) |
| 47 | Stacklok | MCP Optimizer vs Anthropic Tool Search | [Link](https://dev.to/stacklok/stackloks-mcp-optimizer-vs-anthropics-tool-search-tool-a-head-to-head-comparison-2f32) |
| 48 | The Agent Architect | System Prompt Best Practices | [Link](https://theagentarchitect.substack.com/p/4-tips-writing-system-prompts-ai-agents-work) |
| 49 | The New Stack | AI Agent Persona via LLM Prompts | [Link](https://thenewstack.io/how-to-define-an-ai-agent-persona-by-tweaking-llm-prompts/) |
| 50 | Towards AI | Ralph Wiggum Loop Costs | [Link](https://pub.towardsai.net/the-ralph-wiggum-loop-how-developers-are-cutting-ai-costs-by-99-aad1109874d9) |
| 51 | Towards Data Science | Why Your Multi-Agent System is Failing | [Link](https://towardsdatascience.com/why-your-multi-agent-system-is-failing-escaping-the-17x-error-trap-of-the-bag-of-agents/) |
