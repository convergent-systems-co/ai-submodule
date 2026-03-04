package engine

import (
	"math"

	"github.com/SET-Apps/ai-submodule/src/internal/emission"
	"github.com/SET-Apps/ai-submodule/src/internal/evallog"
	"github.com/SET-Apps/ai-submodule/src/internal/policy"
)

// computeWeightedConfidence computes the aggregate confidence score across
// emissions using the profile's weighting configuration. If no weights are
// defined, a simple average is used.
func computeWeightedConfidence(emissions []*emission.Emission, profile *policy.Profile, log *evallog.Log) float64 {
	if len(emissions) == 0 {
		log.Record("confidence", "SKIP", "no emissions to compute confidence")
		return 0.0
	}

	weights := profile.Weighting.Weights
	if len(weights) == 0 {
		// Simple average when no weights defined.
		var sum float64
		for _, em := range emissions {
			sum += em.ConfidenceScore
		}
		avg := sum / float64(len(emissions))
		avg = math.Round(avg*10000) / 10000
		log.Record("confidence", "PASS", "simple average (no weights defined)")
		return avg
	}

	// Build set of present panel names.
	presentPanels := make(map[string]bool)
	for _, em := range emissions {
		presentPanels[em.PanelName] = true
	}

	// Compute the total weight of missing panels (for redistribution).
	var missingWeight float64
	var presentWeight float64
	for panel, w := range weights {
		if presentPanels[panel] {
			presentWeight += w
		} else {
			missingWeight += w
		}
	}

	// Determine the redistribution factor.
	redistributeFactor := 1.0
	if missingWeight > 0 && presentWeight > 0 && profile.Weighting.MissingPanelBehavior == "redistribute" {
		redistributeFactor = (presentWeight + missingWeight) / presentWeight
		log.Record("confidence-redistribute", "PASS", "redistributing missing panel weight")
	}

	var weightedSum float64
	var totalWeight float64
	for _, em := range emissions {
		w, ok := weights[em.PanelName]
		if !ok {
			// Panel not in weights map; use weight of 1.0.
			w = 1.0
		}
		adjustedWeight := w * redistributeFactor
		weightedSum += em.ConfidenceScore * adjustedWeight
		totalWeight += adjustedWeight
	}

	if totalWeight == 0 {
		log.Record("confidence", "WARN", "total weight is zero")
		return 0.0
	}

	result := weightedSum / totalWeight
	result = math.Round(result*10000) / 10000
	log.Record("confidence", "PASS", "weighted average computed")
	return result
}
