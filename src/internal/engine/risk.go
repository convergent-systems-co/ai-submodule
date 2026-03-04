package engine

import (
	"fmt"
	"strings"

	"github.com/SET-Apps/ai-submodule/src/internal/condition"
	"github.com/SET-Apps/ai-submodule/src/internal/emission"
	"github.com/SET-Apps/ai-submodule/src/internal/evallog"
	"github.com/SET-Apps/ai-submodule/src/internal/policy"
)

// computeAggregateRisk determines the aggregate risk level by evaluating
// profile risk aggregation rules. Falls back to the highest severity across
// all emissions if no rule matches.
func computeAggregateRisk(emissions []*emission.Emission, profile *policy.Profile, ctx *condition.EvalContext, log *evallog.Log) string {
	// Build risk context maps.
	panelRiskLevels := make(map[string]string)
	riskCounts := make(map[string]int)
	for _, em := range emissions {
		panelRiskLevels[em.PanelName] = em.RiskLevel
		riskCounts[strings.ToLower(em.RiskLevel)]++
	}

	// Update context with risk data.
	ctx.PanelRiskLevels = panelRiskLevels
	ctx.RiskCounts = riskCounts

	// Evaluate risk aggregation rules.
	for _, rule := range profile.RiskAggregation.Rules {
		if condition.EvaluateRiskCondition(rule.Condition, ctx) {
			log.Record(
				"risk-rule-"+condition.Slugify(rule.Condition),
				"PASS",
				fmt.Sprintf("matched: %s -> %s", rule.Description, rule.Result),
			)
			return rule.Result
		}
		log.Record(
			"risk-rule-"+condition.Slugify(rule.Condition),
			"SKIP",
			fmt.Sprintf("not matched: %s", rule.Description),
		)
	}

	// Fallback: highest severity across emissions.
	highest := emission.RiskNegligible
	highestIdx := 0
	for _, em := range emissions {
		idx := emission.RiskIndex(em.RiskLevel)
		if idx > highestIdx {
			highestIdx = idx
			highest = em.RiskLevel
		}
	}

	log.Record("risk-fallback", "PASS", fmt.Sprintf("no rule matched; using highest severity: %s", highest))
	return highest
}
