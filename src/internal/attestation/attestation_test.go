package attestation

import "testing"

func TestCreateManifestAndVerify(t *testing.T) {
	ma := NewMergeAttestation("test-secret")

	emissions := []map[string]interface{}{
		{"panel": "code-review", "status": "pass", "score": 95},
		{"panel": "security-review", "status": "pass", "score": 100},
	}

	m := ma.CreateManifest(emissions, "approved", "default", "all panels pass", "manifest-1")

	if m.ManifestID != "manifest-1" {
		t.Fatalf("expected manifest-1, got %q", m.ManifestID)
	}
	if m.Decision != "approved" {
		t.Fatalf("expected approved, got %q", m.Decision)
	}
	if m.Signature == "" {
		t.Fatal("expected non-empty signature")
	}
	if len(m.EmissionHashes) != 2 {
		t.Fatalf("expected 2 emission hashes, got %d", len(m.EmissionHashes))
	}

	// Verify should pass.
	err := ma.VerifyManifest(m)
	if err != nil {
		t.Fatalf("verify: %v", err)
	}
}

func TestTamperedSignature(t *testing.T) {
	ma := NewMergeAttestation("test-secret")

	emissions := []map[string]interface{}{
		{"panel": "code-review", "status": "pass"},
	}

	m := ma.CreateManifest(emissions, "approved", "default", "ok", "m-1")

	// Tamper with signature.
	m.Signature = "deadbeef0000"

	err := ma.VerifyManifest(m)
	if err == nil {
		t.Fatal("expected error for tampered signature")
	}
}

func TestVerifyEmissions_Mismatch(t *testing.T) {
	ma := NewMergeAttestation("test-secret")

	origEmissions := []map[string]interface{}{
		{"panel": "code-review", "status": "pass", "score": 95},
		{"panel": "security-review", "status": "pass", "score": 100},
	}

	m := ma.CreateManifest(origEmissions, "approved", "default", "ok", "m-1")

	// Provide modified emissions.
	modifiedEmissions := []map[string]interface{}{
		{"panel": "code-review", "status": "pass", "score": 50}, // different score
		{"panel": "security-review", "status": "pass", "score": 100},
	}

	mismatched := ma.VerifyEmissions(m, modifiedEmissions)
	if len(mismatched) != 1 {
		t.Fatalf("expected 1 mismatch, got %d: %v", len(mismatched), mismatched)
	}
	if mismatched[0] != "code-review" {
		t.Fatalf("expected code-review mismatch, got %q", mismatched[0])
	}
}

func TestVerifyEmissions_AllMatch(t *testing.T) {
	ma := NewMergeAttestation("test-secret")

	emissions := []map[string]interface{}{
		{"panel": "code-review", "status": "pass"},
	}

	m := ma.CreateManifest(emissions, "approved", "default", "ok", "m-1")

	mismatched := ma.VerifyEmissions(m, emissions)
	if len(mismatched) != 0 {
		t.Fatalf("expected no mismatches, got %v", mismatched)
	}
}

func TestGetCommitMessageHash(t *testing.T) {
	ma := NewMergeAttestation("test-secret")

	emissions := []map[string]interface{}{
		{"panel": "code-review", "status": "pass"},
	}

	m := ma.CreateManifest(emissions, "approved", "default", "ok", "m-1")

	hash := ma.GetCommitMessageHash(m)
	if len(hash) != 12 {
		t.Fatalf("expected 12-char hash, got %d chars: %q", len(hash), hash)
	}
}

func TestGetCommitMessageHash_Short(t *testing.T) {
	ma := NewMergeAttestation("test-secret")

	m := &Manifest{AggregateHash: "short"}
	hash := ma.GetCommitMessageHash(m)
	if hash != "short" {
		t.Fatalf("expected 'short', got %q", hash)
	}
}

func TestDifferentSecrets(t *testing.T) {
	ma1 := NewMergeAttestation("secret-1")
	ma2 := NewMergeAttestation("secret-2")

	emissions := []map[string]interface{}{
		{"panel": "code-review", "status": "pass"},
	}

	m := ma1.CreateManifest(emissions, "approved", "default", "ok", "m-1")

	// Verify with wrong secret should fail.
	err := ma2.VerifyManifest(m)
	if err == nil {
		t.Fatal("expected error verifying with wrong secret")
	}
}
