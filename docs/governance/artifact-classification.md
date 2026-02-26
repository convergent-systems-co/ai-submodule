# Artifact Classification Model

## Overview

All artifacts in the `.ai/` system fall into three categories. Each category has distinct storage, validation, versioning, and context-loading requirements.

## Artifact Types

### 1. Cognitive Artifacts (Markdown)

**Purpose:** Preserve reasoning, context, and flexible thinking. These are consumed by AI agents as instruction context and by humans as documentation.

**Format:** Markdown (`.md`)

**Characteristics:**
- Prose-based, flexible structure
- Interpreted by AI models at runtime
- Human-readable and editable
- No schema validation (content is free-form within conventions)
- Loaded JIT based on task type (see Context Management)

**Directory Mapping:**

| Directory | Contents | Loading Strategy |
|-----------|----------|-----------------|
| `governance/personas/agentic/` | Agentic persona definitions | Load only activated personas per `project.yaml` |
| `governance/prompts/reviews/` | Consolidated review prompts | Load only when panel is invoked |
| `governance/prompts/` | Single-task prompt templates | Load on-demand per workflow phase |
| `governance/prompts/workflows/` | Multi-phase orchestration workflows | Load one phase at a time |
| `governance/templates/` | Language-specific conventions | Load once at session start based on project language |
| `instructions.md` | Base AI instructions | Always loaded (compact, < 500 tokens) |
| `docs/` | Architecture and design documents | Reference only, not loaded into agent context |
| `.governance/plans/` | Implementation plans | Load only the active plan for the current task |

**Versioning:** Git commit SHA. Cognitive artifacts evolve with the submodule version.

**Manifest Requirement:** The `persona_set_commit` field in the run manifest records which version of cognitive artifacts was used.

### 2. Enforcement Artifacts (JSON/YAML)

**Purpose:** Provide deterministic, machine-parseable rules and schemas that the governance pipeline evaluates without interpretation.

**Format:** JSON Schema (`.schema.json`), YAML (`.yaml`)

**Characteristics:**
- Structured, schema-validated
- Evaluated programmatically (no AI interpretation required)
- Changes require backward compatibility analysis
- Version-locked per policy profile

**Directory Mapping:**

| Directory | Contents | Validation |
|-----------|----------|------------|
| `governance/schemas/` | JSON Schema definitions for structured outputs | Self-validating (JSON Schema draft 2020-12) |
| `governance/policy/` | Policy profiles with deterministic rules | YAML structure validated against policy schema |
| `config.yaml` | System configuration (symlinks, defaults) | YAML structure validated |
| `governance/templates/*/project.yaml` | Project configuration templates | YAML structure validated |

**Versioning:** Semantic versioning in the `profile_version` or `version` field. Breaking changes require major version bump.

**Manifest Requirement:** The `policy_profile_used` and `panel_graph_version` fields record which enforcement artifacts were active.

### 3. Audit Artifacts (Hybrid)

**Purpose:** Provide complete, reproducible records of governance decisions. Combine structured data (for programmatic replay) with human-readable context.

**Format:** JSON (structured) + Markdown (contextual)

**Characteristics:**
- Immutable once created
- Must be reproducible from inputs alone
- Stored per-run, not edited after creation
- Retained for compliance audit periods
- Manifests are protected via CODEOWNERS. See [manifest-lifecycle.md](manifest-lifecycle.md) for enforcement details.

For detailed retention policy, immutability enforcement mechanisms, and panel name validation notes, see [Manifest Lifecycle](manifest-lifecycle.md).

**Directory Mapping:**

| Directory | Contents | Retention |
|-----------|----------|-----------|
| `governance/manifests/` | Run manifests (JSON per `run-manifest.schema.json`) | Permanent — required for audit replay |
| Panel outputs | Structured emissions (JSON per `panel-output.schema.json`) | Retained with the PR/merge they belong to |
| `.governance/plans/` | Implementation plans (Markdown) | Retained with the branch/PR lifecycle |

**Versioning:** Each audit artifact has a unique `manifest_id` or timestamp. They are append-only.

**Manifest Requirement:** Audit artifacts ARE the manifest. They reference all other artifacts used in the decision.

## Structured Emission Schema

All panels must emit structured output conforming to `governance/schemas/panel-output.schema.json`. The emission is appended after the Markdown reasoning in the panel output.

**Format:**

```
[Markdown reasoning from panel personas]

---

<!-- STRUCTURED_EMISSION_START -->
```json
{
  "panel_name": "code-review",
  "panel_version": "1.0.0",
  ...
}
```
<!-- STRUCTURED_EMISSION_END -->
```

**Validation Rule:** If the `STRUCTURED_EMISSION_START` / `STRUCTURED_EMISSION_END` markers are missing or the JSON does not validate against the schema, panel execution is considered failed.

## Context Loading Rules

To minimize context window usage and prevent instruction loss during context resets:

1. **Base context** (always loaded): `instructions.md` + active `project.yaml` — kept under 1,000 tokens combined
2. **Task context** (loaded JIT): Only the personas, prompts, and workflow phases relevant to the current task
3. **Panel context** (loaded per-panel): Only the panel definition and its constituent persona definitions
4. **Policy context** (never loaded into AI context): Evaluated programmatically, not by the AI model
5. **Audit context** (write-only): Generated as output, never loaded as input except for replay

See `docs/architecture/context-management.md` for the full JIT loading strategy.

## Summary Matrix

| Property | Cognitive | Enforcement | Audit |
|----------|-----------|-------------|-------|
| Format | Markdown | JSON/YAML | JSON + Markdown |
| Validation | Convention-based | Schema-validated | Schema-validated |
| Mutability | Editable | Versioned changes | Immutable |
| AI Interpretation | Yes (JIT loaded) | No (programmatic) | No (reference only) |
| Versioning | Git SHA | Semantic version | Unique ID per run |
| Context Loading | On-demand | Not loaded | Not loaded |
| Human Readable | Yes | Partially | Yes |
