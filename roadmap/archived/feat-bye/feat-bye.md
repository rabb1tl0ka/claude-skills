---
status: done
priority: high
owner: "@rabb1tl0ka"
---

# Feature Spec: /bye — Daily Note Writer

## One-Line Overview
A `/bye` Claude Code skill + shell hook that extracts the last 24h of Claude Code session data and writes a structured daily note to the Obsidian vault before shutdown.

## Goal
When Bruno runs `bye` in the terminal, Claude Code automatically synthesizes everything worked on during the day into a structured daily note in `~/loka/vaults/loka2026/daily/YYYY-MM-DD.md`, then proceeds with vault backup and shutdown. The skill uses a deterministic Python extractor to pull structured session data from Claude's JSONL logs, then uses LLM synthesis to produce a useful, honest note — not a raw dump.

## Expected advantages / benefits

- Replaces zero end-of-day documentation with a consistent daily record, without adding friction
- Surfaces connections to 2026 growth arc (squad building, listening, multiplying impact) that might otherwise go unnoticed
- Creates a searchable history of what projects, files, and tools were touched each day
- The "Claude's Observations" section provides a second-opinion perspective grounded in actual behavior, not self-report
- Works from any terminal directory — no setup per session
- Failure-resilient: a crashed `/bye` run leaves a cache that the next run picks up and continues from

## Downsides / risks

- Depends on Claude Code JSONL log format staying stable (undocumented internal format)
- Sessions must exist in `~/.claude/projects/` — if logs are cleared or rotated, the note will be sparse
- `claude --print "/bye"` adds ~10-30 seconds to the shutdown flow
- Cache file could get stale if session logs are modified after extraction (unlikely but possible)

## Context

### Current flow
1. Bruno types `bye` in terminal
2. Vault backup runs (`vault-backup.sh`)
3. Machine shuts down
4. No record of what was done that day

### Proposed flow
1. Bruno types `bye` in terminal
2. `claude --print "/bye"` runs non-interactively from any directory
3. Skill checks for a pending cache from a previously failed run
   - If cache exists and is from today's work day → reuse it (skip re-extraction)
   - Otherwise → run `extract_sessions.py` fresh and save cache
4. Claude synthesizes session data into a daily note
5. Note written to `~/loka/vaults/loka2026/daily/YYYY-MM-DD.md`
   - If file already exists → append a new timestamped session block
   - If running before 4AM → use yesterday's date (late-night sessions belong to the previous workday)
6. On success → cache file is deleted
7. `claude --print "/bye"` exits (success or failure)
8. `bye()` shell function prints a warning if step 7 failed, then **always** proceeds
9. Vault backup runs
10. Machine shuts down

### Files involved
- `bye/SKILL.md` — skill instructions (deployed to `~/.claude/skills/bye/`)
- `bye/extract_sessions.py` — deterministic JSONL extractor (deployed to `~/.claude/skills/bye/`)
- `~/.oh-my-zsh/custom/my-aliases.zsh` — `bye()` function updated to invoke the skill

**Branch:** `feat/bye`

---

## Design

### extract_sessions.py

Deterministic Python script. No LLM. Reads JSONL files from `~/.claude/projects/*/` modified in the last 24h and outputs structured JSON.

**What it extracts per session:**

| Source field | Extracted as |
|---|---|
| `user.cwd` | `project` (path relative to home) |
| `user.gitBranch` | `git_branch` |
| `user.timestamp` (first/last) | `start_time`, `end_time`, `duration_minutes` |
| `user.message.content` (text) | `user_messages[]` — verbatim prompts |
| `assistant.tool_use` where `name=Edit\|Write` → `file_path` | `files_modified[]` |
| `assistant.tool_use` where `name=Read` → `file_path` | `files_read[]` |
| `assistant.tool_use` where `name=Bash` → `description` | `bash_descriptions[]` |
| `assistant.tool_use` where `name=mcp__*` | `external_tools[]` (Notion, Slack, Jira, etc.) |

**Output shape:**
```json
{
  "date": "2026-04-22",
  "work_day_date": "2026-04-21",
  "sessions": [...],
  "projects": ["loka/code/claude-skills", "loka/projects/cloudsort/..."],
  "total_turns": 14
}
```

`work_day_date`: if the script runs before 4AM, this is yesterday's date. The skill uses `work_day_date` (not `date`) for the note filename.

**Session attribution**: sessions are attributed to the day their first `user` timestamp falls on — a session starting April 21 at 11PM and ending April 22 at 1AM is recorded under April 21.

### Cache mechanism

The extractor saves its output to `~/.claude/skills/bye/cache/YYYY-MM-DD.json` (keyed by `work_day_date`).

**Cache lifecycle:**
- **On extraction** → write cache file
- **On skill start** → check for existing cache matching today's `work_day_date`; if found, use it instead of re-extracting
- **On note write success** → delete the cache file
- **On failure** → cache remains; next `bye` run picks it up automatically

This means: if `bye` fails mid-way (API timeout, etc.), the next run skips re-extraction and retries the note-writing step with the same data. No sessions are lost.

### SKILL.md instructions

The skill tells Claude to:
1. Check for cache at `~/.claude/skills/bye/cache/<work_day_date>.json`
2. If no cache → run `python3 ~/.claude/skills/bye/extract_sessions.py`, which writes the cache
3. Read the cache JSON
4. Determine note path from `work_day_date`
5. Check if the file exists (append vs create)
6. Write the note
7. Delete the cache file on success

### Daily note template

**Fresh note (file does not exist):**
```markdown
---
date: YYYY-MM-DD
---

# Month Day, Year

## Overview
One sentence: what was this day really about?

## Achievements & Progress
- Concrete completions, bullet by bullet
- What exists now that didn't before?

## Projects & Repos
| Project | Activity | Files Changed |
|---------|----------|---------------|

## Things I Learned
- Technical, process, or strategic learnings extracted from prompts + commands

## Claude's Observations
2-4 bullets anchored to growth goals where relevant:
- Decision-making quality (reframing, clarifying, diving in)
- Prompt quality (specific, systemic, reactive)
- Connections to listening / coaching / multiplying-impact goals
- Anything surprising worth reflecting on

## Open Threads
- Things started but not clearly resolved
```

**Append block (file already exists):**
```markdown

---
## Claude Code Session — HH:MM

## Achievements & Progress
...

## Projects & Repos
...

## Things I Learned
...

## Claude's Observations
...

## Open Threads
...
```

### Tone guidance for the skill
Match Bruno's existing daily notes: direct, no fluff, substantive. "Claude's Observations" should be honest and sharp — not flattering, not harsh.

### bye() shell function

```bash
bye() {
  echo "==> Writing daily note..."
  claude --print "/bye"
  if [ $? -ne 0 ]; then
    echo "==> Warning: daily note failed (will retry next time). Proceeding with backup..."
  fi
  echo "==> Backing up vault before shutdown..."
  bash "$HOME/loka/vaults/loka2026/.scripts/vault-backup.sh" && \
  echo "==> Backup done. Shutting down..." && \
  shutdown now
}
```

---

## Changes required

| File | Change |
|------|--------|
| `bye/SKILL.md` | Create — skill instructions |
| `bye/extract_sessions.py` | Create — deterministic session extractor |
| `~/.claude/skills/bye/SKILL.md` | Create — deployed copy (global, available from any dir) |
| `~/.claude/skills/bye/extract_sessions.py` | Create — deployed copy |
| `~/.oh-my-zsh/custom/my-aliases.zsh` | Update `bye()` to invoke skill with error-resilient wrapper |

---

## Test plan

1. Run `python3 ~/.claude/skills/bye/extract_sessions.py` — verify valid JSON output with sessions from the last 24h
2. Verify `work_day_date` is yesterday when run before 4AM
3. Verify cache file is written to `~/.claude/skills/bye/cache/<work_day_date>.json`
4. Run `/bye` inside a Claude Code session — verify daily note created at correct path, cache deleted on success
5. Run `/bye` again same day — verify a timestamped block is appended, not the file overwritten
6. Simulate failure: leave a cache file manually, run `/bye` — verify it reuses cache instead of re-extracting
7. Run `bye` from `/tmp` — verify note is written correctly (absolute paths throughout)
8. Run `bye` with no sessions in last 24h — verify minimal note written, no crash
9. Simulate `claude --print "/bye"` failing (kill it mid-run) — verify `bye()` prints warning and proceeds to backup + shutdown

---

## Open questions

1. **Session log retention**: how long does Claude Code keep JSONL files? Unknown — if logs are pruned, sessions older than the retention window won't appear.
2. **Multiple terminals**: multiple simultaneous sessions are all picked up independently. Correct behavior, worth knowing.
