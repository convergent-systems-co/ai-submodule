# Plan: CLAUDE.md Init — Remaining Work

## Completed
- [x] Created `CLAUDE.md` at repo root with full architecture, conventions, and commands
- [x] Symlinked `.github/copilot-instructions.md` → `../CLAUDE.md` (GitHub Copilot parity)

## Remaining

### 1. Symlink `.cursorrules` → `CLAUDE.md`
Currently missing in this repo. Create it so Cursor IDE users get the same guidance:
```bash
ln -sf CLAUDE.md .cursorrules
```

### 2. Update `config.yaml` symlink targets
The current config says `instructions.md` is the symlink source for CLAUDE.md, .cursorrules, and copilot-instructions. Now that CLAUDE.md is a standalone file (not a symlink to instructions.md), decide whether:
- **Option A**: Keep `instructions.md` as the base for *consuming repos* (lightweight) and CLAUDE.md as the full guide for *this repo* only. No config change needed.
- **Option B**: Update config.yaml to reflect that CLAUDE.md is now the canonical source and consuming repos should symlink to it instead.

Recommendation: **Option A** — consuming repos get the lightweight `instructions.md`; this repo gets the full `CLAUDE.md`. They serve different purposes.

### 3. Update `init.sh` (optional)
If Option B is chosen above, update `init.sh` to symlink to CLAUDE.md instead of instructions.md. If Option A, no change needed.

### 4. Commit and push
```bash
git add CLAUDE.md .github/copilot-instructions.md
git commit -m "feat(governance): add CLAUDE.md with full repo guidance for Claude Code and Copilot"
```

### 5. Merge to main (deferred)
User noted this branch is not merged to origin/main. Address upstream merge separately.
