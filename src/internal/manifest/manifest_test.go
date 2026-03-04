package manifest

import (
	"os"
	"strings"
	"testing"

	"github.com/SET-Apps/ai-submodule/src/internal/emission"
	"github.com/SET-Apps/ai-submodule/src/internal/evallog"
)

func newLog() *evallog.Log {
	return evallog.New(os.Stderr)
}

func TestGenerate_BasicFields(t *testing.T) {
	m := Generate(GenerateParams{
		ProfileName:    "default",
		DecisionAction: "auto_merge",
		DecisionRationale: "all conditions satisfied",
		CommitSHA:      "abc1234def5678",
	})

	if m.ManifestVersion != "1.0" {
		t.Errorf("expected manifest version '1.0', got %q", m.ManifestVersion)
	}
	if m.PolicyProfileUsed != "default" {
		t.Errorf("expected policy profile 'default', got %q", m.PolicyProfileUsed)
	}
	if m.Decision.Action != "auto_merge" {
		t.Errorf("expected decision action 'auto_merge', got %q", m.Decision.Action)
	}
	if m.Decision.Rationale != "all conditions satisfied" {
		t.Errorf("unexpected rationale: %q", m.Decision.Rationale)
	}
	if m.ManifestID == "" {
		t.Error("expected non-empty manifest ID")
	}
	if m.Timestamp == "" {
		t.Error("expected non-empty timestamp")
	}
}

func TestGenerate_RepositoryInfoParsing(t *testing.T) {
	m := Generate(GenerateParams{
		Repo:      "SET-Apps/ai-submodule",
		CommitSHA: "abc1234",
		PRNumber:  42,
	})

	if m.Repository == nil {
		t.Fatal("expected repository info to be set")
	}
	if m.Repository.Owner != "SET-Apps" {
		t.Errorf("expected owner 'SET-Apps', got %q", m.Repository.Owner)
	}
	if m.Repository.Name != "ai-submodule" {
		t.Errorf("expected name 'ai-submodule', got %q", m.Repository.Name)
	}
	if m.Repository.CommitSHA != "abc1234" {
		t.Errorf("expected commit SHA 'abc1234', got %q", m.Repository.CommitSHA)
	}
	if m.Repository.PRNumber != 42 {
		t.Errorf("expected PR number 42, got %d", m.Repository.PRNumber)
	}
}

func TestGenerate_NoRepoInfo(t *testing.T) {
	m := Generate(GenerateParams{
		ProfileName: "default",
	})

	if m.Repository != nil {
		t.Error("expected nil repository when Repo is empty")
	}
}

func TestGenerate_HumanInterventionFlag(t *testing.T) {
	// The current Generate function always sets HumanIntervention to an empty struct.
	// Required is always false regardless of decision action.
	actions := []string{"block", "human_review_required", "auto_merge"}
	for _, action := range actions {
		t.Run(action, func(t *testing.T) {
			m := Generate(GenerateParams{
				DecisionAction: action,
			})
			// Current implementation: HumanIntervention.Required is always false
			if m.HumanIntervention.Required {
				t.Errorf("expected HumanIntervention.Required = false for action %q, got true", action)
			}
		})
	}
}

func TestGenerate_PanelsList(t *testing.T) {
	emissions := []*emission.Emission{
		{
			PanelName:        "code-review",
			AggregateVerdict: "approve",
			ConfidenceScore:  0.95,
			SourcePath:       "/tmp/emissions/code-review.json",
		},
		{
			PanelName:        "security-review",
			AggregateVerdict: "approve",
			ConfidenceScore:  0.88,
			SourcePath:       "/tmp/emissions/security-review.json",
		},
	}
	m := Generate(GenerateParams{
		Emissions: emissions,
	})

	if len(m.PanelsExecuted) != 2 {
		t.Fatalf("expected 2 panels, got %d", len(m.PanelsExecuted))
	}
	if m.PanelsExecuted[0].PanelName != "code-review" {
		t.Errorf("expected first panel 'code-review', got %q", m.PanelsExecuted[0].PanelName)
	}
	if m.PanelsExecuted[0].Verdict != "approve" {
		t.Errorf("expected verdict 'approve', got %q", m.PanelsExecuted[0].Verdict)
	}
	if m.PanelsExecuted[0].ConfidenceScore != 0.95 {
		t.Errorf("expected confidence 0.95, got %f", m.PanelsExecuted[0].ConfidenceScore)
	}
	if m.PanelsExecuted[1].PanelName != "security-review" {
		t.Errorf("expected second panel 'security-review', got %q", m.PanelsExecuted[1].PanelName)
	}
}

func TestGenerate_EvalLogRules(t *testing.T) {
	log := newLog()
	log.Record("block-ci-passed", "PASS", "CI checks passed")
	log.Record("auto-merge", "PASS", "all conditions met")

	m := Generate(GenerateParams{
		EvalLog: log,
	})

	if len(m.Decision.PolicyRulesEvaluated) != 2 {
		t.Fatalf("expected 2 rules, got %d", len(m.Decision.PolicyRulesEvaluated))
	}
	if m.Decision.PolicyRulesEvaluated[0].RuleID != "block-ci-passed" {
		t.Errorf("expected first rule 'block-ci-passed', got %q", m.Decision.PolicyRulesEvaluated[0].RuleID)
	}
	if m.Decision.PolicyRulesEvaluated[0].Result != "PASS" {
		t.Errorf("expected result 'PASS', got %q", m.Decision.PolicyRulesEvaluated[0].Result)
	}
}

func TestGenerate_ModelVersion(t *testing.T) {
	emissions := []*emission.Emission{
		{PanelName: "a"},
		{
			PanelName: "b",
			ExecutionContext: &emission.ExecutionContext{
				ModelVersion: "claude-3-opus-20240229",
			},
		},
	}
	m := Generate(GenerateParams{
		Emissions: emissions,
	})

	if m.ModelVersion != "claude-3-opus-20240229" {
		t.Errorf("expected model version 'claude-3-opus-20240229', got %q", m.ModelVersion)
	}
}

func TestGenerate_ShortSHA(t *testing.T) {
	m := Generate(GenerateParams{
		CommitSHA: "abcdef1234567890",
	})

	// ManifestID should contain the 7-char SHA
	if !strings.Contains(m.ManifestID, "abcdef1") {
		t.Errorf("expected manifest ID to contain short SHA 'abcdef1', got %q", m.ManifestID)
	}

	// Test with SHA shorter than 7 chars
	m2 := Generate(GenerateParams{
		CommitSHA: "abc",
	})
	if !strings.Contains(m2.ManifestID, "abc") {
		t.Errorf("expected manifest ID to contain short SHA 'abc', got %q", m2.ManifestID)
	}

	// Test with empty SHA
	m3 := Generate(GenerateParams{})
	if !strings.Contains(m3.ManifestID, "0000000") {
		t.Errorf("expected manifest ID to contain fallback '0000000', got %q", m3.ManifestID)
	}
}
