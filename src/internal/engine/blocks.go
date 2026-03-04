package engine

import (
	"fmt"
	"strings"

	"github.com/SET-Apps/ai-submodule/src/internal/condition"
	"github.com/SET-Apps/ai-submodule/src/internal/emission"
	"github.com/SET-Apps/ai-submodule/src/internal/evallog"
	"github.com/SET-Apps/ai-submodule/src/internal/policy"
)

// evaluateBlockConditions checks universal block rules and profile-defined
// block conditions. Returns (blocked, reason).
func evaluateBlockConditions(emissions []*emission.Emission, profile *policy.Profile, ctx *condition.EvalContext, log *evallog.Log) (bool, string) {
	// Universal: CI checks failed.
	if !ctx.CIPassed {
		log.Record("block-ci-failed", "FAIL", "CI checks failed")
		return true, "CI checks failed"
	}
	log.Record("block-ci-passed", "PASS", "CI checks passed")

	// Universal: missing required panels.
	if len(ctx.MissingRequired) > 0 {
		reason := fmt.Sprintf("missing required panels: %s", strings.Join(ctx.MissingRequired, ", "))
		log.Record("block-missing-panels", "FAIL", reason)
		return true, reason
	}
	log.Record("block-missing-panels", "PASS", "all required panels present")

	// Profile block conditions.
	for _, bc := range profile.Block.Conditions {
		ruleID := "block-" + condition.Slugify(bc.Condition)
		if condition.EvaluateBlockCondition(bc.Condition, ctx) {
			desc := bc.Description
			if desc == "" {
				desc = bc.Condition
			}
			log.Record(ruleID, "FAIL", fmt.Sprintf("block condition triggered: %s", desc))
			return true, desc
		}
		log.Record(ruleID, "PASS", fmt.Sprintf("block condition not triggered: %s", bc.Condition))
	}

	// Universal: any critical/high severity policy flag.
	for _, em := range emissions {
		for _, pf := range em.PolicyFlags {
			sev := strings.ToLower(pf.Severity)
			if sev == emission.RiskCritical || sev == emission.RiskHigh {
				reason := fmt.Sprintf("policy flag %q with severity %s on panel %s", pf.Flag, pf.Severity, em.PanelName)
				log.Record("block-policy-flag-severity", "FAIL", reason)
				return true, reason
			}
		}
	}
	log.Record("block-policy-flag-severity", "PASS", "no critical/high severity policy flags")

	return false, ""
}
