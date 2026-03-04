# ADR-001: Deterministic Policy Engine

**Status:** Accepted
**Date:** 2024-06-01 (retroactive)
**Author:** Dark Forge Team

---

## Context

The Dark Forge needed a mechanism to evaluate panel review outputs and produce merge decisions. Two fundamental approaches were available: (1) let AI models interpret policy rules expressed in natural language, or (2) build a deterministic engine that evaluates structured data against machine-readable policy profiles.

AI-interpreted policy carries inherent risks. Large language models hallucinate, exhibit inconsistent behavior across invocations, and cannot guarantee that the same input produces the same output. For governance decisions that affect production deployments and compliance posture, non-determinism is unacceptable. A merge decision must be reproducible: given the same panel emissions and the same policy profile, the engine must always produce the same verdict.

The platform also needed to support multiple risk profiles -- from permissive defaults for internal tools to strict SOC2/PCI-DSS/HIPAA/GDPR controls for financial and healthcare applications -- without requiring AI models to understand regulatory nuance.

## Decision

All policy evaluation is performed by a deterministic Python engine (`governance/engine/policy_engine.py`) that reads structured YAML policy profiles (`governance/policy/`) and evaluates them against JSON panel emissions validated by `governance/schemas/panel-output.schema.json`. AI models never interpret, evaluate, or override policy rules.

The engine implements:
- **Weighted confidence aggregation** across panels (configurable per profile)
- **Risk aggregation** using highest-severity-wins with count-based escalation
- **Deterministic exit codes**: 0 = auto_merge, 1 = block, 2 = human_review_required, 3 = auto_remediate
- **Rule-by-rule audit logging** for compliance replay
- **Run manifests** as immutable decision records

Five policy profiles codify distinct risk tolerances:
- `default.yaml` -- standard risk, auto-merge with conditions
- `fin_pii_high.yaml` -- SOC2/PCI-DSS/HIPAA/GDPR, auto-merge disabled
- `infrastructure_critical.yaml` -- mandatory architecture and SRE review
- `fast-track.yaml` -- lightweight profile for trivial changes (docs, typos, chores)
- `reduced_touchpoint.yaml` -- near-full autonomy (Phase 5e)

## Consequences

### Positive

- Every merge decision is reproducible and auditable -- same emissions, same profile, same verdict
- Regulatory compliance is provable: auditors can replay the engine against historical emissions
- Policy profiles are additive -- new profiles can be created without modifying the engine
- The cognitive/enforcement boundary is sharp: AI generates findings, deterministic code makes decisions
- No risk of AI hallucinating a "pass" verdict on a failing security review

### Negative

- The engine must be maintained as Python code, adding a runtime dependency (`pyyaml`, `jsonschema`)
- Policy changes require YAML editing rather than natural-language instructions
- Complex conditional logic (e.g., "block if two high-risk panels AND cost exceeds threshold") must be expressible in YAML, which can become verbose

### Neutral

- Panel scoring logic currently lives in cognitive artifacts (review prompts) rather than the engine -- this boundary may shift in the future (see `docs/decisions/README.md`, ADR-008)
- The engine is the single piece of executable code in an otherwise configuration-only repository

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| AI-interpreted policy (natural language rules) | Non-deterministic; same input can produce different outputs; hallucination risk on compliance-critical decisions; not auditable |
| Hybrid approach (AI proposes, human confirms) | Adds latency to every merge; defeats the goal of autonomous delivery; human bottleneck at scale |
| External policy engine (OPA/Rego) | Additional infrastructure dependency; YAML profiles are simpler for the governance domain; Rego learning curve for contributors |

## References

- `governance/engine/policy_engine.py` -- the deterministic engine (1,701 lines)
- `governance/policy/default.yaml` -- baseline policy profile
- `governance/policy/fin_pii_high.yaml` -- high-compliance profile
- `governance/policy/infrastructure_critical.yaml` -- infrastructure-focused profile
- `governance/policy/reduced_touchpoint.yaml` -- Phase 5e near-autonomy profile
- `governance/schemas/panel-output.schema.json` -- emission schema the engine validates against
- `docs/decisions/README.md` (ADR-002: Three Artifact Types) -- the cognitive/enforcement boundary
- `docs/decisions/README.md` (ADR-008: Panel Pass/Fail Criteria) -- scoring system design
