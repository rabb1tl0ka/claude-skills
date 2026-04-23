# Claude Skills

A collection of custom skills for [Claude Code](https://claude.ai/claude-code).

## What are Skills?

Skills are markdown files that extend Claude Code's capabilities. Each skill defines a set of instructions and workflows that Claude follows when the skill is invoked.

## Installation

1. Copy the skill folder to your Claude Code skills directory:
   ```bash
   # For global skills (available in all projects)
   cp -r <skill-name> ~/.claude/skills/
   ```

2. Follow any skill-specific setup instructions in the skill's section below.

3. Use the skill by typing `/<skill-name>` in Claude Code, or just ask naturally—Claude will auto-invoke the skill when relevant.

---

## Available Skills

### `/recap`

Summarizes your Claude Code sessions from the last 24h (or since the last saved timestamp) and writes a structured session log to your vault.

**Features:**
- Extracts sessions across all projects from `~/.claude/projects/`
- Tracks a high-water mark so re-runs only cover new sessions
- Writes a structured daily note: achievements, projects, learnings, open threads, and Claude's observations
- Appends to an existing note if one already exists for the day
- Vault path configurable via `$CLAUDE_SKILLS_VAULT` (default: `~/2ndbrain`)

**Setup:**

1. Copy the skill to your Claude Code skills directory:
   ```bash
   cp -r recap ~/.claude/skills/
   ```

2. Optionally set `CLAUDE_SKILLS_VAULT` in your shell profile to point to your vault:
   ```bash
   export CLAUDE_SKILLS_VAULT=~/path/to/your/vault
   ```

**Usage:**
```
/recap
```

Can also be invoked programmatically from a shell function (e.g. an end-of-day `bye()` that calls `/recap` before syncing and shutting down).

---

## Contributing

Feel free to submit issues and pull requests. When adding a new skill:

1. Create a folder with the skill name
2. Add a `SKILL.md` with frontmatter (`name`, `description`, `argument-hint`)
3. Update this README with setup instructions

## License

MIT License - see [LICENSE](LICENSE)
