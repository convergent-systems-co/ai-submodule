# Migration (No AI) — Narration Transcript

This demonstration shows how to add dark factory governance to an existing project that has no prior AI or governance setup.

We start with a typical project — a git repository containing source code, tests, a readme, and a package dot json. No governance, no AI configuration.

Here's the existing project structure. Just standard application files.

Step one: run dark governance install. This caches the governance content from the binary to your local machine. Your existing project files are completely untouched.

Step two: run dark governance init. This scaffolds the governance pipeline into your project — CI workflows, artifact directories, the CLAUDE dot MD file, and a lockfile.

Now let's verify that the original project files were not modified. The readme, source code, and package dot json are all exactly as they were before.

And here are the new governance files. The CI workflow, CLAUDE dot MD, the artifacts directory structure, and the integrity lockfile.

Let's look at the final project structure. Your original files coexist cleanly with the governance scaffolding.

Running dark governance verify confirms the integrity of the installation.

That's it. Governance has been added to an existing project in two commands, with zero impact on your existing code.
