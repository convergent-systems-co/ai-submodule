# Workflow: API Design

Designing or evolving an API, from requirements through implementation and consumer documentation.

## Prerequisites

- API need (new API, new endpoint, or changes to existing API)
- Knowledge of consumers (who will call this API)
- System context (what services/data are involved)

## Phases

1. **Requirements** → `[API-1]` — **GATE**
2. **Contract Design** → `[API-2]` — **GATE**
3. **Consumer Review** → `[API-3]` — **GATE**
4. **Implementation** → `[API-4]`
5. **Documentation** → `[API-5]` — **GATE**

---

## Phase 1: Requirements

> **Adopt persona:** `governance/personas/leadership/product-manager.md`
> **Secondary persona:** `governance/personas/architecture/api-designer.md`

### Input

- API need description
- Known consumers and their use cases
- Existing API surface (if evolving an API)

### Process

1. Identify all consumer use cases
2. Define the operations needed (CRUD, actions, queries)
3. Identify data entities involved
4. Define non-functional requirements (latency, rate limits, auth)
5. Identify backwards compatibility constraints (if evolving)

### Output

**Artifact `[API-1]: API Requirements`**

```
## Purpose
<What this API enables>

## Consumers
- <Consumer 1> — <use case>
- <Consumer 2> — <use case>
- ...

## Operations Needed
- <Operation> — <description>
- ...

## Data Entities
- <Entity> — <key fields>
- ...

## Non-Functional Requirements
- **Auth:** <method>
- **Latency:** <target>
- **Rate limits:** <if applicable>
- **Versioning:** <strategy>

## Compatibility Constraints
<Breaking change policy, deprecation approach, or "New API — no constraints">
```

### GATE

**Stop.** Present `[API-1]` for review.

**Approval criteria:** All consumer use cases are captured. Operations map to real needs. Non-functional requirements are defined.

- **Approved** → proceed to Phase 2
- **Revise** → address feedback, re-present `[API-1]`

---

## Phase 2: Contract Design

> **Adopt persona:** `governance/personas/architecture/api-designer.md`

### Input

- `[API-1]: API Requirements`

### Process

1. Design the endpoint structure (paths, methods)
2. Define request/response schemas for each endpoint
3. Design error responses and status codes
4. Define pagination, filtering, sorting patterns (if applicable)
5. Specify authentication and authorization model
6. Ensure consistency with existing API conventions

### Output

**Artifact `[API-2]: API Contract`**

```
## Base Path
<e.g., /api/v2/resources>

## Endpoints

### <METHOD> <path>
**Description:** <what it does>
**Auth:** <required role/scope>
**Request:**
```json
<request body schema>
```
**Response (200):**
```json
<response body schema>
```
**Errors:**
- <status code> — <when this occurs>
- ...

### <METHOD> <path>
...

## Common Patterns
- **Pagination:** <approach>
- **Filtering:** <approach>
- **Error format:** <standard error shape>

## Breaking Changes
<None, or list of breaking changes with migration path>
```

### GATE

**Stop.** Present `[API-2]` for review.

**Approval criteria:** Endpoints cover all operations from `[API-1]`. Schemas are complete. Error cases are handled. Naming is consistent.

- **Approved** → proceed to Phase 3
- **Revise** → address feedback, re-present `[API-2]`

---

## Phase 3: Consumer Review

> **Invoke panel:** `governance/prompts/reviews/api-design-review.md`

### Input

- `[API-1]: API Requirements`
- `[API-2]: API Contract`

### Process

1. Review the contract from each consumer's perspective
2. Verify each use case from `[API-1]` can be achieved with the contract
3. Identify ergonomic issues (too many calls needed, awkward shapes, missing fields)
4. Check for common API design pitfalls
5. Validate naming conventions and consistency

### Output

**Artifact `[API-3]: Consumer Review Feedback`**

```
## Use Case Coverage
- <Use case 1> — <Covered / Gap identified>
- ...

## Ergonomic Issues
- <Issue and suggestion>
- ...

## Design Concerns
- [severity] <concern>
- ...

## Verdict
<Approved / Changes Requested>

## Required Changes (if any)
- <Change>
```

### GATE

**Stop.** Present `[API-3]` for review.

**Approval criteria:** All use cases are covered. No blocking ergonomic issues. Verdict is "Approved."

- **Approved** → proceed to Phase 4
- **Changes Requested** → revise contract in Phase 2, then re-present at Phase 3

---

## Phase 4: Implementation

> **Adopt persona:** `governance/personas/domain/backend-engineer.md`
> **Invoke prompt:** `governance/prompts/plan.md`

### Input

- `[API-2]: API Contract`
- `[API-3]: Consumer Review Feedback` (final approved version)

### Process

1. Plan the implementation (routes, controllers, validation, persistence)
2. Implement endpoints following the approved contract exactly
3. Add input validation matching the contract schemas
4. Implement error handling matching the contract error definitions
5. Run tests

### Output

**Artifact `[API-4]: Implementation Summary`**

```
## Files Created/Modified
- `path/to/file` — <description>
- ...

## Endpoint Implementation Status
- <METHOD> <path> — <Implemented / Partial>
- ...

## Test Results
<Pass/fail summary>

## Deviations from Contract
<None, or deviations with justification>
```

---

## Phase 5: Documentation

> **Adopt persona:** `governance/personas/documentation/documentation-writer.md`
> **Secondary persona:** `governance/personas/specialist/api-consumer.md`

### Input

- `[API-1]: API Requirements`
- `[API-2]: API Contract`
- `[API-4]: Implementation Summary`

### Process

1. Write consumer-facing API documentation
2. Include authentication setup, quickstart, and examples for each endpoint
3. Document error handling and common pitfalls
4. Write from the consumer's perspective — what do they need to accomplish?
5. Include code examples in relevant languages

### Output

**Artifact `[API-5]: API Documentation`**

```
## Documentation Location
<path or URL>

## Contents
- Getting Started / Authentication
- Endpoint Reference (all endpoints with examples)
- Error Handling Guide
- Migration Guide (if evolving existing API)

## Code Examples Included
- <language> — <which endpoints>
- ...
```

### GATE

**Stop.** Present `[API-5]` for review.

**Approval criteria:** Documentation covers all endpoints. Examples are accurate and runnable. Consumer perspective is maintained throughout.

- **Approved** → documentation is complete
- **Revise** → address feedback, re-present `[API-5]`
