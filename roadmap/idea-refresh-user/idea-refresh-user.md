---
status: todo
priority: medium
owner: ""
---

# Idea: /refresh-user skill

## One-Line Overview
A skill that recompiles `user.md` by reading the raw vault directories (goals, challenges, growth-plan) so the user profile stays current as the person evolves.

## What's the idea

`user.md` is a compiled artifact — a flat, readable summary of who the user is. The source of truth lives in subdirectories: `goals/`, `challenges/`, `growth-plan/`, etc. Over time those directories change but `user.md` goes stale.

This skill reads the raw vault directories and rewrites `user.md` with an up-to-date profile — preserving stable sections (Role, Work Style) and refreshing dynamic ones (2026 Arc, Observation Lens, open challenges, active goals).

Belongs in the `2ndbrain-ai` repo (not here), since it's vault-specific. This entry tracks the idea until that repo exists.

## Expected advantages / benefits

- `user.md` never goes stale — a single command refreshes it
- Skills that read `user.md` (like `bye`) always get current context
- Forces a useful structure: stable vs dynamic sections in the profile
- Low-stakes first skill for the `2ndbrain-ai` repo — validates the "skills read from vault" pattern

## Downsides / risks

- Requires consistent structure in `goals/`, `challenges/`, etc. — if those dirs are messy, output is messy
- Claude rewrites a sensitive file; needs a dry-run or diff preview before committing
- Vault path must be set via `CLAUDE_SKILLS_VAULT` — doesn't work out of the box without config

## What's been tried already

None yet. The `bye` skill already reads `user.md` at runtime as a proof of concept.

## Open questions

1. Should the skill show a diff and ask for confirmation before overwriting `user.md`?
2. Which sections of `user.md` are stable (hand-authored) vs dynamic (derived from subdirs)?
3. Does this live in `2ndbrain-ai` from day one, or start here and migrate?
4. Should it also update the `## Structure` table in `user.md` automatically?
