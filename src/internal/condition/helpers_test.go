package condition

import (
	"reflect"
	"testing"
)

// --- ExtractList ---

func TestExtractList(t *testing.T) {
	cases := []struct {
		name  string
		input string
		want  []string
	}{
		{
			name:  "standard list",
			input: `["approve", "abstain"]`,
			want:  []string{"approve", "abstain"},
		},
		{
			name:  "single item",
			input: `["critical"]`,
			want:  []string{"critical"},
		},
		{
			name:  "embedded in condition",
			input: `all_panel_verdicts in ["approve", "abstain"]`,
			want:  []string{"approve", "abstain"},
		},
		{
			name:  "no quotes",
			input: `no quoted strings here`,
			want:  nil,
		},
		{
			name:  "empty list",
			input: `[]`,
			want:  nil,
		},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := ExtractList(tc.input)
			if !reflect.DeepEqual(got, tc.want) {
				t.Errorf("ExtractList(%q) = %v, want %v", tc.input, got, tc.want)
			}
		})
	}
}

// --- ExtractComparison ---

func TestExtractComparison(t *testing.T) {
	cases := []struct {
		name      string
		input     string
		wantOp    string
		wantVal   float64
		wantOK    bool
	}{
		{
			name:    "greater than or equal",
			input:   "aggregate_confidence >= 0.85",
			wantOp:  ">=",
			wantVal: 0.85,
			wantOK:  true,
		},
		{
			name:    "less than",
			input:   "missing_required_panels < 3",
			wantOp:  "<",
			wantVal: 3,
			wantOK:  true,
		},
		{
			name:    "equals integer",
			input:   "fallback_count == 0",
			wantOp:  "==",
			wantVal: 0,
			wantOK:  true,
		},
		{
			name:   "no comparison",
			input:  "some random string",
			wantOK: false,
		},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			op, val, ok := ExtractComparison(tc.input)
			if ok != tc.wantOK {
				t.Fatalf("ExtractComparison(%q): ok=%v, want %v", tc.input, ok, tc.wantOK)
			}
			if !ok {
				return
			}
			if op != tc.wantOp {
				t.Errorf("op = %q, want %q", op, tc.wantOp)
			}
			if val != tc.wantVal {
				t.Errorf("val = %f, want %f", val, tc.wantVal)
			}
		})
	}
}

// --- Compare ---

func TestCompare(t *testing.T) {
	cases := []struct {
		a    float64
		op   string
		b    float64
		want bool
	}{
		{5, ">=", 5, true},
		{5, ">=", 4, true},
		{5, ">=", 6, false},
		{5, "<=", 5, true},
		{5, "<=", 6, true},
		{5, "<=", 4, false},
		{5, ">", 4, true},
		{5, ">", 5, false},
		{5, "<", 6, true},
		{5, "<", 5, false},
		{5, "==", 5, true},
		{5, "==", 6, false},
		{5, "!=", 6, true},
		{5, "!=", 5, false},
		{5, "??", 5, false}, // unknown op
	}
	for _, tc := range cases {
		t.Run(tc.op, func(t *testing.T) {
			got := Compare(tc.a, tc.op, tc.b)
			if got != tc.want {
				t.Errorf("Compare(%f, %q, %f) = %v, want %v", tc.a, tc.op, tc.b, got, tc.want)
			}
		})
	}
}

// --- Slugify ---

func TestSlugify(t *testing.T) {
	cases := []struct {
		input string
		want  string
	}{
		{"aggregate_confidence >= 0.85", "aggregateconfidence-085"},
		{"any_policy_flag == \"pii_exposure\"", "anypolicyflag-piiexposure"},
		{"Hello World!", "hello-world"},
		{"  spaces  and   more  ", "spaces-and-more"},
		{"UPPER_CASE", "uppercase"},
	}
	for _, tc := range cases {
		t.Run(tc.input, func(t *testing.T) {
			got := Slugify(tc.input)
			if got != tc.want {
				t.Errorf("Slugify(%q) = %q, want %q", tc.input, got, tc.want)
			}
		})
	}
}
