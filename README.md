# 🧅 ShallotPeel

**Peel back the layers of your token usage.** A personal dashboard by Shallot that shows you exactly where your Antigravity IDE token and data usage goes — day by day, week by week, tool by tool, and conversation by conversation.

If you use Antigravity IDE and want to understand why your weekly data allotment runs out, or which habits consume the most tokens, ShallotPeel gives you that visibility.

---

## What Does This App Do?

Every time you have a conversation in Antigravity IDE, it creates a log file on your computer. This app **reads those log files** and shows you:

- **How many tokens you've used** in total, per day, and per week
- **Where your data goes** — file reading, code editing, terminal commands, web browsing, etc.
- **Which conversations used the most data** and why
- **Efficiency patterns** — so you can adjust your habits to stay within your weekly budget

Think of it like a "screen time" report, but for your AI coding assistant usage.

---

## How to Use It

You have **two ways** to view your data. No installation or setup is needed — just Python 3.

### Option 1: Visual Web Dashboard (Recommended for First-Time Users)

**Double-click `dashboard.bat`** in this folder.

That's it. A dark-themed interactive dashboard will open in your web browser showing:

- Summary stat cards (total tokens, input vs output, conversations analyzed)
- A "Where Your Data Goes" breakdown with a donut chart
- Daily and weekly bar/line charts
- A searchable, paginated conversation table
- Click any conversation to see exactly which steps consumed the most tokens

If `dashboard.bat` doesn't work, open a terminal in this folder and run:
```
python generate_dashboard.py
```

### Option 2: Terminal Reports (Quick & Lightweight)

**Double-click `run.bat`** for a full text summary, or run specific reports:

```
python tracker.py              # Full summary (daily + weekly + tools + top convos)
python tracker.py --daily      # Day-by-day token usage table
python tracker.py --weekly     # Week-by-week trends
python tracker.py --tools      # Token consumption by tool type
python tracker.py --top 15     # Top 15 heaviest conversations
python tracker.py -c 906245fd  # Inspect one conversation by its ID
```

---

## Understanding the Output

### What Are "Tokens"?

Tokens are the unit of measurement for AI data usage. Roughly:
- **1 token ≈ 4 characters** of text (about ¾ of a word)
- **1,000 tokens ≈ 750 words** (about 1.5 pages of text)
- **100,000 tokens ≈ 75,000 words** (about a short novel)

Every time the AI reads a file, writes code, or responds to you, it consumes tokens. This app estimates your token usage from your local log files.

### What Are "Steps"?

A step is one action in a conversation — you sending a message, the AI responding, reading a file, running a command, etc. A typical conversation has 50–300 steps.

### What Are "Tools"?

Tools are the actions the AI takes during a conversation:

| Tool Name | What It Does | Why It Uses Tokens |
|:---|:---|:---|
| **VIEW_FILE** | Reads a file from your computer | The entire file (or portion) gets loaded into context |
| **CODE_ACTION** | Writes or edits code in your files | The code diff + surrounding context |
| **RUN_COMMAND** | Runs a terminal command | The command output gets loaded into context |
| **GREP_SEARCH** | Searches for text across files | The search results get loaded |
| **BROWSER_SUBAGENT** | Opens and reads web pages | The page content gets loaded |
| **LIST_DIRECTORY** | Lists files in a folder | The file listing gets loaded |

### Key Insight: Where Most Data Goes

Based on typical usage, **~64% of all tool tokens come from VIEW_FILE** — reading files. This means the single biggest way to reduce your data usage is to ask the AI to look at **specific line ranges** rather than entire files.

---

## File Structure

| File | What It Does |
|:---|:---|
| `analyzer.py` | The core engine — reads your log files, parses them, and calculates all the statistics |
| `tracker.py` | The terminal/command-line interface — prints tables and charts in your terminal |
| `generate_dashboard.py` | Generates the interactive HTML dashboard and opens it in your browser |
| `dashboard.html` | The generated dashboard file (auto-created, don't edit manually) |
| `dashboard.bat` | One-click shortcut: generates and opens the web dashboard |
| `run.bat` | One-click shortcut: runs the full terminal report |
| `README.md` | This file — explains how everything works |
| `PROJECT_STATE.md` | Current status of the project — what's working, what's planned |
| `CHANGELOG.md` | History of every change made to this project |

---

## Requirements

- **Python 3.8+** (already installed on your system)
- **No additional packages needed** — everything uses Python's built-in libraries
- **Internet connection** — only needed for the web dashboard (it loads the Chart.js library from a CDN to draw the charts)

---

## Where Does It Read Data From?

Your Antigravity IDE conversation logs are stored at:
```
C:\Users\<your username>\.gemini\antigravity-ide\brain\
```

Each conversation is a folder containing a `transcript.jsonl` file. This app scans all of those files to build its reports. **It only reads data — it never modifies or deletes anything.**

---

## Tips for Reducing Token Usage

1. **Break up long conversations** — start fresh after ~300 steps
2. **Specify line ranges** when asking the AI to look at files (e.g., "look at lines 50–80")
3. **Start with a clear objective** — vague requests lead to wandering, expensive sessions
4. **Don't restart the same task** — if you need a new conversation, summarize what was already done
5. **Use lighter models** for simple tasks (Flash/Sonnet for quick fixes, Opus/Pro for complex work)
