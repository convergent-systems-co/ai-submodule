# Plan: Add guardrails to agentic CI workflows (#564)

## Scope

1. agentic-loop.yml: Reduce timeout from 120m to 60m, sleep from 30s to 10s
2. agentic-issue-worker.yml: Cap self-dispatch chains (max 3)
3. ado-sync.yml: Gate behind repo variable check (early exit if ADO disabled)
4. deploy-docs.yml & publish-dashboard.yml: Use distinct concurrency groups
