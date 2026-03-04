# Governance Layers

The Dark Forge governance architecture consists of five layers, each building on the one below.

```mermaid
graph TB
    subgraph Evolution["5. Evolution Governance"]
        E1[Feedback Loops]
        E2[Metric Collection]
        E3[Policy Refinement]
    end

    subgraph Runtime["4. Runtime Governance"]
        R1[Context Management]
        R2[Capacity Signals]
        R3[Circuit Breakers]
        R4[Gate Checks]
    end

    subgraph Execution["3. Execution Governance"]
        X1[Policy Engine]
        X2[Panel Emissions]
        X3[Merge Decisions]
        X4[Run Manifests]
    end

    subgraph Cognitive["2. Cognitive Governance"]
        C1[Review Panels - 21]
        C2[Personas - 6]
        C3[Prompts - 12]
        C4[Shared Perspectives]
    end

    subgraph Intent["1. Intent Governance"]
        I1[project.yaml]
        I2[Policy Profiles - 5]
        I3[Schemas]
        I4[CLAUDE.md / Instructions]
    end

    Evolution --> Runtime
    Runtime --> Execution
    Execution --> Cognitive
    Cognitive --> Intent

    style Intent fill:#e8f5e9,stroke:#2e7d32
    style Cognitive fill:#e3f2fd,stroke:#1565c0
    style Execution fill:#fff3e0,stroke:#e65100
    style Runtime fill:#fce4ec,stroke:#c62828
    style Evolution fill:#f3e5f5,stroke:#6a1b9a
```

## Layer Descriptions

| Layer | Purpose | Key Artifacts |
|-------|---------|---------------|
| **Intent** | Define what governance means for this project | project.yaml, policy profiles, schemas |
| **Cognitive** | Shape how AI agents think about code | Review prompts, personas, shared perspectives |
| **Execution** | Make deterministic merge decisions | Policy engine, panel emissions, run manifests |
| **Runtime** | Keep agents within resource bounds | Context tiers, gate checks, circuit breakers |
| **Evolution** | Improve governance over time | Feedback loops, metrics, policy refinement |
