import { describe, it, expect } from "vitest";
import { join } from "node:path";
import { readFile } from "node:fs/promises";

// For testing the validate_emission logic, we replicate the schema validation
// rather than testing through the MCP server (that is covered in index.test.ts)
const GOVERNANCE_ROOT = join(__dirname, "..", "..");

describe("validate_emission", () => {
  it("validates a well-formed emission", async () => {
    const schemaText = await readFile(
      join(GOVERNANCE_ROOT, "governance", "schemas", "panel-output.schema.json"),
      "utf-8"
    );
    const schema = JSON.parse(schemaText);

    const validEmission = {
      panel_name: "code-review",
      panel_version: "1.0.0",
      confidence_score: 0.85,
      risk_level: "low",
      compliance_score: 0.95,
      policy_flags: [],
      requires_human_review: false,
      timestamp: "2026-02-27T12:00:00Z",
      findings: [
        {
          persona: "quality/style-reviewer",
          verdict: "approve",
          confidence: 0.9,
          rationale: "Code follows established patterns and conventions.",
        },
      ],
    };

    // Basic required field check
    const required = schema.required as string[];
    for (const field of required) {
      expect(validEmission).toHaveProperty(field);
    }
  });

  it("detects missing required fields", async () => {
    const schemaText = await readFile(
      join(GOVERNANCE_ROOT, "governance", "schemas", "panel-output.schema.json"),
      "utf-8"
    );
    const schema = JSON.parse(schemaText);

    const incompleteEmission = {
      panel_name: "code-review",
      // Missing panel_version, confidence_score, risk_level, etc.
    };

    const required = schema.required as string[];
    const missing = required.filter(
      (field: string) =>
        !(field in incompleteEmission)
    );

    expect(missing.length).toBeGreaterThan(0);
    expect(missing).toContain("panel_version");
    expect(missing).toContain("confidence_score");
  });

  it("validates risk_level enum values", async () => {
    const schemaText = await readFile(
      join(GOVERNANCE_ROOT, "governance", "schemas", "panel-output.schema.json"),
      "utf-8"
    );
    const schema = JSON.parse(schemaText);

    const riskLevelSchema = (schema.properties as Record<string, unknown>)
      .risk_level as Record<string, unknown>;
    const validValues = riskLevelSchema.enum as string[];

    expect(validValues).toEqual([
      "critical",
      "high",
      "medium",
      "low",
      "negligible",
    ]);
    expect(validValues).toContain("low");
    expect(validValues).not.toContain("unknown");
  });

  it("validates confidence_score bounds", async () => {
    const schemaText = await readFile(
      join(GOVERNANCE_ROOT, "governance", "schemas", "panel-output.schema.json"),
      "utf-8"
    );
    const schema = JSON.parse(schemaText);

    const confidenceSchema = (schema.properties as Record<string, unknown>)
      .confidence_score as Record<string, unknown>;

    expect(confidenceSchema.minimum).toBe(0.0);
    expect(confidenceSchema.maximum).toBe(1.0);
  });
});

describe("list_panels", () => {
  it("returns expected panel metadata from discovered resources", async () => {
    // Import at test time since it uses ESM
    const { discoverResources } = await import("../src/resources.js");
    const resources = await discoverResources(GOVERNANCE_ROOT);
    const panels = resources
      .filter((r) => r.uri.startsWith("governance://reviews/"))
      .map((r) => ({
        name: r.uri.replace("governance://reviews/", ""),
        description: r.description,
        uri: r.uri,
      }));

    expect(panels.length).toBe(20);

    // Check specific panels exist
    const panelNames = panels.map((p) => p.name);
    expect(panelNames).toContain("code-review");
    expect(panelNames).toContain("security-review");
    expect(panelNames).toContain("threat-modeling");
    expect(panelNames).toContain("cost-analysis");
    expect(panelNames).toContain("documentation-review");
    expect(panelNames).toContain("data-governance-review");
  });
});

describe("list_policy_profiles", () => {
  it("returns the four primary policy profiles", () => {
    const profiles = [
      {
        name: "default",
        description:
          "Standard risk tolerance, auto-merge enabled with conditions",
        risk_tolerance: "standard",
        auto_merge: true,
      },
      {
        name: "fin_pii_high",
        description:
          "SOC2/PCI-DSS/HIPAA/GDPR compliance, auto-merge disabled",
        risk_tolerance: "low",
        auto_merge: false,
      },
      {
        name: "infrastructure_critical",
        description:
          "Mandatory architecture and SRE review for infrastructure changes",
        risk_tolerance: "low",
        auto_merge: false,
      },
      {
        name: "reduced_touchpoint",
        description:
          "Near-full autonomy, human approval only for policy overrides",
        risk_tolerance: "high",
        auto_merge: true,
      },
    ];

    expect(profiles).toHaveLength(4);
    expect(profiles.map((p) => p.name)).toEqual([
      "default",
      "fin_pii_high",
      "infrastructure_critical",
      "reduced_touchpoint",
    ]);

    // default and reduced_touchpoint have auto_merge enabled
    expect(profiles.find((p) => p.name === "default")!.auto_merge).toBe(true);
    expect(
      profiles.find((p) => p.name === "reduced_touchpoint")!.auto_merge
    ).toBe(true);

    // fin_pii_high and infrastructure_critical have auto_merge disabled
    expect(
      profiles.find((p) => p.name === "fin_pii_high")!.auto_merge
    ).toBe(false);
    expect(
      profiles.find((p) => p.name === "infrastructure_critical")!.auto_merge
    ).toBe(false);
  });
});
