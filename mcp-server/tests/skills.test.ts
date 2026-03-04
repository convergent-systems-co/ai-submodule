import { describe, it, expect, beforeAll } from "vitest";
import { join } from "node:path";
import { mkdtemp, writeFile, rm, mkdir } from "node:fs/promises";
import { tmpdir } from "node:os";

const MCP_SERVER_ROOT = join(__dirname, "..");

describe("SkillMetadataSchema", () => {
  let SkillMetadataSchema: typeof import("../src/skills.js").SkillMetadataSchema;

  beforeAll(async () => {
    const mod = await import("../src/skills.js");
    SkillMetadataSchema = mod.SkillMetadataSchema;
  });

  it("accepts valid frontmatter", () => {
    const data = {
      name: "governance-review",
      description: "Run a governance panel review",
      "allowed-tools": ["Read", "Glob"],
    };
    const result = SkillMetadataSchema.safeParse(data);
    expect(result.success).toBe(true);
  });

  it("rejects name with uppercase", () => {
    const data = {
      name: "Governance-Review",
      description: "Invalid name",
    };
    const result = SkillMetadataSchema.safeParse(data);
    expect(result.success).toBe(false);
  });

  it("rejects name starting with number", () => {
    const data = {
      name: "1-bad-name",
      description: "Invalid name",
    };
    const result = SkillMetadataSchema.safeParse(data);
    expect(result.success).toBe(false);
  });

  it("rejects name longer than 64 characters", () => {
    const data = {
      name: "a".repeat(65),
      description: "Too long",
    };
    const result = SkillMetadataSchema.safeParse(data);
    expect(result.success).toBe(false);
  });

  it("rejects missing description", () => {
    const data = {
      name: "test-skill",
    };
    const result = SkillMetadataSchema.safeParse(data);
    expect(result.success).toBe(false);
  });

  it("accepts optional fields", () => {
    const data = {
      name: "full-skill",
      description: "A fully specified skill",
      license: "MIT",
      "allowed-tools": ["Read", "Bash"],
      metadata: { author: "test", version: "1.0" },
    };
    const result = SkillMetadataSchema.safeParse(data);
    expect(result.success).toBe(true);
  });
});

describe("loadSkill", () => {
  let loadSkill: typeof import("../src/skills.js").loadSkill;

  beforeAll(async () => {
    const mod = await import("../src/skills.js");
    loadSkill = mod.loadSkill;
  });

  it("loads the bundled governance-review skill", async () => {
    const skillPath = join(MCP_SERVER_ROOT, "skills", "governance-review.skill.md");
    const skill = await loadSkill(skillPath);

    expect(skill.metadata.name).toBe("governance-review");
    expect(skill.metadata.description).toContain("governance panel review");
    expect(skill.metadata["allowed-tools"]).toEqual(["Read", "Glob", "Grep", "Bash"]);
    expect(skill.toolName).toBe("skill_governance_review");
    expect(skill.instructions).toContain("Governance Review Skill");
    expect(skill.path).toBe(skillPath);
  });

  it("converts hyphens to underscores in tool name", async () => {
    const skillPath = join(MCP_SERVER_ROOT, "skills", "governance-review.skill.md");
    const skill = await loadSkill(skillPath);
    expect(skill.toolName).toBe("skill_governance_review");
    expect(skill.toolName).not.toContain("-");
  });

  it("rejects a file with invalid frontmatter", async () => {
    const tmpDir = await mkdtemp(join(tmpdir(), "skill-test-"));
    const badSkillPath = join(tmpDir, "bad.skill.md");
    await writeFile(
      badSkillPath,
      `---
name: INVALID_NAME
description: Bad skill
---

# Bad Skill
`,
      "utf-8"
    );

    await expect(loadSkill(badSkillPath)).rejects.toThrow();
    await rm(tmpDir, { recursive: true });
  });

  it("rejects a file with missing required fields", async () => {
    const tmpDir = await mkdtemp(join(tmpdir(), "skill-test-"));
    const badSkillPath = join(tmpDir, "incomplete.skill.md");
    await writeFile(
      badSkillPath,
      `---
name: incomplete
---

# Incomplete
`,
      "utf-8"
    );

    await expect(loadSkill(badSkillPath)).rejects.toThrow();
    await rm(tmpDir, { recursive: true });
  });
});

describe("discoverSkills", () => {
  let discoverSkills: typeof import("../src/skills.js").discoverSkills;

  beforeAll(async () => {
    const mod = await import("../src/skills.js");
    discoverSkills = mod.discoverSkills;
  });

  it("discovers skills from the bundled skills directory", async () => {
    const skillsDir = join(MCP_SERVER_ROOT, "skills");
    const skills = await discoverSkills(skillsDir);

    expect(skills.length).toBeGreaterThanOrEqual(1);
    const names = skills.map((s) => s.metadata.name);
    expect(names).toContain("governance-review");
  });

  it("returns empty array for non-existent directory", async () => {
    const skills = await discoverSkills("/nonexistent/path");
    expect(skills).toEqual([]);
  });

  it("skips non-.skill.md files", async () => {
    const tmpDir = await mkdtemp(join(tmpdir(), "skill-test-"));

    // Create a valid skill file
    await writeFile(
      join(tmpDir, "valid.skill.md"),
      `---
name: valid-skill
description: A valid skill
---

# Valid
`,
      "utf-8"
    );

    // Create a regular .md file (should be skipped)
    await writeFile(join(tmpDir, "readme.md"), "# Not a skill", "utf-8");

    // Create a .txt file (should be skipped)
    await writeFile(join(tmpDir, "notes.txt"), "Not a skill", "utf-8");

    const skills = await discoverSkills(tmpDir);
    expect(skills).toHaveLength(1);
    expect(skills[0].metadata.name).toBe("valid-skill");

    await rm(tmpDir, { recursive: true });
  });

  it("skips invalid skill files with a warning", async () => {
    const tmpDir = await mkdtemp(join(tmpdir(), "skill-test-"));

    // Create a valid skill file
    await writeFile(
      join(tmpDir, "good.skill.md"),
      `---
name: good-skill
description: A good skill
---

# Good
`,
      "utf-8"
    );

    // Create an invalid skill file
    await writeFile(
      join(tmpDir, "bad.skill.md"),
      `---
name: BAD_SKILL
---

# Bad
`,
      "utf-8"
    );

    const skills = await discoverSkills(tmpDir);
    expect(skills).toHaveLength(1);
    expect(skills[0].metadata.name).toBe("good-skill");

    await rm(tmpDir, { recursive: true });
  });

  it("returns skills sorted by name", async () => {
    const tmpDir = await mkdtemp(join(tmpdir(), "skill-test-"));

    await writeFile(
      join(tmpDir, "zebra.skill.md"),
      `---
name: zebra-skill
description: Zebra skill
---

# Zebra
`,
      "utf-8"
    );

    await writeFile(
      join(tmpDir, "alpha.skill.md"),
      `---
name: alpha-skill
description: Alpha skill
---

# Alpha
`,
      "utf-8"
    );

    const skills = await discoverSkills(tmpDir);
    expect(skills).toHaveLength(2);
    expect(skills[0].metadata.name).toBe("alpha-skill");
    expect(skills[1].metadata.name).toBe("zebra-skill");

    await rm(tmpDir, { recursive: true });
  });
});

describe("generateToolDefinition", () => {
  let generateToolDefinition: typeof import("../src/skills.js").generateToolDefinition;
  let loadSkill: typeof import("../src/skills.js").loadSkill;

  beforeAll(async () => {
    const mod = await import("../src/skills.js");
    generateToolDefinition = mod.generateToolDefinition;
    loadSkill = mod.loadSkill;
  });

  it("generates correct tool definition from a skill", async () => {
    const skillPath = join(MCP_SERVER_ROOT, "skills", "governance-review.skill.md");
    const skill = await loadSkill(skillPath);
    const def = generateToolDefinition(skill);

    expect(def.name).toBe("skill_governance_review");
    expect(def.description).toContain("governance panel review");
    expect(def.description).toContain("Allowed tools: Read, Glob, Grep, Bash");
    expect(def.inputSchema).toHaveProperty("task");
    expect(def.inputSchema).toHaveProperty("context");
    expect(def.inputSchema).toHaveProperty("output_format");
  });
});

describe("handleSkillToolCall", () => {
  let handleSkillToolCall: typeof import("../src/skills.js").handleSkillToolCall;
  let loadSkill: typeof import("../src/skills.js").loadSkill;

  beforeAll(async () => {
    const mod = await import("../src/skills.js");
    handleSkillToolCall = mod.handleSkillToolCall;
    loadSkill = mod.loadSkill;
  });

  it("produces output with skill instructions and task", async () => {
    const skillPath = join(MCP_SERVER_ROOT, "skills", "governance-review.skill.md");
    const skill = await loadSkill(skillPath);

    const output = handleSkillToolCall(skill, {
      task: "Review the changes in PR #42",
    });

    expect(output).toContain("# Skill Instructions");
    expect(output).toContain("Governance Review Skill");
    expect(output).toContain("# Task");
    expect(output).toContain("Review the changes in PR #42");
    // Should not contain context or format sections added by handleSkillToolCall
    expect(output).not.toContain("# Additional Context");
    expect(output).not.toContain("Provide output as:");
  });

  it("includes context when provided", async () => {
    const skillPath = join(MCP_SERVER_ROOT, "skills", "governance-review.skill.md");
    const skill = await loadSkill(skillPath);

    const output = handleSkillToolCall(skill, {
      task: "Review changes",
      context: "This is a security-sensitive module",
    });

    expect(output).toContain("# Additional Context");
    expect(output).toContain("security-sensitive module");
  });

  it("includes output format when provided", async () => {
    const skillPath = join(MCP_SERVER_ROOT, "skills", "governance-review.skill.md");
    const skill = await loadSkill(skillPath);

    const output = handleSkillToolCall(skill, {
      task: "Review changes",
      output_format: "code",
    });

    expect(output).toContain("# Output Format");
    expect(output).toContain("Provide output as: code");
  });

  it("includes all sections when all args provided", async () => {
    const skillPath = join(MCP_SERVER_ROOT, "skills", "governance-review.skill.md");
    const skill = await loadSkill(skillPath);

    const output = handleSkillToolCall(skill, {
      task: "Full review",
      context: "New feature addition",
      output_format: "both",
    });

    expect(output).toContain("# Skill Instructions");
    expect(output).toContain("# Task");
    expect(output).toContain("# Additional Context");
    expect(output).toContain("# Output Format");
    expect(output).toContain("Provide output as: both");
  });
});
