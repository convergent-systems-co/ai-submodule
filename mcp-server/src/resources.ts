import { join, basename, relative } from "node:path";
import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import {
  scanMarkdownFiles,
  scanYamlFiles,
  readTextFile,
  extractTitle,
  pathToSlug,
} from "./utils.js";

export interface DiscoveredResource {
  name: string;
  uri: string;
  description: string;
  mimeType: string;
  filePath: string;
}

/**
 * Discover all servable governance resources from the filesystem.
 */
export async function discoverResources(
  governanceRoot: string
): Promise<DiscoveredResource[]> {
  const resources: DiscoveredResource[] = [];

  // Review prompts: governance/prompts/reviews/*.md
  const reviewsDir = join(governanceRoot, "governance", "prompts", "reviews");
  const reviewFiles = await scanMarkdownFiles(reviewsDir);
  for (const filePath of reviewFiles) {
    const slug = pathToSlug(basename(filePath));
    const content = await readTextFile(filePath);
    const title = extractTitle(content, basename(filePath));
    resources.push({
      name: `review-${slug}`,
      uri: `governance://reviews/${slug}`,
      description: title,
      mimeType: "text/markdown",
      filePath,
    });
  }

  // Workflow templates: governance/prompts/workflows/*.md
  const workflowsDir = join(governanceRoot, "governance", "prompts", "workflows");
  const workflowFiles = await scanMarkdownFiles(workflowsDir);
  for (const filePath of workflowFiles) {
    const slug = pathToSlug(basename(filePath));
    const content = await readTextFile(filePath);
    const title = extractTitle(content, basename(filePath));
    resources.push({
      name: `workflow-${slug}`,
      uri: `governance://workflows/${slug}`,
      description: title,
      mimeType: "text/markdown",
      filePath,
    });
  }

  // Personas: governance/personas/agentic/*.md
  const personasDir = join(governanceRoot, "governance", "personas", "agentic");
  const personaFiles = await scanMarkdownFiles(personasDir);
  for (const filePath of personaFiles) {
    const slug = pathToSlug(basename(filePath));
    const content = await readTextFile(filePath);
    const title = extractTitle(content, basename(filePath));
    resources.push({
      name: `persona-${slug}`,
      uri: `governance://personas/${slug}`,
      description: title,
      mimeType: "text/markdown",
      filePath,
    });
  }

  // Shared perspectives
  const sharedPath = join(
    governanceRoot,
    "governance",
    "prompts",
    "shared-perspectives.md"
  );
  try {
    const content = await readTextFile(sharedPath);
    const title = extractTitle(content, "shared-perspectives.md");
    resources.push({
      name: "shared-perspectives",
      uri: "governance://shared/perspectives",
      description: title,
      mimeType: "text/markdown",
      filePath: sharedPath,
    });
  } catch {
    // File may not exist
  }

  // Policy profiles: governance/policy/{default,fin_pii_high,infrastructure_critical,reduced_touchpoint}.yaml
  const primaryPolicies = [
    "default.yaml",
    "fin_pii_high.yaml",
    "infrastructure_critical.yaml",
    "reduced_touchpoint.yaml",
  ];
  const policyDir = join(governanceRoot, "governance", "policy");
  for (const policyFile of primaryPolicies) {
    const filePath = join(policyDir, policyFile);
    try {
      await readTextFile(filePath); // Verify it exists
      const slug = pathToSlug(policyFile);
      resources.push({
        name: `policy-${slug}`,
        uri: `governance://policy/${slug}`,
        description: `Policy profile: ${slug.replace(/_/g, " ")}`,
        mimeType: "text/yaml",
        filePath,
      });
    } catch {
      // Policy file may not exist
    }
  }

  // Developer prompts: prompts/global/*.prompt.md
  const devPromptsDir = join(governanceRoot, "prompts", "global");
  const devPromptFiles = await scanMarkdownFiles(devPromptsDir);
  for (const filePath of devPromptFiles) {
    const slug = pathToSlug(basename(filePath));
    const content = await readTextFile(filePath);
    const title = extractTitle(content, basename(filePath));
    resources.push({
      name: `prompt-${slug}`,
      uri: `governance://prompts/${slug}`,
      description: title,
      mimeType: "text/markdown",
      filePath,
    });
  }

  // Panel output schema
  const schemaPath = join(
    governanceRoot,
    "governance",
    "schemas",
    "panel-output.schema.json"
  );
  try {
    await readTextFile(schemaPath);
    resources.push({
      name: "schema-panel-output",
      uri: "governance://schemas/panel-output",
      description: "Panel structured output JSON schema",
      mimeType: "application/json",
      filePath: schemaPath,
    });
  } catch {
    // Schema may not exist
  }

  return resources;
}

/**
 * Register all discovered resources with the MCP server.
 */
export async function registerResources(
  server: McpServer,
  governanceRoot: string
): Promise<DiscoveredResource[]> {
  const discovered = await discoverResources(governanceRoot);

  for (const resource of discovered) {
    const filePath = resource.filePath;
    server.resource(
      resource.name,
      resource.uri,
      { description: resource.description, mimeType: resource.mimeType },
      async () => ({
        contents: [
          {
            uri: resource.uri,
            mimeType: resource.mimeType,
            text: await readTextFile(filePath),
          },
        ],
      })
    );
  }

  return discovered;
}
