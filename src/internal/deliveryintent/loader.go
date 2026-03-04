package deliveryintent

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

// DefaultIntentDir is the default directory for delivery intent manifests.
const DefaultIntentDir = ".artifacts/delivery-intents"

// DefaultLatestPath is the default path to the latest intent symlink/file.
var DefaultLatestPath = filepath.Join(DefaultIntentDir, "latest.json")

// intentIDPattern validates the intent_id format: di-YYYY-MM-DD-{6 alnum chars}.
var intentIDPattern = regexp.MustCompile(`^di-\d{4}-\d{2}-\d{2}-[a-z0-9]{6}$`)

// checksumPattern validates "sha256:<64 hex chars>".
var checksumPattern = regexp.MustCompile(`^sha256:[0-9a-f]{64}$`)

// validDeliverableActions lists the allowed action values.
var validDeliverableActions = map[string]bool{
	"create": true,
	"update": true,
	"delete": true,
}

// validDeliverableTypes lists the allowed type values.
var validDeliverableTypes = map[string]bool{
	"workflow":  true,
	"config":    true,
	"schema":    true,
	"policy":    true,
	"document":  true,
	"directory": true,
	"script":    true,
}

// LoadFromPath reads and parses a delivery intent from the given file path.
func LoadFromPath(path string) (*DeliveryIntent, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, fmt.Errorf("delivery intent not found at %s: %w", path, err)
		}
		return nil, fmt.Errorf("failed to read delivery intent at %s: %w", path, err)
	}

	var intent DeliveryIntent
	if err := json.Unmarshal(data, &intent); err != nil {
		return nil, fmt.Errorf("invalid JSON in delivery intent at %s: %w", path, err)
	}

	if err := Validate(&intent); err != nil {
		return nil, fmt.Errorf("delivery intent validation failed: %w", err)
	}

	return &intent, nil
}

// LoadLatest reads the latest delivery intent from the default location
// relative to the given root directory.
func LoadLatest(rootDir string) (*DeliveryIntent, error) {
	path := filepath.Join(rootDir, DefaultLatestPath)
	return LoadFromPath(path)
}

// LoadByID reads a specific delivery intent by its ID from the default
// intent directory relative to the given root directory.
func LoadByID(rootDir string, intentID string) (*DeliveryIntent, error) {
	path := filepath.Join(rootDir, DefaultIntentDir, intentID+".json")
	return LoadFromPath(path)
}

// Validate checks that a DeliveryIntent struct has all required fields
// and that field values are well-formed.
func Validate(intent *DeliveryIntent) error {
	if intent.SchemaVersion == "" {
		return fmt.Errorf("missing required field: schema_version")
	}
	if intent.SchemaVersion != SchemaVersion {
		return fmt.Errorf("unsupported schema_version %q (expected %q)", intent.SchemaVersion, SchemaVersion)
	}

	if intent.IntentID == "" {
		return fmt.Errorf("missing required field: intent_id")
	}
	if !intentIDPattern.MatchString(intent.IntentID) {
		return fmt.Errorf("invalid intent_id format %q (expected di-YYYY-MM-DD-xxxxxx)", intent.IntentID)
	}

	if intent.CreatedAt == "" {
		return fmt.Errorf("missing required field: created_at")
	}
	if _, err := time.Parse(time.RFC3339, intent.CreatedAt); err != nil {
		return fmt.Errorf("invalid created_at format (expected RFC3339): %w", err)
	}

	if intent.Source.Branch == "" {
		return fmt.Errorf("missing required field: source.branch")
	}
	if intent.Source.Commit == "" {
		return fmt.Errorf("missing required field: source.commit")
	}

	if len(intent.Deliverables) == 0 {
		return fmt.Errorf("deliverables must contain at least one entry")
	}

	for i, d := range intent.Deliverables {
		if d.Type == "" {
			return fmt.Errorf("deliverable[%d]: missing required field: type", i)
		}
		if !validDeliverableTypes[d.Type] {
			return fmt.Errorf("deliverable[%d]: invalid type %q", i, d.Type)
		}
		if d.Path == "" {
			return fmt.Errorf("deliverable[%d]: missing required field: path", i)
		}
		// Reject absolute paths and traversal segments to prevent path escape.
		if filepath.IsAbs(d.Path) || strings.Contains(d.Path, "..") {
			return fmt.Errorf("deliverable[%d]: path %q must be relative and must not contain '..'", i, d.Path)
		}
		if d.Action == "" {
			return fmt.Errorf("deliverable[%d]: missing required field: action", i)
		}
		if !validDeliverableActions[d.Action] {
			return fmt.Errorf("deliverable[%d]: invalid action %q", i, d.Action)
		}
		if d.Checksum != "" && !checksumPattern.MatchString(d.Checksum) {
			return fmt.Errorf("deliverable[%d]: invalid checksum format %q (expected sha256:<64 hex chars>)", i, d.Checksum)
		}
	}

	// Validate paths in expected_state
	for i, dir := range intent.ExpectedState.RequiredDirectories {
		if filepath.IsAbs(dir) || strings.Contains(dir, "..") {
			return fmt.Errorf("expected_state.required_directories[%d]: path %q must be relative and must not contain '..'", i, dir)
		}
	}

	if intent.ExpectedState.GovernanceVersion == "" {
		return fmt.Errorf("missing required field: expected_state.governance_version")
	}
	if intent.ExpectedState.PolicyProfile == "" {
		return fmt.Errorf("missing required field: expected_state.policy_profile")
	}

	return nil
}
