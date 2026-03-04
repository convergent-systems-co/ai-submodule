package emission

import (
	"fmt"
	"time"

	"github.com/SET-Apps/ai-submodule/src/internal/evallog"
)

// ValidateFreshness checks that an emission is fresh relative to the expected
// commit SHA and current time. Returns a list of warning messages.
func ValidateFreshness(em *Emission, expectedCommitSHA string, log *evallog.Log) []string {
	var warnings []string

	// Rule 1: Commit SHA mismatch.
	if expectedCommitSHA != "" && em.ExecutionContext != nil && em.ExecutionContext.CommitSHA != "" {
		if em.ExecutionContext.CommitSHA != expectedCommitSHA {
			w := fmt.Sprintf("%s: commit_sha mismatch (expected %s, got %s)",
				em.PanelName, expectedCommitSHA, em.ExecutionContext.CommitSHA)
			warnings = append(warnings, w)
			log.Record("freshness-commit-sha", "WARN", w)
		} else {
			log.Record("freshness-commit-sha", "PASS", fmt.Sprintf("%s: commit SHA matches", em.PanelName))
		}
	} else {
		log.Record("freshness-commit-sha", "SKIP", fmt.Sprintf("%s: no commit SHA to compare", em.PanelName))
	}

	// Rule 2: Timestamp older than 24 hours.
	if em.Timestamp != "" {
		t, err := time.Parse(time.RFC3339, em.Timestamp)
		if err != nil {
			// Try alternate format.
			t, err = time.Parse("2006-01-02T15:04:05", em.Timestamp)
		}
		if err == nil {
			age := time.Since(t)
			if age > 24*time.Hour {
				w := fmt.Sprintf("%s: emission is %.1f hours old (>24h)", em.PanelName, age.Hours())
				warnings = append(warnings, w)
				log.Record("freshness-timestamp", "WARN", w)
			} else {
				log.Record("freshness-timestamp", "PASS", fmt.Sprintf("%s: emission age %.1fh", em.PanelName, age.Hours()))
			}
		} else {
			log.Record("freshness-timestamp", "SKIP", fmt.Sprintf("%s: unparseable timestamp: %s", em.PanelName, em.Timestamp))
		}
	} else {
		log.Record("freshness-timestamp", "SKIP", fmt.Sprintf("%s: no timestamp", em.PanelName))
	}

	return warnings
}
