package condition

import (
	"regexp"
	"strconv"
	"strings"

	"github.com/SET-Apps/ai-submodule/src/internal/emission"
)

// EvalContext provides the data needed to evaluate condition expressions.
type EvalContext struct {
	AggregateConfidence  float64
	AggregateRisk        string
	PolicyFlags          []string            // flag names
	PolicyFlagSeverities map[string]string   // flag -> severity
	Emissions            []*emission.Emission
	CIPassed             bool
	MissingRequired      []string
	FallbackCount        int
	RiskCounts           map[string]int
	PanelRiskLevels      map[string]string
}

// EvaluateBlockCondition evaluates a block condition string. Returns true if
// the condition matches (i.e., the PR should be blocked).
func EvaluateBlockCondition(cond string, ctx *EvalContext) bool {
	return evaluateCompound(cond, func(single string) bool {
		return evaluateSingle(single, ctx)
	})
}

// EvaluateEscalationCondition evaluates an escalation condition string.
func EvaluateEscalationCondition(cond string, ctx *EvalContext) bool {
	return evaluateCompound(cond, func(single string) bool {
		return evaluateSingle(single, ctx)
	})
}

// EvaluateAutoMergeCondition evaluates an auto-merge condition string.
func EvaluateAutoMergeCondition(cond string, ctx *EvalContext) bool {
	return evaluateCompound(cond, func(single string) bool {
		return evaluateSingle(single, ctx)
	})
}

// EvaluateAutoRemediateCondition evaluates an auto-remediate condition string.
func EvaluateAutoRemediateCondition(cond string, ctx *EvalContext) bool {
	return evaluateCompound(cond, func(single string) bool {
		return evaluateSingle(single, ctx)
	})
}

// evaluateCompound splits on " and ", handles "not " prefix per clause,
// and requires all clauses to match.
func evaluateCompound(cond string, evalFn func(string) bool) bool {
	parts := strings.Split(cond, " and ")
	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}

		negate := false
		if strings.HasPrefix(part, "not ") {
			negate = true
			part = strings.TrimPrefix(part, "not ")
			part = strings.TrimSpace(part)
		}

		result := evalFn(part)
		if negate {
			result = !result
		}
		if !result {
			return false
		}
	}
	return true
}

var (
	aggConfRe       = regexp.MustCompile(`^aggregate_confidence\s*(>=|<=|>|<|==|!=)\s*([0-9]+(?:\.[0-9]+)?)$`)
	riskLevelEqRe   = regexp.MustCompile(`^risk_level\s*==\s*"([^"]+)"$`)
	riskLevelInRe   = regexp.MustCompile(`^risk_level\s+in\s+\[`)
	anyFlagEqRe     = regexp.MustCompile(`^any_policy_flag\s*==\s*"([^"]+)"$`)
	anyFlagStartsRe = regexp.MustCompile(`^any_policy_flag\s+starts_with\s+"([^"]+)"$`)
	noFlagSevRe     = regexp.MustCompile(`^no_policy_flags_severity\s+in\s+\[`)
	allVerdictsRe   = regexp.MustCompile(`^all_panel_verdicts\s+in\s+\[`)
	ciPassedRe      = regexp.MustCompile(`^ci_checks_passed\s*==\s*(true|false)$`)
	panelDisagreeRe = regexp.MustCompile(`^panel_disagreement_detected\s*==\s*(true|false)$`)
	destructionRe   = regexp.MustCompile(`^destruction_recommended\s*==\s*(true|false)$`)
	autoRemRe       = regexp.MustCompile(`^auto_remediable\s*==\s*(true|false)$`)
	missingReqRe    = regexp.MustCompile(`^missing_required_panels\s*(>=|<=|>|<|==|!=)\s*(\d+)$`)
)

// evaluateSingle handles individual (non-compound) condition patterns.
func evaluateSingle(cond string, ctx *EvalContext) bool {
	cond = strings.TrimSpace(cond)

	// aggregate_confidence >= 0.85
	if m := aggConfRe.FindStringSubmatch(cond); len(m) >= 3 {
		threshold, err := strconv.ParseFloat(m[2], 64)
		if err != nil {
			return false
		}
		return Compare(ctx.AggregateConfidence, m[1], threshold)
	}

	// risk_level == "critical"
	if m := riskLevelEqRe.FindStringSubmatch(cond); len(m) >= 2 {
		return strings.EqualFold(ctx.AggregateRisk, m[1])
	}

	// risk_level in ["low", "negligible"]
	if riskLevelInRe.MatchString(cond) {
		allowed := ExtractList(cond)
		for _, a := range allowed {
			if strings.EqualFold(ctx.AggregateRisk, a) {
				return true
			}
		}
		return false
	}

	// any_policy_flag == "pii_exposure"
	if m := anyFlagEqRe.FindStringSubmatch(cond); len(m) >= 2 {
		target := m[1]
		for _, f := range ctx.PolicyFlags {
			if f == target {
				return true
			}
		}
		return false
	}

	// any_policy_flag starts_with "pii_"
	if m := anyFlagStartsRe.FindStringSubmatch(cond); len(m) >= 2 {
		prefix := m[1]
		for _, f := range ctx.PolicyFlags {
			if strings.HasPrefix(f, prefix) {
				return true
			}
		}
		return false
	}

	// no_policy_flags_severity in ["critical", "high"]
	if noFlagSevRe.MatchString(cond) {
		disallowed := ExtractList(cond)
		disallowedSet := make(map[string]bool)
		for _, d := range disallowed {
			disallowedSet[strings.ToLower(d)] = true
		}
		for _, sev := range ctx.PolicyFlagSeverities {
			if disallowedSet[strings.ToLower(sev)] {
				return false
			}
		}
		return true
	}

	// all_panel_verdicts in ["approve"]
	if allVerdictsRe.MatchString(cond) {
		allowed := ExtractList(cond)
		allowedSet := make(map[string]bool)
		for _, a := range allowed {
			allowedSet[strings.ToLower(a)] = true
		}
		for _, em := range ctx.Emissions {
			if !allowedSet[strings.ToLower(em.AggregateVerdict)] {
				return false
			}
		}
		return len(ctx.Emissions) > 0
	}

	// ci_checks_passed == true
	if m := ciPassedRe.FindStringSubmatch(cond); len(m) >= 2 {
		expected := m[1] == "true"
		return ctx.CIPassed == expected
	}

	// panel_disagreement_detected == true
	if m := panelDisagreeRe.FindStringSubmatch(cond); len(m) >= 2 {
		expected := m[1] == "true"
		detected := panelDisagreementDetected(ctx)
		return detected == expected
	}

	// destruction_recommended == true
	if m := destructionRe.FindStringSubmatch(cond); len(m) >= 2 {
		expected := m[1] == "true"
		found := false
		for _, em := range ctx.Emissions {
			if em.DestructionRecommended {
				found = true
				break
			}
		}
		return found == expected
	}

	// auto_remediable == true
	if m := autoRemRe.FindStringSubmatch(cond); len(m) >= 2 {
		expected := m[1] == "true"
		allRemediable := len(ctx.PolicyFlags) > 0
		for _, em := range ctx.Emissions {
			for _, pf := range em.PolicyFlags {
				if !pf.AutoRemediable {
					allRemediable = false
					break
				}
			}
			if !allRemediable {
				break
			}
		}
		return allRemediable == expected
	}

	// missing_required_panels > 0
	if m := missingReqRe.FindStringSubmatch(cond); len(m) >= 3 {
		threshold, err := strconv.ParseFloat(m[2], 64)
		if err != nil {
			return false
		}
		return Compare(float64(len(ctx.MissingRequired)), m[1], threshold)
	}

	// Delegate risk-specific conditions.
	if strings.HasPrefix(cond, "any_panel_risk") ||
		strings.HasPrefix(cond, "all_panels_risk") ||
		strings.HasPrefix(cond, "count(panel_risk") ||
		strings.HasPrefix(cond, "panel_risk(") {
		return EvaluateRiskCondition(cond, ctx)
	}

	return false
}

// panelDisagreementDetected checks if panels have different verdicts.
func panelDisagreementDetected(ctx *EvalContext) bool {
	if len(ctx.Emissions) < 2 {
		return false
	}
	first := strings.ToLower(ctx.Emissions[0].AggregateVerdict)
	for _, em := range ctx.Emissions[1:] {
		if strings.ToLower(em.AggregateVerdict) != first {
			return true
		}
	}
	return false
}
