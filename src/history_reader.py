"""
history_reader.py - Read and parse transcript.jsonl for chat history display.
"""
import os
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ChatMessage:
    step_index: int = 0
    source: str = ""         # USER_EXPLICIT, MODEL, SYSTEM
    msg_type: str = ""       # USER_INPUT, PLANNER_RESPONSE, GENERIC
    status: str = ""
    created_at: str = ""
    content: str = ""
    thinking: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    has_media: bool = False

    @property
    def is_user(self) -> bool:
        return self.source == "USER_EXPLICIT" or self.msg_type == "USER_INPUT"

    @property
    def is_assistant(self) -> bool:
        return self.source == "MODEL" or self.msg_type == "PLANNER_RESPONSE"

    @property
    def is_system(self) -> bool:
        return self.source == "SYSTEM"

    @property
    def is_tool_result(self) -> bool:
        return self.msg_type == "GENERIC" and self.source == "MODEL"

    @property
    def role_display(self) -> str:
        if self.is_user:
            return "User"
        elif self.is_assistant:
            return "Assistant"
        elif self.is_system:
            return "System"
        return self.source or "Unknown"

    @property
    def time_display(self) -> str:
        if not self.created_at:
            return ""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
            return dt.strftime("%H:%M:%S")
        except Exception:
            return self.created_at

    @property
    def clean_content(self) -> str:
        """Remove XML-like wrapper tags from user content."""
        text = self.content or ""
        # Strip <USER_REQUEST> tags
        text = text.replace("<USER_REQUEST>", "").replace("</USER_REQUEST>", "")
        # Strip <ADDITIONAL_METADATA> blocks
        import re
        text = re.sub(
            r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>",
            "", text, flags=re.DOTALL
        )
        text = re.sub(
            r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>",
            "", text, flags=re.DOTALL
        )
        return text.strip()


# Cache for parsed transcripts: key -> {"mtime": float, "messages": List[ChatMessage]}
_TRANSCRIPT_CACHE: Dict[str, Dict[str, Any]] = {}


def clear_transcript_cache():
    """Clear in-memory transcript cache."""
    _TRANSCRIPT_CACHE.clear()


def read_transcript(brain_dir: str, conversation_id: str,
                    use_full: bool = False) -> List[ChatMessage]:
    """Read transcript.jsonl for a conversation and return chat messages."""
    messages = []

    filename = "transcript_full.jsonl" if use_full else "transcript.jsonl"
    transcript_path = os.path.join(
        brain_dir, conversation_id,
        ".system_generated", "logs", filename
    )

    if not os.path.isfile(transcript_path):
        # Fallback to other file
        alt = "transcript.jsonl" if use_full else "transcript_full.jsonl"
        alt_path = os.path.join(
            brain_dir, conversation_id,
            ".system_generated", "logs", alt
        )
        if os.path.isfile(alt_path):
            transcript_path = alt_path
        else:
            return messages

    try:
        mtime = os.path.getmtime(transcript_path)
        cache_key = f"{conversation_id}_{os.path.basename(transcript_path)}"
        cached = _TRANSCRIPT_CACHE.get(cache_key)
        if cached and cached.get("mtime") == mtime:
            return cached.get("messages", [])

        with open(transcript_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    msg = ChatMessage(
                        step_index=data.get("step_index", line_num),
                        source=data.get("source", ""),
                        msg_type=data.get("type", ""),
                        status=data.get("status", ""),
                        created_at=data.get("created_at", ""),
                        content=data.get("content", ""),
                        thinking=data.get("thinking", ""),
                        input_tokens=data.get("input_tokens", 0),
                        output_tokens=data.get("output_tokens", 0),
                    )

                    # Parse tool calls
                    tc = data.get("tool_calls")
                    if tc and isinstance(tc, list):
                        msg.tool_calls = tc

                    # Check media
                    if data.get("media"):
                        msg.has_media = True

                    messages.append(msg)
                except json.JSONDecodeError:
                    continue

        _TRANSCRIPT_CACHE[cache_key] = {"mtime": mtime, "messages": messages}
    except Exception as e:
        print(f"Error reading transcript: {e}")

    return messages


def get_first_user_message(messages: List[ChatMessage]) -> str:
    """Extract the first user message content from a transcript."""
    for msg in messages:
        if msg.is_user and msg.clean_content:
            content = msg.clean_content
            if len(content) > 200:
                return content[:200] + "..."
            return content
    return ""


def count_messages_by_role(messages: List[ChatMessage]) -> Dict[str, int]:
    """Count messages by role."""
    counts = {"user": 0, "assistant": 0, "system": 0, "tool": 0}
    for msg in messages:
        if msg.is_user:
            counts["user"] += 1
        elif msg.is_assistant:
            counts["assistant"] += 1
        elif msg.is_system:
            counts["system"] += 1
        elif msg.is_tool_result:
            counts["tool"] += 1
    return counts
