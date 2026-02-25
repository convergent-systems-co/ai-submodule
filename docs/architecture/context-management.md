# Context Management and JIT Loading Strategy

## Problem

AI agents have finite context windows. Loading all personas, prompts, workflows, policies, and instructions simultaneously wastes context capacity, reduces reasoning quality, and risks context resets that lose critical guidance. The Dark Factory system contains 15,000+ lines of Markdown — loading everything is neither feasible nor desirable.

## Design Principles

1. **Load what you need, when you need it** — JIT loading based on task phase
2. **Never lose critical instructions** — Base instructions survive context resets
3. **Maximize parallel execution** — Independent agents work with minimal shared context
4. **Decompose for reuse** — Small, composable instruction units over monolithic files
5. **Context budget enforcement** — Hard limits on what gets loaded per phase

## Context Tiers

### Tier 0: Persistent Context (Always Loaded)

Content that must survive context resets. Kept minimal.

| Content | Source | Max Tokens |
|---------|--------|------------|
| Base instructions | `instructions.md` | 200 |
| Project identity | `project.yaml` (name, language, framework only) | 100 |
| Active governance profile | Profile name + decision thresholds only | 50 |
| Current task reference | Issue/DI ID + objective statement | 50 |

**Total Tier 0 budget: ~400 tokens**

Design rule: If `instructions.md` exceeds 500 tokens, decompose it. The base file must contain only universal principles. Everything else belongs in Tier 1 or 2.

### Tier 1: Session Context (Loaded at Session Start)

Content loaded once when an agent begins a task session. Stays in context for the session duration.

| Content | Source | Loaded When |
|---------|--------|-------------|
| Language conventions | `governance/templates/{language}/instructions.md` | Session start, based on `project.yaml` language |
| Active persona set | Persona files listed in `project.yaml` | Session start |
| Current plan | `.plans/{active-plan}.md` | Session start if plan exists |

**Total Tier 1 budget: ~2,000 tokens**

Design rule: If the persona set exceeds the budget, load only the persona headers (Role + Evaluate For sections). Full persona content moves to Tier 2.

### Tier 2: Phase Context (Loaded Per Workflow Phase)

Content loaded and unloaded as the agent moves through workflow phases. Previous phase context is released.

| Content | Source | Loaded When |
|---------|--------|-------------|
| Workflow phase definition | `governance/prompts/workflows/{workflow}.md` (single phase) | Phase entry |
| Phase-specific prompt | `governance/prompts/{prompt}.md` | When the phase invokes it |
| Panel definition | `governance/personas/panels/{panel}.md` | Panel invocation |
| Panel persona details | Individual persona files | Panel invocation |

**Total Tier 2 budget: ~3,000 tokens**

Design rule: Workflow files must be decomposable by phase. Each phase section should work independently without requiring the full workflow in context.

### Tier 3: Reference Context (Never Loaded, Queried On-Demand)

Content accessed via tool calls or file reads, never pre-loaded.

| Content | Source | Access Method |
|---------|--------|--------------|
| Policy profiles | `governance/policy/*.yaml` | Programmatic evaluation |
| JSON schemas | `governance/schemas/*.schema.json` | Schema validation tool |
| Run manifests | `governance/manifests/*.json` | File read on-demand |
| Architecture docs | `docs/**/*.md` | File read when referenced |
| Other personas | `governance/personas/**/*.md` not in active set | File read when invoked |

**Tier 3 budget: 0 tokens (no context cost)**

## Tier Budget Exceptions

Some prompts intentionally exceed their assigned tier budget. These exceptions are documented here with rationale. Prompts not listed below must stay within their tier budget.

### Documented Exceptions

| Prompt | Tier | Budget | Actual | Rationale |
|--------|------|--------|--------|-----------|
| `governance/prompts/startup.md` | 0+1 | ~2,400 tokens | ~4,700 tokens | Contains the full agentic loop with ANCHOR section that must survive context resets. Splitting into phases would fragment the critical shutdown protocol and risk lost instructions on context compaction. Loaded once at session start; not reloaded during the session. |
| `governance/prompts/reviews/threat-modeling.md` | 2 | ~3,000 tokens | ~5,350 tokens | Self-contained review prompt implementing Anthropic's Parallelization (Voting) pattern. Inlines 5 threat perspectives with full evaluation criteria. Splitting would break prompt locality — each perspective needs access to all others for cross-referencing. Loaded only during threat-modeling panel execution. |
| `governance/prompts/reviews/security-review.md` | 2 | ~3,000 tokens | ~3,400 tokens | Self-contained review prompt with 5 security perspectives. Marginally over budget. Same locality rationale as threat-modeling. |

### When Exceptions Are Acceptable

An exception is justified when:
1. **Splitting would degrade output quality** — the prompt relies on cross-referencing between sections
2. **The prompt implements a recognized AI pattern** (Parallelization, Voting) that requires locality
3. **The prompt contains ANCHOR content** that must survive context resets
4. **The prompt is loaded infrequently** — exceeding budget on a rarely-loaded prompt has less impact than on a frequently-loaded one

### When Exceptions Are NOT Acceptable

Do not add exceptions for:
- Prompts that can be decomposed without quality loss
- Prompts loaded at multiple tiers simultaneously
- Instructional content that could move to Tier 3 (on-demand)

> **Note:** Token counts are approximate (1 token ≈ 4 characters) and tied to the prompt content at the time of this documentation. Counts may drift as prompts evolve.

## Instruction Decomposition

### Current Problem

Monolithic instruction files force full loading even when only a fraction is relevant. A 2,000-token `instructions.md` wastes 1,800 tokens when only the base principles apply.

### Decomposition Strategy

Split instructions into composable units:

```
instructions.md                  (Tier 0 — universal principles, < 200 tokens)
instructions/
  code-quality.md               (Tier 1 — loaded for code tasks)
  testing.md                    (Tier 1 — loaded for test tasks)
  security.md                   (Tier 1 — loaded for security-sensitive tasks)
  communication.md              (Tier 1 — loaded for PR/issue tasks)
  governance.md                 (Tier 1 — loaded for governance tasks)
```

Each decomposed file:
- Has a clear, single responsibility
- Is under 500 tokens
- Can be loaded independently
- Has no dependencies on other decomposed files

### Persona Decomposition

Personas are already well-decomposed (one file per persona). Optimization:

1. **Header extraction**: For Tier 1 loading, extract only `## Role` and `## Evaluate For` (~100 tokens per persona vs. ~400 for the full file)
2. **Full load on invocation**: Load the complete persona only when it is actively executing a review
3. **Panel optimization**: Load only the moderator pattern and persona names; load individual personas as they speak

### Workflow Phase Decomposition

Workflows must support phase-level loading. Convention:

```markdown
<!-- PHASE:1 -->
## Phase 1: Requirements Analysis
...
<!-- /PHASE:1 -->

<!-- PHASE:2 -->
## Phase 2: Design
...
<!-- /PHASE:2 -->
```

The agent loader extracts only the current phase section, keeping previous phases out of context. Phase artifacts (e.g., `[FEAT-1]`) are passed forward as compact references, not full content.

## Parallel Execution Model

### Agent Independence

Each parallel agent receives:
- Tier 0 context (identical across all agents)
- Its own Tier 1 context (specific to its role)
- Its own Tier 2 context (specific to its current phase)

No shared mutable state between agents. Results are aggregated by the Code Manager after all agents complete.

### Panel Parallelism

Panels can execute personas in parallel:

```mermaid
graph TD
    P["Code Review Panel"] --> A1["Agent 1: Code Reviewer\n(Tier 0 + persona context)"]
    P --> A2["Agent 2: Security Auditor\n(Tier 0 + persona context)"]
    P --> A3["Agent 3: Performance Engineer\n(Tier 0 + persona context)"]
    P --> A4["Agent 4: Test Engineer\n(Tier 0 + persona context)"]
    P --> A5["Agent 5: Refactor Specialist\n(Tier 0 + persona context)"]
    A1 --> M["Moderator aggregates findings\ninto structured emission"]
    A2 --> M
    A3 --> M
    A4 --> M
    A5 --> M
```

Each persona agent:
- Loads only Tier 0 + its own persona definition + the code diff
- Produces independent findings
- Has no dependency on other persona agents
- Can be terminated independently on timeout

### Workflow Parallelism

Independent workflow phases can execute in parallel:

```mermaid
flowchart TD
    FI["Feature Implementation"] --> P1["Phase 1: Requirements"]
    P1 --> P2["Phase 2: Design"]
    P2 --> P3a["Phase 3a: Implementation"]
    P2 --> P3b["Phase 3b: Test Planning"]
    P3a --> P4["Phase 4: Review"]
    P3b --> P4
```

## Context Reset Protection

### The Reset Problem

When a context window fills, the AI runtime may truncate or summarize early context. This risks losing:
- Base instructions (Tier 0)
- Active persona definitions (Tier 1)
- Governance constraints

Uncontrolled compaction is the worst outcome. If the context compacts while the working tree has uncommitted changes, merge conflicts, or in-progress operations, the agent loses both the instructions that explain what it was doing and the ability to recover cleanly. This must never happen.

### Context Pressure Detection (Platform-Specific)

The agent must actively monitor for context pressure using platform-specific signals:

#### Claude Code
- **Token counter**: Visible in `--verbose` mode on the right side of the terminal. Shows current token usage vs. model context window.
- **System warnings**: Claude Code emits warnings when approaching context limits. These appear as system messages in the conversation.
- **Automatic summarization**: When Claude Code summarizes earlier messages, this is a signal that context is already under pressure. If this happens mid-task, immediately checkpoint.

#### GitHub Copilot (VS Code)

Copilot does not expose per-request token usage via a public API the way OpenAI-style APIs do. Detection relies on a combination of UI signals, the VS Code Language Model API, and heuristic estimation.

**Primary: VS Code Language Model API (Extensions)**

If operating as a VS Code extension or chat participant, use the Language Model API for token counting:

```typescript
import * as vscode from "vscode";

// Window size depends on mode: 128k for Insiders, 64k for standard
const MODEL_WINDOW = parseInt(process.env.COPILOT_CONTEXT_WINDOW ?? "64000", 10);
const CHECKPOINT_THRESHOLD = 0.70; // Don't start new issues above this
const HARD_STOP_THRESHOLD = 0.80;  // Stop immediately, execute shutdown protocol

async function checkContextCapacity(payloadText: string) {
  const tokens = await vscode.lm.countTokens(payloadText);
  const ratio = tokens / MODEL_WINDOW;
  if (ratio >= HARD_STOP_THRESHOLD) return { action: "shutdown", ratio, tokens };
  if (ratio >= CHECKPOINT_THRESHOLD) return { action: "checkpoint", ratio, tokens };
  return { action: "continue", ratio, tokens };
}
```

**Track what you send**: system instructions + conversation summary + recent turns + selected context (files/snippets). Call `countTokens()` on the assembled payload before each request.

**Secondary: UI Context Meter (Interactive Sessions)**

In Copilot Chat (VS Code), a token usage indicator appears in the chat input area. Hovering it shows an exact token count (e.g., `15K/128K`) with a category breakdown (chat history, files, instructions, etc.). Monitor this meter:
- **Below 70%**: Continue normally.
- **70-80%**: Do not start new issues. Finish current work, write checkpoint, and proactively summarize context to stay below 80%. Use rolling summaries to extend the useful working window.
- **At/above 80%**: Hard stop. Execute the full Capacity Shutdown Protocol immediately (stop, clean git, write checkpoint, request context reset via new thread).

**Note**: VS Code automatically summarizes conversation history when the context fills. If you observe auto-summarization happening, context is already under pressure — immediately checkpoint.

**Secondary: Heuristic Estimation (When API Unavailable)**

When operating as a Copilot agent without direct access to `vscode.lm.countTokens()`:

| Signal | Threshold | Action |
|--------|-----------|--------|
| Chat turns (back-and-forth) | > 30 turns | Assume 70%+ capacity. Monitor closely. |
| Character count of conversation | > 200,000 chars | Assume ~50K tokens (~80% of 64K window). Checkpoint. |
| Files in context | > 10 files referenced | Significant context consumption. Review necessity. |
| Response quality degradation | Suggestions become generic or lose project context | Context pressure likely. Checkpoint immediately. |
| Response truncation | Responses cut short mid-sentence or lose coherence | Near or at capacity. Execute hard reset. |
| Re-reading files | Agent re-reads files it already processed | Context has been compacted. Checkpoint immediately. |

**Copilot-Specific Context Window Sizes:**

| Mode | Model | Context Window |
|------|-------|----------------|
| VS Code Copilot Chat | GPT-4o | 64K tokens |
| VS Code Insiders | GPT-4o | 128K tokens |
| GitHub.com Copilot Chat | GPT-4o | 64K tokens |
| Copilot in CLI | Varies | Check model-specific limits |

**Copilot Shutdown Protocol:**

Copilot agents follow the same two-tier threshold system as Claude Code:

- **At 70%**: Do not start new issues. Finish current work, checkpoint. Proactively summarize context to extend the working window.
- **At 80%**: Hard stop. Execute the full Capacity Shutdown Protocol (steps 1-5 below) immediately.

Copilot-specific adaptations:

1. **Context reset**: Instead of `/clear`, start a new Copilot Chat thread. Copilot does not have a `/clear` equivalent — a new thread is the reset mechanism.
2. **Checkpoint handoff**: In the new thread, paste: "Resume from checkpoint: `.checkpoints/{file}`" so the agent reads the checkpoint and continues.
3. **Proactive summarization** (between 60-70%): Create rolling summaries of completed work and drop older raw turns. This extends the useful working window. VS Code auto-summarization also helps, but the agent should summarize proactively rather than waiting for the system to do it.

#### Universal Heuristics (All Platforms)
- **Issue count**: After 3 completed issues, stop regardless of token count.
- **Tool call count**: After ~50 tool calls in a session, assume 70%+ capacity.
- **Conversation exchanges**: After ~100 back-and-forth exchanges, assume 70%+ capacity.
- **Self-detection**: If the agent re-reads files it already read, forgets earlier decisions, or produces contradictory output, context pressure is the likely cause.

**The user should never have to manage context.** The agent is responsible for detecting pressure and executing the shutdown protocol before the user notices any degradation.

### Capacity Shutdown Protocol

**This is the primary defense against context loss. It is mandatory and overrides all other work.**

The agent must check context capacity before starting any new issue, and after completing each major step (plan, implement, review, merge). When context reaches 80% capacity or any detection signal triggers:

1. **Stop immediately** — do not start the next task, issue, or step
2. **Clean all git state**:
   - Run `git status` on every branch touched in the session
   - Commit any pending changes with a `wip:` prefix if needed
   - Abort any in-progress merges (`git merge --abort`) or rebases (`git rebase --abort`)
   - Verify `git status` shows `nothing to commit, working tree clean`
3. **Write a checkpoint** to `.checkpoints/{timestamp}-{branch}.json`:
   ```json
   {
     "timestamp": "2026-02-21T14:30:00Z",
     "branch": "itsfwcp/current-branch",
     "issues_completed": ["#5", "#6"],
     "issues_remaining": ["#7", "#8"],
     "current_issue": null,
     "current_step": "Completed Phase 4 for issue #6",
     "git_state": "clean",
     "pending_work": "Issues #7 and #8 need implementation. PRs #13-#15 need governance approval.",
     "prs_created": ["#13", "#14", "#15"],
     "manifests_written": ["20260221-143000-abc1234"],
     "branches_touched": ["itsfwcp/5-agile-coach", "itsfwcp/6-finops-group"]
   }
   ```
4. **Report to user** — summarize what was completed, what remains, and the checkpoint file path
5. **Request context reset** — tell the user to run `/clear` and provide the checkpoint path for the next session to read

### Checkpoint Recovery

When resuming from a checkpoint:
1. Read the checkpoint file referenced by the user
2. Verify git state matches the checkpoint (`git branch`, `git status`)
3. Load only the Tier 1 + Tier 2 context needed for the next pending task
4. Continue from where the checkpoint left off

### Protection Mechanisms

1. **Tier 0 pinning**: Base instructions are re-injected at every agent turn as system-level context. They are never part of the conversation history that gets truncated.

2. **Checkpoint artifacts**: At each workflow gate, the agent writes a checkpoint file to `.checkpoints/`. Contains: current state, decisions made, findings so far. If context resets, the agent reads the checkpoint to resume.

3. **Context budget monitoring**: Track approximate token usage per tier. When Tier 2 exceeds budget, the agent must:
   - Write current findings to a checkpoint
   - Release Tier 2 context
   - Load the next phase's Tier 2 context
   - Read the checkpoint to restore state

4. **Instruction anchoring**: Critical instructions include a marker:
   ```markdown
   <!-- ANCHOR: This instruction must survive context resets -->
   ```
   The agent loader treats anchored content as Tier 0, ensuring it is always present.

5. **Decomposed re-loading**: If context is reset mid-task, the agent:
   1. Reads Tier 0 (always available as system context)
   2. Reads the checkpoint file for current state
   3. Loads only the Tier 1 + Tier 2 context needed for the current phase
   4. Continues from the checkpoint

## Implementation Requirements

### For Persona Authors

- Keep persona files under 500 tokens
- Put the most critical information in `## Role` and `## Evaluate For` (loaded first)
- Put detailed guidance in `## Principles` and `## Anti-patterns` (loaded on full invocation)

### For Workflow Authors

- Use `<!-- PHASE:N -->` markers to enable phase-level extraction
- Keep each phase under 1,000 tokens
- Pass forward only artifact references, not full artifact content
- Design phases to be resumable from a checkpoint

### For Instruction Authors

- Keep `instructions.md` under 200 tokens (universal principles only)
- Decompose domain-specific guidance into `instructions/` subdirectory
- Mark critical instructions with `<!-- ANCHOR -->` markers
- Never put implementation details in base instructions

### For the Agent Runtime

- Implement a context loader that respects tier budgets
- Re-inject Tier 0 at every turn
- Monitor approximate token usage and warn at 80% budget
- Write checkpoints at every workflow gate
- Support phase-level extraction from workflow files
