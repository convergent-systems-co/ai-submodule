// Package attestation provides HMAC-SHA256 signing and verification for
// governance merge attestation manifests. Each manifest ties a set of
// panel emission hashes to a policy decision.
//
// Ported from Python: governance/engine/attestation.py
package attestation

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"sort"
	"time"
)

// ---------------------------------------------------------------------------
// Manifest
// ---------------------------------------------------------------------------

// Manifest captures the signed attestation for a merge decision.
type Manifest struct {
	ManifestID     string            `json:"manifest_id"`
	AggregateHash  string            `json:"aggregate_hash"`
	EmissionHashes map[string]string `json:"emission_hashes"`
	Decision       string            `json:"decision"`
	Profile        string            `json:"profile"`
	Rationale      string            `json:"rationale"`
	Signature      string            `json:"signature"`
	Timestamp      string            `json:"timestamp"`
}

// ---------------------------------------------------------------------------
// MergeAttestation
// ---------------------------------------------------------------------------

// MergeAttestation creates and verifies HMAC-signed manifests.
type MergeAttestation struct {
	secret string
}

// NewMergeAttestation creates an attestation signer with the given secret.
func NewMergeAttestation(secret string) *MergeAttestation {
	return &MergeAttestation{secret: secret}
}

// CreateManifest builds a signed manifest from a set of emissions.
// Each emission map must have a "panel" key (string) for labeling.
func (ma *MergeAttestation) CreateManifest(
	emissions []map[string]interface{},
	decision, profile, rationale, manifestID string,
) *Manifest {
	hashes := make(map[string]string, len(emissions))
	for _, em := range emissions {
		panel, _ := em["panel"].(string)
		if panel == "" {
			panel = "unknown"
		}
		hashes[panel] = hashEmission(em)
	}

	agg := aggregateHash(hashes)

	m := &Manifest{
		ManifestID:     manifestID,
		AggregateHash:  agg,
		EmissionHashes: hashes,
		Decision:       decision,
		Profile:        profile,
		Rationale:      rationale,
		Timestamp:      time.Now().UTC().Format(time.RFC3339),
	}

	m.Signature = ma.sign(m)
	return m
}

// VerifyManifest checks the HMAC signature of a manifest.
func (ma *MergeAttestation) VerifyManifest(m *Manifest) error {
	expected := ma.sign(m)
	if !hmac.Equal([]byte(expected), []byte(m.Signature)) {
		return fmt.Errorf("attestation: signature mismatch")
	}
	return nil
}

// VerifyEmissions compares manifest emission hashes against a fresh set.
// Returns the panel names whose hashes do not match.
func (ma *MergeAttestation) VerifyEmissions(m *Manifest, emissions []map[string]interface{}) []string {
	var mismatched []string
	current := make(map[string]string, len(emissions))
	for _, em := range emissions {
		panel, _ := em["panel"].(string)
		if panel == "" {
			panel = "unknown"
		}
		current[panel] = hashEmission(em)
	}

	for panel, expected := range m.EmissionHashes {
		actual, ok := current[panel]
		if !ok || actual != expected {
			mismatched = append(mismatched, panel)
		}
	}

	sort.Strings(mismatched)
	return mismatched
}

// GetCommitMessageHash returns a short hash suitable for embedding in
// a commit message, derived from the manifest's aggregate hash.
func (ma *MergeAttestation) GetCommitMessageHash(m *Manifest) string {
	if len(m.AggregateHash) >= 12 {
		return m.AggregateHash[:12]
	}
	return m.AggregateHash
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

// sign computes the HMAC-SHA256 of the manifest's payload fields.
func (ma *MergeAttestation) sign(m *Manifest) string {
	payload := map[string]interface{}{
		"manifest_id":    m.ManifestID,
		"aggregate_hash": m.AggregateHash,
		"emission_hashes": m.EmissionHashes,
		"decision":       m.Decision,
		"profile":        m.Profile,
		"rationale":      m.Rationale,
		"timestamp":      m.Timestamp,
	}
	canonical, _ := json.Marshal(payload)

	mac := hmac.New(sha256.New, []byte(ma.secret))
	mac.Write(canonical)
	return hex.EncodeToString(mac.Sum(nil))
}

// hashEmission produces the SHA-256 hex digest of a canonically-serialized emission.
func hashEmission(em map[string]interface{}) string {
	canonical, _ := json.Marshal(em)
	h := sha256.Sum256(canonical)
	return hex.EncodeToString(h[:])
}

// aggregateHash produces a SHA-256 digest over all individual emission hashes
// (sorted by panel name for determinism).
func aggregateHash(hashes map[string]string) string {
	panels := make([]string, 0, len(hashes))
	for p := range hashes {
		panels = append(panels, p)
	}
	sort.Strings(panels)

	h := sha256.New()
	for _, p := range panels {
		h.Write([]byte(p))
		h.Write([]byte(hashes[p]))
	}
	return hex.EncodeToString(h.Sum(nil))
}
