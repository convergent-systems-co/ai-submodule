package engine

import (
	"fmt"

	"github.com/SET-Apps/ai-submodule/src/internal/condition"
	"github.com/SET-Apps/ai-submodule/src/internal/evallog"
	"github.com/SET-Apps/ai-submodule/src/internal/policy"
)

// evaluateAutoRemediate checks whether auto-remediate conditions are satisfied.
// Returns true if auto-remediate is enabled and all conditions pass.
func evaluateAutoRemediate(profile *policy.Profile, ctx *condition.EvalContext, log *evallog.Log) bool {
	if !profile.AutoRemediate.Enabled {
		log.Record("auto-remediate-enabled", "SKIP", "auto-remediate is disabled")
		return false
	}
	log.Record("auto-remediate-enabled", "PASS", "auto-remediate is enabled")

	for _, cond := range profile.AutoRemediate.Conditions {
		ruleID := "auto-remediate-" + condition.Slugify(cond.Condition)
		if !condition.EvaluateAutoRemediateCondition(cond.Condition, ctx) {
			desc := cond.Description
			if desc == "" {
				desc = cond.Condition
			}
			log.Record(ruleID, "FAIL", fmt.Sprintf("auto-remediate condition failed: %s", desc))
			return false
		}
		log.Record(ruleID, "PASS", fmt.Sprintf("auto-remediate condition passed: %s", cond.Condition))
	}

	log.Record("auto-remediate", "PASS", "all auto-remediate conditions satisfied")
	return true
}
