# Capacity Signal Model

The four-tier context capacity model prevents context overflow and ensures clean shutdowns.

```mermaid
graph TB
    subgraph Signals["Capacity Signals"]
        TC[Tool Calls]
        TN[Turns]
        IC[Issues Completed]
    end

    subgraph Classification["Tier Classification"]
        CL[classify_tier]
    end

    subgraph Tiers["Capacity Tiers"]
        G["GREEN<br/>Normal operation"]
        Y["YELLOW<br/>Approaching limits"]
        O["ORANGE<br/>Checkpoint required"]
        R["RED<br/>Emergency stop"]
    end

    Signals --> Classification
    Classification --> Tiers

    style G fill:#c8e6c9,stroke:#2e7d32
    style Y fill:#fff9c4,stroke:#f9a825
    style O fill:#ffe0b2,stroke:#e65100
    style R fill:#ffcdd2,stroke:#c62828
```

## Tier Thresholds

```mermaid
graph LR
    subgraph Green["GREEN"]
        GT["tool_calls < 300<br/>turns < 30<br/>issues < 5"]
    end

    subgraph Yellow["YELLOW"]
        YT["tool_calls 300-500<br/>turns 30-50<br/>issues 5-8"]
    end

    subgraph Orange["ORANGE"]
        OT["tool_calls 500-700<br/>turns 50-70<br/>issues 8-10"]
    end

    subgraph Red["RED"]
        RT["tool_calls >= 700<br/>turns >= 70<br/>issues >= 10"]
    end

    Green --> Yellow --> Orange --> Red

    style Green fill:#c8e6c9,stroke:#2e7d32
    style Yellow fill:#fff9c4,stroke:#f9a825
    style Orange fill:#ffe0b2,stroke:#e65100
    style Red fill:#ffcdd2,stroke:#c62828
```

## Phase-Specific Gate Actions

| Phase | GREEN | YELLOW | ORANGE | RED |
|-------|-------|--------|--------|-----|
| 1 (Triage) | PROCEED | PROCEED | CHECKPOINT | EMERGENCY_STOP |
| 2 (Plan) | PROCEED | PROCEED | CHECKPOINT | EMERGENCY_STOP |
| 3 (Dispatch) | PROCEED | SKIP_DISPATCH | CHECKPOINT | EMERGENCY_STOP |
| 4 (Collect) | PROCEED | PROCEED | CHECKPOINT | EMERGENCY_STOP |
| 5 (Merge) | PROCEED | PROCEED | CHECKPOINT | EMERGENCY_STOP |
