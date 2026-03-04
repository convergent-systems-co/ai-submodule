package engine

import (
	"fmt"
	"io"
	"strings"

	"github.com/SET-Apps/ai-submodule/src/internal/emission"
	"github.com/SET-Apps/ai-submodule/src/internal/evallog"
	"github.com/SET-Apps/ai-submodule/src/internal/exitcode"
	"github.com/SET-Apps/ai-submodule/src/internal/manifest"
	"github.com/SET-Apps/ai-submodule/src/internal/policy"
	"github.com/SET-Apps/ai-submodule/src/internal/condition"
)

// EvaluateParams holds the inputs for the governance evaluation pipeline.
type EvaluateParams struct {
	EmissionsDir string
	ProfileData  []byte
	SchemaData   []byte
	CIPassed     bool
	CommitSHA    string
	PRNumber     int
	Repo         string
	DryRun       bool
	LogWriter    io.Writer
}

// EvaluateResult holds the output of the governance evaluation pipeline.
type EvaluateResult struct {
	Manifest *manifest.RunManifest
	ExitCode int
}

// Evaluate runs the 13-step governance evaluation pipeline.
func Evaluate(params EvaluateParams) (*EvaluateResult, error) {
	log := evallog.New(params.LogWriter)

	// ── Step 1: Load emissions ──────────────────────────────────────────
	loadResult, err := emission.LoadEmissions(params.EmissionsDir, params.SchemaData, log)
	if err != nil {
		return nil, fmt.Errorf("loading emissions: %w", err)
	}

	emissions := loadResult.Emissions

	// No emissions → block immediately.
	if len(emissions) == 0 {
		log.Record("pipeline", "FAIL", "no emissions found")
		m := manifest.Generate(manifest.GenerateParams{
			ProfileName:       "default",
			DecisionAction:    "block",
			DecisionRationale: "no emissions found",
			EvalLog:           log,
			CommitSHA:         params.CommitSHA,
			PRNumber:          params.PRNumber,
			Repo:              params.Repo,
		})
		code := exitcode.Block
		if params.DryRun {
			code = 0
		}
		return &EvaluateResult{Manifest: m, ExitCode: code}, nil
	}

	// ── Step 2: Validate consistency ────────────────────────────────────
	for _, em := range emissions {
		emission.ValidateConsistency(em, log)
	}

	// ── Step 3: Validate freshness ──────────────────────────────────────
	if params.CommitSHA != "" {
		for _, em := range emissions {
			emission.ValidateFreshness(em, params.CommitSHA, log)
		}
	}

	// ── Step 4: Load profile ────────────────────────────────────────────
	var profile *policy.Profile
	if len(params.ProfileData) > 0 {
		profile, err = policy.LoadProfile(params.ProfileData)
		if err != nil {
			return nil, fmt.Errorf("loading profile: %w", err)
		}
		log.Record("profile-load", "PASS", fmt.Sprintf("loaded profile: %s", profile.ProfileName))
	} else {
		profile = defaultProfile()
		log.Record("profile-load", "PASS", "using default profile")
	}

	// ── Step 5: Check required panels ───────────────────────────────────
	missing := checkRequiredPanels(emissions, profile.RequiredPanels, log)
	hasMissing := len(missing) > 0

	// ── Step 5b: Apply execution status adjustments ─────────────────────
	emissions = applyExecutionStatusAdjustments(emissions, log)

	// ── Step 6: Compute weighted confidence ─────────────────────────────
	aggregateConfidence := computeWeightedConfidence(emissions, profile, log)
	log.Record("aggregate-confidence", "PASS", fmt.Sprintf("%.4f", aggregateConfidence))

	// ── Step 8: Collect policy flags (needed before risk/block eval) ────
	flags, flagSeverities := collectPolicyFlags(emissions)
	if len(flags) > 0 {
		log.Record("policy-flags", "PASS", fmt.Sprintf("collected %d flags: %s", len(flags), strings.Join(flags, ", ")))
	} else {
		log.Record("policy-flags", "PASS", "no policy flags")
	}

	// Build evaluation context.
	ctx := &condition.EvalContext{
		AggregateConfidence:  aggregateConfidence,
		PolicyFlags:          flags,
		PolicyFlagSeverities: flagSeverities,
		Emissions:            emissions,
		CIPassed:             params.CIPassed,
		MissingRequired:      missing,
	}

	// ── Step 7: Compute aggregate risk ──────────────────────────────────
	aggregateRisk := computeAggregateRisk(emissions, profile, ctx, log)
	ctx.AggregateRisk = aggregateRisk
	log.Record("aggregate-risk", "PASS", aggregateRisk)

	// ── Step 8b: Validate canary results ────────────────────────────────
	canaryViolations := validateCanaryResults(emissions, log)

	// ── Step 9: Evaluate block conditions ───────────────────────────────
	// Decision tree evaluation.
	var decisionAction string
	var decisionRationale string
	var code int

	// Decision: blocked by missing required panels.
	if hasMissing {
		decisionAction = "block"
		decisionRationale = fmt.Sprintf("missing required panels: %s", strings.Join(missing, ", "))
		code = exitcode.Block
		log.Record("decision", "FAIL", decisionRationale)
	}

	// Decision: canary failures.
	if decisionAction == "" && len(canaryViolations) > 0 {
		decisionAction = "block"
		decisionRationale = fmt.Sprintf("canary validation failed: %s", strings.Join(canaryViolations, "; "))
		code = exitcode.Block
		log.Record("decision", "FAIL", decisionRationale)
	}

	// Decision: block conditions.
	if decisionAction == "" {
		blocked, reason := evaluateBlockConditions(emissions, profile, ctx, log)
		if blocked {
			decisionAction = "block"
			decisionRationale = reason
			code = exitcode.Block
			log.Record("decision", "FAIL", fmt.Sprintf("blocked: %s", reason))
		}
	}

	// ── Step 10: Evaluate escalation rules ──────────────────────────────
	if decisionAction == "" {
		action, reason := evaluateEscalationRules(emissions, profile, ctx, log)
		switch action {
		case "block":
			decisionAction = "block"
			decisionRationale = fmt.Sprintf("escalation (block): %s", reason)
			code = exitcode.Block
			log.Record("decision", "FAIL", decisionRationale)
		case "human_review":
			decisionAction = "human_review_required"
			decisionRationale = fmt.Sprintf("escalation (human_review): %s", reason)
			code = exitcode.HumanReviewRequired
			log.Record("decision", "WARN", decisionRationale)
		}
	}

	// ── Step 10b: Evaluate panel execution rules ────────────────────────
	if decisionAction == "" {
		if evaluatePanelExecutionRules(emissions, profile, ctx, log) {
			decisionAction = "human_review_required"
			decisionRationale = "panel execution rules triggered"
			code = exitcode.HumanReviewRequired
			log.Record("decision", "WARN", decisionRationale)
		}
	}

	// ── Step 11: Evaluate auto-merge ────────────────────────────────────
	if decisionAction == "" {
		if evaluateAutoMerge(profile, ctx, log) {
			decisionAction = "auto_merge"
			decisionRationale = "all auto-merge conditions satisfied"
			code = exitcode.AutoMerge
			log.Record("decision", "PASS", decisionRationale)
		}
	}

	// ── Step 12: Evaluate auto-remediate ────────────────────────────────
	if decisionAction == "" {
		if evaluateAutoRemediate(profile, ctx, log) {
			decisionAction = "auto_remediate"
			decisionRationale = "all auto-remediate conditions satisfied"
			code = exitcode.AutoRemediate
			log.Record("decision", "PASS", decisionRationale)
		}
	}

	// ── Step 13: Default → human_review_required ────────────────────────
	if decisionAction == "" {
		decisionAction = "human_review_required"
		decisionRationale = "no auto-merge or auto-remediate conditions matched"
		code = exitcode.HumanReviewRequired
		log.Record("decision", "WARN", decisionRationale)
	}

	// DryRun override.
	if params.DryRun {
		code = 0
		log.Record("dry-run", "PASS", "dry-run mode: exit code forced to 0")
	}

	// ── Generate manifest ───────────────────────────────────────────────
	profileName := profile.ProfileName
	if profileName == "" {
		profileName = "default"
	}

	m := manifest.Generate(manifest.GenerateParams{
		Emissions:           emissions,
		ProfileName:         profileName,
		AggregateConfidence: aggregateConfidence,
		AggregateRisk:       aggregateRisk,
		DecisionAction:      decisionAction,
		DecisionRationale:   decisionRationale,
		EvalLog:             log,
		CommitSHA:           params.CommitSHA,
		PRNumber:            params.PRNumber,
		Repo:                params.Repo,
	})

	return &EvaluateResult{Manifest: m, ExitCode: code}, nil
}

// defaultProfile returns a minimal profile with sensible defaults when no
// profile data is provided.
func defaultProfile() *policy.Profile {
	return &policy.Profile{
		ProfileName: "default",
		Weighting: policy.Weighting{
			MissingPanelBehavior: "redistribute",
		},
		AutoMerge: policy.AutoMerge{
			Operator: "all",
		},
		AutoRemediate: policy.AutoRemediate{
			MaxAttempts: 3,
		},
	}
}
