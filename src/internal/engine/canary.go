package engine

import (
	"fmt"

	"github.com/SET-Apps/ai-submodule/src/internal/emission"
	"github.com/SET-Apps/ai-submodule/src/internal/evallog"
)

// validateCanaryResults checks canary injection results across all emissions
// and returns a list of violation strings.
func validateCanaryResults(emissions []*emission.Emission, log *evallog.Log) []string {
	var allCanaries []emission.CanaryResult
	var securityCanaries []emission.CanaryResult

	for _, em := range emissions {
		if len(em.CanaryResults) == 0 {
			continue
		}
		allCanaries = append(allCanaries, em.CanaryResults...)
		if em.PanelName == "security-review" {
			securityCanaries = append(securityCanaries, em.CanaryResults...)
		}
	}

	if len(allCanaries) == 0 {
		log.Record("canary-validation", "SKIP", "no canary results found")
		return nil
	}

	var violations []string

	// Check 1: Overall pass rate < 0.70.
	detected := 0
	for _, c := range allCanaries {
		if c.Detected {
			detected++
		}
	}
	passRate := float64(detected) / float64(len(allCanaries))
	if passRate < 0.70 {
		v := fmt.Sprintf("canary pass rate %.2f < 0.70 (%d/%d detected)", passRate, detected, len(allCanaries))
		violations = append(violations, v)
		log.Record("canary-pass-rate", "FAIL", v)
	} else {
		log.Record("canary-pass-rate", "PASS", fmt.Sprintf("canary pass rate %.2f >= 0.70", passRate))
	}

	// Check 2: Zero detections on security-review canaries.
	if len(securityCanaries) > 0 {
		secDetected := 0
		for _, c := range securityCanaries {
			if c.Detected {
				secDetected++
			}
		}
		if secDetected == 0 {
			v := fmt.Sprintf("zero detections on %d security-review canaries", len(securityCanaries))
			violations = append(violations, v)
			log.Record("canary-security-zero", "FAIL", v)
		} else {
			log.Record("canary-security-zero", "PASS", fmt.Sprintf("%d/%d security-review canaries detected", secDetected, len(securityCanaries)))
		}
	}

	// Check 3: Severity mismatch rate > 0.50.
	canariesWithExpected := 0
	mismatches := 0
	for _, c := range allCanaries {
		if c.ExpectedSeverity != "" && c.Detected {
			canariesWithExpected++
			if !c.SeverityMatch {
				mismatches++
			}
		}
	}
	if canariesWithExpected > 0 {
		mismatchRate := float64(mismatches) / float64(canariesWithExpected)
		if mismatchRate > 0.50 {
			v := fmt.Sprintf("severity mismatch rate %.2f > 0.50 (%d/%d mismatched)", mismatchRate, mismatches, canariesWithExpected)
			violations = append(violations, v)
			log.Record("canary-severity-mismatch", "FAIL", v)
		} else {
			log.Record("canary-severity-mismatch", "PASS", fmt.Sprintf("severity mismatch rate %.2f <= 0.50", mismatchRate))
		}
	}

	return violations
}
