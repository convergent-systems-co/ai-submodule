# Copilot Context Management

<!-- PHASE:context -->

Loaded for GitHub Copilot agents to manage context capacity. Supplements the base Context Capacity Protocol in `instructions.md`.

## Detection Strategy

Copilot does not expose per-request token counts. Use these signals in order of reliability:

1. **VS Code LM API** — If available, call `vscode.lm.countTokens()` on the assembled payload. This is the most accurate signal.
2. **UI context meter** — In VS Code Copilot Chat, the token usage indicator shows exact counts (e.g., `15K/128K`). Monitor before each major action.
3. **Heuristic estimation** — If neither API nor UI is available:
   - 30+ chat turns → assume 70%+ capacity
   - 200,000+ characters in conversation → assume ~80% capacity
   - 10+ files referenced in context → significant consumption
   - Response quality drops or truncation occurs → at or near capacity

## Context Window Reference

| Mode | Window Size |
|------|-------------|
| VS Code Copilot Chat (stable) | 64K tokens |
| VS Code Copilot Chat (Insiders) | 128K tokens |
| GitHub.com Copilot Chat | 64K tokens |

## Shutdown Differences from Claude Code

| Step | Claude Code | Copilot |
|------|------------|---------|
| Context reset | `/clear` command | Start a new Copilot Chat thread |
| Token visibility | Terminal token counter | UI meter (hover chat input) or `countTokens()` API |
| Auto-summarization | System-level warnings | Auto-summarization happens silently; watch for it |
| Checkpoint handoff | User runs `/clear`, agent reads checkpoint | User starts new thread, pastes checkpoint path |

## Threshold Actions

The same two-tier thresholds from the base Context Capacity Protocol apply:

| Threshold | Action |
|-----------|--------|
| Below 70% | Continue normally. Proactively summarize at ~60% to extend useful window. |
| 70-80% | Do not start new issues. Finish current work. Write checkpoint. Summarize context. |
| At/above 80% | **Hard stop.** Execute the full Capacity Shutdown Protocol (stop, clean git, checkpoint, request new thread). |

### Proactive Summarization (60-70%)

Between 60-70%, proactively compress context to stay below the 80% hard stop:

1. Write a rolling summary of completed work to the checkpoint file
2. Drop older raw conversation turns from context
3. Continue in the same thread with the compact summary

This extends the useful working window. Do not rely on VS Code's auto-summarization — summarize before it triggers.
