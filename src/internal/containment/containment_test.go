package containment

import "testing"

const testPolicy = `
mode: enforced
personas:
  coder:
    denied_paths:
      - "*.env"
      - "jm-compliance.yml"
    denied_operations:
      - force_push
      - delete_branch
    resource_limits:
      max_files: 50
      max_lines: 5000
  document_writer:
    allowed_operations:
      - write_docs
      - update_readme
    resource_limits:
      max_files: 10
`

func newTestChecker(t *testing.T) *Checker {
	t.Helper()
	c, err := NewChecker([]byte(testPolicy), "")
	if err != nil {
		t.Fatalf("new checker: %v", err)
	}
	return c
}

func TestCheckPath_Denied(t *testing.T) {
	c := newTestChecker(t)
	result := c.CheckPath("coder", ".env")
	if !result.Blocked {
		t.Fatal("expected .env to be blocked for coder")
	}
	if result.Reason == "" {
		t.Fatal("expected non-empty reason")
	}
}

func TestCheckPath_Allowed(t *testing.T) {
	c := newTestChecker(t)
	result := c.CheckPath("coder", "src/main.go")
	if result.Blocked {
		t.Fatalf("expected src/main.go to be allowed: %s", result.Reason)
	}
	if !result.Allowed {
		t.Fatal("expected Allowed=true")
	}
}

func TestCheckPath_UnknownPersona(t *testing.T) {
	c := newTestChecker(t)
	result := c.CheckPath("unknown_persona", ".env")
	if result.Blocked {
		t.Fatal("unknown persona should not be blocked")
	}
	if !result.Allowed {
		t.Fatal("expected Allowed=true for unknown persona")
	}
}

func TestCheckOperation_Denied(t *testing.T) {
	c := newTestChecker(t)
	result := c.CheckOperation("coder", "force_push")
	if !result.Blocked {
		t.Fatal("expected force_push to be blocked for coder")
	}
}

func TestCheckOperation_Allowed_Denylist(t *testing.T) {
	c := newTestChecker(t)
	result := c.CheckOperation("coder", "write_code")
	if result.Blocked {
		t.Fatal("expected write_code to be allowed for coder")
	}
}

func TestCheckOperation_AllowedByAllowlist(t *testing.T) {
	c := newTestChecker(t)

	// document_writer uses allowlist mode.
	result := c.CheckOperation("document_writer", "write_docs")
	if !result.Allowed || result.Blocked {
		t.Fatal("expected write_docs to be allowed for document_writer")
	}

	// Operation not in allowlist should be blocked.
	result = c.CheckOperation("document_writer", "delete_branch")
	if !result.Blocked {
		t.Fatal("expected delete_branch to be blocked for document_writer (not in allowlist)")
	}
}

func TestCheckResourceLimit_Under(t *testing.T) {
	c := newTestChecker(t)
	result := c.CheckResourceLimit("coder", "max_files", 30)
	if result.Blocked {
		t.Fatal("expected under limit to be allowed")
	}
}

func TestCheckResourceLimit_Over(t *testing.T) {
	c := newTestChecker(t)
	result := c.CheckResourceLimit("coder", "max_files", 100)
	if !result.Blocked {
		t.Fatal("expected over limit to be blocked")
	}
}

func TestCheckResourceLimit_ExactlyAtLimit(t *testing.T) {
	c := newTestChecker(t)
	result := c.CheckResourceLimit("coder", "max_files", 50)
	if result.Blocked {
		t.Fatal("expected exactly at limit to be allowed (value > limit, not >=)")
	}
}

func TestCheckResourceLimit_UnknownResource(t *testing.T) {
	c := newTestChecker(t)
	result := c.CheckResourceLimit("coder", "max_memory", 9999)
	if result.Blocked {
		t.Fatal("expected unknown resource to be allowed")
	}
}

func TestMode(t *testing.T) {
	c := newTestChecker(t)
	if c.Mode() != "enforced" {
		t.Fatalf("expected enforced, got %q", c.Mode())
	}
}
