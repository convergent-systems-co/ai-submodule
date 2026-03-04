# Plan: Add data classification and PII redaction to panel emissions (#610)

## Scope

1. `governance/schemas/panel-output.schema.json`: Make `data_classification` required, add `redaction_rules` field
2. `governance/prompts/reviews/`: Add data classification and redaction section to all 21 review prompts
3. Update baseline emissions if needed

## Approach

1. Make `data_classification` required in schema
2. Add `redaction_rules` sub-object with patterns
3. Add a standard redaction section to all review prompts
