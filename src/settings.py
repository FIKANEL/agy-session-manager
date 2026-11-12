"""
settings.py - User preferences and configuration persistence.
"""
import os
import json
from dataclasses import dataclass, asdict
from typing import Optional


SETTINGS_DIR = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    "AgySessionManager"
)
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")


@dataclass
class AppSettings:
    agy_executable: str = ""
    default_working_directory: str = ""
    theme: str = "dark"       # "dark" or "light"
    show_subagents: bool = False
    min_steps_filter: int = 0
    sort_by: str = "last_modified"
    window_width: int = 1400
    window_height: int = 850
    splitter_sizes: list = None
    last_search: str = ""
    terminal_preference: str = "auto"  # "auto", "wt", "pwsh", "powershell"
    starred_sessions: list = None      # List[str] of conversation_ids
    custom_titles: dict = None         # Dict[str, str] of conversation_id -> custom_title
    forked_sessions: dict = None       # Dict[str, dict] of conversation_id -> fork metadata
    trashed_sessions: dict = None      # Dict[str, dict] of conversation_id -> {"trashed_at": str, "title": str}

    def __post_init__(self):
        if self.splitter_sizes is None:
            self.splitter_sizes = [220, 380, 800]
        if self.starred_sessions is None:
            self.starred_sessions = []
        if self.custom_titles is None:
            self.custom_titles = {}
        if self.forked_sessions is None:
            self.forked_sessions = {}
        if self.trashed_sessions is None:
            self.trashed_sessions = {}

    def is_starred(self, conversation_id: str) -> bool:
        """Check if a conversation ID is starred. Forks inherit parent's star status."""
        if conversation_id in (self.starred_sessions or []):
            return True
        fork_info = self.get_fork_info(conversation_id)
        if fork_info and fork_info.get("parent_id"):
            return fork_info.get("parent_id") in (self.starred_sessions or [])
        return False

    def toggle_star(self, conversation_id: str) -> bool:
        """Toggle starred status for a conversation ID. For forks, syncs with parent thread."""
        if self.starred_sessions is None:
            self.starred_sessions = []
        target_id = conversation_id
        fork_info = self.get_fork_info(conversation_id)
        if fork_info and fork_info.get("parent_id"):
            target_id = fork_info.get("parent_id")

        if target_id in self.starred_sessions:
            self.starred_sessions.remove(target_id)
            if conversation_id in self.starred_sessions:
                self.starred_sessions.remove(conversation_id)
            return False
        else:
            self.starred_sessions.append(target_id)
            if conversation_id not in self.starred_sessions:
                self.starred_sessions.append(conversation_id)
            return True

    def get_custom_title(self, conversation_id: str) -> Optional[str]:
        """Get custom renamed title for a conversation ID, or None."""
        if not self.custom_titles:
            return None
        return self.custom_titles.get(conversation_id)

    def set_custom_title(self, conversation_id: str, title: str):
        """Set or remove custom renamed title for a conversation ID."""
        if self.custom_titles is None:
            self.custom_titles = {}
        cleaned = title.strip()
        if cleaned:
            self.custom_titles[conversation_id] = cleaned
        else:
            self.custom_titles.pop(conversation_id, None)

    def record_fork(self, new_id: str, parent_id: str, parent_title: str):
        """Record metadata for a newly forked session."""
        if self.forked_sessions is None:
            self.forked_sessions = {}
        from datetime import datetime
        self.forked_sessions[new_id] = {
            "parent_id": parent_id,
            "parent_title": parent_title,
            "forked_at": datetime.now().isoformat(),
        }

    def get_fork_info(self, conversation_id: str) -> Optional[dict]:
        """Retrieve fork metadata for a conversation ID."""
        if not self.forked_sessions:
            return None
        return self.forked_sessions.get(conversation_id)

    def is_fork(self, conversation_id: str) -> bool:
        """Check if a conversation ID was recorded as a fork."""
        return bool(self.forked_sessions and conversation_id in self.forked_sessions)

    def is_trashed(self, conversation_id: str) -> bool:
        """Check if a session (or its parent) is in Trash."""
        if not self.trashed_sessions:
            return False
        if conversation_id in self.trashed_sessions:
            return True
        fork_info = self.get_fork_info(conversation_id)
        if fork_info and fork_info.get("parent_id"):
            return fork_info.get("parent_id") in self.trashed_sessions
        return False

    def move_to_trash(self, conversation_id: str, title: str = ""):
        """Move a conversation ID (and any child forks) into Trash."""
        if self.trashed_sessions is None:
            self.trashed_sessions = {}
        from datetime import datetime
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.trashed_sessions[conversation_id] = {
            "trashed_at": now_str,
            "title": title
        }
        # If this is a parent, also trash all its child forks
        if self.forked_sessions:
            for child_id, info in self.forked_sessions.items():
                if info.get("parent_id") == conversation_id:
                    self.trashed_sessions[child_id] = {
                        "trashed_at": now_str,
                        "title": info.get("parent_title", "")
                    }

    def restore_from_trash(self, conversation_id: str):
        """Restore a conversation ID (and its parent/forks) from Trash."""
        if not self.trashed_sessions:
            return
        self.trashed_sessions.pop(conversation_id, None)
        # If it's a fork, also ensure parent is restored
        fork_info = self.get_fork_info(conversation_id)
        if fork_info and fork_info.get("parent_id"):
            parent_id = fork_info.get("parent_id")
            self.trashed_sessions.pop(parent_id, None)
        # If it's a parent, restore its child forks
        if self.forked_sessions:
            for child_id, info in self.forked_sessions.items():
                if info.get("parent_id") == conversation_id:
                    self.trashed_sessions.pop(child_id, None)

    def purge_from_settings(self, conversation_id: str):
        """Completely remove all metadata references to a permanently deleted session."""
        if self.trashed_sessions:
            self.trashed_sessions.pop(conversation_id, None)
        if self.starred_sessions and conversation_id in self.starred_sessions:
            self.starred_sessions.remove(conversation_id)
        if self.custom_titles:
            self.custom_titles.pop(conversation_id, None)
        if self.forked_sessions:
            self.forked_sessions.pop(conversation_id, None)
            # If deleted session was a parent, detach remaining forks so they become root sessions
            for child_id, info in list(self.forked_sessions.items()):
                if info.get("parent_id") == conversation_id:
                    self.forked_sessions.pop(child_id, None)


def load_settings() -> AppSettings:
    """Load settings from disk with fallback to backup."""
    settings = AppSettings()
    file_to_load = SETTINGS_FILE
    if not os.path.isfile(file_to_load) and os.path.isfile(f"{SETTINGS_FILE}.bak"):
        file_to_load = f"{SETTINGS_FILE}.bak"
    if os.path.isfile(file_to_load):
        try:
            with open(file_to_load, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key, value in data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        except Exception:
            pass
    return settings


def save_settings(settings: AppSettings):
    """Save settings to disk with automatic backup."""
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    try:
        if os.path.isfile(SETTINGS_FILE):
            import shutil
            try:
                shutil.copy2(SETTINGS_FILE, f"{SETTINGS_FILE}.bak")
            except Exception:
                pass
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")
