import { describe, it, expect } from "vitest";
import { join } from "node:path";
import { discoverResources } from "../src/resources.js";

// The governance root is two levels up from mcp-server/tests/
const GOVERNANCE_ROOT = join(__dirname, "..", "..");

describe("discoverResources", () => {
  it("discovers review prompt resources", async () => {
    const resources = await discoverResources(GOVERNANCE_ROOT);
    const reviews = resources.filter((r) =>
      r.uri.startsWith("governance://reviews/")
    );

    // There are 20 review prompt files
    expect(reviews.length).toBe(20);
  });

  it("generates correct URIs for review prompts", async () => {
    const resources = await discoverResources(GOVERNANCE_ROOT);
    const codeReview = resources.find(
      (r) => r.uri === "governance://reviews/code-review"
    );

    expect(codeReview).toBeDefined();
    expect(codeReview!.name).toBe("review-code-review");
    expect(codeReview!.mimeType).toBe("text/markdown");
  });

  it("discovers workflow template resources", async () => {
    const resources = await discoverResources(GOVERNANCE_ROOT);
    const workflows = resources.filter((r) =>
      r.uri.startsWith("governance://workflows/")
    );

    // There are 10 workflow template files
    expect(workflows.length).toBe(10);
  });

  it("discovers persona resources", async () => {
    const resources = await discoverResources(GOVERNANCE_ROOT);
    const personas = resources.filter((r) =>
      r.uri.startsWith("governance://personas/")
    );

    // There are 5 persona files
    expect(personas.length).toBe(5);
  });

  it("discovers shared perspectives resource", async () => {
    const resources = await discoverResources(GOVERNANCE_ROOT);
    const shared = resources.find(
      (r) => r.uri === "governance://shared/perspectives"
    );

    expect(shared).toBeDefined();
    expect(shared!.name).toBe("shared-perspectives");
  });

  it("discovers policy profile resources", async () => {
    const resources = await discoverResources(GOVERNANCE_ROOT);
    const policies = resources.filter((r) =>
      r.uri.startsWith("governance://policy/")
    );

    // 4 primary policy profiles
    expect(policies.length).toBe(4);
    expect(
      policies.map((p) => p.uri).sort()
    ).toEqual([
      "governance://policy/default",
      "governance://policy/fin_pii_high",
      "governance://policy/infrastructure_critical",
      "governance://policy/reduced_touchpoint",
    ]);
  });

  it("discovers panel output schema resource", async () => {
    const resources = await discoverResources(GOVERNANCE_ROOT);
    const schema = resources.find(
      (r) => r.uri === "governance://schemas/panel-output"
    );

    expect(schema).toBeDefined();
    expect(schema!.mimeType).toBe("application/json");
  });

  it("extracts titles from review prompts", async () => {
    const resources = await discoverResources(GOVERNANCE_ROOT);
    const securityReview = resources.find(
      (r) => r.uri === "governance://reviews/security-review"
    );

    expect(securityReview).toBeDefined();
    // The title should be extracted from the first heading
    expect(securityReview!.description).toBeTruthy();
    expect(securityReview!.description.length).toBeGreaterThan(0);
  });

  it("returns resources sorted by URI within categories", async () => {
    const resources = await discoverResources(GOVERNANCE_ROOT);
    const reviews = resources.filter((r) =>
      r.uri.startsWith("governance://reviews/")
    );

    // Since scanMarkdownFiles sorts, URIs should be in order
    const uris = reviews.map((r) => r.uri);
    const sorted = [...uris].sort();
    expect(uris).toEqual(sorted);
  });
});
