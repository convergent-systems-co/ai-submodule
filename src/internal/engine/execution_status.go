package engine

import (
	"fmt"
	"strings"

	"github.com/SET-Apps/ai-submodule/src/internal/condition"
	"github.com/SET-Apps/ai-submodule/src/internal/emission"
	"github.com/SET-Apps/ai-submodule/src/internal/evallog"
	"github.com/SET-Apps/ai-submodule/src/internal/policy"
)

// checkRequiredPanels compares the set of loaded emissions against the list of
// required panel names and returns the names of any missing panels.
func checkRequiredPanels(emissions []*emission.Emission, required []string, log *evallog.Log) []string {
	present := make(map[string]bool)
	for _, em := range emissions {
		present[em.PanelName] = true
	}

	var missing []string
	for _, name := range required {
		if !present[name] {
			missing = append(missing, name)
			log.Record("required-panel-"+condition.Slugify(name), "FAIL", fmt.Sprintf("required panel missing: %s", name))
		} else {
			log.Record("required-panel-"+condition.Slugify(name), "PASS", fmt.Sprintf("required panel present: %s", name))
		}
	}

	return missing
}

// applyExecutionStatusAdjustments modifies emissions based on their execution
// status:
//   - Fallback emissions have their confidence capped to 0.50.
//   - Error emissions are removed entirely.
//
// Returns the filtered list of emissions.
func applyExecutionStatusAdjustments(emissions []*emission.Emission, log *evallog.Log) []*emission.Emission {
	var result []*emission.Emission

	for _, em := range emissions {
		status := em.EffectiveExecutionStatus()

		switch status {
		case emission.ExecStatusError:
			log.Record("exec-status-"+condition.Slugify(em.PanelName), "WARN",
				fmt.Sprintf("removing error emission: %s", em.PanelName))
			continue

		case emission.ExecStatusFallback:
			if em.ConfidenceScore > 0.50 {
				log.Record("exec-status-"+condition.Slugify(em.PanelName), "WARN",
					fmt.Sprintf("capping fallback confidence from %.2f to 0.50: %s", em.ConfidenceScore, em.PanelName))
				em.ConfidenceScore = 0.50
			} else {
				log.Record("exec-status-"+condition.Slugify(em.PanelName), "PASS",
					fmt.Sprintf("fallback confidence already <= 0.50: %s", em.PanelName))
			}
			result = append(result, em)

		default:
			result = append(result, em)
		}
	}

	return result
}

// evaluatePanelExecutionRules evaluates the profile's panel execution rules.
// Returns true if any rule triggers (indicating human review is needed).
func evaluatePanelExecutionRules(emissions []*emission.Emission, profile *policy.Profile, ctx *condition.EvalContext, log *evallog.Log) bool {
	// Count fallback emissions for context.
	fallbackCount := 0
	for _, em := range emissions {
		if em.EffectiveExecutionStatus() == emission.ExecStatusFallback {
			fallbackCount++
		}
	}
	ctx.FallbackCount = fallbackCount

	for _, rule := range profile.PanelExecution.Rules {
		ruleID := "panel-exec-" + condition.Slugify(rule.Condition)
		if condition.EvaluatePanelExecutionCondition(rule.Condition, ctx) {
			desc := rule.Description
			if desc == "" {
				desc = rule.Condition
			}
			log.Record(ruleID, "FAIL", fmt.Sprintf("panel execution rule triggered: %s (action=%s)", desc, rule.Action))
			return true
		}
		log.Record(ruleID, "PASS", fmt.Sprintf("panel execution rule not triggered: %s", rule.Condition))
	}

	return false
}

// collectPolicyFlags collects all policy flag names and builds a flag-to-severity
// map from all emissions.
func collectPolicyFlags(emissions []*emission.Emission) ([]string, map[string]string) {
	var flags []string
	severities := make(map[string]string)

	seen := make(map[string]bool)
	for _, em := range emissions {
		for _, pf := range em.PolicyFlags {
			if !seen[pf.Flag] {
				flags = append(flags, pf.Flag)
				seen[pf.Flag] = true
			}
			// Keep highest severity for each flag.
			existing, ok := severities[pf.Flag]
			if !ok || emission.RiskIndex(strings.ToLower(pf.Severity)) > emission.RiskIndex(strings.ToLower(existing)) {
				severities[pf.Flag] = pf.Severity
			}
		}
	}

	return flags, severities
}
