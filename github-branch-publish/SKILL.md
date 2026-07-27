---
name: github-branch-publish
description: Commits the working tree (grouped by theme, same flow as /github-commit), pushes to a branch, and opens a PR — all in one shot. Defaults to the user's own branch per this repo's branch conventions if one isn't given. Triggers on "/github-branch-publish", "publish my branch", "commit push and PR this".
argument-hint: [branch-name] [--base <branch>]
---

# /github-branch-publish — commit, push, PR in one shot

Works in any git repo. Runs the same grouped-commit flow as `/github-commit`, then pushes the result to a branch and opens a PR against the right base — so a new contributor can go from "I made some changes" to "there's a PR waiting for review" without knowing any git commands.

## Step 1 — Determine the target branch

- If a branch name was passed as an argument, use it.
- Otherwise, check this repo's own `CLAUDE.md` (root or directory-scoped) for a documented branch convention (e.g. "each contributor gets `<scope>/<name>`"). If one exists and the user has identified themselves this session, derive the branch name from it.
- If no convention is documented and no argument was given, ask which branch to target. Never guess silently — the whole point of this skill is to publish somewhere specific.
- If the resolved branch name is `main` (or whatever this repo's default branch is) or a branch this repo's own instructions mark as shared/protected (e.g. an integration branch multiple people commit to), stop and ask for confirmation before doing anything — same rule as `/github-commit`'s inherited git safety rules, just checked before step 2 instead of after.

## Step 2 — Get on the target branch

- If the branch already exists locally, check it out.
- If it exists on `origin` but not locally, fetch and check it out (`git checkout -b <branch> origin/<branch>`).
- If it doesn't exist anywhere, create it off the current branch (or off `--base` if one was passed) and note what it was branched from — this becomes the default PR base in Step 5.

## Step 3 — Group and commit (same as `/github-commit`)

Follow `/github-commit`'s Steps 1–6 verbatim: inspect the full working tree, group changes into themes, draft one message per group, present the full plan for one approval, then execute in commit order. Do not stage or commit anything before that approval.

If the tree is already clean (nothing to commit), skip straight to Step 4 only if the branch has unpushed commits already sitting on it; otherwise stop and say there's nothing to publish.

## Step 4 — Push

```bash
git push -u origin <branch>   # -u only needed the first time the branch is pushed
```

## Step 5 — Open the PR

Determine the base branch, in order of preference:
1. `--base <branch>` if passed explicitly.
2. This repo's own `CLAUDE.md` convention, if it documents where this branch's PRs should target (e.g. a per-person branch merging into a shared integration branch, not `main`).
3. The branch this one was created from in Step 2, if it was just created.
4. Otherwise ask — never default to `main` silently when the repo has its own stated convention.

```bash
gh pr create --base <base> --head <branch> --title "<short, from commit themes>" --body "$(cat <<'EOF'
## Summary
<1-3 bullets from the commit messages>
EOF
)"
```

## Step 6 — Report

Report: the branch committed to, each commit (hash + message), the push result, and the PR URL. If a group was dropped or something looked like a secret during Step 3, restate that too — don't bury it under the PR link.

## Non-negotiables (inherited from `/github-commit`'s global git safety rules)

- Never stage with a wildcard/blanket add — always name files.
- Never commit something that looks like a secret without flagging it first.
- Never force-push, amend past a failed hook, or skip hooks unless explicitly asked.
- Never push to or PR against a branch this repo's own instructions mark as protected/shared without explicit confirmation first.
