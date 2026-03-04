# Issue Draft: Sub-Agent Context Capacity Monitoring for Parallel Dispatch

**Type:** enhancement
**Priority:** high

## Title
feat: sub-agent context capacity monitoring for parallel dispatch

## Body

### Summary

When the orchestrator dispatches multiple Coder agents in parallel (via Claude Code's Agent tool), each sub-agent runs in its own context window. The parent orchestrator has no visibility into how much context each sub-agent has consumed. This creates a blind spot:

- A sub-agent approaching 80% context capacity may silently degrade (lost instructions, incomplete work)
- The parent's context gate thresholds (tool_calls, turns) only track the parent window
- No mechanism exists to signal "sub-agent is running low" back to the parent
- If a sub-agent hits compaction, the parent has no way to detect or recover

### Problem

The current context management model (4-tier Green/Yellow/Orange/Red) only monitors the **parent** conversation. With `parallel_coders: 6`, there could be 6+ independent context windows consuming tokens with zero observability.

### Proposed Solutions

#### Option A: Agent SDK token reporting
If Claude Code exposes token usage metadata when an Agent tool returns, the orchestrator could:
- Read token counts from each agent's result
- Flag agents that consumed >70% of their context
- Retry failed agents with smaller scope

#### Option B: Checkpoint-based health signals
Sub-agents could write health signals to disk (e.g., `.governance/state/agent-health/{agent-id}.json`) containing estimated context usage. The parent polls between dispatch and collect phases.

#### Option C: Task decomposition limits
Rather than monitoring context, prevent the problem by enforcing maximum task complexity:
- Limit lines changed per agent
- Limit files touched per agent
- Split large issues into sub-tasks before dispatch

### Acceptance Criteria

- [ ] Research: Can Claude Code Agent tool return token usage metadata?
- [ ] Research: Can sub-agents estimate their own context usage?
- [ ] Design a monitoring mechanism that works with parallel dispatch
- [ ] Implement context health reporting for sub-agents
- [ ] Parent orchestrator can detect and react to sub-agent context pressure

### Notes

The Agent tool does return `total_tokens` and `tool_uses` in its usage metadata (we saw this in the current session). This could be captured and used as a proxy for context consumption. For example, the #15 coder agent used 81,333 tokens and 105 tool uses — this is useful signal.
