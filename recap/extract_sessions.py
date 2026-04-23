#!/usr/bin/env python3
"""
Deterministic extractor for Claude Code session logs (last 24h).
Outputs structured JSON. No LLM. Used by the /bye skill.

Cache: writes output to ~/.claude/skills/bye/cache/<work_day_date>.json
"""
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path


CACHE_DIR = Path.home() / ".claude" / "skills" / "recap" / "cache"
STATE_FILE = Path.home() / ".claude" / "skills" / "recap" / "state.json"
PROJECTS_DIR = Path.home() / ".claude" / "projects"
HOURS_BACK = 24
WORKDAY_CUTOFF_HOUR = 4  # before 4AM = previous workday


def load_last_covered() -> datetime | None:
    try:
        data = json.loads(STATE_FILE.read_text())
        ts = data.get("last_covered_until")
        if ts:
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
    except Exception:
        pass
    return None


def work_day_date(now: datetime) -> str:
    """Return the workday date string. Before 4AM rolls back to yesterday."""
    if now.hour < WORKDAY_CUTOFF_HOUR:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")
    return now.strftime("%Y-%m-%d")


def project_name_from_folder(folder_name: str) -> str:
    """
    Convert folder name to readable project path.
    -home-rabb1tl0ka-loka-code-claude-skills -> loka/code/claude-skills
    """
    parts = folder_name.lstrip("-").split("-")
    try:
        home_idx = parts.index("home")
        parts = parts[home_idx + 2:]  # skip 'home' and username
    except ValueError:
        pass
    return "/".join(parts) if parts else folder_name


def parse_session(log_file: Path, proj_folder: str) -> dict | None:
    records = []
    try:
        for line in log_file.read_text(errors="replace").strip().splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        return None

    if not records:
        return None

    session_id = None
    cwd = None
    git_branch = None
    timestamps = []
    user_messages = []
    files_modified = []
    files_read = []
    bash_descriptions = []
    external_tools = set()

    for rec in records:
        rtype = rec.get("type")

        if rtype == "user":
            msg = rec.get("message", {})
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                # Skip skill invocations and very short system-like messages
                text = content.strip()
                if not text.startswith("/") and len(text) > 3:
                    user_messages.append(text)

            ts = rec.get("timestamp")
            if ts:
                timestamps.append(ts)

            if not cwd:
                cwd = rec.get("cwd")
            if not git_branch:
                git_branch = rec.get("gitBranch")
            if not session_id:
                session_id = rec.get("sessionId")

        elif rtype == "assistant":
            content = rec.get("message", {}).get("content", [])
            if not isinstance(content, list):
                continue
            for item in content:
                if not isinstance(item, dict) or item.get("type") != "tool_use":
                    continue
                name = item.get("name", "")
                inp = item.get("input", {})

                if name in ("Edit", "Write"):
                    fp = inp.get("file_path", "")
                    if fp:
                        files_modified.append(fp)
                elif name == "Read":
                    fp = inp.get("file_path", "")
                    if fp:
                        files_read.append(fp)
                elif name == "Bash":
                    desc = inp.get("description", "")
                    if desc:
                        bash_descriptions.append(desc)
                elif name.startswith("mcp__"):
                    # mcp__claude_ai_Notion__notion-fetch -> notion
                    parts = name.split("__")
                    if len(parts) >= 2:
                        svc = parts[1].lower()
                        svc = svc.replace("claude_ai_", "").replace("cloudsort_", "").replace("_", " ").strip()
                        external_tools.add(svc)

    if not user_messages and not files_modified and not bash_descriptions:
        return None

    # Prefer cwd (exact path) over folder-name reconstruction
    if cwd:
        home = str(Path.home())
        project = cwd.replace(home + "/", "").replace(home, "") or cwd
    else:
        project = project_name_from_folder(proj_folder)

    start_time = min(timestamps) if timestamps else None
    end_time = max(timestamps) if timestamps else None

    duration_minutes = None
    if start_time and end_time and start_time != end_time:
        try:
            t0 = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            duration_minutes = max(1, int((t1 - t0).total_seconds() / 60))
        except Exception:
            pass

    # Deduplicate while preserving order
    def dedup(lst):
        seen = set()
        out = []
        for x in lst:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return {
        "session_id": session_id,
        "project": project,
        "cwd": cwd,
        "git_branch": git_branch,
        "start_time": start_time,
        "end_time": end_time,
        "duration_minutes": duration_minutes,
        "turn_count": len(user_messages),
        "user_messages": user_messages,
        "files_modified": dedup(files_modified),
        "files_read": dedup(files_read),
        "bash_descriptions": bash_descriptions,
        "external_tools": sorted(external_tools),
    }


def extract_sessions() -> dict:
    now = datetime.now(timezone.utc)
    last_covered = load_last_covered()
    cutoff_mtime = last_covered.timestamp() if last_covered else time.time() - (HOURS_BACK * 3600)
    wday = work_day_date(now.astimezone())

    sessions = []

    if PROJECTS_DIR.exists():
        for proj_dir in sorted(PROJECTS_DIR.iterdir()):
            if not proj_dir.is_dir():
                continue
            for log_file in proj_dir.glob("*.jsonl"):
                if log_file.stat().st_mtime < cutoff_mtime:
                    continue
                session = parse_session(log_file, proj_dir.name)
                if session:
                    # Attribute session to the day it started
                    if session["start_time"]:
                        try:
                            t = datetime.fromisoformat(
                                session["start_time"].replace("Z", "+00:00")
                            ).astimezone()
                            session["session_date"] = work_day_date(t)
                        except Exception:
                            session["session_date"] = wday
                    else:
                        session["session_date"] = wday
                    sessions.append(session)

    # Drop sessions already covered by a previous log run
    if last_covered:
        sessions = [
            s for s in sessions
            if s.get("end_time") and
            datetime.fromisoformat(s["end_time"].replace("Z", "+00:00")) > last_covered
        ]

    sessions.sort(key=lambda s: s.get("start_time") or "")

    end_times = [s["end_time"] for s in sessions if s.get("end_time")]
    covered_until = max(end_times) if end_times else None

    projects = list(dict.fromkeys(s["project"] for s in sessions if s.get("project")))
    total_turns = sum(s["turn_count"] for s in sessions)

    return {
        "date": now.strftime("%Y-%m-%d"),
        "work_day_date": wday,
        "extracted_at": now.isoformat(),
        "covered_from": last_covered.isoformat() if last_covered else None,
        "covered_until": covered_until,
        "sessions": sessions,
        "projects": projects,
        "total_turns": total_turns,
    }


def main():
    data = extract_sessions()
    wday = data["work_day_date"]

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{wday}.json"
    cache_file.write_text(json.dumps(data, indent=2))

    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
