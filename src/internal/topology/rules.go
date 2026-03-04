package topology

import (
	"encoding/json"
	"os"
)

// TopologyRules defines the constraints loaded from project.yaml config.
type TopologyRules struct {
	PMEnabled         bool                `json:"pm_mode_enabled"`
	ParallelTeamLeads int                 `json:"parallel_team_leads"`
	ParallelCoders    int                 `json:"parallel_coders"`
	RequiredPersonas  []string            `json:"required_personas"`
	Constraints       TopologyConstraints `json:"constraints"`
}

// TopologyConstraints defines the individual topology constraint switches.
type TopologyConstraints struct {
	EveryTechLeadMustHaveCoders bool `json:"every_techLead_must_have_coders"`
	EveryCoderMustHaveParent    bool `json:"every_coder_must_have_parent"`
	DevOpsRequiredInPMMode      bool `json:"devops_required_in_pm_mode"`
}

// DefaultRules returns the default topology rules.
func DefaultRules() *TopologyRules {
	return &TopologyRules{
		PMEnabled:         false,
		ParallelTeamLeads: 1,
		ParallelCoders:    5,
		RequiredPersonas:  []string{"PM", "TechLead", "Coder", "DevOps"},
		Constraints: TopologyConstraints{
			EveryTechLeadMustHaveCoders: true,
			EveryCoderMustHaveParent:    true,
			DevOpsRequiredInPMMode:      true,
		},
	}
}

// LoadRules loads topology rules from a JSON file.
// Returns DefaultRules if the file does not exist.
func LoadRules(path string) (*TopologyRules, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return DefaultRules(), nil
		}
		return nil, err
	}

	var rules TopologyRules
	if err := json.Unmarshal(data, &rules); err != nil {
		return nil, err
	}

	return &rules, nil
}

// SaveRules writes topology rules to a JSON file.
func SaveRules(path string, rules *TopologyRules) error {
	data, err := json.MarshalIndent(rules, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(data, '\n'), 0644)
}
