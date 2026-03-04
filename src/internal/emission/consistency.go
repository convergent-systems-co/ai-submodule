package emission

import (
	"fmt"

	"github.com/SET-Apps/ai-submodule/src/internal/evallog"
)

// ValidateConsistency checks an emission for internal inconsistencies and
// returns a list of warning messages.
func ValidateConsistency(em *Emission, log *evallog.Log) []string {
	var warnings []string

	// Rule 1: A finding with verdict "block" combined with an aggregate
	// verdict of "approve" is contradictory.
	hasBlockFinding := false
	for _, f := range em.Findings {
		if f.Verdict == VerdictBlock {
			hasBlockFinding = true
			break
		}
	}
	if hasBlockFinding && em.AggregateVerdict == VerdictApprove {
		w := fmt.Sprintf("%s: block finding contradicts approve verdict", em.PanelName)
		warnings = append(warnings, w)
		log.Record("consistency-block-approve", "WARN", w)
	} else {
		log.Record("consistency-block-approve", "PASS", fmt.Sprintf("%s: no block/approve contradiction", em.PanelName))
	}

	// Rule 2: Critical or high severity policy flags with negligible risk
	// level is contradictory.
	hasCriticalHighFlag := false
	for _, pf := range em.PolicyFlags {
		if pf.Severity == RiskCritical || pf.Severity == RiskHigh {
			hasCriticalHighFlag = true
			break
		}
	}
	if hasCriticalHighFlag && em.RiskLevel == RiskNegligible {
		w := fmt.Sprintf("%s: critical/high policy flags with negligible risk", em.PanelName)
		warnings = append(warnings, w)
		log.Record("consistency-flag-risk", "WARN", w)
	} else {
		log.Record("consistency-flag-risk", "PASS", fmt.Sprintf("%s: policy flags consistent with risk level", em.PanelName))
	}

	return warnings
}
