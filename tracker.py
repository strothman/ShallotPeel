#!/usr/bin/env python3
"""
Antigravity IDE - Token & Data Usage Tracker
Analyzes transcript logs from ~/.gemini/antigravity-ide/brain/
"""

import sys
import os
import argparse

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from analyzer import TranscriptAnalyzer, DEFAULT_BRAIN_DIR

def format_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}k"
    return str(n)

def format_bytes(n: int) -> str:
    if n >= 1024 * 1024 * 1024:
        return f"{n / (1024**3):.2f} GB"
    elif n >= 1024 * 1024:
        return f"{n / (1024**2):.2f} MB"
    elif n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} B"

def render_bar(val: int, max_val: int, width: int = 25) -> str:
    if max_val <= 0:
        return ""
    fill = int((val / max_val) * width)
    return "#" * fill + "-" * (width - fill)

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def print_summary(analyzer: TranscriptAnalyzer):
    metrics = analyzer.get_summary_metrics()
    print_header("[*] ANTIGRAVITY IDE TOKEN & USAGE SUMMARY")
    print(f" Total Analyzed Conversations : {metrics['total_conversations']:,}")
    print(f" Total Estimated Tokens      : {metrics['total_tokens']:,} (~{format_tokens(metrics['total_tokens'])})")
    print(f"   |-- Input / Context Tokens : {metrics['total_input_tokens']:,} ({metrics['total_input_tokens']/(metrics['total_tokens'] or 1)*100:.1f}%)")
    print(f"   |-- Output Tokens          : {metrics['total_output_tokens']:,} ({metrics['total_output_tokens']/(metrics['total_tokens'] or 1)*100:.1f}%)")
    print(f"   \\-- Thinking / Reasoning   : {metrics['total_thinking_tokens']:,} ({metrics['total_thinking_tokens']/(metrics['total_tokens'] or 1)*100:.1f}%)")
    print(f" Total Interaction Steps     : {metrics['total_steps']:,}")
    print(f" Raw Log File Size on Disk   : {format_bytes(metrics['total_bytes'])}")
    print(f" Average Tokens / Convo      : {metrics['avg_tokens_per_conv']:,}")
    print(f" Average Steps / Convo       : {metrics['avg_steps_per_conv']}")
    print("=" * 80)

def print_daily(analyzer: TranscriptAnalyzer, limit: int = 14):
    print_header(f"[+] DAILY TOKEN USAGE (LAST {limit} ACTIVE DAYS)")
    days = sorted(analyzer.daily_stats.keys(), reverse=True)[:limit]
    if not days:
        print(" No daily records found.")
        return

    days = list(reversed(days)) # Oldest to newest for visual graph
    max_tokens = max((analyzer.daily_stats[d]["tokens"] for d in days), default=1)

    print(f"{'Date':<12} | {'Convs':<5} | {'Steps':<6} | {'Tokens':<10} | {'Visual Usage':<25}")
    print("-" * 80)
    for d in days:
        data = analyzer.daily_stats[d]
        tok = data["tokens"]
        bar = render_bar(tok, max_tokens, 25)
        print(f"{d:<12} | {len(data['conversations']):<5} | {data['steps']:<6} | {format_tokens(tok):<10} | {bar}")

def print_weekly(analyzer: TranscriptAnalyzer, limit: int = 12):
    print_header(f"[+] WEEK-BY-WEEK TOKEN USAGE (LAST {limit} WEEKS)")
    weeks = sorted(analyzer.weekly_stats.keys(), reverse=True)[:limit]
    if not weeks:
        print(" No weekly records found.")
        return

    weeks = list(reversed(weeks))
    max_tokens = max((analyzer.weekly_stats[w]["tokens"] for w in weeks), default=1)

    print(f"{'Week':<12} | {'Convs':<5} | {'Steps':<6} | {'Tokens':<10} | {'Input / Output':<15} | {'Visual Usage':<20}")
    print("-" * 80)
    for w in weeks:
        data = analyzer.weekly_stats[w]
        tok = data["tokens"]
        bar = render_bar(tok, max_tokens, 20)
        in_out = f"{format_tokens(data['input_tokens'])} / {format_tokens(data['output_tokens'])}"
        print(f"{w:<12} | {len(data['conversations']):<5} | {data['steps']:<6} | {format_tokens(tok):<10} | {in_out:<15} | {bar}")

def print_tools(analyzer: TranscriptAnalyzer):
    print_header("[+] DATA & TOKEN CONSUMPTION BY TOOL / OPERATION")
    tools = sorted(analyzer.tool_breakdown.items(), key=lambda x: x[1]["tokens"], reverse=True)
    if not tools:
        print(" No tool statistics found.")
        return

    max_tool_tok = max((item[1]["tokens"] for item in tools), default=1)
    print(f"{'Tool / Action':<22} | {'Invocations':<11} | {'Total Tokens':<12} | {'Share %':<8} | {'Visual'}")
    print("-" * 80)
    
    total_tool_tok = sum(item[1]["tokens"] for item in tools) or 1
    for tool_name, data in tools:
        tok = data["tokens"]
        calls = data["calls"]
        pct = (tok / total_tool_tok) * 100
        bar = render_bar(tok, max_tool_tok, 18)
        print(f"{tool_name:<22} | {calls:<11} | {format_tokens(tok):<12} | {pct:>6.1f}% | {bar}")

def print_top_conversations(analyzer: TranscriptAnalyzer, top_n: int = 10):
    print_header(f"[+] TOP {top_n} LARGEST CONVERSATIONS (HIGHEST TOKEN USAGE)")
    sorted_convs = sorted(analyzer.conversations, key=lambda c: c["total_tokens"], reverse=True)[:top_n]
    
    print(f"{'#':<3} | {'Tokens':<9} | {'Steps':<5} | {'Date':<10} | {'ID':<10} | {'Title / Objective'}")
    print("-" * 80)
    for idx, c in enumerate(sorted_convs, 1):
        date_str = c["start_time"][:10] if c.get("start_time") else "Unknown"
        title_snip = c["title"][:38] + ("..." if len(c["title"]) > 38 else "")
        print(f"{idx:<3} | {format_tokens(c['total_tokens']):<9} | {c['total_steps']:<5} | {date_str:<10} | {c['id'][:8]:<10} | {title_snip}")

def print_conversation_detail(analyzer: TranscriptAnalyzer, conv_id: str):
    matches = [c for c in analyzer.conversations if c["id"].startswith(conv_id)]
    if not matches:
        print(f"[!] No conversation found matching prefix: {conv_id}")
        return
    c = matches[0]

    print_header(f"[*] CONVERSATION INSPECTION: {c['id']}")
    print(f" Title       : {c['title']}")
    print(f" Start Time  : {c['start_time']}")
    print(f" End Time    : {c['end_time']}")
    print(f" Model       : {c['model']}")
    print(f" Total Steps : {c['total_steps']:,}")
    print(f" Total Tokens: {c['total_tokens']:,} (~{format_tokens(c['total_tokens'])})")
    print(f"   |-- Input Tokens  : {c['input_tokens']:,} ({c['input_tokens']/(c['total_tokens'] or 1)*100:.1f}%)")
    print(f"   |-- Output Tokens : {c['output_tokens']:,} ({c['output_tokens']/(c['total_tokens'] or 1)*100:.1f}%)")
    print(f"   \\-- Thinking      : {c['thinking_tokens']:,}")

    if c["tool_tokens"]:
        print("\n [*] Tool Token Breakdown:")
        for tname, ttok in sorted(c["tool_tokens"].items(), key=lambda x: x[1], reverse=True):
            print(f"   * {tname:<20} : {format_tokens(ttok):>8} tokens ({c['tool_counts'].get(tname, 0)} calls)")

    if c["heavy_steps"]:
        print("\n [!] Heaviest Individual Steps (>2.5k tokens):")
        for hs in c["heavy_steps"]:
            print(f"   * Step #{hs['step_index']:<3} [{hs['type']:<16}] : {format_tokens(hs['tokens']):>7} tokens | {hs['snippet']}")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="ShallotPeel — Peel back the layers of your token usage")
    parser.add_argument("--daily", action="store_true", help="Display daily token usage")
    parser.add_argument("--weekly", action="store_true", help="Display week-by-week trends")
    parser.add_argument("--top", type=int, nargs="?", const=10, help="Show top N token-heavy conversations (default: 10)")
    parser.add_argument("--tools", action="store_true", help="Show token breakdown by tool/operation")
    parser.add_argument("--conversation", "-c", type=str, help="Inspect a specific conversation ID or prefix")
    parser.add_argument("--dashboard", "-d", action="store_true", help="Generate interactive HTML dashboard")
    parser.add_argument("--all", "-a", action="store_true", help="Show all terminal reports (Daily, Weekly, Tools, Top Convs)")
    parser.add_argument("--brain-dir", type=str, default=DEFAULT_BRAIN_DIR, help="Path to Antigravity brain logs")

    args = parser.parse_args()

    print(f"Scanning transcript logs in {args.brain_dir} ...")
    analyzer = TranscriptAnalyzer(brain_dir=args.brain_dir)
    analyzer.scan()

    if args.dashboard:
        from generate_dashboard import build_and_open_dashboard
        build_and_open_dashboard(analyzer)
        return

    if args.conversation:
        print_conversation_detail(analyzer, args.conversation)
        return

    # If no flags or --all, show comprehensive report
    if args.all or not any([args.daily, args.weekly, args.top is not None, args.tools]):
        print_summary(analyzer)
        print_daily(analyzer, limit=7)
        print_weekly(analyzer, limit=8)
        print_tools(analyzer)
        print_top_conversations(analyzer, top_n=10)
        print("\nRun `python tracker.py --dashboard` or click `dashboard.bat` to launch the visual web viewer!")
    else:
        print_summary(analyzer)
        if args.daily:
            print_daily(analyzer)
        if args.weekly:
            print_weekly(analyzer)
        if args.tools:
            print_tools(analyzer)
        if args.top is not None:
            print_top_conversations(analyzer, top_n=args.top)

if __name__ == "__main__":
    main()
