package engine

import (
	"fmt"
	"strings"

	"github.com/SET-Apps/ai-submodule/src/internal/condition"
	"github.com/SET-Apps/ai-submodule/src/internal/emission"
	"github.com/SET-Apps/ai-submodule/src/internal/evallog"
	"github.com/SET-Apps/ai-submodule/src/internal/policy"
)

// evaluateEscalationRules evaluates the profile's escalation rules and returns
// the action ("block", "human_review", or "") and a reason string.
func evaluateEscalationRules(emissions []*emission.Emission, profile *policy.Profile, ctx *condition.EvalContext, log *evallog.Log) (string, string) {
	// Build a set of panels that require human review but have an approve verdict
	// (these should be skipped for escalation purposes).
	skipPanels := make(map[string]bool)
	for _, em := range emissions {
		if em.RequiresHumanReview && strings.EqualFold(em.AggregateVerdict, emission.VerdictApprove) {
			skipPanels[em.PanelName] = true
		}
	}

	if len(skipPanels) > 0 {
		log.Record("escalation-skip-approved", "PASS",
			fmt.Sprintf("skipping %d panel(s) with requires_human_review=true but verdict=approve", len(skipPanels)))
	}

	for _, rule := range profile.Escalation.Rules {
		ruleID := "escalation-" + condition.Slugify(rule.Name)
		if condition.EvaluateEscalationCondition(rule.Condition, ctx) {
			desc := rule.Description
			if desc == "" {
				desc = rule.Name
			}
			log.Record(ruleID, "FAIL", fmt.Sprintf("escalation triggered: %s (action=%s)", desc, rule.Action))
			return rule.Action, desc
		}
		log.Record(ruleID, "PASS", fmt.Sprintf("escalation not triggered: %s", rule.Name))
	}

	return "", ""
}
