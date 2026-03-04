package condition

import (
	"regexp"
	"strconv"
	"strings"
)

var (
	listRe       = regexp.MustCompile(`"([^"]*)"`)
	comparisonRe = regexp.MustCompile(`(>=|<=|>|<|==|!=)\s*([0-9]+(?:\.[0-9]+)?)`)
	slugRe       = regexp.MustCompile(`[^a-z0-9-]+`)
)

// ExtractList extracts quoted strings from a bracketed list like ["a", "b"].
func ExtractList(s string) []string {
	matches := listRe.FindAllStringSubmatch(s, -1)
	var result []string
	for _, m := range matches {
		if len(m) >= 2 {
			result = append(result, m[1])
		}
	}
	return result
}

// ExtractComparison parses a comparison expression like ">= 0.85" and returns
// the operator, threshold value, and whether parsing succeeded.
func ExtractComparison(s string) (op string, threshold float64, ok bool) {
	m := comparisonRe.FindStringSubmatch(s)
	if len(m) < 3 {
		return "", 0, false
	}
	val, err := strconv.ParseFloat(m[2], 64)
	if err != nil {
		return "", 0, false
	}
	return m[1], val, true
}

// Compare performs a numeric comparison: a op b.
func Compare(a float64, op string, b float64) bool {
	switch op {
	case ">=":
		return a >= b
	case "<=":
		return a <= b
	case ">":
		return a > b
	case "<":
		return a < b
	case "==":
		return a == b
	case "!=":
		return a != b
	default:
		return false
	}
}

// Slugify converts a condition string to a rule ID: lowercase, spaces to
// hyphens, special characters removed.
func Slugify(s string) string {
	s = strings.ToLower(s)
	s = strings.ReplaceAll(s, " ", "-")
	s = slugRe.ReplaceAllString(s, "")
	// Collapse multiple hyphens.
	for strings.Contains(s, "--") {
		s = strings.ReplaceAll(s, "--", "-")
	}
	s = strings.Trim(s, "-")
	return s
}
