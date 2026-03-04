# Developer Quickstart

Get governance running on your repo in under 5 minutes. No background knowledge required.

---

## 1. Install

### Option A: Binary Installation (Recommended)

```bash
# Install the CLI
brew install SET-Apps/tap/dark-governance

# From your project root:
dark-governance init
```

Verify it worked:

```bash
dark-governance verify
```

### Option B: Submodule Installation (Legacy)

```bash
# From your project root:
git submodule add https://github.com/convergent-systems-co/dark-forge.git .ai
bash .ai/bin/init.sh --quick
```

Verify it worked:

```bash
bash .ai/bin/init.sh --verify
```

## 2. Daily Workflow

You do not need to change how you work. Governance runs automatically.

1. **Write code and open a PR** -- nothing special needed
2. **Automated reviews run** -- code quality, security, and documentation are checked
3. **Findings appear as PR comments** -- each one tells you what to fix and why
4. **Fix critical/high findings** -- then the PR auto-merges (if enabled)

That is the entire workflow. There is nothing to run manually.

## 3. When You See a Finding

Findings are posted as PR comments with a severity level:

| Severity | Action Required |
|----------|----------------|
| **Critical / High** | Must fix before merge |
| **Medium** | Should fix; explain in the PR if you skip |
| **Low / Info** | Optional -- no action required |

Each finding includes the file, line number, and a suggested fix. Follow the suggestion or explain why you disagree.

## 4. Configuration

Governance reads `project.yaml` in your project root. Most settings are auto-detected at install. The only setting most teams change is the policy profile:

```yaml
governance:
  policy_profile: default  # options: default, fin_pii_high, infrastructure_critical, fast_track
```

## 5. Common Tasks

### Unified CLI (`dark-governance`)

| Task | Command |
|------|---------|
| Check status | `dark-governance engine status` |
| Run policy evaluation | `dark-governance engine run` |
| Update governance | `dark-governance update` |
| Verify install | `dark-governance verify` |

### Legacy (submodule-based)

| Task | Command |
|------|---------|
| Check status | `bash .ai/bin/governance-status.sh` |
| Update governance | `git submodule update --remote .ai && bash .ai/bin/init.sh --refresh` |
| Configure IDEs | `bash .ai/bin/install-ide.sh` |
| Verify install | `bash .ai/bin/init.sh --verify` |

---

**Want more depth?** See the [unified CLI reference](unified-cli-reference.md), [full developer guide](../onboarding/developer-guide.md), [cheat sheet](../onboarding/cheat-sheet.md), or [architecture docs](../architecture/governance-model.md).
