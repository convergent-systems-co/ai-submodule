package emission

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/SET-Apps/ai-submodule/src/internal/evallog"
)

// LoadResult holds the result of loading emissions from a directory.
type LoadResult struct {
	Emissions    []*Emission
	AllValid     bool
	FailedPanels []string
	Log          *evallog.Log
}

// LoadEmissions reads all *.json files from dir, optionally validates each
// against the provided JSON Schema bytes, and unmarshals them into Emission
// structs. If schemaData is nil or empty, schema validation is skipped.
func LoadEmissions(dir string, schemaData []byte, log *evallog.Log) (*LoadResult, error) {
	result := &LoadResult{
		AllValid: true,
		Log:      log,
	}

	matches, err := filepath.Glob(filepath.Join(dir, "*.json"))
	if err != nil {
		return nil, fmt.Errorf("globbing emission files: %w", err)
	}

	if len(matches) == 0 {
		log.Record("emission-load", "WARN", fmt.Sprintf("no JSON files found in %s", dir))
		return result, nil
	}

	for _, path := range matches {
		data, err := os.ReadFile(path)
		if err != nil {
			log.Record("emission-load", "FAIL", fmt.Sprintf("read error: %s: %v", filepath.Base(path), err))
			result.AllValid = false
			result.FailedPanels = append(result.FailedPanels, filepath.Base(path))
			continue
		}

		// Optional schema validation.
		if len(schemaData) > 0 {
			if err := ValidateEmission(data, schemaData); err != nil {
				log.Record("schema-validation", "FAIL", fmt.Sprintf("%s: %v", filepath.Base(path), err))
				result.AllValid = false
				result.FailedPanels = append(result.FailedPanels, filepath.Base(path))
				continue
			}
			log.Record("schema-validation", "PASS", filepath.Base(path))
		}

		var em Emission
		if err := json.Unmarshal(data, &em); err != nil {
			log.Record("json-unmarshal", "FAIL", fmt.Sprintf("%s: %v", filepath.Base(path), err))
			result.AllValid = false
			result.FailedPanels = append(result.FailedPanels, filepath.Base(path))
			continue
		}

		em.SourcePath = path

		// Use filename (without extension) as panel name fallback.
		if em.PanelName == "" {
			base := filepath.Base(path)
			em.PanelName = strings.TrimSuffix(base, filepath.Ext(base))
		}

		result.Emissions = append(result.Emissions, &em)
		log.Record("emission-load", "PASS", fmt.Sprintf("loaded %s (confidence=%.2f, risk=%s)", em.PanelName, em.ConfidenceScore, em.RiskLevel))
	}

	return result, nil
}
