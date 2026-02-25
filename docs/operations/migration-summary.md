# Dark Factory Governance — Migration Summary

## Required Repo Structure Changes

### New Directories

| Directory | Purpose | Contents |
|-----------|---------|----------|
| `docs/` | Architecture and design documents | 7 governance documents |
| `governance/schemas/` | JSON Schema enforcement artifacts | panel-output, run-manifest schemas |
| `governance/policy/` | Deterministic policy profiles | default, fin_pii_high, infrastructure_critical |
| `governance/manifests/` | Append-only audit trail | Run manifests (one per merge decision) |
| `governance/personas/panels/` | Formal review panel definitions | copilot-review.md |
| `governance/personas/governance/` | Governance-specific personas | Governance Auditor, Policy Evaluator |
| `governance/personas/agentic/` | Autonomous agent personas | Code Manager, Coder |

### New Files

| File | Type | Purpose |
|------|------|---------|
| `docs/architecture/governance-model.md` | Cognitive | 5-layer governance architecture |
| `docs/governance/artifact-classification.md` | Cognitive | Cognitive/Enforcement/Audit artifact taxonomy |
| `docs/architecture/context-management.md` | Cognitive | JIT loading, context budgets, reset protection |
| `docs/architecture/runtime-feedback.md` | Cognitive | Phase 5 design: drift detection, incident-to-DI |
| `docs/operations/autonomy-metrics.md` | Cognitive | Autonomy index, weekly reporting specification |
| `docs/configuration/ci-gating.md` | Cognitive | CI checks, branch protection, auto-merge config |
| `docs/governance/naming-review.md` | Cognitive | Persona/panel naming consistency proposals |
| `governance/schemas/panel-output.schema.json` | Enforcement | Structured emission validation schema |
| `governance/schemas/run-manifest.schema.json` | Enforcement | Merge audit manifest validation schema |
| `governance/policy/default.yaml` | Enforcement | Baseline policy profile |
| `governance/policy/fin_pii_high.yaml` | Enforcement | Financial/PII compliance profile |
| `governance/policy/infrastructure_critical.yaml` | Enforcement | Infrastructure stability profile |
| `governance/policy/README.md` | Cognitive | Policy framework documentation |
| `governance/personas/panels/copilot-review.md` | Cognitive | Copilot as formal governance panel |
| `governance/personas/governance/governance-auditor.md` | Cognitive | Pipeline audit persona |
| `governance/personas/governance/policy-evaluator.md` | Cognitive | Deterministic policy application persona |
| `governance/personas/agentic/code-manager.md` | Cognitive | Orchestration persona |
| `governance/personas/agentic/coder.md` | Cognitive | Execution persona |
| `governance/prompts/templates/plan-template.md` | Cognitive | Standardized plan template |
| `governance/manifests/.gitkeep` | — | Placeholder for manifest directory |

### Modified Files

| File | Change |
|------|--------|
| `README.md` | Rewritten to document governance platform |
| `governance/personas/index.md` | Added Governance, Agentic, and Copilot Review entries |

### Removed Files

| File | Reason |
|------|--------|
| `mcp/servicenow-mcp/servicenow_mcp.egg-info/*` | Build artifact cruft |

## Risk Areas

| Risk | Severity | Mitigation |
|------|----------|------------|
| Context window overflow from loading too many personas | Medium | Context management tiers with JIT loading (docs/architecture/context-management.md) |
| Policy profiles are not yet machine-executable | Medium | Profiles are declarative YAML; a policy engine runtime needs to be built |
| Structured emissions require panel modification | Medium | Panels continue emitting Markdown; JSON block is appended, not replacing |
| Naming renames break existing project.yaml references | Low | Renames are proposed only, not executed (docs/governance/naming-review.md) |
| jm-compliance.yml cannot be modified | Low | New CI workflow runs alongside it, no conflicts |
| Manifest storage grows unbounded | Low | Retention policy needed; gitignore manifests from submodule, store per-repo |
| Override procedure requires cultural adoption | Medium | Document and train; start with logging-only mode |

## Migration Steps

### Phase 4a (Current Deliverables)

1. **Merge this branch** — All governance framework files are in place
2. **Update consuming repos** — `git submodule update --remote .ai` in each project
3. **Configure project.yaml** — Add `governance.policy_profile` to each project
4. **Add CI workflow** — Copy `dark-factory-governance.yml` from ci-gating-blueprint into each repo's `.github/workflows/`
5. **Configure branch protection** — Add Dark Factory status checks as required
6. **Train teams** — Introduce the governance model, plan template, and override procedure

### Phase 4b (Next Iteration)

1. **Build policy engine runtime** — Implement YAML policy evaluation as a CLI tool or GitHub Action
2. **Implement structured emission parsing** — Extract JSON from panel output Markdown
3. **Implement manifest generation** — Produce run-manifest.schema.json artifacts in CI
4. **Execute proposed renames** — If approved, rename persona directories per naming-review.md
5. **Implement instruction decomposition** — Split instructions.md per context-management.md
6. **Add checkpoint system** — Implement `.checkpoints/` for context reset recovery

### Phase 5 (Future)

1. **Implement runtime anomaly ingestion** — Per runtime-feedback-architecture.md
2. **Build incident-to-DI generator** — Automatic Design Intent creation from incidents
3. **Implement drift detection** — Baseline capture and deviation monitoring
4. **Enable automatic panel re-execution** — With circuit breakers and rate limiting
5. **Build autonomy dashboard** — Weekly metrics per autonomy-metrics.md
6. **Achieve self-evolution** — Governance model proposes its own improvements

## Breaking Changes

**None.** All changes are additive:

- Existing personas, prompts, workflows, and templates are unchanged
- No file paths were renamed (renames are proposed but not executed)
- The `jm-compliance.yml` workflow is untouched
- `config.yaml` and `instructions.md` are unchanged
- New directories and files do not conflict with existing structure
- Consuming repositories continue to work without changes until they opt into governance features

## Repo Rename

The repository is currently `SET-Apps/ai-submodule`. Given its evolution into a governance platform, renaming is recommended. Top candidates:

| Name | Pros | Cons |
|------|------|------|
| `dark-factory` | Aligns with governance model, memorable | May not be immediately clear to newcomers |
| `ai-governance` | Descriptive, professional | Less distinctive |
| `forge` | Short, manufacturing metaphor | May be confused with other tools |

The rename should be done via GitHub repository settings and requires updating the submodule URL in all consuming repos:

```bash
# In each consuming repo
git submodule set-url .ai git@github.com:SET-Apps/<new-name>.git
git commit -m "Update .ai submodule URL after rename"
```

## Deliverable Checklist

| # | Deliverable | File | Status |
|---|-------------|------|--------|
| 1 | Governance model document | `docs/architecture/governance-model.md` | Complete |
| 2 | Artifact classification | `docs/governance/artifact-classification.md` | Complete |
| 3 | Structured emission schema | `governance/schemas/panel-output.schema.json` | Complete |
| 4 | Policy framework | `governance/policy/` (3 profiles + README) | Complete |
| 5 | Copilot panel design | `governance/personas/panels/copilot-review.md` | Complete |
| 6 | Manifest schema | `governance/schemas/run-manifest.schema.json` | Complete |
| 7 | CI gating blueprint | `docs/configuration/ci-gating.md` | Complete |
| 8 | Runtime feedback architecture | `docs/architecture/runtime-feedback.md` | Complete |
| 9 | Autonomy metrics specification | `docs/operations/autonomy-metrics.md` | Complete |
| + | Context management strategy | `docs/architecture/context-management.md` | Complete |
| + | Naming review | `docs/governance/naming-review.md` | Complete |
| + | Plan template | `governance/prompts/templates/plan-template.md` | Complete |
| + | Code Manager persona | `governance/personas/agentic/code-manager.md` | Complete |
| + | Coder persona | `governance/personas/agentic/coder.md` | Complete |
| + | Governance Auditor persona | `governance/personas/governance/governance-auditor.md` | Complete |
| + | Policy Evaluator persona | `governance/personas/governance/policy-evaluator.md` | Complete |
| + | Updated README | `README.md` | Complete |
| + | Updated personas index | `governance/personas/index.md` | Complete |
