package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/SET-Apps/ai-submodule/src/internal/topology"
)

func TestLoadTopologyRegistry(t *testing.T) {
	t.Run("valid session file", func(t *testing.T) {
		dir := t.TempDir()
		sessionDir := filepath.Join(dir, "sessions")
		if err := os.MkdirAll(sessionDir, 0755); err != nil {
			t.Fatal(err)
		}

		state := topologySessionState{
			Agents: []topology.AgentRegistration{
				{AgentID: "pm-1", Role: topology.RolePM},
				{AgentID: "tl-1", Role: topology.RoleTechLead, ParentTaskID: "pm-1"},
			},
			PMEnabled:     true,
			TopologyValid: true,
		}
		data, _ := json.MarshalIndent(state, "", "  ")
		sessionPath := filepath.Join(sessionDir, "latest.json")
		if err := os.WriteFile(sessionPath, data, 0644); err != nil {
			t.Fatal(err)
		}

		rules := topology.DefaultRules()
		registry, pmEnabled, err := loadTopologyRegistry(sessionPath, rules)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if !pmEnabled {
			t.Error("expected PM mode enabled")
		}
		if len(registry) != 2 {
			t.Errorf("expected 2 agents, got %d", len(registry))
		}
	})

	t.Run("missing session file", func(t *testing.T) {
		rules := topology.DefaultRules()
		_, _, err := loadTopologyRegistry("/nonexistent/latest.json", rules)
		if err == nil {
			t.Fatal("expected error for missing file")
		}
	})

	t.Run("invalid JSON", func(t *testing.T) {
		dir := t.TempDir()
		path := filepath.Join(dir, "latest.json")
		if err := os.WriteFile(path, []byte("not json"), 0644); err != nil {
			t.Fatal(err)
		}

		rules := topology.DefaultRules()
		_, _, err := loadTopologyRegistry(path, rules)
		if err == nil {
			t.Fatal("expected error for invalid JSON")
		}
	})
}

func TestTopologyReportJSON(t *testing.T) {
	report := topologyReport{
		Status:     "valid",
		PMEnabled:  true,
		AgentCount: 4,
	}

	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		t.Fatalf("failed to marshal: %v", err)
	}

	var parsed topologyReport
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("failed to unmarshal: %v", err)
	}

	if parsed.Status != "valid" {
		t.Errorf("status = %q, want %q", parsed.Status, "valid")
	}
	if !parsed.PMEnabled {
		t.Error("expected PM enabled")
	}
	if parsed.AgentCount != 4 {
		t.Errorf("agent count = %d, want 4", parsed.AgentCount)
	}
}

func TestTopologyReportViolation(t *testing.T) {
	report := topologyReport{
		Status:     "violation",
		PMEnabled:  true,
		AgentCount: 2,
		Violations: []string{"missing DevOps", "orphaned coder"},
	}

	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		t.Fatalf("failed to marshal: %v", err)
	}

	var parsed topologyReport
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("failed to unmarshal: %v", err)
	}

	if parsed.Status != "violation" {
		t.Errorf("status = %q, want %q", parsed.Status, "violation")
	}
	if len(parsed.Violations) != 2 {
		t.Errorf("violations count = %d, want 2", len(parsed.Violations))
	}
}

func TestTopologyReportWarning(t *testing.T) {
	report := topologyReport{
		Status:     "warning",
		PMEnabled:  true,
		AgentCount: 3,
		Warnings:   []string{"TechLead has no coders"},
	}

	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		t.Fatalf("failed to marshal: %v", err)
	}

	var parsed topologyReport
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("failed to unmarshal: %v", err)
	}

	if parsed.Status != "warning" {
		t.Errorf("status = %q, want %q", parsed.Status, "warning")
	}
	if len(parsed.Warnings) != 1 {
		t.Errorf("warnings count = %d, want 1", len(parsed.Warnings))
	}
}
