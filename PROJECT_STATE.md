# Project State

> **Last Updated:** September 1, 2026  
> **Version:** 1.1.0  
> **Status:** Fully functional — actively used for personal token usage tracking

---

## What's Working

Everything listed below is complete and working as of the last update.

### Core Analysis Engine (`analyzer.py`)
- [x] Scans all conversation transcripts from `~/.gemini/antigravity-ide/brain/`
- [x] Parses JSONL log files and extracts step-by-step token estimates
- [x] Classifies tokens as Input (context) vs Output (generation) vs Thinking (reasoning)
- [x] Tracks per-tool token consumption (VIEW_FILE, CODE_ACTION, RUN_COMMAND, etc.)
- [x] Aggregates data by day and by week
- [x] Extracts conversation titles from user requests
- [x] Detects model names (Gemini 3, Claude Opus 4, Claude Sonnet 4, etc.)
- [x] Flags "heavy steps" — individual actions that consume over 2,500 tokens

### Terminal CLI (`tracker.py`)
- [x] Full summary report with all key metrics
- [x] Daily token usage table with ASCII bar charts
- [x] Weekly trend table with input/output breakdown
- [x] Tool consumption breakdown with percentages
- [x] Top N heaviest conversations leaderboard
- [x] Single conversation deep-inspection mode (`-c <id>`)
- [x] All reports accessible via command-line flags (`--daily`, `--weekly`, `--tools`, `--top`)
- [x] UTF-8 encoding fix for Windows console output

### Web Dashboard (`generate_dashboard.py` → `dashboard.html`)
- [x] Self-contained HTML file (no build step, no npm, no framework)
- [x] Dark theme with Inter font and modern design
- [x] Summary stat cards (total tokens, input, output, thinking)
- [x] "Where Your Data Goes" hero section with donut chart
- [x] Tool consumption horizontal bar chart
- [x] Daily stacked bar chart (input vs output tokens)
- [x] Weekly trend line chart
- [x] Paginated conversation table (15 per page) with search filtering
- [x] Column sorting (date, title, model, steps, tokens, log size)
- [x] Click-to-inspect modal with per-conversation tool breakdown and heavy steps
- [x] Escape key closes modal
- [x] Fixed chart sizing (no infinite resize loop)

### Shortcuts
- [x] `dashboard.bat` — one-click dashboard generation and browser launch
- [x] `run.bat` — one-click full terminal report

---

## Known Limitations

These are not bugs — they're design trade-offs or things that aren't built yet.

| Limitation | Impact | Notes |
|:---|:---|:---|
| Token counts are **estimates**, not exact | Numbers may differ from actual billing by 10-20% | Uses ~4 chars/token heuristic blended with word count |
| Dashboard requires internet | Won't render charts if offline | Chart.js is loaded from a CDN (`cdn.jsdelivr.net`) |
| No real-time / auto-refresh | You must re-run the script to see new data | Dashboard is a static HTML snapshot at generation time |
| Large log directories may be slow | First scan takes a few seconds with 200+ conversations | ~2-3 seconds for 231 conversations on a typical machine |
| No export to CSV/JSON | Can't currently export the analysis data | Data is embedded in the HTML as JSON; could be extracted |

---

## What's Not Built Yet (Potential Future Ideas)

These are features that could be added but haven't been started:

- [ ] **Budget tracker** — set a weekly token target and see a progress bar
- [ ] **Efficiency scoring** — rate each conversation's efficiency (tokens per step)
- [ ] **Cost estimation** — estimate dollar cost based on model pricing
- [ ] **Offline chart support** — bundle Chart.js locally instead of CDN
- [ ] **Auto-refresh** — watch for new log files and update dashboard automatically
- [ ] **CSV export** — export analysis data to spreadsheet format
- [ ] **Date range filter** — analyze only a specific time period
- [ ] **Conversation comparison** — side-by-side view of two conversations

---

## Architecture Overview

```
You double-click          What happens                     What you see
─────────────────    ─────────────────────────────    ─────────────────────
dashboard.bat    →   Python reads all log files    →  HTML dashboard opens
                     in your brain/ folder              in your browser
                     (analyzer.py)
                           ↓
                     Calculates stats, builds
                     charts data, generates
                     dashboard.html
                     (generate_dashboard.py)

run.bat          →   Same log scanning             →  Tables & charts print
                     (analyzer.py)                      in your terminal
                           ↓                            window
                     Formats and prints reports
                     (tracker.py)
```

---

## File Sizes (Current)

| File | Size | Notes |
|:---|:---|:---|
| `analyzer.py` | ~11.5 KB | Core engine, 286 lines |
| `tracker.py` | ~9.3 KB | CLI interface, 204 lines |
| `generate_dashboard.py` | ~31.8 KB | Dashboard generator, mostly HTML/CSS/JS template |
| `dashboard.html` | ~250 KB | Generated output (large because it embeds all conversation data as JSON) |
