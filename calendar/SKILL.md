---
name: calendar
description: Query your Google Calendar for events, availability, scheduling conflicts, and meeting prep needs. Use when user asks about their schedule, what's on today, finding free time, or preparing for meetings.
argument-hint: [query - e.g., "today", "free thursday", "prep", "next week"]
---

# Calendar Assistant

Help the user interact with their Google Calendar.

## Calendar Feed

**iCal URL**: `YOUR_ICAL_FEED_URL_HERE`

Replace the URL above with your Google Calendar's secret iCal feed URL. To get it:
1. Go to Google Calendar → Settings (gear icon)
2. Click your calendar name in the left sidebar
3. Scroll to "Integrate calendar"
4. Copy "Secret address in iCal format"

**Important**: The feed is too large for WebFetch (includes all historical events). Use curl via Bash instead.

## Caching Strategy

Cache extracted events locally to avoid repeated API calls.

### Cache Location & Naming

- **Directory**: `.claude/skills/calendar/cache/`
- **Single day**: `calendar-YYYY-MM-DD.ics`
- **Date range**: `calendar-YYYY-MM-DD-to-YYYY-MM-DD.ics`

### Cache Logic

1. **Past dates**: Always use cache if it exists (events don't change)
2. **Today/future dates**: Check cache file age
   - If cache < 2 hours old → use it
   - If cache ≥ 2 hours old → ask user: "Calendar cache is X hours old. Want me to refresh it?"
3. **User says "refresh"**: Fetch fresh data regardless of cache age

### Fetch & Cache Workflow

1. Determine the date range needed (single day or week)
2. Check if cache file exists for that exact range
3. Apply cache logic (past = use cache, today/future = check age)
4. If fetching fresh:
   - Fetch from API
   - Extract only VEVENT blocks for the requested date range
   - Save extracted events to cache file
5. Read from cache file for all subsequent queries

### Fetching a Date Range

For a week (or multi-day range), fetch the whole range fresh—don't try to merge partial day caches.

To extract events for a date range (e.g., 20260205 to 20260211):

```bash
curl -s "[ICAL_URL]" | awk -v start="20260205" -v end="20260211" '
/BEGIN:VEVENT/ { block = $0; in_block = 1; next }
in_block { block = block "\n" $0 }
/END:VEVENT/ && in_block {
  if (match(block, /DTSTART[^:]*:([0-9]{8})/, arr)) {
    date = arr[1]
    if (date >= start && date <= end) print block
  }
  in_block = 0
}
' > .claude/skills/calendar/cache/calendar-2026-02-05-to-2026-02-11.ics
```

## Supported Queries

When the user asks about `$ARGUMENTS`, determine the query type and respond accordingly:

### View Events
- **today** / **tomorrow** / **[day name]** / **[date]** - Show events for that period
- **this week** / **next week** - Overview of upcoming events
- Example: `/calendar today` or `/calendar friday`

### Find Availability
- **free [date/time]** - Find open time blocks
- **available [date]** - Show gaps between meetings
- Example: `/calendar free thursday afternoon`

### Check Conflicts
- **conflicts [date/time]** - Check if a proposed time overlaps existing events
- Example: `/calendar conflicts friday 2pm`

### Meeting Prep
- **prep** / **prep today** / **prep [date]** - List meetings that need preparation
- For each meeting, identify: who's attending, what context might be needed, any prep materials
- Example: `/calendar prep` (defaults to today)

## How to Process

### Step 1: Fetch events for the target date

**Key lesson**: `DTSTAMP` ≠ `DTSTART`. Every event has a `DTSTAMP` field showing when the feed was generated (today's date), NOT when the event occurs. Always explicitly match `DTSTART` to find events on a specific date.

iCal timestamps come in TWO formats - the awk pattern below catches BOTH:

1. **UTC format**: `DTSTART:YYYYMMDDT...Z` (e.g., `DTSTART:20260205T103000Z`)
2. **Timezone format**: `DTSTART;TZID=...:YYYYMMDD...` (e.g., `DTSTART;TZID=Europe/Lisbon:20260205T090000`)

**Working approach** (replace YYYYMMDD with target date):

```bash
curl -s "[ICAL_URL]" | awk '
/BEGIN:VEVENT/ { block = $0; in_block = 1; next }
in_block { block = block "\n" $0 }
/END:VEVENT/ && in_block {
  if (block ~ /DTSTART[^:]*:YYYYMMDD/) print block
  in_block = 0
}
' | grep -E "(DTSTART|DTEND|SUMMARY|ATTENDEE.*CN=)"
```

This captures complete VEVENT blocks (regardless of size), only prints blocks where DTSTART contains the target date, then extracts the relevant fields. Works reliably even for events with many attendees.

### Step 2: Parse the iCal format

Key fields in each VEVENT:
- `DTSTART` / `DTEND` - Start/end times (check format: Z = UTC, TZID = local)
- `SUMMARY` - Event title
- `ATTENDEE;...CN=name` - Attendee names (CN= is the display name)
- `LOCATION` - Optional location
- `DESCRIPTION` - Optional details (often contains Meet links)
- `STATUS:CONFIRMED` - Event is active (ignore CANCELLED)

### Step 3: Convert times to user's timezone

- **UTC times (ending in Z)**: Convert based on user's timezone and DST
- **TZID=Europe/Lisbon**: Already in that timezone
- **TZID=America/Los_Angeles**: Convert to user's timezone

### Step 4: Filter and format

Based on the query (date range, morning/afternoon, availability, etc.), filter results and present clearly with:
- Date and time (in user's timezone)
- Event title
- Duration
- Location (if present)
- Attendees (if relevant for prep queries)

## Output Format

**For event listings:**
```
## [Date]

- **[Time]** - [Event Title] ([Duration])
  Location: [if present]
```

**For availability:**
```
## Free time on [Date]

- [Start] - [End] ([Duration] available)
```

**For prep:**
```
## Meetings needing prep

### [Event Title] - [Time]
- **Attendees**: [list]
- **Context**: [what this meeting is likely about based on title/attendees]
- **Prep needed**: [suggestions]
```
