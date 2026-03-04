package condition

import (
	"testing"

	"github.com/SET-Apps/ai-submodule/src/internal/emission"
)

// --- Block conditions ---

func TestBlock_AggregateConfidenceLessThanThreshold(t *testing.T) {
	ctx := &EvalContext{
		AggregateConfidence: 0.50,
	}
	if !EvaluateBlockCondition(`aggregate_confidence < 0.70`, ctx) {
		t.Error("expected block: confidence 0.50 < 0.70")
	}
	ctx.AggregateConfidence = 0.85
	if EvaluateBlockCondition(`aggregate_confidence < 0.70`, ctx) {
		t.Error("should not block: confidence 0.85 >= 0.70")
	}
}

func TestBlock_AnyPolicyFlagMatch(t *testing.T) {
	ctx := &EvalContext{
		PolicyFlags: []string{"pii_exposure", "cost_overrun"},
	}
	if !EvaluateBlockCondition(`any_policy_flag == "pii_exposure"`, ctx) {
		t.Error("expected block: pii_exposure present")
	}
	if EvaluateBlockCondition(`any_policy_flag == "nonexistent_flag"`, ctx) {
		t.Error("should not block: nonexistent_flag not present")
	}
}

func TestBlock_AnyPolicyFlagStartsWith(t *testing.T) {
	ctx := &EvalContext{
		PolicyFlags: []string{"pii_exposure", "pii_leak"},
	}
	if !EvaluateBlockCondition(`any_policy_flag starts_with "pii_"`, ctx) {
		t.Error("expected block: pii_ prefix present")
	}
	ctx.PolicyFlags = []string{"cost_overrun"}
	if EvaluateBlockCondition(`any_policy_flag starts_with "pii_"`, ctx) {
		t.Error("should not block: no pii_ prefix")
	}
}

func TestBlock_CompoundAndCondition(t *testing.T) {
	ctx := &EvalContext{
		AggregateConfidence: 0.50,
		PolicyFlags:         []string{"pii_exposure"},
	}
	cond := `aggregate_confidence < 0.70 and any_policy_flag == "pii_exposure"`
	if !EvaluateBlockCondition(cond, ctx) {
		t.Error("expected block: both conditions true")
	}

	// Make one condition false
	ctx.AggregateConfidence = 0.90
	if EvaluateBlockCondition(cond, ctx) {
		t.Error("should not block: confidence is above threshold")
	}
}

func TestBlock_DestructionRecommended(t *testing.T) {
	ctx := &EvalContext{
		Emissions: []*emission.Emission{
			{DestructionRecommended: true},
		},
	}
	if !EvaluateBlockCondition(`destruction_recommended == true`, ctx) {
		t.Error("expected block: destruction recommended")
	}

	ctx.Emissions[0].DestructionRecommended = false
	if EvaluateBlockCondition(`destruction_recommended == true`, ctx) {
		t.Error("should not block: destruction not recommended")
	}
}

// --- Auto-merge conditions ---

func TestAutoMerge_AllPanelVerdictsInSet(t *testing.T) {
	ctx := &EvalContext{
		Emissions: []*emission.Emission{
			{AggregateVerdict: "approve"},
			{AggregateVerdict: "approve"},
		},
	}
	if !EvaluateAutoMergeCondition(`all_panel_verdicts in ["approve"]`, ctx) {
		t.Error("expected auto-merge: all verdicts are approve")
	}

	ctx.Emissions[1].AggregateVerdict = "request_changes"
	if EvaluateAutoMergeCondition(`all_panel_verdicts in ["approve"]`, ctx) {
		t.Error("should not auto-merge: one verdict is request_changes")
	}
}

func TestAutoMerge_NoPolicyFlagsSeverityInSet(t *testing.T) {
	ctx := &EvalContext{
		PolicyFlagSeverities: map[string]string{
			"minor_thing": "low",
		},
	}
	if !EvaluateAutoMergeCondition(`no_policy_flags_severity in ["critical", "high"]`, ctx) {
		t.Error("expected auto-merge: no critical/high flags")
	}

	ctx.PolicyFlagSeverities["big_issue"] = "critical"
	if EvaluateAutoMergeCondition(`no_policy_flags_severity in ["critical", "high"]`, ctx) {
		t.Error("should not auto-merge: critical flag present")
	}
}

// --- Auto-remediate conditions ---

func TestAutoRemediate_AutoRemediable(t *testing.T) {
	ctx := &EvalContext{
		PolicyFlags: []string{"auto_fix_issue"},
		Emissions: []*emission.Emission{
			{
				PolicyFlags: []emission.PolicyFlag{
					{Flag: "auto_fix_issue", AutoRemediable: true},
				},
			},
		},
	}
	if !EvaluateAutoRemediateCondition(`auto_remediable == true`, ctx) {
		t.Error("expected auto-remediate: all flags are auto-remediable")
	}

	ctx.Emissions[0].PolicyFlags[0].AutoRemediable = false
	if EvaluateAutoRemediateCondition(`auto_remediable == true`, ctx) {
		t.Error("should not auto-remediate: flag is not auto-remediable")
	}
}

// --- Panel disagreement ---

func TestPanelDisagreementDetected(t *testing.T) {
	ctx := &EvalContext{
		Emissions: []*emission.Emission{
			{AggregateVerdict: "approve"},
			{AggregateVerdict: "block"},
		},
	}
	if !EvaluateBlockCondition(`panel_disagreement_detected == true`, ctx) {
		t.Error("expected disagreement: approve vs block")
	}

	ctx.Emissions[1].AggregateVerdict = "approve"
	if EvaluateBlockCondition(`panel_disagreement_detected == true`, ctx) {
		t.Error("should not detect disagreement: both approve")
	}
}
