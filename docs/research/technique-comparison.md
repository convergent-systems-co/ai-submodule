# Technique Comparison: Persona Consolidation & Agentic Loop Conversion

**Issue:** #220 — Migrate personas to prompts and agentic updates
**Date:** 2026-02-25
**Purpose:** Ground all design decisions in trusted sources before implementation, per the issue's Goals and Anti-Pattern.

---

## Research Sources

All claims in this document are grounded in the following trusted sources:

| Source | Author/Org | URL |
|--------|-----------|-----|
| Building Effective Agents | Anthropic (Erik Schluntz, Barry Zhang) | [anthropic.com/research/building-effective-agents](https://www.anthropic.com/research/building-effective-agents) |
| Effective Harnesses for Long-Running Agents | Anthropic | [anthropic.com/engineering/effective-harnesses-for-long-running-agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) |
| Writing Tools for Agents | Anthropic | [anthropic.com/engineering/writing-tools-for-agents](https://www.anthropic.com/engineering/writing-tools-for-agents) |
| Anthropic Cookbook — Agent Patterns | Anthropic | [github.com/anthropics/anthropic-cookbook/tree/main/patterns/agents](https://github.com/anthropics/anthropic-cookbook/tree/main/patterns/agents) |
| Ralph Wiggum Technique | Geoffrey Huntley | [ghuntley.com/ralph](https://ghuntley.com/ralph/) |
| Everything is a Ralph Loop | Geoffrey Huntley | [ghuntley.com/loop](https://ghuntley.com/loop/) |
| Supervising Ralph: Principal Skinner Pattern | Secure Trajectories | [securetrajectories.substack.com](https://securetrajectories.substack.com/p/ralph-wiggum-principal-skinner-agent-reliability) |
| Inventing the Ralph Wiggum Loop | Dev Interrupted (Huntley interview) | [devinterrupted.substack.com](https://devinterrupted.substack.com/p/inventing-the-ralph-wiggum-loop-creator) |
| 2026 — The Year of the Ralph Loop Agent | DEV Community | [dev.to/alexandergekov](https://dev.to/alexandergekov/2026-the-year-of-the-ralph-loop-agent-1gkj) |
| Prompt Chaining Guide | Prompt Engineering Guide | [promptingguide.ai/techniques/prompt_chaining](https://www.promptingguide.ai/techniques/prompt_chaining) |
| LLM01:2025 Prompt Injection | OWASP | [genai.owasp.org/llmrisk/llm01-prompt-injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) |
| Prompt Injection Attacks Review | MDPI/Information | [mdpi.com/2078-2489/17/1/54](https://www.mdpi.com/2078-2489/17/1/54) |
| NIST AI RMF 2025 Updates | NIST/IS Partners | [ispartnersllc.com](https://www.ispartnersllc.com/blog/nist-ai-rmf-2025-updates-what-you-need-to-know-about-the-latest-framework-changes/) |
| NIST SP 800-53 R5 | NIST | [csrc.nist.gov](https://csrc.nist.gov/news/2025) |
| Locality of Behaviour | Carson Gross (htmx) | [htmx.org/essays/locality-of-behaviour](https://htmx.org/essays/locality-of-behaviour/) |
| Prompt Repetition Improves Accuracy | Google Research / Analytics Vidhya | [analyticsvidhya.com](https://www.analyticsvidhya.com/blog/2026/02/prompt-repetition/) |
| Context Engineering | Simon Willison | [simonwillison.net](https://simonwillison.net/2025/jun/27/context-engineering/) |
| Scaling Agent Systems | Google DeepMind / MIT | [research.google](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/) |
| Practical Guide to Building Agents | OpenAI | [openai.com](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/) |
| EU AI Act Compliance | Label Studio, THRON | [labelstud.io](https://labelstud.io/blog/operationalizing-compliance-with-the-eu-ai-act-s-high-risk-requirements/) |
| Claude Code Security Review | Anthropic | [github.com/anthropics/claude-code-security-review](https://github.com/anthropics/claude-code-security-review) |
| Claude 4 Best Practices | Anthropic | [docs.anthropic.com](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices) |
| LLM Powered Autonomous Agents | Lilian Weng | [lilianweng.github.io](https://lilianweng.github.io/posts/2023-06-23-agent/) |
| Role Prompting Research | PromptHub | [prompthub.us/blog/role-prompting](https://www.prompthub.us/blog/role-prompting-does-adding-personas-to-your-prompts-really-make-a-difference) |
| AI Agent Persona via LLM Prompts | The New Stack | [thenewstack.io](https://thenewstack.io/how-to-define-an-ai-agent-persona-by-tweaking-llm-prompts/) |
| System Prompt Best Practices | The Agent Architect | [theagentarchitect.substack.com](https://theagentarchitect.substack.com/p/4-tips-writing-system-prompts-ai-agents-work) |
| Prompt Chaining for AI Agents | NivaLabs AI | [medium.com/@nivalabs.ai](https://medium.com/@nivalabs.ai/prompt-chaining-for-the-ai-agents-modular-reliable-and-scalable-workflows-a22d15fd5d33) |
| Ralph Wiggum Loop Costs | Towards AI | [pub.towardsai.net](https://pub.towardsai.net/the-ralph-wiggum-loop-how-developers-are-cutting-ai-costs-by-99-aad1109874d9) |
| Mastering Ralph Loops | LinearB | [linearb.io](https://linearb.io/blog/ralph-loop-agentic-engineering-geoffrey-huntley) |
| Building Effective Agents (Simon Willison summary) | Simon Willison | [simonwillison.net](https://simonwillison.net/2024/Dec/20/building-effective-agents/) |
| Design Patterns for Agentic Workflows | HuggingFace | [huggingface.co/blog/dcarpintero/design-patterns-for-building-agentic-workflows](https://huggingface.co/blog/dcarpintero/design-patterns-for-building-agentic-workflows) |

---

## 1. Terminology Conflict: "Prompt Injection Loop"

### Issue #220 Goal #4 states:
> "The Governance workflow transitions to a prompt injection loop."

### Research finding — CONFLICT DETECTED:

**"Prompt injection" is exclusively a security vulnerability, not a workflow pattern.** Per OWASP's 2025 Top 10 for LLM Applications, prompt injection is the #1 critical vulnerability, appearing in over 73% of production AI deployments assessed during security audits. It refers to manipulating an LLM's instruction-following logic for malicious purposes.

The correct terms for what the issue describes are:

| Issue Term | Correct Term | Definition | Source |
|-----------|-------------|------------|--------|
| "Prompt injection loop" | **Prompt chaining** | Breaking tasks into sequential subtasks where each step's output feeds the next | [Anthropic](https://www.anthropic.com/research/building-effective-agents), [Prompt Engineering Guide](https://www.promptingguide.ai/techniques/prompt_chaining) |
| "Prompt injection loop" | **Ralph Wiggum Loop** | External validation loop that re-injects task prompts until external criteria pass | [Geoffrey Huntley](https://ghuntley.com/ralph/) |
| "Prompt injection loop" | **Evaluator-Optimizer** | One LLM generates, another evaluates, loop until criteria met | [Anthropic Cookbook](https://github.com/anthropics/anthropic-cookbook/tree/main/patterns/agents) |

**Recommendation:** Replace "prompt injection loop" with the correct term based on which pattern is intended. Using security vulnerability terminology for a workflow pattern creates confusion and could trigger security tooling false positives.

---

## 2. Ralph Wiggum Loop — The Missing Pattern

### What it is

The Ralph Wiggum Loop (coined by Geoffrey Huntley, mid-2025) is an iterative pattern where:
1. An AI agent runs against a task
2. External checks (tests, linters, schema validators) determine success/failure
3. On failure, the agent receives the task again with fresh context
4. Progress lives in **files and git**, not in the context window
5. The harness (not the model) decides when work is complete

Anthropic formalized this into an official Claude Code plugin (December 2025) using Stop Hooks.

### How it applies to governance

The current governance loop (startup.md) already partially implements a Ralph Wiggum pattern:
- External checks: CI checks, Copilot recommendations, panel emissions
- Iteration: Max 3 review cycles per PR
- Progress in git: Branch commits, plan files, panel emissions on disk

**What's missing:** The current loop relies on the agent's self-assessment to decide what to do next. The Ralph pattern would have the harness (bash script / Stop hook) reinject the governance task until all external validators pass.

### Key principle from Huntley

> "Instead of asking the model when it's done, the harness decides."

This directly addresses Issue #220 Goal #1: *"ensure that an agentic loop continues without human intervention."*

### Risk: "Principal Skinner" governance concern

From [Secure Trajectories](https://securetrajectories.substack.com/p/ralph-wiggum-principal-skinner-agent-reliability): *"If Ralph Wiggum represents the tireless engine of agentic work, builders must implement a Principal Skinner harness as a deterministic control plane."*

Without governance constraints, Ralph loops can:
- Enter "sycophancy loops" where the model overrides safety to fulfill completion promises
- "Overbake" on impossible tasks
- Consume unbounded API costs

**The governance framework's existing policy engine IS the Principal Skinner.** This is a natural fit.

---

## 3. Anthropic's Agent Patterns — Which Apply

Anthropic identifies five workflow patterns and autonomous agents. Here's how each maps to the governance pipeline:

| Pattern | Anthropic Definition | Current Governance Equivalent | Applicable? |
|---------|---------------------|------------------------------|-------------|
| **Prompt Chaining** | Sequential subtasks, output feeds next | Workflow phases (FEAT-1 → FEAT-2 → ...) | Already used |
| **Routing** | Classify input, route to specialist | Policy profile selection (default, fin_pii_high, etc.) | Already used |
| **Parallelization (Voting)** | Same task, multiple prompts, aggregate | Panels with multiple persona perspectives | **Key pattern** |
| **Parallelization (Sectioning)** | Independent subtasks in parallel | Running code-review + security-review simultaneously | **Should adopt** |
| **Orchestrator-Workers** | Central LLM delegates dynamically | Tech Lead → Coder delegation | Already used |
| **Evaluator-Optimizer** | Generate → evaluate → loop | PR review cycles (implement → check → fix) | Already used |

### Critical finding: Parallelization Voting

Anthropic explicitly calls out the governance use case:

> *"You can use voting when reviewing a piece of code for vulnerabilities, where several different prompts review and flag the code if they find a problem."* — [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)

This is exactly what panels do. Each persona in a panel is a "vote" from a different perspective. The current implementation runs them sequentially in one context. Anthropic's pattern runs them in parallel with aggregation.

### What Anthropic says about adding complexity

> *"Start with simple prompts, optimize them with comprehensive evaluation, and add multi-step agentic systems only when simpler solutions fall short."*

> *"Consider adding complexity only when it demonstrably improves outcomes."*

This is critical for evaluating Part 2 of the issue (true multi-agent conversion).

---

## 4. Compare and Contrast: Consolidation vs. Status Quo

### Counter-Argument Claim 1: "Single source of truth prevents duplication drift"

**Claim:** Having one `security-auditor.md` referenced by multiple panels prevents inconsistency.

**Research assessment: PARTIALLY VALID, but the solution is wrong.**

Carson Gross's **Locality of Behaviour** principle (htmx creator): *"The behaviour of a unit of code should be as obvious as possible by looking only at that unit of code."* Having persona definitions in separate files is the worst-case LoB violation — *"if it is in a separate file entirely"* ([htmx.org](https://htmx.org/essays/locality-of-behaviour/)).

Google Research found that **simply repeating a prompt literally improves LLM accuracy** — across 70 comparisons, prompt repetition improved accuracy 47 times and never significantly reduced performance ([Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/02/prompt-repetition/)). LLMs cannot "import" or dereference references — information must be literally in context to be used.

Simon Willison and Andrej Karpathy endorse **"context engineering"** over "prompt engineering": *"filling the context window with just the right information for the next step"* — not maintaining canonical definitions elsewhere ([simonwillison.net](https://simonwillison.net/2025/jun/27/context-engineering/)).

The risk of duplication drift is real, but the mitigation is:
- A `shared-perspectives.md` file (as proposed in the issue) serves as the canonical definition at **authoring time**
- A build-time template system (Jinja2/mustache) compiles canonical definitions into self-contained prompts — **DRY at authoring time, locality at runtime**
- **Schema validation** (`panel-output.schema.json`) ensures emissions use consistent persona labels regardless of prompt organization

**Verdict:** The counter-argument identifies a real risk, but the issue's proposed `shared-perspectives.md` addresses it. The current 60-file indirection is not the only way to maintain consistency — and research shows locality beats indirection for LLMs.

---

### Counter-Argument Claim 2: "Audit traceability from emissions to definitions"

**Claim:** The `"persona": "Security Auditor"` field in emissions traces back to `governance/personas/compliance/security-auditor.md`. Consolidation breaks this.

**Research assessment: NOT SUPPORTED by compliance frameworks.**

NIST SP 800-53 and the AI RMF require audit trails for:
- Model changes and data versioning
- Security events and access control
- Decision rationale and override documentation

They do **not** require traceability from AI-generated review findings to the specific prompt file that generated them. The audit property that matters is:
1. What decision was made (approve/block)
2. What evidence supported it (findings with severity)
3. Who/what made it (panel name, persona label, timestamp)
4. Whether it was overridden (and by whom)

The `panel-output.schema.json` captures all of this. The `findings[].persona` field uses **string labels**, not file paths. Moving from `governance/personas/compliance/security-auditor.md` to a section header in `governance/prompts/reviews/security-review.md` does not change the emission structure at all.

**Verdict:** The counter-argument assumes audit requirements that don't exist in NIST/SOC2/PCI-DSS. The emission schema is the audit contract, not the file structure.

---

### Counter-Argument Claim 3: "Consuming repo composability"

**Claim:** Consuming repos could customize individual personas or mix them into custom panels.

**Research assessment: THEORETICAL, not exercised.**

The issue's own codebase analysis found:
- 19 personas appear in only 1 panel — no reuse
- 8 personas are not referenced by any panel at all
- 11 language + 2 platform personas are never referenced by any panel

There is no mechanism in the codebase (`config.yaml`, `project.yaml`, `panels.local.json`) for consuming repos to define custom panel compositions. The composability is architecturally possible but not implemented.

Anthropic's Orchestrator-Workers pattern suggests composability should live at the **orchestration layer** (the Tech Lead deciding which panels to run), not at the **file layer** (individual persona files).

**Verdict:** Composability is a valid goal, but the current architecture doesn't achieve it. The consolidated prompts don't prevent future composability — they make the orchestrator-level composition clearer.

---

### Counter-Argument Claim 4: "Phase 5 multi-agent justifies current architecture"

**Claim:** The separate persona files are correct architecture for the Phase 5 multi-agent future.

**Research assessment: CONTRADICTED by Anthropic's core principle AND quantitative research.**

> *"Consider adding complexity only when it demonstrably improves outcomes. Agentic systems often trade latency and cost for better task performance, and you should consider when this tradeoff makes sense."* — [Anthropic](https://www.anthropic.com/research/building-effective-agents)

**Google DeepMind's quantitative research is devastating for this claim.** Their "Towards a Science of Scaling Agent Systems" (Dec 2025) found that multi-agent systems **degraded performance by up to 70% on sequential tasks** and that single agents averaged 67 successful tasks per 1,000 tokens vs. just 21 for centralized multi-agent systems. Their "45% rule": if a single agent solves more than 45% of a task correctly, multi-agent systems usually are not worth it ([research.google](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/)).

Building for a hypothetical runtime that doesn't exist yet is textbook **premature abstraction**: *"Premature abstraction happens when you create an abstraction too early, before you truly understand the problem"* ([codeworld.blog](https://codeworld.blog/posts/system%20design/architecture/PrematureAbstraction/)). The GOALS.md itself acknowledges: *"Runtime blocked: [...] does not exist in current AI tooling."*

Furthermore, if Phase 5 multi-agent ships, the consolidated review prompts serve as **better** agent definitions than the current persona files. Per [The Agent Architect](https://theagentarchitect.substack.com/p/4-tips-writing-system-prompts-ai-agents-work): agent system prompts need structured sections for persona/role, primary goal, guardrails, tools, workflow policy, and output format. The current ~20-line persona fragments lack most of these. The consolidated prompts would include all of them.

**Verdict:** The consolidation produces better agent definitions for Phase 5 than the current persona files. Building for hypothetical futures contradicts both Anthropic guidance and Google DeepMind's quantitative research.

---

### Counter-Argument Claim 5: "Context cost is solved by JIT loading"

**Claim:** The 5-7 file reads per panel are JIT-loaded and don't persist in context.

**Research assessment: PARTIALLY TRUE but misses the real cost.**

The real cost isn't context tokens per se — it's **tool calls and latency**. Each file read is a tool call. 6 required panels x 5-7 reads = 30-42 tool calls just for loading persona definitions. In a Claude Code session with an 80% context hard-stop and max 50 tool calls before checkpoint, persona loading alone consumes 60-84% of the tool call budget.

The Ralph Wiggum Loop research reinforces this: *"Every failed attempt stays in the conversation history, which means that after a few iterations, the model must process a long history of noise."* The solution is fresh context per iteration — which means self-contained prompts that don't require file-chasing.

**Verdict:** JIT loading reduces persistent context, but the tool call overhead and latency of 30-42 file reads per PR is real. Self-contained prompts eliminate this entirely.

---

### Counter-Argument Claim 6: "File count is misleading — complexity moves, not reduces"

**Claim:** A 200-line consolidated file is harder to diff than 5 x 25-line files.

**Research assessment: NUANCED — depends on change frequency.**

This argument has merit for frequently-changed files. But the persona files are governance artifacts versioned by git SHA — they change infrequently. When they do change, the change is typically to all personas in a panel simultaneously (e.g., updating scoring criteria), which means editing 5 files vs. 1 file.

The Anthropic cookbook examples use single-file prompt definitions with structured sections, not multi-file compositions. Their orchestrator-workers pattern has the orchestrator generate worker task descriptions inline, not reference external files.

**Verdict:** Valid concern, but the change patterns in this codebase favor consolidated files. Governance artifacts change as a unit, not individually.

---

### Counter-Argument Claim 7: "It's just one agent with hats — assumes current tooling"

**Claim:** The policy engine evaluates persona-level results regardless of runtime architecture.

**Research assessment: VALID — this is the strongest counter-argument.**

The `panel-output.schema.json` schema with per-persona findings is genuinely valuable. It allows:
- Persona-level confidence weighting in the policy engine
- Individual persona effectiveness tracking (`persona-effectiveness.schema.json`)
- Granular audit of which perspective flagged what

This structured output should be preserved regardless of how prompts are organized. The consolidation must ensure that each perspective section in the consolidated prompt still emits discrete findings per persona label.

**Verdict:** The emission structure (per-persona findings) must be preserved. This is a constraint on the consolidation, not an argument against it.

---

## 5. Recommended Architecture (Research-Grounded)

Based on the research, the optimal architecture combines:

### Phase 0: Research (This Document)
- Ground all decisions in sources (complete)
- Flag terminology conflicts (complete — "prompt injection loop")

### Phase 1: Consolidation as Anthropic's Parallelization (Voting) Pattern

Convert each panel into a self-contained review prompt that implements Anthropic's **Voting** pattern:

```
governance/prompts/reviews/code-review.md
├── System context (what is being reviewed, schema contract)
├── Perspective: Code Reviewer (inline, ~20 lines)
├── Perspective: Security Auditor (from shared-perspectives.md)
├── Perspective: Performance Engineer (inline)
├── Perspective: Test Engineer (inline)
├── Perspective: Refactor Specialist (inline)
├── Scoring criteria (confidence, pass/fail thresholds)
└── Output format (STRUCTURED_EMISSION with per-persona findings)
```

The `shared-perspectives.md` file contains canonical definitions for the 19 perspectives appearing in 2+ panels, addressing the duplication drift risk.

### Phase 2: Ralph Wiggum Loop Integration

Wrap the governance review in a Ralph Wiggum-style loop:

1. **Task:** Review PR against all required panels
2. **External validators:** Schema validation, policy engine evaluation, CI checks
3. **Loop condition:** All validators pass OR max iterations reached
4. **Harness decides:** The bash loop / Stop hook determines completion, not the model
5. **Fresh context per iteration:** Each review cycle gets a fresh context with the current state of the code

This directly addresses Goal #1: *"ensure that an agentic loop continues without human intervention"* and Goal #4 (correctly restated): *"governance workflow transitions to an evaluator-optimizer loop with external validation."*

### Phase 3: Deprecation and Cleanup

Per the issue's Phase 2 and Phase 3 — deprecate old files, validate emission parity, then remove.

### Phase 4 (Future): True Multi-Agent

Only when Anthropic's parallelization pattern can be executed with actual parallel model calls (multiple Claude instances). The consolidated prompts become agent system prompts directly.

---

## 6. Decision Matrix

| Aspect | Status Quo (60 files) | Consolidation (19 prompts) | Research Recommendation |
|--------|----------------------|---------------------------|------------------------|
| Context efficiency | 30-42 tool calls per PR | 6 file reads per PR | **Consolidate** |
| Duplication risk | None (single source) | Managed via shared-perspectives.md | **Consolidate** (with shared-perspectives.md) |
| Audit traceability | File path → emission | Section header → emission | **Equivalent** (emissions unchanged) |
| Composability | Theoretical, not exercised | Orchestrator-level | **Consolidate** |
| Phase 5 readiness | Persona fragments | Full agent system prompts | **Consolidate** (better agent definitions) |
| Anthropic alignment | Contradicts "start simple" | Matches voting pattern | **Consolidate** |
| Ralph Loop compatibility | Requires file-chasing | Self-contained per iteration | **Consolidate** |
| Schema compliance | Preserved | Preserved | **Equivalent** |
| Git diff clarity | 5 small files per change | 1 file per change | **Nuanced** (favor consolidation for governance artifacts) |

---

## 7. Conflicts Requiring Discussion

Per the Anti-Pattern: *"If there is a conflict, prompt me and we can discuss."*

### Conflict 1: "Prompt injection loop" terminology — RESOLVED
- **Issue said:** "transitions to a prompt injection loop"
- **Clarification from author:** This was a typo. The intended term is **"prompt chaining loop"**
- **Research alignment:** Prompt chaining is a well-supported pattern (Anthropic, AWS, LangChain). No conflict.

### Conflict 2: Part 2 scope and timing
- **Issue says:** Build agent orchestration runtime, consensus service, CI integration
- **Research says:** "Consider adding complexity only when it demonstrably improves outcomes" (Anthropic)
- **Proposed resolution:** Part 2 should be limited to defining agent system prompts (which the consolidation produces) and documenting the target architecture. Runtime implementation deferred until multi-agent tooling exists.

### Conflict 3: Runtime options evaluation
- **Issue lists:** LangGraph, CrewAI, AutoGen, Custom orchestrator
- **Research says:** Anthropic advises against frameworks: "Frameworks often create extra layers of abstraction that can obscure the underlying prompts and responses, making them harder to debug"
- **Proposed resolution:** The Ralph Wiggum pattern (bash loop + Stop hooks) plus Anthropic's native parallelization pattern may be sufficient without a framework. Evaluate concrete requirements before selecting a framework.

---

## 8. Summary

The research supports consolidation (Part 1) with high confidence. The counter-argument raises valid concerns about duplication drift and per-persona emission fidelity, both of which are addressable with `shared-perspectives.md` and schema validation.

The research does **not** support building a multi-agent runtime (Part 2) now. It supports:
1. Consolidating personas into self-contained review prompts (Anthropic's Voting pattern)
2. Integrating a Ralph Wiggum Loop for continuous governance execution
3. Producing consolidated prompts that can serve as agent system prompts when multi-agent tooling matures

The strongest argument for action is practical: the current architecture costs 30-42 tool calls per PR review in a system with a 50 tool-call budget. Consolidation makes the governance loop viable within Claude Code's constraints.

> **Note:** This research has been consolidated into `docs/research/README.md`, which
> includes both the technique comparison findings documented here and the MCP skills evaluation.
> For the canonical, up-to-date version of this research, refer to that file.

---

## 9. Recommended Direction

Given the framework's goals (autonomous governance, prompt chaining loop, personas as agents), here is the research-grounded direction:

### What to do now (Phase 1 — Consolidation)

1. **Create 19 self-contained review prompts** in `governance/prompts/reviews/` using Anthropic's Parallelization (Voting) pattern. Each prompt inlines its participant perspectives as named sections with full evaluation criteria, scoring, and output schema.

2. **Create `shared-perspectives.md`** as a build-time canonical source for the 19 perspectives appearing in 2+ panels. This is the authoring-time DRY mechanism — the compiled review prompts have full locality at runtime.

3. **Preserve per-persona emission structure.** The `findings[].persona` field in `panel-output.schema.json` remains unchanged. Each perspective section in the consolidated prompt emits its own finding. The policy engine's weighted aggregation works identically.

4. **Update workflow references** to point to new prompts. Both old and new structures coexist during validation.

### What to do next (Phase 2 — Ralph Wiggum Integration)

5. **Wrap the governance review in a Ralph Wiggum-style loop** using Claude Code Stop hooks. The external validators are: schema validation on emissions, policy engine evaluation, CI checks. The harness decides completion, not the model. This directly achieves Goal #1 (agentic loop without human intervention) and Goal #4 (prompt chaining loop).

6. **Each review cycle gets fresh context** (Ralph's stateless resampling). The self-contained review prompts make this possible — no file-chasing across the formerly 60 persona files (now consolidated into 21 review prompts; only 7 agentic personas remain) per iteration.

### What to defer (Part 2 — True Multi-Agent)

7. **Do not build a multi-agent runtime now.** Google DeepMind's research shows multi-agent degrades sequential task performance by up to 70%. Anthropic advises against adding complexity until simpler solutions prove insufficient. The consolidated prompts ARE the agent definitions — when multi-agent tooling matures, each prompt becomes an agent's system prompt with zero refactoring.

8. **Do not select a framework (LangGraph/CrewAI/AutoGen) now.** Anthropic: *"Frameworks often create extra layers of abstraction that can obscure the underlying prompts."* The Ralph pattern (bash + Stop hooks) plus native Claude Code subagents may be sufficient. Evaluate concrete requirements before committing to a framework.

### Why this direction

- **Grounded in Anthropic's own patterns** (Voting, Evaluator-Optimizer, "start simple")
- **Grounded in the Ralph Wiggum pattern** (external validation, fresh context per iteration)
- **Validated against Google DeepMind** (single-agent 3x more efficient than multi-agent)
- **Addresses all four Goals** from the issue:
  - Goal 1 (continuous loop): Ralph Wiggum + Stop hooks
  - Goal 2 (prompts work as well or better): self-contained with locality of behavior
  - Goal 3 (personas become agents): consolidated prompts are agent-ready system prompts
  - Goal 4 (prompt chaining loop): sequential pipeline with parallel panel execution
