import os
import glob
import json
import re
from datetime import datetime, timezone
from collections import defaultdict

DEFAULT_BRAIN_DIR = os.path.expanduser(r"~\.gemini\antigravity-ide\brain")

def estimate_tokens(text: str) -> int:
    """
    Estimates token count from text using standard ~4 chars per token approximation,
    with word-count fallback.
    """
    if not text:
        return 0
    # Common standard: 1 token ~= 4 chars or 0.75 words
    char_estimate = len(text) / 4.0
    word_estimate = len(text.split()) / 0.75
    # Blend them for a more realistic estimate
    return int((char_estimate * 0.7 + word_estimate * 0.3))

def extract_objective_from_user_input(content: str) -> str:
    """Extracts the core user question or objective from user input XML/markdown."""
    if not content:
        return "Untitled Conversation"
    
    # Check for <USER_REQUEST>...</USER_REQUEST>
    req_match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
    if req_match:
        text = req_match.group(1).strip()
    else:
        text = content.strip()
    
    # Strip markdown headers, tags, leading metadata
    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("```") and not l.startswith("<")]
    if lines:
        summary = lines[0]
        if len(summary) > 80:
            summary = summary[:77] + "..."
        return summary
    return "Untitled Conversation"

class TranscriptAnalyzer:
    def __init__(self, brain_dir: str = DEFAULT_BRAIN_DIR):
        self.brain_dir = os.path.abspath(brain_dir)
        self.conversations = []
        self.daily_stats = defaultdict(lambda: {
            "tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "thinking_tokens": 0,
            "steps": 0,
            "conversations": set(),
            "tool_tokens": defaultdict(int),
            "step_counts": defaultdict(int)
        })
        self.weekly_stats = defaultdict(lambda: {
            "tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "thinking_tokens": 0,
            "steps": 0,
            "conversations": set(),
            "tool_tokens": defaultdict(int),
            "step_counts": defaultdict(int)
        })
        self.tool_breakdown = defaultdict(lambda: {"tokens": 0, "calls": 0, "bytes": 0})
        self.is_loaded = False

    def scan(self, max_conversations=None):
        """Scans all transcripts in brain directory."""
        if not os.path.exists(self.brain_dir):
            return []

        conv_paths = glob.glob(os.path.join(self.brain_dir, "*", ".system_generated", "logs", "transcript.jsonl"))
        self.conversations = []
        self.daily_stats.clear()
        self.weekly_stats.clear()
        self.tool_breakdown.clear()

        for path in conv_paths:
            conv_id = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path))))
            conv_data = self._parse_transcript(conv_id, path)
            if conv_data and conv_data["total_steps"] > 0:
                self.conversations.append(conv_data)
                self._aggregate_conv(conv_data)
            
            if max_conversations and len(self.conversations) >= max_conversations:
                break

        # Sort conversations by start time descending
        self.conversations.sort(key=lambda c: c["start_time"] or "", reverse=True)
        self.is_loaded = True
        return self.conversations

    def _parse_transcript(self, conv_id: str, file_path: str) -> dict:
        total_steps = 0
        total_tokens = 0
        input_tokens = 0
        output_tokens = 0
        thinking_tokens = 0
        total_bytes = 0
        
        start_time = None
        end_time = None
        title = None
        first_user_request = ""
        model_name = "Gemini"
        
        step_breakdown = defaultdict(int)
        tool_counts = defaultdict(int)
        tool_tokens = defaultdict(int)
        heavy_steps = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        step = json.loads(line)
                    except Exception:
                        continue

                    total_steps += 1
                    line_len = len(line)
                    total_bytes += line_len
                    
                    step_type = step.get("type", "UNKNOWN")
                    source = step.get("source", "UNKNOWN")
                    created_at = step.get("created_at")
                    content = step.get("content") or ""
                    thinking = step.get("thinking") or ""
                    tool_calls = step.get("tool_calls") or []

                    if created_at:
                        if not start_time:
                            start_time = created_at
                        end_time = created_at

                    # Check for model settings in USER_INPUT
                    if step_type == "USER_INPUT" and "<USER_SETTINGS_CHANGE>" in content:
                        model_match = re.search(r"Model Selection` from None to ([^\.\n]+)", content)
                        if model_match:
                            model_name = model_match.group(1).strip()

                    # Extract first title/objective
                    if step_type == "USER_INPUT" and not first_user_request:
                        first_user_request = extract_objective_from_user_input(content)
                    elif step_type == "CHECKPOINT" and not title and "# USER Objective:" in content:
                        obj_match = re.search(r"# USER Objective:\s*([^\n]+)", content)
                        if obj_match:
                            title = obj_match.group(1).strip()

                    # Estimate tokens
                    content_tok = estimate_tokens(content)
                    thinking_tok = estimate_tokens(thinking)
                    tool_calls_tok = estimate_tokens(json.dumps(tool_calls)) if tool_calls else 0
                    step_tok = content_tok + thinking_tok + tool_calls_tok

                    total_tokens += step_tok
                    thinking_tokens += thinking_tok

                    # Classify input vs output
                    if source in ("USER_EXPLICIT", "SYSTEM") or step_type in ("VIEW_FILE", "RUN_COMMAND", "GREP_SEARCH", "LIST_DIRECTORY"):
                        input_tokens += step_tok
                    else: # MODEL
                        output_tokens += step_tok

                    # Track step types and tools
                    step_breakdown[step_type] += 1
                    
                    if step_type in ("VIEW_FILE", "RUN_COMMAND", "GREP_SEARCH", "LIST_DIRECTORY", "BROWSER_SUBAGENT", "CODE_ACTION"):
                        tool_counts[step_type] += 1
                        tool_tokens[step_type] += step_tok
                    
                    for tc in tool_calls:
                        tc_name = tc.get("name", "tool")
                        tool_counts[tc_name] += 1

                    # Flag heavy steps (> 2,500 tokens in a single step)
                    if step_tok >= 2500:
                        heavy_steps.append({
                            "step_index": step.get("step_index", total_steps - 1),
                            "type": step_type,
                            "source": source,
                            "tokens": step_tok,
                            "snippet": (content[:120] + "...") if len(content) > 120 else content
                        })

        except Exception as e:
            return None

        if not title:
            title = first_user_request or f"Conversation {conv_id[:8]}"

        # Sort heavy steps by token count descending
        heavy_steps.sort(key=lambda s: s["tokens"], reverse=True)

        return {
            "id": conv_id,
            "title": title,
            "model": model_name,
            "start_time": start_time,
            "end_time": end_time,
            "total_steps": total_steps,
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "thinking_tokens": thinking_tokens,
            "total_bytes": total_bytes,
            "step_breakdown": dict(step_breakdown),
            "tool_counts": dict(tool_counts),
            "tool_tokens": dict(tool_tokens),
            "heavy_steps": heavy_steps[:10]
        }

    def _aggregate_conv(self, conv: dict):
        start_time_str = conv.get("start_time")
        if not start_time_str:
            return

        try:
            # Parse ISO date (e.g. 2026-09-01T14:31:14Z or with offset)
            clean_ts = start_time_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_ts)
            day_key = dt.strftime("%Y-%m-%d")
            # Format week as YYYY-Www (e.g., 2026-W36)
            week_key = dt.strftime("%Y-W%U")
        except Exception:
            return

        # Daily aggregation
        d = self.daily_stats[day_key]
        d["tokens"] += conv["total_tokens"]
        d["input_tokens"] += conv["input_tokens"]
        d["output_tokens"] += conv["output_tokens"]
        d["thinking_tokens"] += conv["thinking_tokens"]
        d["steps"] += conv["total_steps"]
        d["conversations"].add(conv["id"])
        for tool, toks in conv["tool_tokens"].items():
            d["tool_tokens"][tool] += toks
        for stype, cnt in conv["step_breakdown"].items():
            d["step_counts"][stype] += cnt

        # Weekly aggregation
        w = self.weekly_stats[week_key]
        w["tokens"] += conv["total_tokens"]
        w["input_tokens"] += conv["input_tokens"]
        w["output_tokens"] += conv["output_tokens"]
        w["thinking_tokens"] += conv["thinking_tokens"]
        w["steps"] += conv["total_steps"]
        w["conversations"].add(conv["id"])
        for tool, toks in conv["tool_tokens"].items():
            w["tool_tokens"][tool] += toks
        for stype, cnt in conv["step_breakdown"].items():
            w["step_counts"][stype] += cnt

        # Global tool breakdown
        for tool, toks in conv["tool_tokens"].items():
            self.tool_breakdown[tool]["tokens"] += toks
            self.tool_breakdown[tool]["calls"] += conv["tool_counts"].get(tool, 1)

    def get_summary_metrics(self) -> dict:
        """Returns high-level overall metrics."""
        total_convs = len(self.conversations)
        total_tokens = sum(c["total_tokens"] for c in self.conversations)
        total_input = sum(c["input_tokens"] for c in self.conversations)
        total_output = sum(c["output_tokens"] for c in self.conversations)
        total_thinking = sum(c["thinking_tokens"] for c in self.conversations)
        total_steps = sum(c["total_steps"] for c in self.conversations)
        total_bytes = sum(c["total_bytes"] for c in self.conversations)

        return {
            "total_conversations": total_convs,
            "total_tokens": total_tokens,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_thinking_tokens": total_thinking,
            "total_steps": total_steps,
            "total_bytes": total_bytes,
            "avg_tokens_per_conv": int(total_tokens / total_convs) if total_convs else 0,
            "avg_steps_per_conv": round(total_steps / total_convs, 1) if total_convs else 0
        }
