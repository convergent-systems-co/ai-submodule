package condition

import (
	"testing"

	"github.com/SET-Apps/ai-submodule/src/internal/emission"
)

func TestRisk_AnyPanelRiskMatch(t *testing.T) {
	ctx := &EvalContext{
		Emissions: []*emission.Emission{
			{RiskLevel: "low"},
			{RiskLevel: "critical"},
		},
	}
	if !EvaluateRiskCondition(`any_panel_risk == "critical"`, ctx) {
		t.Error("expected match: critical risk present")
	}
	if EvaluateRiskCondition(`any_panel_risk == "high"`, ctx) {
		t.Error("should not match: no high risk present")
	}
}

func TestRisk_AllPanelsRiskInSet(t *testing.T) {
	ctx := &EvalContext{
		Emissions: []*emission.Emission{
			{RiskLevel: "low"},
			{RiskLevel: "negligible"},
		},
	}
	if !EvaluateRiskCondition(`all_panels_risk in ["low", "negligible"]`, ctx) {
		t.Error("expected match: all panels are low or negligible")
	}

	ctx.Emissions = append(ctx.Emissions, &emission.Emission{RiskLevel: "high"})
	if EvaluateRiskCondition(`all_panels_risk in ["low", "negligible"]`, ctx) {
		t.Error("should not match: high risk panel present")
	}
}

func TestRisk_CountPanelRisk(t *testing.T) {
	ctx := &EvalContext{
		Emissions: []*emission.Emission{
			{RiskLevel: "high"},
			{RiskLevel: "high"},
			{RiskLevel: "low"},
		},
	}
	if !EvaluateRiskCondition(`count(panel_risk == "high") >= 2`, ctx) {
		t.Error("expected match: 2 high-risk panels >= 2")
	}
	if EvaluateRiskCondition(`count(panel_risk == "high") >= 3`, ctx) {
		t.Error("should not match: only 2 high-risk panels, need >= 3")
	}
}

func TestRisk_PanelSpecificRisk(t *testing.T) {
	ctx := &EvalContext{
		PanelRiskLevels: map[string]string{
			"security-review": "critical",
			"code-review":     "low",
		},
	}
	if !EvaluateRiskCondition(`panel_risk("security-review") == "critical"`, ctx) {
		t.Error("expected match: security-review is critical")
	}
	if EvaluateRiskCondition(`panel_risk("security-review") == "low"`, ctx) {
		t.Error("should not match: security-review is not low")
	}
	if EvaluateRiskCondition(`panel_risk("nonexistent") == "critical"`, ctx) {
		t.Error("should not match: panel not found")
	}

	// Test != operator
	if !EvaluateRiskCondition(`panel_risk("security-review") != "low"`, ctx) {
		t.Error("expected match: security-review is not low")
	}
}

func TestRisk_OrExpressions(t *testing.T) {
	ctx := &EvalContext{
		Emissions: []*emission.Emission{
			{RiskLevel: "medium"},
		},
	}
	// Neither matches
	if EvaluateRiskCondition(`any_panel_risk == "critical" or any_panel_risk == "high"`, ctx) {
		t.Error("should not match: no critical or high")
	}

	ctx.Emissions[0].RiskLevel = "high"
	if !EvaluateRiskCondition(`any_panel_risk == "critical" or any_panel_risk == "high"`, ctx) {
		t.Error("expected match: high risk panel present")
	}
}
