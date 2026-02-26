# Evaluate and Add Missing Personas and Panels

**Author:** Code Manager (agentic)
**Date:** 2026-02-21
**Status:** completed
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/53
**Branch:** itsfwcp/feat/53/evaluate-personas-panels

---

## 1. Objective

Audit existing personas/panels against issue requirements and create all missing artifacts to provide comprehensive governance coverage for the listed languages, platforms, and domains.

## 2. Rationale

The governance framework has 42 personas across 11 categories but lacks language-specific review personas. When reviewing code in Rust, Go, Python, etc., the system cannot invoke domain experts who understand language-specific idioms, safety patterns, and ecosystem conventions. A Cost Analyst Panel is also explicitly missing.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Add language knowledge to existing role-based personas | Yes | Role-based personas (code-reviewer, backend-engineer) are language-agnostic by design; language expertise is a separate axis |
| Create a single "polyglot" persona | Yes | Each language has distinct idioms, safety concerns, and ecosystem conventions that warrant dedicated personas |
| Skip platform personas (SharePoint, Power Platform) | Yes | Issue explicitly requests them |

## 3. Scope

### Gap Analysis

| Requested Domain | Existing Coverage | Action |
|-----------------|-------------------|--------|
| Rust | None | Create `language/rust-engineer.md` |
| Go | None | Create `language/go-engineer.md` |
| Documents (md) | documentation-reviewer, documentation-writer | Already covered |
| .NET/C# | None | Create `language/dotnet-engineer.md` |
| Python | None | Create `language/python-engineer.md` |
| JavaScript | None | Create `language/javascript-engineer.md` |
| TypeScript | None | Create `language/typescript-engineer.md` |
| Java | None | Create `language/java-engineer.md` |
| C++ (top 10) | None | Create `language/cpp-engineer.md` |
| PHP (top 10) | None | Create `language/php-engineer.md` |
| Swift (top 10) | None | Create `language/swift-engineer.md` |
| Kotlin (top 10) | None | Create `language/kotlin-engineer.md` |
| LLM | ml-engineer (traditional ML focus) | Create `domain/llm-engineer.md` |
| Dark Factories | code-manager, coder | Already covered |
| SharePoint | None | Create `platform/sharepoint-developer.md` |
| Power Platform | None | Create `platform/power-platform-developer.md` |
| Costing of AI/Azure | finops-analyst, finops-engineer, cost-optimizer | Already covered; add Cost Analysis Panel |
| Cost Analyst Panel | None | Create `panels/cost-analysis.md` |

### Files to Create

| File | Purpose |
|------|---------|
| `governance/personas/language/rust-engineer.md` | Rust-specific code review |
| `governance/personas/language/go-engineer.md` | Go-specific code review |
| `governance/personas/language/dotnet-engineer.md` | .NET/C#-specific code review |
| `governance/personas/language/python-engineer.md` | Python-specific code review |
| `governance/personas/language/javascript-engineer.md` | JavaScript-specific code review |
| `governance/personas/language/typescript-engineer.md` | TypeScript-specific code review |
| `governance/personas/language/java-engineer.md` | Java-specific code review |
| `governance/personas/language/cpp-engineer.md` | C++-specific code review |
| `governance/personas/language/php-engineer.md` | PHP-specific code review |
| `governance/personas/language/swift-engineer.md` | Swift-specific code review |
| `governance/personas/language/kotlin-engineer.md` | Kotlin-specific code review |
| `governance/personas/domain/llm-engineer.md` | LLM/prompt engineering specialist |
| `governance/personas/platform/sharepoint-developer.md` | SharePoint development |
| `governance/personas/platform/power-platform-developer.md` | Power Platform development |
| `governance/personas/panels/cost-analysis.md` | Cost Analyst Panel |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `CLAUDE.md` | Update persona count (42→57), category count (11→13), panel count (15→16) |
| `governance/schemas/panels.defaults.json` | Add cost-analysis panel defaults |
| `governance/docs/governance-model.md` | Update persona/panel counts if referenced |

### Files to Delete

N/A — all changes are additive.

## 4. Approach

1. Create `governance/personas/language/` directory with 11 language personas
2. Create `governance/personas/platform/` directory with 2 platform personas
3. Create `governance/personas/domain/llm-engineer.md`
4. Create `governance/personas/panels/cost-analysis.md` with pass/fail criteria
5. Add cost-analysis entry to `panels.defaults.json`
6. Update CLAUDE.md counts
7. Update governance model doc counts
8. Commit and push

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | All new files | Verify each persona follows the standard template format |
| Schema | panels.defaults.json | Verify JSON is valid after adding cost-analysis entry |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Persona template inconsistency | Low | Low | Use existing personas as template; maintain same section structure |
| Context capacity from large scope | Medium | Medium | Create files efficiently; checkpoint early if needed |

## 7. Dependencies

- [x] None — purely additive cognitive artifacts

## 8. Backward Compatibility

Fully additive. No existing files are modified in a breaking way. New personas and panels are opt-in via panel selection.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| ai-expert-review | Yes | Changes to governance artifacts |
| documentation-review | Yes | Large number of new markdown files |
| copilot-review | Yes | Standard PR review |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Separate language/ and platform/ categories | Language-specific and platform-specific personas are distinct axes from existing role-based categories |
| 2026-02-21 | Include top 10 languages beyond issue list | Issue says "any other language in top 10" — added C++, PHP, Swift, Kotlin |
| 2026-02-21 | LLM engineer under domain/ not language/ | LLM engineering is a domain concern, not a language |
