# Governance Cheat Sheet

Five operations. One page. No scrolling.

---

## 1. Install Governance

```bash
git submodule add https://github.com/convergent-systems-co/dark-forge.git .ai
bash .ai/bin/init.sh --quick
```

## 2. Check Status

```bash
bash .ai/bin/governance-status.sh
```

Shows: active policy profile, recent panel results, pending issues.

## 3. Open a Governed PR

Just open a PR normally. Governance runs automatically:
- Panels review your code
- Findings posted as comments
- Fix critical/high findings before merge

## 4. Change Policy Profile

Edit `project.yaml` in your project root:

```yaml
governance:
  policy_profile: default    # or: fin_pii_high, infrastructure_critical, fast_track
```

## 5. Update Governance

```bash
git submodule update --remote .ai
bash .ai/bin/init.sh --refresh
```

---

**New to governance?** Start with the [Developer Quickstart](../guides/developer-quickstart.md). **Need more depth?** See the [progressive disclosure guide](progressive-disclosure.md) for incremental learning, or the [full documentation](../index.md).
