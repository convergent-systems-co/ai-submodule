# Install Test — Narration Transcript

This is a demonstration of the dark governance install command, which extracts embedded governance content to your local cache.

First, we set up an isolated home directory so we don't affect your real configuration.

Now we run dark governance install. This extracts all governance policies, schemas, prompts, and templates from the binary into a versioned cache directory.

Let's verify the installation. The versions directory should exist with the extracted content.

Here we can see the governance files — YAML policies, JSON schemas, and markdown prompts — all extracted and ready to use.

Now we test reinstalling with the force flag. This overwrites the existing cache, useful when upgrading to a new version.

The install command is complete. Your governance content is cached locally and ready for dark governance init.
