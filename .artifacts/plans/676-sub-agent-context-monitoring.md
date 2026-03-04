# Sub-Agent Context Capacity Monitoring

**Author:** Project Manager (agentic)
**Date:** 2026-03-02
**Status:** approved
**Issue:** #676
**Branch:** itsfwcp/feat/676/sub-agent-context-monitoring

---

## 1. Objective

Give the parent orchestrator visibility into sub-agent context consumption so it can detect degradation before agents silently fail.

## 2. Rationale

Sub-agents run in isolated context windows. The parent has no way to know when a sub-agent is approaching 80% capacity. Agent SDK metadata (`total_tokens`, `tool_uses`) can be used.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Health signal files | Yes | Requires sub-agent cooperation |
| Extend AgentResult | Yes — chosen | Clean, uses existing dispatch pipeline |
| Task decomposition limits | Yes | Complementary, not sufficient alone |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/engine/orchestrator/agent_context.py` | SubAgentContextMonitor class |
| `governance/engine/tests/test_agent_context.py` | Tests |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/engine/orchestrator/dispatcher.py` | Add tokens_consumed, context_tier to AgentResult |
| `governance/engine/orchestrator/step_runner.py` | Read context signals from agent results in Phase 4 |

## 4. Approach

1. Extend AgentResult with token/tier fields
2. Create SubAgentContextMonitor that evaluates agent health from results
3. Integrate into Phase 4 collect step
4. Flag agents that are Orange/Red tier

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | agent_context.py | Tier classification from token counts |
| Unit | dispatcher.py | Extended AgentResult serialization |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Token counts not available | Medium | Low | Graceful fallback to unknown tier |

## 7. Dependencies

- [ ] None (but benefits from #687 agent registry)

## 8. Backward Compatibility

Additive only — existing AgentResult fields unchanged, new fields optional.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New engine module |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Extend AgentResult over separate health channel | Simpler, uses existing pipeline |
