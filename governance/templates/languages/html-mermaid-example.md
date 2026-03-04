# Mermaid.js Integration Patterns for Governance Documentation

This example document demonstrates Mermaid.js diagram patterns commonly used in Dark Forge governance documentation. Use these as starting templates when creating architecture, flow, and relationship diagrams.

## Governance Pipeline Flow

```mermaid
flowchart TD
    A[Plan Created] --> B[Panels Execute]
    B --> C{All Panels Pass?}
    C -->|Yes| D[PR Created]
    C -->|No| E[Fix Issues]
    E --> B
    D --> F[Governance Workflow Runs]
    F --> G{Policy Decision}
    G -->|approved| H[Auto-Merge]
    G -->|human_review_required| I[Escalate to User]
    G -->|denied| J[Block Merge]
```

## Agent Communication Sequence

```mermaid
sequenceDiagram
    participant PM as Project Manager
    participant TL as Tech Lead
    participant C as Coder
    participant DW as Document Writer

    PM->>TL: ASSIGN (issue batch)
    TL->>C: ASSIGN (implementation task)
    C->>C: Create branch + implement
    C->>TL: RESULT (implementation complete)
    TL->>DW: ASSIGN (documentation update)
    DW->>DW: Detect staleness + fix
    DW->>TL: RESULT (docs updated)
    TL->>PM: RESULT (batch complete)
```

## Governance Layer Architecture

```mermaid
classDiagram
    class IntentLayer {
        +Plans
        +Issues
        +Requirements
    }
    class CognitiveLayer {
        +Personas
        +Prompts
        +Reviews
    }
    class ExecutionLayer {
        +PolicyEngine
        +Orchestrator
        +Panels
    }
    class RuntimeLayer {
        +CIWorkflows
        +BranchProtection
        +AutoMerge
    }
    class EvolutionLayer {
        +Metrics
        +Feedback
        +PolicyTuning
    }

    IntentLayer --> CognitiveLayer
    CognitiveLayer --> ExecutionLayer
    ExecutionLayer --> RuntimeLayer
    RuntimeLayer --> EvolutionLayer
```

## Issue Lifecycle State Diagram

```mermaid
stateDiagram-v2
    [*] --> Open: Issue created
    Open --> Planned: Plan written
    Planned --> InProgress: Coder assigned
    InProgress --> InReview: PR created
    InReview --> Approved: Panels pass
    Approved --> Merged: Auto-merge
    Merged --> [*]

    InReview --> InProgress: Feedback
    InProgress --> Blocked: Dependency
    Blocked --> InProgress: Unblocked
```

## Panel Dependency Relationships

```mermaid
erDiagram
    PLAN ||--o{ PANEL : triggers
    PANEL ||--|| EMISSION : produces
    EMISSION }|--|| POLICY_ENGINE : evaluated_by
    POLICY_ENGINE ||--o{ DECISION : outputs
    DECISION ||--o| PR_APPROVAL : controls

    PLAN {
        string id
        string issue_ref
        string status
    }
    PANEL {
        string name
        string prompt_path
        string type
    }
    EMISSION {
        string panel_name
        string risk_level
        json findings
    }
```

## Sprint Timeline

```mermaid
gantt
    title Governance Feature Delivery
    dateFormat YYYY-MM-DD
    section Planning
        Write plans           :plan, 2026-03-03, 1d
    section Implementation
        HTML template          :impl1, after plan, 1d
        Mermaid integration    :impl2, after plan, 1d
    section Review
        Panel reviews          :review, after impl2, 1d
        Documentation update   :docs, after review, 1d
    section Delivery
        PR + merge             :merge, after docs, 1d
```

## Standalone HTML Usage

For self-contained HTML reports, include Mermaid via CDN:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Governance Report</title>
</head>
<body>
    <h1>Architecture Overview</h1>

    <div class="mermaid" role="img" aria-label="System architecture showing three layers">
        flowchart LR
            A[Client] --> B[API Gateway]
            B --> C[Service Layer]
            C --> D[(Database)]
    </div>

    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({ startOnLoad: true });</script>
</body>
</html>
```

## Tips

- Keep diagrams focused -- one concept per diagram, not an entire system
- Use descriptive node labels, not abbreviations
- Add `aria-label` to every `<div class="mermaid">` container in HTML
- In Markdown, GitHub renders Mermaid natively -- no configuration needed
- For complex diagrams that exceed ~30 nodes, consider splitting into multiple diagrams
