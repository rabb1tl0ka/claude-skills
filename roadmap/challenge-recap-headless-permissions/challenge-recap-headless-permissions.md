---
status: in-progress
priority: high
owner: "@rabb1tl0ka"
---

# Challenge: /recap headless Write permission

## One-Line Overview
The `recap` skill fails silently in headless (`--print`) mode because Claude Code skips workspace trust and requires explicit Write permission rules that no tested format has matched yet.

## What's the problem

`bye-recap()` runs `claude --print "/recap"` before shutdown. In this mode, Claude Code skips workspace trust (by design — the docs say so explicitly). That means Write tool calls need an explicit allow rule in `settings.json`. 

Every format tried so far fails silently — Claude outputs "waiting for permission" text and exits 0, but the file is never written. The Bash commands have a secondary issue: multi-line commands starting with `WORK_DAY=...` don't match any permission pattern because Claude Code's Bash matching appears not to match across newlines.

Interactive `test_recap` works because workspace trust is applied when the user approves the `~` directory.

## Why it matters

`bye-recap()` is a shutdown script — it runs unattended. Silent failure means no session log is written and no error is surfaced. The vault backup proceeds and the machine shuts down regardless.

## Constraints

- Must not use `--dangerously-skip-permissions`
- Must work unattended (no interactive prompts at shutdown)
- Must write to `$CLAUDE_SKILLS_VAULT/user/private/daily-claude-sessions/`

## Approaches considered

| Approach | Status | Why ruled out / still open |
|----------|--------|----------------------------|
| `Write(/home/rabb1tl0ka/.../daily-claude-sessions/**)` | Failed | Single `/` treated as project-relative, not absolute |
| `Write(~/loka/.../daily-claude-sessions/**)` | Failed | Tilde not resolving correctly at match time |
| `Write(//home/rabb1tl0ka/.../daily-claude-sessions/**)` | Failed | `//` absolute format + `**` glob not matching |
| `Write(//home/rabb1tl0ka/.../daily-claude-sessions/*)` | Failed | Same with `*` |
| `Write(//home/rabb1tl0ka/.../daily-claude-sessions/claude-session-*)` | Failed | Specific prefix, still `//` |
| `Write(/home/rabb1tl0ka/.../daily-claude-sessions/claude-session-*)` | **Untested** | Single slash + specific prefix — last format to try |
| `--permission-mode acceptEdits` on bye-recap/test_recap_headless | Open | Auto-approves all Write/Edit calls; semantically correct but Bruno wants to exhaust settings.json options first |
| Bash: `Bash(WORK_DAY=*)` in settings.json | Untested | Covers multi-line cache check command if `*` matches newlines |

## Open questions

1. Does `*` in Bash permission patterns match newlines? The multi-line `WORK_DAY=$(python3...)` command needs this.
2. Does single-slash `Write(/home/...)` with a specific prefix (not glob directory) work?
3. If settings.json format never works: is `--permission-mode acceptEdits` acceptable for a trusted shutdown script?
