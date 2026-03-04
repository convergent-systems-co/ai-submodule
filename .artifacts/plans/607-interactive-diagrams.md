# Plan: Add interactive architectural diagrams

**Issue:** #607
**Type:** Feature
**Priority:** Medium

## Problem

Complex architecture with zero interactive visualizations. DACH has 27.

## Solution

Create Mermaid-based diagrams embedded in markdown for GitHub rendering, plus a standalone HTML page using Mermaid.js for interactive viewing. Cover the 6 key architectural views.

## Deliverables

1. `docs/architecture/diagrams/governance-layers.md` — 5-layer governance model
2. `docs/architecture/diagrams/orchestrator-state-machine.md` — 6-phase state machine
3. `docs/architecture/diagrams/agent-hierarchy.md` — persona hierarchy
4. `docs/architecture/diagrams/policy-engine-flow.md` — emission to decision flow
5. `docs/architecture/diagrams/capacity-model.md` — tier model
6. `docs/architecture/diagrams/index.html` — interactive HTML viewer with all diagrams
