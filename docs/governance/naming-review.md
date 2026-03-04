# Persona and Panel Naming Review

> **Note:** This is a historical decision record. The individual persona and panel files referenced below were deprecated (Issue #220) and removed (Issue #257). Review prompts are now consolidated at `governance/prompts/reviews/`.

## Review Criteria

Names should be:
1. **Instantly interpretable** — a new user (human or AI) understands the role from the name alone
2. **Consistent** — follow a uniform naming convention across all categories
3. **Distinct** — no two names are easily confused
4. **Action-oriented** — suggest what the persona does, not just what it is

## Current Naming Issues

### Issue 1: "Reviewer" vs "Code Reviewer" Ambiguity

`governance/personas/code_quality/reviewer.md` and `governance/personas/code_quality/code-reviewer.md` are too similar.

| Current Name | Role | Problem |
|-------------|------|---------|
| Reviewer | Broad quality review — readability, naming, structure | Name is generic, overlaps with Code Reviewer |
| Code Reviewer | Production-level review — correctness, security, concurrency | Name implies it subsumes Reviewer |

**Recommendation:** Rename `reviewer.md` to `style-reviewer.md` with persona name "Style Reviewer". This clarifies that it focuses on readability, naming, and structural conventions rather than correctness.

### Issue 2: "Round Tables" vs "Panels" Inconsistency

The plan document uses "panels" throughout. The codebase uses "round_tables". The Copilot integration uses "panels". This creates confusion about what to call multi-persona reviews.

| Term | Used In | Context |
|------|---------|---------|
| Round Tables | `governance/personas/round_tables/` directory | Original codebase |
| Panels | Governance plan, `governance/personas/panels/` directory | New governance model |
| Review | Panel filenames (`code-review.md`) | File names |

**Recommendation:** Standardize on "panels" as the term. Rename `governance/personas/round_tables/` to `governance/personas/panels/`. Update `governance/personas/index.md` to use "Panels" instead of "Round Tables". The governance model already uses "panels" exclusively.

### Issue 3: Directory Name Inconsistencies

Category directories use different conventions:

| Directory | Convention | Issue |
|-----------|-----------|-------|
| `code_quality/` | snake_case | Inconsistent with kebab-case filenames |
| `compliance_governance/` | snake_case | Inconsistent with kebab-case filenames |
| `domain_specific/` | snake_case | Inconsistent with kebab-case filenames |
| `operations_reliability/` | snake_case | Long, could be shortened |
| `process_people/` | snake_case | Vague — "people" adds no clarity |
| `special_purpose/` | snake_case | Vague — everything is "special purpose" |

**Recommendation:** Rename directories to kebab-case for consistency with filenames. Shorten where possible:

| Current | Proposed | Rationale |
|---------|----------|-----------|
| `code_quality/` | `quality/` | Shorter, still clear |
| `compliance_governance/` | `compliance/` | "Governance" is now its own category |
| `domain_specific/` | `domain/` | Shorter, still clear |
| `operations_reliability/` | `operations/` | Shorter, "reliability" is implicit |
| `process_people/` | `leadership/` | More descriptive of the actual roles |
| `special_purpose/` | `specialist/` | More descriptive |
| `round_tables/` | `governance/personas/panels/` | Aligns with governance model terminology |

### Issue 4: New Persona Categories

The governance model introduces new categories that need clear naming:

| Directory | Contents | Naming |
|-----------|----------|--------|
| `governance/` | Governance Auditor, Policy Evaluator | Clear and specific |
| `agentic/` | Tech Lead, Coder | Clear — these are autonomous agent roles |

These are well-named. No changes needed.

### Issue 5: Panel File Names

Panel filenames are clear and consistent (`code-review.md`, `security-review.md`, etc.). The `-review` suffix works well.

One addition: the new `copilot-review.md` in `governance/personas/panels/` (not `governance/personas/panels/`) is in a different directory than the other panel definitions. This could cause confusion.

**Recommendation:** After renaming `round_tables/` to `governance/personas/panels/`, move `copilot-review.md` from the top-level `governance/personas/panels/` directory into `governance/personas/panels/` to keep all panel definitions together. The top-level `governance/personas/panels/` directory can then be removed.

## Summary of Proposed Renames

### Directory Renames

| From | To |
|------|----|
| `governance/personas/code_quality/` | `governance/personas/quality/` |
| `governance/personas/compliance_governance/` | `governance/personas/compliance/` |
| `governance/personas/domain_specific/` | `governance/personas/domain/` |
| `governance/personas/operations_reliability/` | `governance/personas/operations/` |
| `governance/personas/process_people/` | `governance/personas/leadership/` |
| `governance/personas/special_purpose/` | `governance/personas/specialist/` |
| `governance/personas/round_tables/` | `governance/personas/panels/` |

### File Renames

| From | To |
|------|----|
| `governance/personas/code_quality/reviewer.md` | `governance/personas/quality/style-reviewer.md` |

### Moves

| From | To |
|------|----|
| `governance/personas/panels/copilot-review.md` | `governance/personas/panels/copilot-review.md` |

## Impact Assessment

- **Backward compatibility**: Any `project.yaml` files referencing old paths will need updating. The `config.yaml` symlink targets are unaffected.
- **Migration**: A simple find-and-replace in `project.yaml` files across consuming repositories.
- **Risk**: Low — these are path references in configuration, not runtime code.

## Decision

All renames have been executed as a single atomic commit. References in `governance/personas/index.md` and `README.md` have been updated.
