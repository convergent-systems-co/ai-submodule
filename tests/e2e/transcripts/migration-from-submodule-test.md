# Migration (From Submodule) — Narration Transcript

This demonstration shows how to install the dark governance binary alongside a project that already uses the dot AI submodule.

We start with a project that has the dot AI directory as a git submodule — containing governance policies, prompts, schemas, and the shell bootstrap script. This is the legacy distribution model.

Here's the existing submodule structure with its policy files and project configuration.

Step one: run dark governance install. The binary extracts its embedded governance content to a local cache. The existing dot AI submodule directory is not modified.

Step two: run dark governance init. This scaffolds the binary-based governance pipeline. The init command is designed to coexist with the submodule — it adds CI workflows and artifact directories without conflicting.

Let's verify the submodule is untouched. The policy file and project dot YAML are exactly as they were. The binary does not overwrite or remove submodule content.

And here are the new binary-managed files — the CI workflow, CLAUDE dot MD, and the integrity lockfile. These complement the submodule rather than replacing it.

We can check the binary version to confirm which release is installed.

Running dark governance verify confirms the binary installation integrity.

The binary and submodule coexist cleanly. When you're ready to fully migrate, simply remove the dot AI submodule — the binary provides everything it contained.
