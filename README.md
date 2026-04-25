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

## Vault Skills

Skills that power the 2nd brain vault live in a separate repo:
**[rabb1tl0ka/ai-2ndbrain](https://github.com/rabb1tl0ka/ai-2ndbrain)** → `claude-skills/`

These are installed automatically when you run `setup.sh` from that repo. Current vault skills: `/recap`.

---

## Available Skills

*(Non-vault skills listed here)*

---

## Contributing

Feel free to submit issues and pull requests. When adding a new skill:

1. Create a folder with the skill name
2. Add a `SKILL.md` with frontmatter (`name`, `description`, `argument-hint`)
3. Update this README with setup instructions

## License

MIT License - see [LICENSE](LICENSE)
