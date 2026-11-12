"""
agy_detector.py - Detect Agy CLI executable, version, and data directories.
"""
import os
import shutil
import subprocess
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgyInfo:
    executable: str = ""
    version: str = ""
    data_dir: str = ""
    conversations_dir: str = ""
    brain_dir: str = ""
    summaries_db: str = ""
    history_file: str = ""
    settings_file: str = ""
    available: bool = False
    supports_conversation: bool = False
    supports_skip_permissions: bool = False
    supports_continue: bool = False
    help_text: str = ""


def detect_agy() -> AgyInfo:
    """Detect Agy CLI installation and capabilities."""
    info = AgyInfo()

    # 1. Find executable
    exe = shutil.which("agy")
    if not exe:
        # Check common locations
        candidates = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "agy", "bin", "agy.exe"),
            os.path.join(os.environ.get("USERPROFILE", ""), ".agy", "bin", "agy.exe"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                exe = c
                break

    if not exe:
        return info

    info.executable = exe
    info.available = True

    # 2. Get version
    try:
        result = subprocess.run(
            [exe, "--version"],
            capture_output=True, text=True, timeout=10
        )
        version_text = (result.stdout + result.stderr).strip()
        # Version is usually a line like "1.4.0"
        for line in version_text.splitlines():
            line = line.strip()
            if line and line[0].isdigit():
                info.version = line
                break
    except Exception:
        pass

    # 3. Get help text and check capabilities
    try:
        result = subprocess.run(
            [exe, "--help"],
            capture_output=True, text=True, timeout=10
        )
        info.help_text = result.stdout + result.stderr
        help_lower = info.help_text.lower()
        info.supports_conversation = "--conversation" in info.help_text
        info.supports_skip_permissions = "--dangerously-skip-permissions" in info.help_text
        info.supports_continue = "--continue" in info.help_text
    except Exception:
        pass

    # 4. Locate data directory
    data_dir = os.path.join(
        os.environ.get("USERPROFILE", os.path.expanduser("~")),
        ".gemini", "antigravity-cli"
    )
    if os.path.isdir(data_dir):
        info.data_dir = data_dir
        info.conversations_dir = os.path.join(data_dir, "conversations")
        info.brain_dir = os.path.join(data_dir, "brain")
        info.summaries_db = os.path.join(data_dir, "conversation_summaries.db")
        info.history_file = os.path.join(data_dir, "history.jsonl")
        info.settings_file = os.path.join(data_dir, "settings.json")

    return info
