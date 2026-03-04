# Agent Persona Hierarchy

The agentic architecture supports two modes: Standard (flat) and Project Manager (hierarchical).

## Standard Mode

```mermaid
graph TB
    O[Orchestrator CLI] --> CM1[Tech Lead 1]
    O --> CM2[Tech Lead 2]
    O --> CM3[Tech Lead 3]

    CM1 --> C1[Coder]
    CM1 --> C2[Coder]
    CM2 --> C3[Coder]
    CM2 --> C4[Coder]
    CM3 --> C5[Coder]

    O --> T[Tester]
    O --> DE[DevOps Engineer]

    style O fill:#e8eaf6,stroke:#283593
    style CM1 fill:#e3f2fd,stroke:#1565c0
    style CM2 fill:#e3f2fd,stroke:#1565c0
    style CM3 fill:#e3f2fd,stroke:#1565c0
    style T fill:#fce4ec,stroke:#c62828
    style DE fill:#e8f5e9,stroke:#2e7d32
```

## Project Manager Mode

```mermaid
graph TB
    PM[Project Manager] --> DE[DevOps Engineer]
    PM --> CM1[Tech Lead 1]
    PM --> CM2[Tech Lead 2]
    PM --> CM3[Tech Lead 3]

    CM1 --> C1[Coder]
    CM1 --> C2[Coder]
    CM1 --> IC1[IaC Engineer]

    CM2 --> C3[Coder]
    CM2 --> C4[Coder]

    CM3 --> C5[Coder]
    CM3 --> T1[Tester]

    style PM fill:#f3e5f5,stroke:#6a1b9a
    style DE fill:#e8f5e9,stroke:#2e7d32
    style CM1 fill:#e3f2fd,stroke:#1565c0
    style CM2 fill:#e3f2fd,stroke:#1565c0
    style CM3 fill:#e3f2fd,stroke:#1565c0
    style T1 fill:#fce4ec,stroke:#c62828
    style IC1 fill:#fff3e0,stroke:#e65100
```

## Persona Capabilities

| Persona | Role | Dispatch Context |
|---------|------|-----------------|
| **Project Manager** | Orchestrates code managers, background DevOps | PM mode only |
| **DevOps Engineer** | CI/CD, infrastructure, repo config | Background task |
| **Tech Lead** | Plans, dispatches, reviews a batch of issues | Manages N coders |
| **Coder** | Implements a single issue in a worktree | Isolated branch |
| **IaC Engineer** | Infrastructure-as-code (Terraform, Bicep) | Specialized coder |
| **Tester** | Evaluates PR quality, provides feedback | Review gate |
