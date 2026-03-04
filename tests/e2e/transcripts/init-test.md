# Init Test — Narration Transcript

This demonstration shows how dark governance init scaffolds a complete governance pipeline into a new repository.

We start by creating a fresh git repository to simulate a new consumer project.

First, we run init with the dry run flag. This previews what files will be created without actually writing anything. Useful for understanding the impact before committing.

Now we run init for real with JSON output. The command creates CI workflows, a CLAUDE dot MD file, artifact directories, and a lockfile.

Let's verify each scaffolded component. The CI workflow enables automated governance checks on every pull request. CLAUDE dot MD provides AI assistant instructions. The artifacts directories store plans, panels, checkpoints, and emissions.

The lockfile records the exact version and content hashes, enabling integrity verification later.

Now we run dark governance verify to confirm everything was scaffolded correctly and the lockfile matches.

Finally, we test idempotency by running init again. It should detect existing files and skip them, ensuring init is safe to re-run.

Init is complete. The repository now has a full governance pipeline ready for autonomous delivery.
