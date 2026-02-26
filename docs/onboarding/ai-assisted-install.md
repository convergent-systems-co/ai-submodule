# AI-Assisted Install

Install Dark Factory in your consuming repo by telling your AI tool to read the source repository and set it up. No manual steps required.

---

## How It Works

The governance framework includes an interactive bootstrap prompt (`governance/prompts/init.md`) designed for AI agents. When you point your AI tool at the repository, it reads the instructions, walks you through language/framework selection, and installs everything automatically — including the submodule, symlinks, Python dependencies, and `project.yaml` configuration.

---

## Claude Code

Open your terminal in the consuming repo and run:

```bash
claude
```

Then tell Claude:

```
Read https://github.com/SET-Apps/ai-submodule and install it as a
git submodule at .ai in this repo. Then read and execute
.ai/governance/prompts/init.md for interactive setup.
```

Claude will:

1. Add the submodule: `git submodule add git@github.com:SET-Apps/ai-submodule.git .ai`
2. Read `governance/prompts/init.md` and begin interactive setup
3. Ask you which language template to use (Python, Node, Go, C#, React)
4. Create `project.yaml` with your project name and settings
5. Run `bash .ai/bin/init.sh --install-deps` to create symlinks, Python venv, and directories
6. Commit the setup

### One-liner (non-interactive)

If you want to skip the interactive prompts and just install with defaults:

```
Add git@github.com:SET-Apps/ai-submodule.git as a submodule at .ai,
then run bash .ai/bin/init.sh --install-deps
```

---

## GitHub Copilot CLI

Open your terminal in the consuming repo and run:

```bash
gh copilot
```

Then tell Copilot:

```
I want to add the Dark Factory governance framework to this repo.
Add git@github.com:SET-Apps/ai-submodule.git as a git submodule at .ai,
then read and follow the setup instructions in .ai/governance/prompts/init.md
```

Copilot will follow the same interactive setup flow — language selection, project configuration, dependency installation.

### Alternative: Manual submodule + AI bootstrap

If your AI tool can't add submodules directly, do step 1 manually:

```bash
git submodule add git@github.com:SET-Apps/ai-submodule.git .ai
```

Then tell your AI tool:

```
Read .ai/governance/prompts/init.md and execute the interactive setup
```

---

## What the Interactive Setup Does

The `init.md` prompt walks through these steps:

| Step | What Happens |
|------|-------------|
| **1. Language detection** | Scans your repo and asks which template to use (Python, Node, Go, C#, React, or custom) |
| **2. Project configuration** | Creates `project.yaml` with your project name, language conventions, and governance settings |
| **3. Policy profile selection** | Asks which policy profile to use: `default`, `fin_pii_high`, `infrastructure_critical`, or `reduced_touchpoint` |
| **4. Bootstrap execution** | Runs `init.sh` / `init.ps1` — creates symlinks, directories, Python venv, and validates setup |
| **5. Initial commit** | Commits the submodule and all generated files |

---

## After Install

Once installed, start the governance pipeline:

```
/startup
```

This begins the 5-phase agentic loop: DevOps Engineer pre-flight → Code Manager planning → parallel Coder dispatch → Tester evaluation → merge.

---

## Troubleshooting

| Issue | Solution |
|-------|---------|
| **Permission denied on submodule** | Ensure you have SSH access to `SET-Apps/ai-submodule`. Test: `ssh -T git@github.com` |
| **AI tool can't find init.md** | Add the submodule manually first, then point the AI to `.ai/governance/prompts/init.md` |
| **Symlinks not working (Windows)** | Enable Developer Mode or use `init.ps1` which falls back to file copies |
| **Python not found** | Install Python 3.12+ and ensure it's in your PATH. The `--install-deps` flag handles the rest. |

---

*Back to [Windows Onboarding](windows-onboarding.md) · [Developer Guide](developer-guide.md)*
