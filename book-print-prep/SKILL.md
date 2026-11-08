---
name: book-print-prep
description: Prepares a book PDF for home printing and loose-leaf (double fan) binding. Output is a duplex PDF on A4 sheets, two leaves per sheet, to be cut in half into A5 leaves, in cut-and-stack order. Handles scanned PDFs with two book pages per PDF page (landscape spreads, like Origen) and born-digital PDFs with one page per PDF page (like Synesius). Cleans scans (drops red ink, whitens yellowed paper, fades pencil, crops margin notes), adds a spine margin, builds a test sheet and verifies page pairing before the full build. Triggers on "/book-print-prep <pdf>", "prep this book for printing", "get this book ready to print and bind".
argument-hint: <path to the book PDF> [--skip-gap-check] [optional: deviations, e.g. "fade pencil harder"]
---

# /book-print-prep: book PDF to cut-and-stack A4 print file

The tool lives at `~/code/rabb1tl0ka/book-print-prep/bookprep.py` (README next to it). This skill is the judgment layer around it: it decides the flags, checks the result with your eyes, and hands Bruno print instructions.

## Fixed decisions (never ask)

- A4 sheets, landscape, duplex, cut in half into A5 leaves. Do not offer other paper sizes.
- Printer flip is **Short Edge (Flip)** with **Landscape** orientation (verified on Bruno's printer).
- Defaults: 10 mm margin, 8 mm extra spine margin per leaf. Only change if Bruno asks or names a preset.

## Presets (only when Bruno asks for one by name)

- **`notes-margins`** (a.k.a. "preset B", "the Timaeus margins", "roomy margins"): `--margin 18 --gutter 15`. Text shrinks to ~90% of the original print size. On the Timaeus (Cornford) A5 leaf that gave a 91×160 mm text block, 36 mm at the spine (glue room for double fan), 21 mm outer and 25 mm top/bottom for notes. Use for books whose pages are crammed with text. The exact mm depend on the book's text-block shape (tall and narrow blocks are limited by height), so measure the rendered leaf and report the real numbers.
- To compare options, build `--test-sheet N` once per setting and show Bruno a labelled side-by-side PNG, opened with `xdg-open` (images you Read are not visible to him).

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

## Step 1b: Missing-page check (skip only with `--skip-gap-check`)

Scans silently drop pages: the Timaeus scan was missing 5 whole leaves (10 pages of text) and Gnosis of the Mind was missing pp. 64-65, both found only after the print file was "ready". Run this check on every book unless Bruno passes `--skip-gap-check` (e.g. a book he already printed and read through). If skipped, say so in the hand-over.

1. Get the printed page number of every book page:
   - Text layer present: `pdftotext -layout`, split on `\f`, take the number from the header line (spread mode: left number at the start, right at the end) or the last short line.
   - Scans only: render at 100 dpi and OCR a strip (`convert -gravity south -crop 100%x8%` then `tesseract --psm 6`; try the top strip too, depending on where the book puts its numbers). Run in parallel (`xargs -P 12`).
2. Compute `offset = book page - PDF position` (spread mode: `L - 2*pdf_page`). OCR is noisy, so don't check page to page: take a histogram of offsets. The body should hold one dominant offset. A **run** of a different offset that continues afterwards means pages are missing (offset falls) or extra (offset rises). Lone odd values are misreads.
3. Roman-numbered front matter: read the numerals from the header and check that they step by 1 (single) or 2 (spread).
4. For every suspected gap, look at the page before and after it (end of one page, start of the next). A break mid-sentence or a skipped section start confirms it. A blank page or part-title missing before a section is harmless; note it and move on.
5. If real pages are missing:
   - Tell Bruno the exact book pages and the evidence before building anything.
   - Look for another scan on archive.org (`advancedsearch.php`, then `/metadata/<id>`; skip `access-restricted-item: true`). Save the copies Bruno wants next to the original in the books folder, named `<Book> - archive.org <identifier> (<pages>pp, <dpi>).pdf`.
   - A higher-dpi copy of the same scan has the same gaps. Check every candidate for the missing pages themselves.
   - Patch: render the donor pages so their text block matches the main source. Measure the scale ratio from 2+ book pages present in both sources, using text-block bounding boxes with the scan border excluded. Then paste each page onto a canvas the size of the main source, aligned to a same-side neighbour's text box. Flatten grey backgrounds but leave the contrast to `--clean` (otherwise the patched pages come out too bold). Insert with `pdfseparate` + `pdfunite`. Save the result next to the original as `<Book> - complete (<what was patched from where>).pdf` and build from that.
   - Run a test sheet that contains a patched page next to an original page.

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

First copy the final build next to the source PDF in the books folder as `<source name without .pdf> [PRINT-BOOK].pdf`. Bruno's goal is one ready-to-print file per book that he can print again later. One file per book: never leave a book as a main build plus separate patch sheets. Delete the test sheets and superseded builds from `out/`.

Give him exactly this, adapted with the real numbers (sheet count, file path):

- Print dialog: Two-sided **Short Edge (Flip)**, Orientation **Landscape**, Paper **A4**, Scale **100%**, Pages per side **1**, Color **grayscale / black ink only**.
- Print in batches of 10 sheets (20 PDF pages, odd start and even end, e.g. 21-40). Larger batches hit false paper-jam and low-ink stops on a home inkjet. Give him the expected front page numbers per batch (left and right piles) so he can verify.
- The Face Up output tray reverses each batch, so sort the sheets by front page number ascending before cutting. Count the sheets: if a batch stops early, ask for the front page numbers he sees to work out the missing range.
- Cut each sheet in half along the center ticks with a trimmer or guillotine (a knife without a steel ruler tears the paper).
- Stack all **left halves** in order, then all **right halves** under them. That is the book order. Each new batch goes under the previous one, on both piles.
- Binding tip (cartolina cover): glue the spine, optionally add a cotton mull strip, then a wrap-around cartolina cover (200-250 g/m2, grain parallel to the spine) scored at the spine and with a hinge crease about 6-8 mm in. Press the block flat between boards with even weight (spring clamps put uneven pressure and the shoulders slide out of square). Thread lines across the spine are not needed when a cover is glued on.
- If the printer or flip setting is new or the backs come out upside down or swapped, print `--test-sheet` first and rebuild with `--flip long`.

## Optional: print and bind a book in parts (only if Bruno asks)

Use when Bruno wants to read the first half now and print the rest later, as two bound books (Part One, Part Two).

**Do not just print half the sheets of the full PDF.** In the cut-and-stack layout the left halves are the first half of the book and the right halves are the second half. The first half of the sheets gives the first quarter plus the third quarter, which cannot be bound as a book.

**Instead build one PDF per part** with the page-range flags, so each part is its own complete cut-and-stack book with its own sheet count:

- Part One: `--first A --last N`. Part Two: `--first N+1 --last B`.
- Pick N at a chapter boundary near the middle: read the table of contents (`pdftotext` on the first pages) and propose a split that gives roughly equal halves. Let Bruno confirm.
- Spread mode: N is a spread number, and each part starts on a left page, so the automatic blank front keeps working.
- Single mode: re-derive `--first-side` for Part Two from its own test sheet, because page N+1 may be a left-hand page (then `--first-side verso`, which adds a blank recto in front).
- Use separate work dirs and names: `<slug>-part1`, `<slug>-part2`, and outputs `<slug>-part1-A4.pdf`, `<slug>-part2-A4.pdf`. Run the cleanup preview and test sheet once per part.
- The two parts cannot be merged into one bound volume later. If Bruno might want one volume, build the whole book instead.

Related, and true for the whole-book layout: while a book is printing in batches, the left pile is the first half of the book in order, so Bruno can start reading it before the right pile exists.

## Gotchas

- Do not guess paper, spine margin or flip: they are settled. Ask Bruno only about things the PDF cannot tell you.
- A PDF where the cover is page 1 and the real text starts later: use `--first` to skip, and re-derive `--first-side` from the test sheet.
- Books that mix colored plates with text are cropped to the text block. Check that the plates are not clipped before the full build.
- Never put copies of books or build output into a git repo.
