---
name: book-print-prep
description: Prepares a book PDF for home printing and loose-leaf (double fan) binding. Output is a duplex PDF on A4 sheets, two leaves per sheet, to be cut in half into A5 leaves, in cut-and-stack order. Handles scanned PDFs with two book pages per PDF page (landscape spreads, like Origen) and born-digital PDFs with one page per PDF page (like Synesius). Cleans scans (drops red ink, whitens yellowed paper, fades pencil, crops margin notes), adds a spine margin, builds a test sheet and verifies page pairing before the full build. Triggers on "/book-print-prep <pdf>", "prep this book for printing", "get this book ready to print and bind".
argument-hint: <path to the book PDF> [optional: deviations, e.g. "fade pencil harder"]
---

# /book-print-prep: book PDF to cut-and-stack A4 print file

The tool lives at `~/code/rabb1tl0ka/book-print-prep/bookprep.py` (README next to it). This skill is the judgment layer around it: it decides the flags, checks the result with your eyes, and hands Bruno print instructions.

## Fixed decisions (never ask)

- A4 sheets, landscape, duplex, cut in half into A5 leaves. Do not offer other paper sizes.
- Printer flip is **Short Edge (Flip)** with **Landscape** orientation (verified on Bruno's printer).
- Defaults: 10 mm margin, 8 mm extra spine margin per leaf. Only change if Bruno asks.

## Step 1: Look before deciding

1. `pdfinfo` (pages, page size) and `pdffonts` / `pdfimages -list` (is there a real text layer or only page scans?).
2. Pick the mode:
   - Landscape pages with two book pages side by side, usually scanned: `--mode spread`.
   - Portrait pages, one book page per PDF page, real fonts: `--mode single`.
   - One scanned book page per PDF page: `--mode single --clean`.
3. Render the first ~8 and last ~6 pages small (`pdftoppm -r 25`, then `montage`) into a scratch dir and look at the montage. From it decide:
   - `--first` / `--last`: skip the cover and any trailing junk.
   - Pure handwriting or notes pages with no book text: list them for `--blank` (spread mode: `290R`, `287L`; single mode: bare page numbers). Handwriting in the margins is cropped automatically; handwriting inside the text block is not, so only blank pages that have no real text.
   - Tell Bruno what you decided and why in a few lines. Pages that have real text but handwriting in the text block stay in, and are flagged to him.

## Step 2: Cleanup preview (scans only, skip for born-digital)

Before the full cleanup run (minutes for a few hundred pages), check what the cleanup does on 3 pages:

- Pick 3 consecutive pages from the body, about 40% into the book. Build them in a separate work dir:
  `python3 ~/code/rabb1tl0ka/book-print-prep/bookprep.py <pdf> --mode ... --first X --last X+2 --work ~/.cache/book-print-prep/<slug>-preview --out .../<slug>-preview.pdf --test-sheet 0`
- Render both sides at low resolution and look. Check:
  1. Paper is white and text is crisp, not thinned.
  2. Red ink, pencil underlines and margin notes are gone or faint.
  3. No clipped letters or page numbers.
- If pencil is still visible, try `--levels 0.62 0.92` and re-preview. If letters get thin, go back down. Settle on levels here, then use them for every later step.
- Show Bruno what you see in a couple of lines. Move on once the preview is acceptable (his yes is not required when it clearly is).
- The preview is only about cleanup. The text-block crop is computed from 3 pages, so the exact crop and page pairing are checked in step 3.

## Step 3: Test sheet, and verify parity yourself

- Work dir per book (the cache is keyed on parameters, but keep books apart): `~/.cache/book-print-prep/<slug>`.
- Output next to the tool: `~/code/rabb1tl0ka/book-print-prep/out/<slug>-A4.pdf` (gitignored).
- Build one sheet from roughly 40% into the book:
  `python3 ~/code/rabb1tl0ka/book-print-prep/bookprep.py <pdf> --mode ... --first ... --work ... --out .../<slug>-test-sheet.pdf --test-sheet N`
- Render both sides of the test sheet at low resolution and look at them. Check ALL of:
  1. On the front, the pages are right-hand pages (page number at the outer right, or the book's own recto convention). Backs are left-hand pages.
  2. Each leaf is consecutive: the front's page number n has n+1 on the back.
  3. Everything is upright, no clipped letters at the edges, no handwriting in the margins.
- **Single mode parity:** a cover or front matter can shift whether PDF page 2 is a right-hand or left-hand page. If check 1 or 2 fails, flip `--first-side` (recto/verso) and rebuild. This was the Synesius lesson: guessing wrong pairs each page with its neighbor's reverse.
- Spread mode: the first left-hand page gets a blank recto in front automatically. Leave it unless the book obviously starts differently.

## Step 4: Full build

Run the same command without `--test-sheet`. Then verify: output page count equals 2 times the sheet count in the tool's summary line, and view a montage of ~6 sheets (first, middle, last) for a last sanity look. For scans, report remaining pencil marks inside text areas as known flaws and offer `--levels 0.65 0.92` (thins the letters a little).

## Step 5: Hand over to Bruno

Give him exactly this, adapted with the real numbers (sheet count, file path):

- Print dialog: Two-sided **Short Edge (Flip)**, Orientation **Landscape**, Paper **A4**, Scale **100%**, Pages per side **1**, Color **grayscale / black ink only**.
- Print in batches of 20 to 30 sheets, keeping the order.
- Cut each sheet in half along the center ticks with a trimmer or guillotine (a knife without a steel ruler tears the paper).
- Stack all **left halves** in order, then all **right halves** under them. That is the book order.
- If the printer or flip setting is new or the backs come out upside down or swapped, print `--test-sheet` first and rebuild with `--flip long`.

## Gotchas

- Do not guess paper, spine margin or flip: they are settled. Ask Bruno only about things the PDF cannot tell you.
- A PDF where the cover is page 1 and the real text starts later: use `--first` to skip, and re-derive `--first-side` from the test sheet.
- Books that mix colored plates with text are cropped to the text block. Check that the plates are not clipped before the full build.
- Never put copies of books or build output into a git repo.
