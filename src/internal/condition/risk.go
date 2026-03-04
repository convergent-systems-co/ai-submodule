package condition

import (
	"regexp"
	"strconv"
	"strings"

	"github.com/SET-Apps/ai-submodule/src/internal/emission"
)

var (
	panelRiskFnRe = regexp.MustCompile(`panel_risk\("([^"]+)"\)\s*(==|!=)\s*"([^"]+)"`)
	countPanelRe  = regexp.MustCompile(`count\(panel_risk\s*==\s*"([^"]+)"\)\s*(>=|<=|>|<|==|!=)\s*(\d+)`)
)

// EvaluateRiskCondition evaluates risk-specific condition patterns against
// the evaluation context.
func EvaluateRiskCondition(cond string, ctx *EvalContext) bool {
	// Handle or-expressions.
	if strings.Contains(cond, " or ") {
		parts := strings.Split(cond, " or ")
		for _, part := range parts {
			if EvaluateRiskCondition(strings.TrimSpace(part), ctx) {
				return true
			}
		}
		return false
	}

	cond = strings.TrimSpace(cond)

	// count(panel_risk == "high") >= 2
	if m := countPanelRe.FindStringSubmatch(cond); len(m) >= 4 {
		targetRisk := m[1]
		op := m[2]
		threshold, err := strconv.ParseFloat(m[3], 64)
		if err != nil {
			return false
		}
		count := 0
		for _, em := range ctx.Emissions {
			if strings.EqualFold(em.RiskLevel, targetRisk) {
				count++
			}
		}
		return Compare(float64(count), op, threshold)
	}

	// panel_risk("security-review") == "critical"
	if m := panelRiskFnRe.FindStringSubmatch(cond); len(m) >= 4 {
		panelName := m[1]
		op := m[2]
		targetRisk := m[3]
		actual, ok := ctx.PanelRiskLevels[panelName]
		if !ok {
			return false
		}
		if op == "==" {
			return strings.EqualFold(actual, targetRisk)
		}
		return !strings.EqualFold(actual, targetRisk)
	}

	// any_panel_risk == "critical"
	if strings.HasPrefix(cond, "any_panel_risk") {
		parts := strings.SplitN(cond, "==", 2)
		if len(parts) == 2 {
			target := strings.Trim(strings.TrimSpace(parts[1]), `"`)
			for _, em := range ctx.Emissions {
				if strings.EqualFold(em.RiskLevel, target) {
					return true
				}
			}
			return false
		}
	}

	// all_panels_risk in ["low", "negligible"]
	if strings.HasPrefix(cond, "all_panels_risk") {
		if idx := strings.Index(cond, " in "); idx >= 0 {
			allowed := ExtractList(cond[idx:])
			allowedSet := make(map[string]bool)
			for _, a := range allowed {
				allowedSet[strings.ToLower(a)] = true
			}
			for _, em := range ctx.Emissions {
				if !allowedSet[strings.ToLower(em.RiskLevel)] {
					return false
				}
			}
			return len(ctx.Emissions) > 0
		}
	}

	return false
}

// EvaluatePanelExecutionCondition evaluates panel execution rule conditions.
func EvaluatePanelExecutionCondition(cond string, ctx *EvalContext) bool {
	cond = strings.TrimSpace(cond)

	// Fallback-related conditions.
	if strings.HasPrefix(cond, "fallback_count") {
		op, threshold, ok := ExtractComparison(cond)
		if ok {
			return Compare(float64(ctx.FallbackCount), op, threshold)
		}
	}

	// Missing panels condition.
	if strings.HasPrefix(cond, "missing_required_panels") {
		op, threshold, ok := ExtractComparison(cond)
		if ok {
			return Compare(float64(len(ctx.MissingRequired)), op, threshold)
		}
	}

	// Execution status checks.
	if strings.Contains(cond, "execution_status") {
		for _, em := range ctx.Emissions {
			status := em.EffectiveExecutionStatus()
			if strings.Contains(cond, `"timeout"`) && status == emission.ExecStatusTimeout {
				return true
			}
			if strings.Contains(cond, `"error"`) && status == emission.ExecStatusError {
				return true
			}
			if strings.Contains(cond, `"fallback"`) && status == emission.ExecStatusFallback {
				return true
			}
		}
		return false
	}

	return false
}
