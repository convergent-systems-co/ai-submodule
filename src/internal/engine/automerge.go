package engine

import (
	"fmt"

	"github.com/SET-Apps/ai-submodule/src/internal/condition"
	"github.com/SET-Apps/ai-submodule/src/internal/evallog"
	"github.com/SET-Apps/ai-submodule/src/internal/policy"
)

// evaluateAutoMerge checks whether auto-merge conditions are satisfied.
// Returns true if auto-merge is enabled and all conditions pass.
func evaluateAutoMerge(profile *policy.Profile, ctx *condition.EvalContext, log *evallog.Log) bool {
	if !profile.AutoMerge.Enabled {
		log.Record("auto-merge-enabled", "SKIP", "auto-merge is disabled")
		return false
	}
	log.Record("auto-merge-enabled", "PASS", "auto-merge is enabled")

	// All conditions must pass (operator "all" is the default).
	for _, cond := range profile.AutoMerge.Conditions {
		ruleID := "auto-merge-" + condition.Slugify(cond.Condition)
		if !condition.EvaluateAutoMergeCondition(cond.Condition, ctx) {
			desc := cond.Description
			if desc == "" {
				desc = cond.Condition
			}
			log.Record(ruleID, "FAIL", fmt.Sprintf("auto-merge condition failed: %s", desc))
			return false
		}
		log.Record(ruleID, "PASS", fmt.Sprintf("auto-merge condition passed: %s", cond.Condition))
	}

	log.Record("auto-merge", "PASS", "all auto-merge conditions satisfied")
	return true
}
