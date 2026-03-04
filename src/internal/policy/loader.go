package policy

import (
	"fmt"

	"gopkg.in/yaml.v3"
)

// LoadProfile unmarshals YAML data into a Profile, parsing the raw map and
// applying defaults.
func LoadProfile(data []byte) (*Profile, error) {
	var p Profile
	if err := yaml.Unmarshal(data, &p); err != nil {
		return nil, fmt.Errorf("unmarshaling profile: %w", err)
	}

	// Also parse into raw map for dynamic access.
	var raw map[string]interface{}
	if err := yaml.Unmarshal(data, &raw); err != nil {
		return nil, fmt.Errorf("unmarshaling raw profile: %w", err)
	}
	p.Raw = raw

	// Apply defaults.
	if p.Weighting.MissingPanelBehavior == "" {
		p.Weighting.MissingPanelBehavior = "redistribute"
	}
	if p.AutoMerge.Operator == "" {
		p.AutoMerge.Operator = "all"
	}
	if p.AutoRemediate.MaxAttempts == 0 {
		p.AutoRemediate.MaxAttempts = 3
	}

	return &p, nil
}

// LoadProfileFromEmbed loads a profile by name using the provided read function.
// The readFn should return the file bytes for the given name.
func LoadProfileFromEmbed(name string, readFn func(string) ([]byte, error)) (*Profile, error) {
	data, err := readFn(name)
	if err != nil {
		return nil, fmt.Errorf("reading profile %q: %w", name, err)
	}
	return LoadProfile(data)
}

// GetRequiredPanelsForChangeType returns the required panels for a specific
// change type, falling back to the profile's default RequiredPanels.
// security-review is always included.
func GetRequiredPanelsForChangeType(p *Profile, changeType string) []string {
	var panels []string

	if override, ok := p.PanelOverridesByChangeType[changeType]; ok {
		panels = make([]string, len(override.RequiredPanels))
		copy(panels, override.RequiredPanels)
	} else {
		panels = make([]string, len(p.RequiredPanels))
		copy(panels, p.RequiredPanels)
	}

	// Ensure security-review is always included.
	hasSecurityReview := false
	for _, pn := range panels {
		if pn == "security-review" {
			hasSecurityReview = true
			break
		}
	}
	if !hasSecurityReview {
		panels = append(panels, "security-review")
	}

	return panels
}

// LoadPanelTimeoutConfig unmarshals YAML data into a PanelTimeoutConfig and
// applies defaults.
func LoadPanelTimeoutConfig(data []byte) (*PanelTimeoutConfig, error) {
	var cfg PanelTimeoutConfig
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("unmarshaling panel timeout config: %w", err)
	}

	// Apply defaults.
	if cfg.DefaultTimeoutMinutes == 0 {
		cfg.DefaultTimeoutMinutes = 5
	}
	if cfg.MaxRetries == 0 {
		cfg.MaxRetries = 1
	}
	if cfg.FallbackStrategy == "" {
		cfg.FallbackStrategy = "baseline"
	}
	if cfg.FallbackConfidenceCap == 0 {
		cfg.FallbackConfidenceCap = 0.50
	}
	if cfg.MaxFallbacksPerPR == 0 {
		cfg.MaxFallbacksPerPR = 2
	}

	return &cfg, nil
}
