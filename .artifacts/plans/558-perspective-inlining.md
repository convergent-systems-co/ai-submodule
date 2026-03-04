# Plan: Complete perspective inlining in all review prompts (#558)

## Objective

Inline all referenced perspectives from `shared-perspectives.md` into each review prompt, so models have full evaluation criteria at runtime.

## Scope

All review prompts in `governance/prompts/reviews/` that reference `shared-perspectives.md`.

## Approach

1. Parse shared-perspectives.md to extract each perspective's full definition
2. For each review prompt, find perspective references and replace with inlined definitions
3. Convert reference links to authoring-time comments
4. Verify no dangling references remain
