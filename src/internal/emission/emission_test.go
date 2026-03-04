package emission

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/SET-Apps/ai-submodule/src/internal/evallog"
)

func newLog() *evallog.Log {
	return evallog.New(os.Stderr)
}

// --- LoadEmissions ---

func TestLoadEmissions_ValidJSON(t *testing.T) {
	dir := t.TempDir()
	em := Emission{
		PanelName:       "code-review",
		ConfidenceScore: 0.92,
		RiskLevel:       RiskLow,
		AggregateVerdict: VerdictApprove,
	}
	data, _ := json.Marshal(em)
	os.WriteFile(filepath.Join(dir, "code-review.json"), data, 0644)

	log := newLog()
	result, err := LoadEmissions(dir, nil, log)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(result.Emissions) != 1 {
		t.Fatalf("expected 1 emission, got %d", len(result.Emissions))
	}
	if result.Emissions[0].PanelName != "code-review" {
		t.Errorf("expected panel name 'code-review', got %q", result.Emissions[0].PanelName)
	}
	if result.Emissions[0].ConfidenceScore != 0.92 {
		t.Errorf("expected confidence 0.92, got %f", result.Emissions[0].ConfidenceScore)
	}
	if !result.AllValid {
		t.Error("expected AllValid to be true")
	}
}

func TestLoadEmissions_NonexistentDir(t *testing.T) {
	log := newLog()
	result, err := LoadEmissions("/nonexistent/path/to/dir", nil, log)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(result.Emissions) != 0 {
		t.Errorf("expected 0 emissions, got %d", len(result.Emissions))
	}
}

func TestLoadEmissions_SkipsNonJSON(t *testing.T) {
	dir := t.TempDir()

	em := Emission{PanelName: "valid-panel", ConfidenceScore: 0.80, AggregateVerdict: VerdictApprove}
	data, _ := json.Marshal(em)
	os.WriteFile(filepath.Join(dir, "valid.json"), data, 0644)
	os.WriteFile(filepath.Join(dir, "readme.txt"), []byte("not json"), 0644)
	os.WriteFile(filepath.Join(dir, "config.yaml"), []byte("key: val"), 0644)

	log := newLog()
	result, err := LoadEmissions(dir, nil, log)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(result.Emissions) != 1 {
		t.Fatalf("expected 1 emission (only .json), got %d", len(result.Emissions))
	}
}

func TestLoadEmissions_InvalidJSON(t *testing.T) {
	dir := t.TempDir()
	os.WriteFile(filepath.Join(dir, "bad.json"), []byte("{not valid json}"), 0644)

	log := newLog()
	result, err := LoadEmissions(dir, nil, log)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(result.Emissions) != 0 {
		t.Errorf("expected 0 emissions for invalid JSON, got %d", len(result.Emissions))
	}
	if result.AllValid {
		t.Error("expected AllValid to be false for invalid JSON")
	}
	if len(result.FailedPanels) != 1 {
		t.Errorf("expected 1 failed panel, got %d", len(result.FailedPanels))
	}
}

func TestLoadEmissions_EmptyDir(t *testing.T) {
	dir := t.TempDir()

	log := newLog()
	result, err := LoadEmissions(dir, nil, log)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(result.Emissions) != 0 {
		t.Errorf("expected 0 emissions for empty dir, got %d", len(result.Emissions))
	}
}

// --- ValidateConsistency ---

func TestValidateConsistency_BlockFindingApproveVerdict(t *testing.T) {
	em := &Emission{
		PanelName:        "sec-panel",
		AggregateVerdict: VerdictApprove,
		Findings: []Finding{
			{Verdict: VerdictBlock, Confidence: 0.9},
		},
	}
	log := newLog()
	warnings := ValidateConsistency(em, log)
	if len(warnings) == 0 {
		t.Fatal("expected warnings for block finding + approve verdict")
	}
}

func TestValidateConsistency_SevereFlagsNegligibleRisk(t *testing.T) {
	em := &Emission{
		PanelName: "policy-panel",
		RiskLevel: RiskNegligible,
		PolicyFlags: []PolicyFlag{
			{Flag: "pii_exposure", Severity: RiskCritical},
		},
	}
	log := newLog()
	warnings := ValidateConsistency(em, log)
	if len(warnings) == 0 {
		t.Fatal("expected warnings for critical flags with negligible risk")
	}
}

func TestValidateConsistency_NoIssues(t *testing.T) {
	em := &Emission{
		PanelName:        "clean-panel",
		AggregateVerdict: VerdictApprove,
		RiskLevel:        RiskLow,
		Findings: []Finding{
			{Verdict: VerdictApprove, Confidence: 0.95},
		},
		PolicyFlags: []PolicyFlag{
			{Flag: "minor_thing", Severity: RiskLow},
		},
	}
	log := newLog()
	warnings := ValidateConsistency(em, log)
	if len(warnings) != 0 {
		t.Errorf("expected 0 warnings, got %d: %v", len(warnings), warnings)
	}
}

// --- ValidateFreshness ---

func TestValidateFreshness_CommitSHAMismatch(t *testing.T) {
	em := &Emission{
		PanelName: "panel-a",
		ExecutionContext: &ExecutionContext{
			CommitSHA: "abc1234",
		},
	}
	log := newLog()
	warnings := ValidateFreshness(em, "def5678", log)
	if len(warnings) == 0 {
		t.Fatal("expected warnings for commit SHA mismatch")
	}
}

func TestValidateFreshness_StaleTimestamp(t *testing.T) {
	staleTime := time.Now().Add(-48 * time.Hour).Format(time.RFC3339)
	em := &Emission{
		PanelName: "stale-panel",
		Timestamp: staleTime,
	}
	log := newLog()
	warnings := ValidateFreshness(em, "", log)
	if len(warnings) == 0 {
		t.Fatal("expected warnings for stale timestamp (48h old)")
	}
}

func TestValidateFreshness_FreshTimestamp(t *testing.T) {
	freshTime := time.Now().Add(-1 * time.Hour).Format(time.RFC3339)
	em := &Emission{
		PanelName: "fresh-panel",
		Timestamp: freshTime,
	}
	log := newLog()
	warnings := ValidateFreshness(em, "", log)
	if len(warnings) != 0 {
		t.Errorf("expected 0 warnings for fresh timestamp, got %d: %v", len(warnings), warnings)
	}
}

// --- RiskIndex ---

func TestRiskIndex_AllLevels(t *testing.T) {
	cases := []struct {
		level string
		want  int
	}{
		{RiskCritical, 4},
		{RiskHigh, 3},
		{RiskMedium, 2},
		{RiskLow, 1},
		{RiskNegligible, 0},
		{"unknown_level", -1},
		{"", -1},
	}
	for _, tc := range cases {
		t.Run(tc.level, func(t *testing.T) {
			got := RiskIndex(tc.level)
			if got != tc.want {
				t.Errorf("RiskIndex(%q) = %d, want %d", tc.level, got, tc.want)
			}
		})
	}
}

// --- EffectiveExecutionStatus ---

func TestEffectiveExecutionStatus_Default(t *testing.T) {
	em := &Emission{}
	if got := em.EffectiveExecutionStatus(); got != ExecStatusSuccess {
		t.Errorf("expected %q, got %q", ExecStatusSuccess, got)
	}
}

func TestEffectiveExecutionStatus_Explicit(t *testing.T) {
	cases := []struct {
		status string
		want   string
	}{
		{ExecStatusTimeout, ExecStatusTimeout},
		{ExecStatusError, ExecStatusError},
		{ExecStatusFallback, ExecStatusFallback},
		{ExecStatusSuccess, ExecStatusSuccess},
	}
	for _, tc := range cases {
		t.Run(tc.status, func(t *testing.T) {
			em := &Emission{ExecutionStatus: tc.status}
			if got := em.EffectiveExecutionStatus(); got != tc.want {
				t.Errorf("expected %q, got %q", tc.want, got)
			}
		})
	}
}
