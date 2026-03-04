# Configuring GitHub Copilot for Auto-Fixing Issues

*Last updated: 2026-02-23. Copilot features evolve rapidly — verify against [official docs](https://docs.github.com/copilot) before implementing.*

## Overview

GitHub Copilot offers several mechanisms for detecting and fixing code issues. This document evaluates each mechanism, provides configuration steps, and recommends an integration approach for the Dark Forge governance workflow.

**Key finding:** As of early 2026, no Copilot mechanism fully auto-applies fixes without human review. Every path produces a suggestion or PR that requires approval. The governance workflow's current approach (Tech Lead reads Copilot comments, directs Coder to implement fixes) remains the most reliable automation strategy.

## Capabilities

### 1. Copilot Code Review (GA)

**What it does:** Automatically reviews PRs and posts inline suggestions with code changes.

**Auto-fix capability:** Suggestions require manual application. The "Implement suggestion" button (public preview) hands off to the Copilot coding agent, which creates a new PR — still requires review.

**Configuration:**
1. Enable Copilot Code Review in repository settings:
   - Settings > Rules > Rulesets > Add rule > Select "Copilot code review"
   - Enable "Run on each push" and optionally "Run on draft PRs"
2. No additional configuration needed — it runs automatically on PR events

**Integration with governance:** Already integrated. `governance/prompts/startup.md` Phase 4e fetches Copilot review comments, classifies them, and assigns fixes to the Coder persona via the Tech Lead. This is the current production flow.

### 2. Copilot Autofix for Code Scanning (GA)

**What it does:** When CodeQL detects security vulnerabilities, Copilot automatically generates fix suggestions with explanations and can create PRs.

**Auto-fix capability:** Generates fix PRs but does not merge them. Since October 2025 (public preview), you can assign alerts directly to Copilot, which autonomously creates remediation PRs.

**Configuration:**
1. Enable CodeQL code scanning:
   - Settings > Security > Code security > Code scanning > Enable
2. Copilot Autofix is enabled by default when CodeQL is active
3. To assign alerts to Copilot:
   - Navigate to a code scanning alert
   - Click "Assign to Copilot" (requires Copilot subscription and public preview opt-in)

**Supported languages:** C#, C/C++, Go, Java/Kotlin, Swift, JavaScript/TypeScript, Python, Ruby, Rust.

**Integration with governance:** The governance workflow's JM Compliance checks already run CodeQL. Copilot Autofix PRs would appear as separate PRs that enter startup.md Phase 1c (resolve open PRs) flow. No additional governance integration needed.

### 3. Copilot Coding Agent (GA)

**What it does:** Assign a GitHub issue to Copilot, and it autonomously creates a branch, implements code, and opens a PR.

**Auto-fix capability:** Creates PRs autonomously but requires human approval before CI workflows run ("Approve and run workflows" button).

**Configuration:**
1. Enable Copilot coding agent:
   - Organization settings > Copilot > Policies > Enable "Copilot coding agent"
2. Assign issues to Copilot via the GitHub UI or API:
   ```bash
   gh issue edit <number> --add-assignee @copilot
   ```

**Integration with governance:** Not directly compatible with the Dark Forge agentic loop. The Copilot coding agent would compete with the Tech Lead for issue ownership. Use selectively for issues tagged for Copilot rather than the governance loop.

### 4. GitHub Agentic Workflows (Technical Preview, Feb 2026)

**What it does:** Define workflows in Markdown that run coding agents (Copilot CLI, Claude Code, etc.) in response to repository events.

**Auto-fix capability:** Agents run in sandboxed environments with read-only-by-default permissions. Write operations produce "safe outputs" that require review.

**Configuration:**
1. Opt into the technical preview at https://github.com/settings/preview_features
2. Create workflow files in `.github/workflows/` using Markdown format
3. Install the `gh aw` CLI extension:
   ```bash
   gh extension install github/gh-aw
   ```
4. Define workflow goals in natural language

**Integration with governance:** Most promising long-term path for automation. An Agentic Workflow could:
- Trigger on PR creation
- Run an agent to analyze Copilot review suggestions
- Automatically apply low-risk fixes and push commits
- Leave high-risk suggestions for the Tech Lead to review

**Limitation:** Technical preview, read-only by default. Not production-ready.

## Recommended Approach

### Current State (No Changes Needed)

The existing governance workflow already achieves the goal through a different mechanism:

1. Copilot Code Review runs automatically on PRs (configured via repository ruleset)
2. The Tech Lead (startup.md Phase 4e) reads Copilot comments, classifies severity, and assigns fixes to the Coder via ASSIGN messages
3. This loop repeats for up to 3 cycles until all findings are addressed

This is functionally equivalent to "Copilot auto-fix" — the agentic loop acts as the automation layer between Copilot's detection and the fix application.

### Near-Term Enhancement (When Available)

When GitHub Agentic Workflows reach GA:

1. Create a Markdown workflow that triggers on Copilot review comments
2. Configure the agent to auto-apply `low` and `info` severity suggestions
3. Leave `critical`, `high`, and `medium` findings for the Tech Lead
4. This would reduce review cycle time by handling trivial findings automatically

### Configuration Checklist

For repositories using the Dark Forge governance framework:

- [x] Copilot Code Review ruleset enabled (automatic reviews on push)
- [ ] Copilot Autofix enabled for code scanning (default — verify not disabled)
- [ ] Consider enabling "Implement suggestion" preview for manual review acceleration
- [ ] Monitor GitHub Agentic Workflows GA timeline for automated fix application

## Limitations

| Limitation | Impact | Workaround |
|-----------|--------|------------|
| No auto-apply for PR review suggestions | Must manually implement or use agentic loop | Current Tech Lead flow handles this |
| Copilot Autofix limited to CodeQL alerts | Only security issues, not general code quality | Tech Lead handles non-security findings |
| Coding agent PRs require human approval | Cannot fully automate issue-to-merge | Governance workflow provides equivalent automation |
| Copilot cannot engage in review conversations | Dismissed suggestions may be re-raised | Tech Lead tracks dismissals across cycles |
| Non-deterministic review results | May miss issues or produce false positives | Multiple review cycles + panel redundancy |
| Custom instructions inconsistently applied | Automated reviews may ignore repo-level guidance | Rely on governance panels for consistent enforcement |

## References

- [GitHub Copilot Code Review](https://docs.github.com/copilot/using-github-copilot/code-review/using-copilot-code-review) — Official docs
- [Copilot Code Review Repository Ruleset](https://github.blog/changelog/2025-09-10-copilot-code-review-independent-repository-rule-for-automatic-reviews/) — Auto-review configuration
- [Copilot Autofix for Code Scanning](https://docs.github.com/en/code-security/responsible-use/responsible-use-autofix-code-scanning) — Security autofix docs
- [Assign Code Scanning Alerts to Copilot](https://github.blog/changelog/2025-10-28-assign-code-scanning-alerts-to-copilot-for-automated-fixes-in-public-preview/) — Alert assignment
- [Copilot Coding Agent](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent) — Issue-to-PR agent
- [GitHub Agentic Workflows](https://github.blog/changelog/2026-02-13-github-agentic-workflows-are-now-in-technical-preview/) — Markdown workflow definitions
