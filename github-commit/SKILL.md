---
name: github-commit
description: Groups the current working tree's changes by topic/theme, proposes one commit message per group, and — only after Bruno approves the full plan — stages and creates each commit in sequence. Triggers on "/github-commit", "commit my changes", "commit these grouped by theme".
argument-hint: [optional: a hint about scope, e.g. "just the docs changes"]
---

# /github-commit — grouped, approved commits

Works in any git repo. Looks at the *entire* working tree (staged + unstaged + untracked), groups changes into logical themes, and turns each theme into its own commit — never a single "everything" commit unless everything genuinely is one theme.

## Step 1 — See the full picture

Run in parallel:
- `git status` (never `-uall`)
- `git diff` (unstaged) and `git diff --cached` (already staged)
- `git log --oneline -15` to match this repo's existing commit message style (conventional commits? plain imperative? emoji? mirror whatever's there)

If the tree is clean, say so and stop.

## Step 2 — Group changes into themes

Group by what the change is *for*, not by directory alone — read enough of each diff to know why a file changed, don't just pattern-match on path. Typical signals for a group boundary: different feature/bugfix/refactor, different subsystem, unrelated file touched incidentally vs. the main change.

A single file can only belong to one group. If a file's diff genuinely mixes two unrelated concerns, flag that to Bruno rather than silently picking one side — don't split a file's own diff across two commits.

Before finalizing groups, check for anything that shouldn't be committed at all: `.env`, credentials, key files, anything that looks like a secret even under an innocuous name. Pull those out of every group and call them out explicitly rather than silently including or silently dropping them.

## Step 3 — Draft one commit message per group

For each group, write a concise message following this repo's observed style (from `git log` above). Default style if the repo has no clear convention: present-tense summary line focused on *why*, not *what* (the diff already shows what changed), under ~70 chars, body only if the why needs more than one line.

## Step 4 — Present the full plan, get one approval

Show Bruno, for every group in commit order:
- the theme name
- the list of files in it
- the proposed commit message

Ask for approval on the whole batch at once (not per-commit). Bruno may:
- approve as-is
- edit specific messages or regroup files
- drop a group entirely (leave those files uncommitted)

Do not stage or commit anything before this approval.

## Step 5 — Execute, in order

Once approved, for each group in sequence:
1. `git add <specific files>` — never `-A` or `.`, name the files explicitly
2. `git commit -m "$(cat <<'EOF' ... EOF)"` with the approved message, ending with the same `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` trailer used elsewhere in this environment
3. If a pre-commit hook fails: fix the underlying issue, re-stage, and make a **new** commit — never `--amend` past a failed hook, never `--no-verify`

After each commit, confirm it landed (`git log -1 --oneline`) before moving to the next group.

## Step 6 — Report

Summarize what was committed: one line per commit (hash + message), and whether anything was intentionally left out (dropped group, or files pulled for looking like secrets). Run a final `git status` to show the tree is clean (or what's left, if a group was dropped).

## Non-negotiables (inherited from global git safety rules)

- Never `git push` unless explicitly asked in this same request.
- Never amend, force-push, or skip hooks unless explicitly asked.
- Never stage with a wildcard/blanket add — always name files.
- Never commit something that looks like a secret without flagging it first.
