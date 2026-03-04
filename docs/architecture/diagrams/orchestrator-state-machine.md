# Orchestrator State Machine

The step-based orchestrator manages 6 phases with capacity-gated transitions.

```mermaid
stateDiagram-v2
    [*] --> Phase0: init_session()
    Phase0: Phase 0 - Checkpoint Recovery
    Phase1: Phase 1 - Pre-flight & Triage
    Phase2: Phase 2 - Parallel Planning
    Phase3: Phase 3 - Parallel Dispatch
    Phase4: Phase 4 - Collect & Review
    Phase5: Phase 5 - Merge & Loop Decision

    Phase0 --> Phase1: Fresh start
    Phase0 --> Phase2: Resume from checkpoint
    Phase0 --> Phase3: Resume from checkpoint

    Phase1 --> Phase2: issues_selected
    Phase2 --> Phase3: plans created
    Phase3 --> Phase4: agents dispatched
    Phase4 --> Phase5: PRs created/resolved
    Phase5 --> Phase1: Work remaining (Green/Yellow)
    Phase5 --> [*]: All done OR Orange+

    Phase1 --> [*]: Shutdown (Red)
    Phase2 --> [*]: Shutdown (Red)
    Phase3 --> [*]: Shutdown (Orange+)
    Phase4 --> [*]: Shutdown (Orange+)
```

## Gate Actions by Tier

```mermaid
graph LR
    subgraph Green["Green Tier"]
        G[PROCEED to all phases]
    end

    subgraph Yellow["Yellow Tier"]
        Y1[PROCEED to phases 1-4]
        Y2[SKIP_DISPATCH at phase 3]
    end

    subgraph Orange["Orange Tier"]
        O1[CHECKPOINT at any phase]
        O2[No new dispatch]
    end

    subgraph Red["Red Tier"]
        R[EMERGENCY_STOP]
    end

    style Green fill:#c8e6c9,stroke:#2e7d32
    style Yellow fill:#fff9c4,stroke:#f9a825
    style Orange fill:#ffe0b2,stroke:#e65100
    style Red fill:#ffcdd2,stroke:#c62828
```

## Phase Outputs

| Phase | Outputs Expected | Next Phase |
|-------|-----------------|------------|
| 0 | Resume phase | 1 (fresh) or N (resume) |
| 1 | issues_selected | 2 |
| 2 | plans | 3 |
| 3 | dispatched_task_ids | 4 |
| 4 | prs_created, prs_resolved | 5 |
| 5 | merged_prs | 1 (loop) or done |
