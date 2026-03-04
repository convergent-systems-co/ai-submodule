package emission

import (
	"bytes"
	"fmt"
	"strings"

	"github.com/santhosh-tekuri/jsonschema/v6"
)

// ValidateEmission validates raw JSON emission data against the provided
// JSON Schema bytes. Returns nil if valid or if schemaData is empty.
func ValidateEmission(data, schemaData []byte) error {
	if len(schemaData) == 0 {
		return nil
	}

	c := jsonschema.NewCompiler()
	schema, err := jsonschema.UnmarshalJSON(bytes.NewReader(schemaData))
	if err != nil {
		return fmt.Errorf("parsing schema JSON: %w", err)
	}
	if err := c.AddResource("schema.json", schema); err != nil {
		return fmt.Errorf("adding schema resource: %w", err)
	}
	sch, err := c.Compile("schema.json")
	if err != nil {
		return fmt.Errorf("compiling schema: %w", err)
	}

	doc, err := jsonschema.UnmarshalJSON(bytes.NewReader(data))
	if err != nil {
		return fmt.Errorf("parsing emission JSON: %w", err)
	}

	err = sch.Validate(doc)
	if err == nil {
		return nil
	}

	ve, ok := err.(*jsonschema.ValidationError)
	if !ok {
		return err
	}

	errs := collectValidationErrors(ve)
	return fmt.Errorf("schema validation failed:\n  %s", strings.Join(errs, "\n  "))
}

// collectValidationErrors recursively collects error messages from a
// jsonschema.ValidationError tree.
func collectValidationErrors(ve *jsonschema.ValidationError) []string {
	var msgs []string
	if ve.ErrorKind != nil {
		loc := "/" + strings.Join(ve.InstanceLocation, "/")
		msg := fmt.Sprintf("%v", ve.ErrorKind)
		msgs = append(msgs, fmt.Sprintf("%s: %s", loc, msg))
	}
	for _, cause := range ve.Causes {
		msgs = append(msgs, collectValidationErrors(cause)...)
	}
	return msgs
}
