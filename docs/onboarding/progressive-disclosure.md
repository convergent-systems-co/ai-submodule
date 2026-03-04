# Progressive Disclosure Onboarding Guide

Learn governance concepts incrementally. Each tier introduces only what you need at that stage.

---

## Tier 0: Installation (What You See at Install)

> **Just want the essentials?** See the [Developer Quickstart](../guides/developer-quickstart.md) -- a 5-minute cliff notes guide covering install, daily use, and configuration.

**You need to know:** Governance is now active on your repository. PRs will be automatically reviewed.

That's it. You don't need to configure anything else to get started.

### What Happens Automatically

When you open a PR, the governance platform will:
1. **Review your code** for security issues, code quality, and best practices
2. **Check compliance** against your organization's policy
3. **Post findings** as PR comments with suggested fixes

### One Command to Check Status

```bash
bash .ai/bin/governance-status.sh
```

---

## Tier 1: Your First PR (What You See After Opening a PR)

**You need to know:** Governance runs **panels** — automated reviewers that check different aspects of your code.

### Default Panels

| Panel | What It Checks |
|-------|---------------|
| Code Review | Code quality, patterns, complexity |
| Security Review | Vulnerabilities, secrets, injection risks |
| Documentation Review | Missing docs, outdated references |

### Reading Panel Results

Panel results appear as PR comments. Each finding has:
- **Severity:** critical, high, medium, low, info
- **What to fix:** Specific file, line, and suggested change
- **Why it matters:** Brief explanation of the risk

### What to Do

- **Critical/High findings:** Must fix before merge
- **Medium findings:** Should fix; explain if you skip
- **Low/Info findings:** Nice to have; no action required

---

## Tier 2: Customization (When You Want to Tune Governance)

**You need to know:** Governance behavior is controlled by `project.yaml` and **policy profiles**.

### project.yaml

This file (in your project root) tells governance about your project:

```yaml
project:
  name: my-app
  language: python
  framework: fastapi

governance:
  policy_profile: default
```

Most fields are auto-detected at install. Edit only what you need to change.

### Policy Profiles

| Profile | When to Use |
|---------|-------------|
| `default` | Most projects (auto-selected) |
| `fin_pii_high` | Projects handling financial data or PII |
| `infrastructure_critical` | Infrastructure-as-code projects |
| `fast_track` | Low-risk documentation changes |

Change your profile in `project.yaml`:
```yaml
governance:
  policy_profile: fin_pii_high
```

### Custom Panel Configuration

Add or remove panels for your project:
```yaml
governance:
  panels:
    - code-review        # Always recommended
    - security-review    # Always recommended
    - cost-analysis      # Add for infrastructure projects
    - data-governance    # Add for data/PII projects
```

---

## Tier 3: Advanced (Power Users and Automation)

**You need to know:** The full governance platform includes an orchestrator, personas, and multi-agent dispatch.

### The Orchestrator

The orchestrator is a CLI that manages the governance pipeline end-to-end:

```bash
# Initialize a governance session
python -m governance.engine.orchestrator init --config project.yaml

# Check session status
python -m governance.engine.orchestrator status
```

### Personas

Governance uses 7 AI personas that play specific roles:

| Persona | Role |
|---------|------|
| Project Manager | Coordinates multi-team work |
| Tech Lead | Plans, dispatches, reviews |
| DevOps Engineer | CI/CD, deployment, monitoring |
| Coder | Implements features and fixes |
| IaC Engineer | Infrastructure-as-code |
| Test Evaluator | Validates implementations |
| Documentation Reviewer | Reviews documentation quality |

### Multi-Agent Dispatch

The agentic loop (`/startup` in Claude Code) orchestrates multiple agents working on issues in parallel. Each agent operates in its own git worktree.

```bash
# Start the agentic loop (in Claude Code)
/startup

# Or manually control the orchestrator
python -m governance.engine.orchestrator step --complete 1
```

### Containment Policy

Agent behavior is constrained by `governance/policy/agent-containment.yaml`:
- Agents cannot modify governance policy or schemas
- Each agent is limited to its assigned issue scope
- Push/merge requires policy engine approval

---

## Quick Reference

| I want to... | Do this |
|--------------|---------|
| Check if governance is working | `bash .ai/bin/governance-status.sh` |
| See what panels will run on my PR | Check `project.yaml` → `governance.panels` |
| Change the policy profile | Edit `project.yaml` → `governance.policy_profile` |
| Skip governance for a commit | You can't (by design) |
| Add a custom review panel | See `governance/prompts/reviews/` for examples |
| Run the agentic loop | `/startup` in Claude Code |
| Update governance | `git submodule update --remote .ai && bash .ai/bin/init.sh --refresh` |
