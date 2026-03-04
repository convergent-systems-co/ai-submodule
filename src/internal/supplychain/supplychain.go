// Package supplychain provides SHA-256 integrity verification for
// governance-critical files. It generates and verifies manifests that
// capture file hashes for policy, schema, persona, and prompt files.
//
// Ported from Python: governance/engine/supply_chain.py
package supplychain

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

// VerificationResult captures the outcome of a manifest verification.
type VerificationResult struct {
	Valid        bool     `json:"valid"`
	TotalFiles   int      `json:"total_files"`
	VerifiedFiles int     `json:"verified_files"`
	Failures     []string `json:"failures"`
	MissingFiles []string `json:"missing_files"`
	NewFiles     []string `json:"new_files"`
}

// ---------------------------------------------------------------------------
// Critical directories and extensions
// ---------------------------------------------------------------------------

type criticalDir struct {
	Dir        string
	Extensions []string
}

var criticalDirs = []criticalDir{
	{Dir: "governance/policy", Extensions: []string{".yaml", ".yml"}},
	{Dir: "governance/schemas", Extensions: []string{".json"}},
	{Dir: "governance/personas/agentic", Extensions: []string{".md"}},
	{Dir: "governance/prompts/reviews", Extensions: []string{".md"}},
}

// ---------------------------------------------------------------------------
// IntegrityVerifier
// ---------------------------------------------------------------------------

// IntegrityVerifier manages supply-chain integrity for a repository.
type IntegrityVerifier struct {
	repoRoot string
}

// NewIntegrityVerifier creates a verifier for the given repository root.
func NewIntegrityVerifier(repoRoot string) *IntegrityVerifier {
	return &IntegrityVerifier{repoRoot: repoRoot}
}

// GenerateManifest scans critical directories and produces a manifest map
// keyed by relative path with SHA-256 hex digests as values.
func (v *IntegrityVerifier) GenerateManifest() (map[string]interface{}, error) {
	files := make(map[string]string)

	for _, cd := range criticalDirs {
		dir := filepath.Join(v.repoRoot, cd.Dir)
		entries, err := os.ReadDir(dir)
		if err != nil {
			if os.IsNotExist(err) {
				continue
			}
			return nil, fmt.Errorf("supplychain: read dir %s: %w", dir, err)
		}
		for _, e := range entries {
			if e.IsDir() {
				continue
			}
			ext := strings.ToLower(filepath.Ext(e.Name()))
			if !matchExt(ext, cd.Extensions) {
				continue
			}
			absPath := filepath.Join(dir, e.Name())
			hash, err := hashFile(absPath)
			if err != nil {
				return nil, err
			}
			rel, _ := filepath.Rel(v.repoRoot, absPath)
			files[rel] = hash
		}
	}

	manifest := map[string]interface{}{
		"version":    "1.0",
		"generated":  time.Now().UTC().Format(time.RFC3339),
		"file_count": len(files),
		"files":      files,
	}
	return manifest, nil
}

// WriteManifest generates and writes the manifest to the given path.
func (v *IntegrityVerifier) WriteManifest(path string) error {
	manifest, err := v.GenerateManifest()
	if err != nil {
		return err
	}
	data, err := json.MarshalIndent(manifest, "", "  ")
	if err != nil {
		return fmt.Errorf("supplychain: marshal manifest: %w", err)
	}
	data = append(data, '\n')
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return fmt.Errorf("supplychain: create dir: %w", err)
	}
	return os.WriteFile(path, data, 0644)
}

// LoadManifest reads a previously written manifest file.
func (v *IntegrityVerifier) LoadManifest(path string) (map[string]interface{}, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("supplychain: read manifest %s: %w", path, err)
	}
	var manifest map[string]interface{}
	if err := json.Unmarshal(data, &manifest); err != nil {
		return nil, fmt.Errorf("supplychain: parse manifest %s: %w", path, err)
	}
	return manifest, nil
}

// Verify checks that all files recorded in the manifest still match.
func (v *IntegrityVerifier) Verify(manifestPath string) (*VerificationResult, error) {
	manifest, err := v.LoadManifest(manifestPath)
	if err != nil {
		return nil, err
	}

	filesRaw, ok := manifest["files"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("supplychain: manifest missing 'files' key")
	}

	result := &VerificationResult{
		Valid:      true,
		TotalFiles: len(filesRaw),
	}

	// Build a sorted list of expected files for deterministic output.
	expected := make([]string, 0, len(filesRaw))
	for path := range filesRaw {
		expected = append(expected, path)
	}
	sort.Strings(expected)

	for _, relPath := range expected {
		expectedHash, _ := filesRaw[relPath].(string)
		absPath := filepath.Join(v.repoRoot, relPath)
		actualHash, err := hashFile(absPath)
		if err != nil {
			if os.IsNotExist(err) {
				result.MissingFiles = append(result.MissingFiles, relPath)
				result.Valid = false
				continue
			}
			return nil, err
		}
		if actualHash != expectedHash {
			result.Failures = append(result.Failures, relPath)
			result.Valid = false
		} else {
			result.VerifiedFiles++
		}
	}

	// Detect new files not in the manifest.
	currentManifest, err := v.GenerateManifest()
	if err != nil {
		return result, nil // best-effort
	}
	if currentFiles, ok := currentManifest["files"].(map[string]string); ok {
		for path := range currentFiles {
			if _, found := filesRaw[path]; !found {
				result.NewFiles = append(result.NewFiles, path)
			}
		}
	}

	return result, nil
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

func hashFile(path string) (string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	h := sha256.Sum256(data)
	return hex.EncodeToString(h[:]), nil
}

func matchExt(ext string, allowed []string) bool {
	for _, a := range allowed {
		if ext == a {
			return true
		}
	}
	return false
}
