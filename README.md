# Claude Skills

A collection of custom skills for [Claude Code](https://claude.ai/claude-code).

## What are Skills?

Skills are markdown files that extend Claude Code's capabilities. Each skill defines a set of instructions and workflows that Claude follows when the skill is invoked.

## Installation

1. Copy the skill folder to your Claude Code skills directory:
   ```bash
   # For project-specific skills
   cp -r <skill-name> /path/to/your/project/.claude/skills/

   # For global skills (available in all projects)
   cp -r <skill-name> ~/.claude/skills/
   ```

2. Follow any skill-specific setup instructions in the skill's section below.

3. Use the skill by typing `/<skill-name>` in Claude Code, or just ask naturally—Claude will auto-invoke the skill when relevant.

---

## Available Skills

### `/calendar`

Query your Google Calendar for events, availability, scheduling conflicts, and meeting prep needs.

**Features:**
- View events by day, week, or date range
- Find available time blocks
- Check for scheduling conflicts
- Get meeting prep summaries

**Setup:**

1. Get your Google Calendar iCal feed URL:
   - Go to [Google Calendar](https://calendar.google.com)
   - Click the gear icon → Settings
   - Click on your calendar name in the left sidebar
   - Scroll to "Integrate calendar"
   - Copy the "Secret address in iCal format" URL

2. Open `calendar/SKILL.md` and replace `YOUR_ICAL_FEED_URL_HERE` with your URL

3. Copy the skill to your Claude Code skills directory

**Usage:**
```
/calendar today
/calendar free thursday afternoon
/calendar prep
/calendar this week
```

---

### `/voice_note`

Record voice notes using automatic silence detection and save to vault inbox.

**Features:**
- Automatic silence detection (~1.5s pause stops recording)
- Transcription via Whisper
- Save to current vault or specify target vault
- Custom titles or timestamp-based filenames

**Setup:**

Requires [MCP-voice server](https://github.com/your-repo/MCP-voice) configured with voice-tools.

**Usage:**
```
/voice_note
/voice_note "meeting notes"
/voice_note loka2026 "daily reflection"
```

---

### `/voice_prompt`

Record your voice and execute the transcription as a prompt for Claude.

**Features:**
- Speak commands instead of typing
- Automatic transcription and execution
- Hands-free Claude interaction

**Setup:**

Requires MCP-voice server.

**Usage:**
```
/voice_prompt
[Speak: "Create a new note about quantum computing"]
[Claude executes the spoken command]
```

---

### `/listen_start` & `/listen_stop`

Record desktop audio (speakers/headphones) for meeting notes, video summaries, etc.

**Features:**
- Background recording of desktop audio output
- Full transcription with timestamps
- AI-generated summary
- Saved to inbox with both summary and full transcript

**Setup:**

Requires MCP-voice server with PulseAudio loopback configured.

**Usage:**
```
/listen_start    # Start recording desktop audio
[... attend meeting, watch video, etc ...]
/listen_stop     # Stop, transcribe, summarize, save to inbox
```

---

## Contributing

Feel free to submit issues and pull requests. When adding a new skill:

1. Create a folder with the skill name
2. Add a `SKILL.md` with frontmatter (`name`, `description`, `argument-hint`)
3. Update this README with setup instructions

## License

MIT License - see [LICENSE](LICENSE)
