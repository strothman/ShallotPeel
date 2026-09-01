# Changelog

All notable changes to the ShallotPeel project are documented here.

Each entry lists the date, what changed, and why — written so that anyone can understand it without needing to read the code.

---

## [1.1.0] — September 1, 2026

### What Changed

This was a major overhaul of the web dashboard. The old version had critical bugs that made it unusable.

### Dashboard — Complete Rebuild (`generate_dashboard.py`)

**Fixed: Infinite page resizing / refresh loop**
- The old dashboard used Chart.js charts without fixed-size containers. This caused the browser's resize observer to fire continuously — the charts would grow taller, triggering a resize, which made them grow taller again, forever. The page would become thousands of pixels tall and keep flickering.
- **Fix:** Every chart canvas is now wrapped in a container with `position: relative` and a fixed `height` (300px for most charts, 260px for the weekly chart, 220px for the donut). This gives Chart.js a stable reference size so it stops resizing.

**Fixed: Extremely tall, unreadable conversation table**
- The old table rendered all 231 conversations in one giant list with no pagination. On a typical screen, you'd have to scroll for ages to find anything.
- **Fix:** Added proper pagination — 15 conversations per page with Previous/Next buttons and a page counter ("Showing 1–15 of 231 conversations"). Search filtering still works across all conversations.

**Added: "Where Your Data Goes" hero section**
- New prominent section at the top of the dashboard with a donut chart showing the tool consumption breakdown (VIEW_FILE 64%, CODE_ACTION 20%, RUN_COMMAND 9%, etc.)
- Includes a plain-English explanation and color-coded breakdown pills

**Added: Modern design refresh**
- Switched to Inter font (loaded from Google Fonts)
- Added hover animations on stat cards
- Improved table styling with header row background, hover states, and proper column spacing
- Status pill in header shows conversation count
- Max-width container (1400px) to prevent ultra-wide layouts on large monitors

**Added: Better modal details**
- Tool breakdown in the inspection modal now sorts by highest token consumption first
- Heavy steps show in a cleaner layout with side-by-side step number and token badge

**Added: Keyboard shortcut**
- Pressing `Escape` now closes the conversation detail modal

**Fixed: Unicode crash on Windows**
- The old code printed a `✅` checkmark emoji to console, which crashed on Windows terminals using the CP1252 encoding. Replaced with `[OK]`.

### No Changes to Other Files
- `analyzer.py` — no changes (core engine unchanged)
- `tracker.py` — no changes (terminal CLI unchanged)
- `dashboard.bat` / `run.bat` — no changes

---

## [1.0.0] — September 1, 2026

### Initial Release

The first working version of ShallotPeel, built as a single conversation.

### Core Analysis Engine (`analyzer.py`)
- Scans all conversation transcript logs from `~/.gemini/antigravity-ide/brain/`
- Parses JSONL (JSON Lines) files — each line is one step in a conversation
- Estimates token counts using a blended heuristic: 70% character-based (~4 chars/token) + 30% word-based (~0.75 words/token)
- Classifies each step as input (things the AI reads) or output (things the AI writes)
- Tracks which "tools" the AI used (VIEW_FILE, CODE_ACTION, RUN_COMMAND, GREP_SEARCH, BROWSER_SUBAGENT, LIST_DIRECTORY) and how many tokens each consumed
- Aggregates stats by day and by ISO week
- Extracts conversation titles from the first user message or checkpoint metadata
- Detects which AI model was used per conversation
- Flags "heavy steps" — any single step consuming over 2,500 tokens

### Terminal CLI (`tracker.py`)
- `python tracker.py` — prints a full summary with daily, weekly, tool, and top conversation reports
- `python tracker.py --daily` — shows a day-by-day table with ASCII bar chart
- `python tracker.py --weekly` — shows week-by-week trends with input/output split
- `python tracker.py --tools` — shows token consumption ranked by tool type
- `python tracker.py --top N` — lists the N most token-heavy conversations
- `python tracker.py -c <id>` — deep-inspects a single conversation by ID prefix
- `python tracker.py --dashboard` — generates and opens the web dashboard
- Includes UTF-8 encoding fix for Windows consoles

### Web Dashboard (`generate_dashboard.py`)
- Generates a single self-contained `dashboard.html` file
- Dark theme with gradient header
- Summary stat cards (total tokens, input, output, conversations)
- Daily stacked bar chart (input vs output tokens per day)
- Weekly line chart showing consumption trajectory
- Horizontal bar chart for tool token breakdown
- Full conversation table with search and column sorting
- Click-to-inspect modal showing per-conversation tool usage and heaviest steps

### Shortcuts
- `dashboard.bat` — double-click to generate and open the web dashboard
- `run.bat` — double-click to run the full terminal report
