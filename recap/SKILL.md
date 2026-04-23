---
name: recap
description: Extracts Claude Code sessions from the last 24h and writes a structured session log to $CLAUDE_SKILLS_VAULT/user/private/daily-claude-sessions/ (default: ~/2ndbrain). Can be run standalone or invoked by bye-recap() before vault backup and shutdown.
argument-hint: (none)
---

# /recap — Daily Session Summary

Write today's session log based on Claude Code sessions from the last 24 hours. Then clean up.

---

## Step 0: Resolve vault path and load user profile

Run this bash command and capture the output — this is your `VAULT_PATH` for all subsequent steps:

```bash
echo "${CLAUDE_SKILLS_VAULT:-$HOME/2ndbrain}"
```

Call the output `VAULT_PATH`. Use this **exact resolved string** (e.g. `/home/alice/2ndbrain`) everywhere a path is needed — never use `$VAULT` or `$CLAUDE_SKILLS_VAULT` as literals in tool calls.

Then read the user profile at `<VAULT_PATH>/user/user.md`.

Use the **Role**, **2026 Arc**, **Observation Lens**, and **Tone** sections from that file to inform the note — especially "Claude's Observations." If the file doesn't exist, proceed without it.

---

## Step 1: Get session data

### Check for existing cache first

```bash
WORK_DAY=$(python3 -c "
from datetime import datetime, timedelta
now = datetime.now()
d = (now - timedelta(days=1)).strftime('%Y-%m-%d') if now.hour < 4 else now.strftime('%Y-%m-%d')
print(d)
")
CACHE_FILE="$HOME/.claude/skills/recap/cache/${WORK_DAY}.json"
ls "$CACHE_FILE" 2>/dev/null && echo "CACHE_EXISTS" || echo "NO_CACHE"
```

- If cache exists → read it with `cat "$CACHE_FILE"` — skip extraction
- If no cache → run the extractor:

```bash
python3 ~/.claude/skills/recap/extract_sessions.py
```

The extractor writes the cache automatically and prints the same JSON to stdout.

---

## Step 2: Determine note path

Use `work_day_date` from the JSON (not `date`) — this handles sessions that run past midnight.

`work_day_date_nodash` = `work_day_date` with dashes removed (e.g. `2026-04-21` → `20260421`).

Note path: `<VAULT_PATH>/user/private/daily-claude-sessions/claude-session-<work_day_date_nodash>.md`

Check if the file already exists:
```bash
ls "<VAULT_PATH>/user/private/daily-claude-sessions/claude-session-<work_day_date_nodash>.md" 2>/dev/null && echo "EXISTS" || echo "NEW"
```

---

## Step 3: Write the note

### If the file does NOT exist — write a full note:

```markdown
---
date: YYYY-MM-DD
---

# <Month Day, Year>

## Overview
<One sentence capturing the theme of the day. What was this day actually about?>

## Achievements & Progress
<Bullet list of concrete completions. What exists now that didn't before? Be specific.>

## Projects & Repos
| Project | Activity | Files Changed |
|---------|----------|---------------|
<One row per project. Use short file names, not full paths.>

## Things I Learned
<Technical, process, or strategic learnings extracted from user prompts and bash command descriptions. If Notion/Slack/Jira tools were used, note what external work happened.>

## Claude's Observations
<2–4 bullets. Anchor to the user's growth goals where relevant. Honest and sharp.>

## Open Threads
<Things started but not clearly resolved — infer from prompts without obvious follow-through, files read but not modified, tasks that seemed mid-flight.>
```

### If the file ALREADY EXISTS — append this block at the end:

```markdown

---

## Claude Code Session — <HH:MM>

### Achievements & Progress
<...>

### Projects & Repos
| Project | Activity | Files Changed |
|---------|----------|---------------|

### Things I Learned
<...>

### Claude's Observations
<...>

### Open Threads
<...>
```

Use the current local time for `HH:MM`.

---

## Step 4: Write the file

Use the Write tool (for new files) or Edit tool (to append to existing files).

The file path is the resolved absolute path from Step 0:
`<VAULT_PATH>/user/private/daily-claude-sessions/claude-session-<work_day_date_nodash>.md`

Do not use shell variables or `~` in the path passed to the Write/Edit tool — use the concrete string.

---

## Step 5: Save state and clean up cache

After successfully writing the note, save the high-water mark from the cache (so the next run doesn't re-cover these sessions), then delete the cache:

```bash
python3 -c "
import json, sys
from pathlib import Path
cache = json.loads(Path('$HOME/.claude/skills/recap/cache/<work_day_date>.json').read_text())
covered_until = cache.get('covered_until')
if covered_until:
    state = Path('$HOME/.claude/skills/recap/state.json')  # matches STATE_FILE in extractor
    state.write_text(json.dumps({'last_covered_until': covered_until}))
"
rm -f ~/.claude/skills/recap/cache/<work_day_date>.json
```

---

## Edge cases

- **No sessions in last 24h**: write a minimal note — date frontmatter, header, and one line: `No Claude Code sessions recorded today.`
- **Cache exists but is from a different work_day_date**: ignore it, run fresh extraction
- **Extraction fails**: print the error and exit non-zero. The shell wrapper will warn the user and proceed to shutdown anyway. The cache (if written) will be reused next time.
- **user.md missing**: proceed without user context — don't fail the skill
