# Quickstart: Add Governance to Your Repo

**Time:** 5 minutes | **Prerequisites:** git, Python 3.9+

---

## Step 1: Add the Submodule

```bash
git submodule add https://github.com/convergent-systems-co/dark-forge.git .ai
```

This adds the governance platform as a git submodule at `.ai/`.

## Step 2: Run the Installer

```bash
bash .ai/bin/init.sh --quick
```

This will:
- Create configuration symlinks (CLAUDE.md, copilot-instructions.md)
- Copy GitHub Actions governance workflows
- Create `.artifacts/` directories for plans, panels, and checkpoints
- Set up CODEOWNERS for automated reviews
- Auto-detect your project language and create `project.yaml`

## Step 3: Commit the Setup

```bash
git add .ai .gitmodules CLAUDE.md .github/ .artifacts/ project.yaml
git commit -m "feat: add Dark Forge governance"
git push
```

## What You Get

After installation, every PR in your repo will be automatically reviewed for:

| Review | What It Checks |
|--------|---------------|
| Code quality | Patterns, complexity, maintainability |
| Security | Vulnerabilities, secrets, injection risks |
| Documentation | Missing or outdated docs |
| Compliance | Policy profile requirements |

## Verify Installation

```bash
bash .ai/bin/init.sh --verify
```

## Next Steps

- [Your first governed PR](first-governed-pr.md) - See governance in action
- [Customize policy profiles](customize-policy.md) - Tune governance for your project
- [Run the agentic loop](run-agentic-loop.md) - Automated issue-to-PR pipeline

---

## Troubleshooting

**Python not found:**
```bash
brew install python3   # macOS
apt install python3    # Linux
```

**Permission denied on init.sh:**
```bash
chmod +x .ai/bin/init.sh
bash .ai/bin/init.sh --quick
```

**Submodule access denied (cross-org):**
You need access to the SET-Apps organization. Contact your admin or use the vendored installation method (see [cross-org setup](../guides/cross-org-installation.md)).
