---
name: flashcards
description: Quiz the user with multiple-choice flashcards generated from course/chapter notes in the current directory. Caches question banks locally so cards aren't regenerated every run, and logs every answer so weak topics can be identified over time. Triggers on "/flashcards", "quiz me", "flashcards on X", "new flashcards", "clear flashcards".
argument-hint: [scope] [count] [new|clear]
---

# /flashcards — Multiple-choice quiz from your notes

Operates relative to the **current working directory** (a course/learning-path folder containing a `CLAUDE.md` with a Progress section and chapter note files). All storage lives under `<cwd>/.flashcards/`.

## Step 0: Parse arguments

Arguments can appear in any order/combination, all optional:
- **scope** — a course name or chapter name (substring match, case-insensitive) against the course directories / chapter files listed in the Progress section of `CLAUDE.md`. If omitted → scope is everything currently marked completed across all courses.
- **count** — an integer, how many questions to ask this session. Default **10**. If the scoped question pool has fewer than `count` questions, ask what's available and say so.
- **mode** — `new` or `clear`:
  - `new` (optionally scoped): regenerate cached cards for the chapters in scope only. Delete just those chapters' cache files before regenerating.
  - `clear` (never scoped — always global): deletes the entire `.flashcards/` directory, including history. **This is destructive and cannot be undone (loses all quiz history/weak-spot data)** — confirm with the user before deleting. If confirmed, delete and stop (no quiz runs after a clear).

## Step 1: Resolve scope to chapter files

Read `CLAUDE.md` in cwd, specifically the `## Progress` section, to get the list of completed chapters and their file paths per course. Filter this list by the scope argument if given. If nothing matches, tell the user and stop.

## Step 2: Ensure cards are cached for each chapter in scope

Cache layout:
```
.flashcards/
  cards/<course-slug>/<chapter-slug>.json
  history.jsonl
  weak-spots.md
```

For each chapter file in scope:
- If its cache JSON exists and mode isn't `new`, reuse it — do not regenerate.
- Otherwise, read the chapter note (summary + user's notes/insights) and generate a question bank directly (you are the question generator — no external call needed). Aim for 6-10 questions per chapter covering distinct topics from that chapter, each with exactly 4 options and one correct answer. Write the cache file as:

```json
{
  "course": "Introduction to agent skills",
  "chapter": "What are Skills",
  "generated": "<today's date>",
  "questions": [
    {
      "id": "q1",
      "topic": "short topic tag, e.g. 'skill frontmatter'",
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "answer_index": 0
    }
  ]
}
```

Use kebab-case slugs for course/chapter directory and file names.

## Step 3: Build the question pool and pick questions

Combine all questions from the in-scope cache files into one pool.

Read `.flashcards/history.jsonl` if it exists (one JSON object per line: `date`, `course`, `chapter`, `question_id`, `topic`, `correct`). Compute a wrong-rate per `topic` (wrong answers / total attempts for that topic; topics never attempted count as highest priority, i.e. unknown = treat as weakest). Weight question selection toward higher wrong-rate topics, but still sample across the whole scope rather than hammering one chapter — don't let a single weak chapter crowd out the rest of the requested count.

Pick `min(count, pool size)` questions. If truncating the pool, mention how many questions exist in total.

## Step 4: Run the quiz

For each picked question, use the AskUserQuestion tool: single-select, the 4 options as choices (shuffle option order so the correct answer isn't always in the same position), header = the chapter or topic tag (kept ≤12 chars for the UI).

Immediately after each answer:
1. Tell the user right/wrong and give a one-line reason (grounded in the chapter note).
2. Append a line to `.flashcards/history.jsonl`: `{"date":"YYYY-MM-DD","course":"...","chapter":"...","question_id":"q1","topic":"...","correct":true|false}`

Do this per-question (not batched at the end) so progress is saved even if the user stops mid-quiz.

## Step 5: Wrap up

After all picked questions are answered:
- Report the score (`X/N`) and list which topics/chapters had wrong answers this session.
- Regenerate `.flashcards/weak-spots.md` from the **full** history.jsonl: a markdown table of topics sorted by wrong-rate descending (topic, course/chapter, attempts, wrong, wrong-rate%), so future sessions and the user can see where to focus.
