# Dark Forge

AI governance framework for autonomous software delivery. Add it to your repo and every PR gets automatic code review, security scanning, and compliance checks -- no configuration required.

## Install

```bash
git submodule add https://github.com/convergent-systems-co/dark-forge.git .ai
bash .ai/bin/init.sh --quick
```

## How It Works

1. **Open a PR** -- governance runs automatically
2. **Review findings** -- posted as PR comments with severity and suggested fixes
3. **Merge** -- fix critical/high findings, then merge (auto-merge available)

## Guides

| Guide | Description |
|-------|-------------|
| [Developer Quickstart](docs/guides/developer-quickstart.md) | 5-minute cliff notes -- install, daily use, configuration |
| [Cheat Sheet](docs/onboarding/cheat-sheet.md) | One-page command reference |
| [Full Documentation](docs/README.md) | Complete docs index |
| [Architecture](docs/architecture/governance-model.md) | For contributors and power users |

## Key Commands

```bash
bash .ai/bin/init.sh --verify          # Verify installation
bash .ai/bin/governance-status.sh      # Status dashboard
bash .ai/bin/install-ide.sh            # Configure IDEs
```

## License

[MIT](LICENSE)
