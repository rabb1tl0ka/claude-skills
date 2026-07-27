---
name: action-board
description: Scans markdown files in a repo for `## Actions` sections (checkbox items, optional due dates) and prints a consolidated, prioritized board of everything still open. Works in any repo that follows the `- [ ] task (due: yyyy-MM-dd)` convention under an `## Actions` heading — no per-repo dependency on any particular project structure. Triggers on "/action-board", "what's on my plate", "what do I need to do", "show my open actions", "my todos".
argument-hint: [path] [--all|--overdue]
---

# /action-board — consolidated open-actions board

Generic, repo-agnostic. Works anywhere `## Actions` sections follow the convention below — no setup beyond a small config file for the default owner name.

## Convention this skill reads

Any `.md` file in a repo may contain an `## Actions` section:

```markdown
## Actions
- [ ] Write unit tests for the parser (owner: alex) (due: 2026-08-01)
- [ ] Ask about X
- [ ] Research Jupyter notebook setup (owner: claude)
- [x] Set up the repo skeleton
```

- Checkbox syntax: `- [ ]` open, `- [x]` (case-insensitive) done.
- Due date is optional, appended in parentheses at the end of the line: `(due: yyyy-MM-dd)`. No suffix = no due date.
- Owner is optional, appended in parentheses: `(owner: name)`. No suffix defaults to the configured `default_owner` (see **Config file** below). Order of the two suffixes doesn't matter when parsing.
- The owner tag may list multiple people comma-separated, e.g. `(owner: Bruno Coelho, Ana Markovic)`, for genuinely joint actions. Store the parsed `owner` as the raw string as-is — matching against it (see `--owner` below) is substring-based, not exact-equality, specifically so each named person in a joint tag is matched.
- Detail link is optional: a `[detail](relative/path.md)` markdown link anywhere in the description points to a file with more context than the one-liner can hold (a fuller spec, a roadmap item, a doc). Useful when one file's `## Actions` section is a rollup pointing at several other files — e.g. an index/README listing items that each live in their own file. Strip it from the displayed description and use its target as the link in the report (Step 4) instead of the host file.
- The section runs until the next heading of equal or higher level (`#` or `##`), or end of file.

## Config file (per-repo)

Read `.claude/action-board.config.yaml`:

```yaml
default_owner: alex   # who untagged items are attributed to
```

If the file doesn't exist, ask once and create it:

> "Who should I attribute untagged `## Actions` items to (used as the default `owner` when a checkbox item doesn't have an explicit `(owner: ...)` tag)?"

Write the answer as `default_owner` in the config file, then proceed with the run using that value.

## Step 0: Parse arguments

- **path** (optional): directory to scope the scan to. Default: current working directory.
- **--all**: also include completed (`[x]`) items in the report (as a collapsed count, not itemized, unless the user then asks to see them). Default: open items only.
- **--overdue**: only show open items whose due date is before today.
- **--owner <name>**: only show open items owned by `name` — case-insensitive **substring** match against the parsed `owner` tag (so `--owner "Ana Markovic"` matches an item tagged `owner: Bruno Coelho, Ana Markovic`), defaulting untagged items to `default_owner`. Default: show all owners.

## Step 1: Find candidate files

Recursively search under `path` for `*.md` files, excluding `.git`, `node_modules`, `.claude`, and other common vendor/build directories. Grep for a `## Actions` heading to shortlist files before fully reading them.

## Step 2: Extract the Actions section per file

For each shortlisted file, read it and extract the content between `## Actions` and the next `#`/`##` heading (or EOF). Parse each checkbox line into `{checked, description, owner, due, file}`, defaulting `owner` to `default_owner` when the `(owner: ...)` tag is absent. Ignore non-checkbox lines in that section (free text, sub-bullets) — only top-level checkbox lines count as actions.

## Step 3: Filter and sort

- Filter per Step 0 args (open-only by default; overdue-only if `--overdue`; owner-only if `--owner <name>`, case-insensitive substring match against the parsed `owner`).
- Sort: overdue first (oldest due date first), then upcoming due dates ascending, then no-due-date items last. Preserve file discovery order within each group.
- "Overdue" = due date is before today's date.

## Step 4: Report

Print one consolidated list, one line per action:

```
[⚠ overdue yyyy-MM-dd | due yyyy-MM-dd | no due date] description — relative/path/to/file.md
```

Append `[owner: name]` after the description only when `owner` isn't `default_owner` — that's the common case and stays implicit to keep the board readable; a Claude-owned (or other) item gets called out explicitly since it's the exception.

Group under headers only when non-empty: **Overdue**, **Upcoming**, **No due date**. End with a one-line summary: `N open (M overdue)` — and if any non-default owners are present and `--owner` wasn't used to filter, add a breakdown like `(N <default_owner>, M claude)`.

If `--all` was passed, also print a `Done: N` line at the end (count only).

If no `## Actions` sections are found anywhere in scope, say so plainly — don't invent a report.
