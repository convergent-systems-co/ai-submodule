package version

import (
	"encoding/json"
	"runtime"
	"strings"
	"testing"
)

func TestGetReturnsInfo(t *testing.T) {
	info := Get()
	if info.Version == "" {
		t.Error("expected non-empty version")
	}
	if info.GoVersion == "" {
		t.Error("expected non-empty go_version")
	}
	if info.Platform == "" {
		t.Error("expected non-empty platform")
	}
	if info.GoVersion != runtime.Version() {
		t.Errorf("expected go_version %q, got %q", runtime.Version(), info.GoVersion)
	}
}

func TestInfoString(t *testing.T) {
	info := Info{
		Version:   "1.0.0",
		Commit:    "abc1234",
		Date:      "2026-01-01T00:00:00Z",
		GoVersion: "go1.22.0",
		Platform:  "linux/amd64",
	}
	s := info.String()
	if !strings.Contains(s, "dark-governance 1.0.0") {
		t.Errorf("expected version in string, got: %s", s)
	}
	if !strings.Contains(s, "abc1234") {
		t.Errorf("expected commit in string, got: %s", s)
	}
	if !strings.Contains(s, "2026-01-01T00:00:00Z") {
		t.Errorf("expected date in string, got: %s", s)
	}
}

func TestInfoJSON(t *testing.T) {
	info := Info{
		Version:   "1.0.0",
		Commit:    "abc1234",
		Date:      "2026-01-01T00:00:00Z",
		GoVersion: "go1.22.0",
		Platform:  "linux/amd64",
	}
	jsonStr, err := info.JSON()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	var decoded Info
	if err := json.Unmarshal([]byte(jsonStr), &decoded); err != nil {
		t.Fatalf("failed to unmarshal JSON: %v", err)
	}
	if decoded.Version != "1.0.0" {
		t.Errorf("expected version 1.0.0, got %s", decoded.Version)
	}
	if decoded.Commit != "abc1234" {
		t.Errorf("expected commit abc1234, got %s", decoded.Commit)
	}
}

func TestDefaultValues(t *testing.T) {
	// Default values should be set (dev/unknown) when not injected via ldflags
	info := Get()
	// In test context, these won't be overridden by ldflags
	if info.Version != "dev" {
		t.Errorf("expected default version 'dev', got %q", info.Version)
	}
	if info.Commit != "unknown" {
		t.Errorf("expected default commit 'unknown', got %q", info.Commit)
	}
}
