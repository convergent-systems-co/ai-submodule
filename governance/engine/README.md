# Dark Forge Policy Engine

Deterministic AI governance policy engine for merge decisions. Evaluates
structured panel emissions against YAML policy profiles to produce
auto-merge, block, escalation, or auto-remediate decisions with full
audit trails.

## Installation

```bash
pip install dark-factory-policy-engine
```

## Quick start

```python
from governance.engine.policy_engine import PolicyEngine, EvaluationLog

log = EvaluationLog()
engine = PolicyEngine(profile=profile_dict, emissions=emissions_list, log=log)
result = engine.evaluate()

print(result["decision"])       # auto_merge | block | human_review_required | auto_remediate
print(result["confidence"])     # 0.0 – 1.0
print(result["risk_level"])     # critical | high | medium | low | negligible
```

## Bundled assets

The package ships with:

- **Schemas** — `panel-output.schema.json` and `run-manifest.schema.json`
  for validating panel emissions and run manifests.
- **Policy profiles** — `default.yaml` and five additional profiles
  (`fast-track`, `fin_pii_high`, `infrastructure_critical`,
  `reduced_touchpoint`, `cost-optimization`).

## Usage with the submodule

If you already use the `dark-factory-governance` submodule (`.ai/`), the
policy engine continues to work as before. This package provides an
alternative installation path for consumers who only need the engine.

## License

MIT
