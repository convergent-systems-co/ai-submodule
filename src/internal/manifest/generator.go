package manifest

import (
	"fmt"
	"strings"
	"time"

	"github.com/SET-Apps/ai-submodule/src/internal/emission"
	"github.com/SET-Apps/ai-submodule/src/internal/evallog"
)

// GenerateParams holds the inputs needed to generate a run manifest.
type GenerateParams struct {
	Emissions           []*emission.Emission
	ProfileName         string
	AggregateConfidence float64
	AggregateRisk       string
	DecisionAction      string
	DecisionRationale   string
	EvalLog             *evallog.Log
	CommitSHA           string
	PRNumber            int
	Repo                string
}

// Generate creates a RunManifest from the provided parameters.
func Generate(params GenerateParams) *RunManifest {
	now := time.Now().UTC()

	// Build manifest ID: YYYYMMDD-HHMMSS-<sha7>
	sha7 := params.CommitSHA
	if len(sha7) > 7 {
		sha7 = sha7[:7]
	}
	if sha7 == "" {
		sha7 = "0000000"
	}
	manifestID := fmt.Sprintf("%s-%s", now.Format("20060102-150405"), sha7)

	// Extract model version from first emission with execution context.
	modelVersion := ""
	for _, em := range params.Emissions {
		if em.ExecutionContext != nil && em.ExecutionContext.ModelVersion != "" {
			modelVersion = em.ExecutionContext.ModelVersion
			break
		}
	}

	// Build panels executed list.
	var panels []PanelExecuted
	for _, em := range params.Emissions {
		panels = append(panels, PanelExecuted{
			PanelName:       em.PanelName,
			Verdict:         em.AggregateVerdict,
			ConfidenceScore: em.ConfidenceScore,
			ArtifactPath:    em.SourcePath,
		})
	}

	// Build policy rules evaluated from eval log.
	var rules []RuleResult
	if params.EvalLog != nil {
		for _, entry := range params.EvalLog.Entries() {
			rules = append(rules, RuleResult{
				RuleID: entry.RuleID,
				Result: entry.Result,
				Detail: entry.Detail,
			})
		}
	}

	// Build repository info.
	var repoInfo *RepositoryInfo
	if params.Repo != "" {
		owner := ""
		name := params.Repo
		if parts := strings.SplitN(params.Repo, "/", 2); len(parts) == 2 {
			owner = parts[0]
			name = parts[1]
		}
		repoInfo = &RepositoryInfo{
			Name:      name,
			Owner:     owner,
			CommitSHA: params.CommitSHA,
			PRNumber:  params.PRNumber,
		}
	}

	return &RunManifest{
		ManifestVersion:     "1.0",
		ManifestID:          manifestID,
		Timestamp:           now.Format(time.RFC3339),
		PolicyProfileUsed:   params.ProfileName,
		ModelVersion:        modelVersion,
		AggregateConfidence: params.AggregateConfidence,
		RiskLevel:           params.AggregateRisk,
		HumanIntervention:   HumanIntervention{},
		Decision: Decision{
			Action:               params.DecisionAction,
			Rationale:            params.DecisionRationale,
			PolicyRulesEvaluated: rules,
		},
		PanelsExecuted: panels,
		Repository:     repoInfo,
	}
}
