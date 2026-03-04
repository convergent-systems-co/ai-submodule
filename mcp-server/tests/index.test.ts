import { describe, it, expect } from "vitest";
import { join } from "node:path";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerResources } from "../src/resources.js";
import { registerTools } from "../src/tools.js";
import { registerPrompts } from "../src/prompts.js";

const GOVERNANCE_ROOT = join(__dirname, "..", "..");

describe("MCP Server", () => {
  it("creates a server instance", () => {
    const server = new McpServer(
      { name: "test-server", version: "0.1.0" },
      {
        capabilities: {
          resources: {},
          tools: {},
          prompts: {},
        },
      }
    );

    expect(server).toBeDefined();
    expect(server.server).toBeDefined();
  });

  it("registers resources successfully", async () => {
    const server = new McpServer(
      { name: "test-server", version: "0.1.0" },
      {
        capabilities: {
          resources: {},
          tools: {},
          prompts: {},
        },
      }
    );

    const discovered = await registerResources(server, GOVERNANCE_ROOT);

    // 20 reviews + 10 workflows + 5 personas + 1 shared + 4 policies + 1 schema = 41
    expect(discovered.length).toBeGreaterThanOrEqual(40);
  });

  it("registers tools without error", () => {
    const server = new McpServer(
      { name: "test-server", version: "0.1.0" },
      {
        capabilities: {
          resources: {},
          tools: {},
          prompts: {},
        },
      }
    );

    expect(() => registerTools(server, GOVERNANCE_ROOT)).not.toThrow();
  });

  it("registers prompts without error", () => {
    const server = new McpServer(
      { name: "test-server", version: "0.1.0" },
      {
        capabilities: {
          resources: {},
          tools: {},
          prompts: {},
        },
      }
    );

    expect(() => registerPrompts(server, GOVERNANCE_ROOT)).not.toThrow();
  });

  it("registers all components together", async () => {
    const server = new McpServer(
      { name: "test-server", version: "0.1.0" },
      {
        capabilities: {
          resources: {},
          tools: {},
          prompts: {},
        },
      }
    );

    const discovered = await registerResources(server, GOVERNANCE_ROOT);
    registerTools(server, GOVERNANCE_ROOT);
    registerPrompts(server, GOVERNANCE_ROOT);

    // Verify resources were discovered
    expect(discovered.length).toBeGreaterThanOrEqual(40);

    // Verify the server object is still healthy
    expect(server).toBeDefined();
  });
});
