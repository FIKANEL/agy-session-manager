"""
session_discovery.py - Discover sessions from Agy conversation_summaries.db
"""
import sqlite3
import os
import json
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class SessionInfo:
    conversation_id: str = ""
    title: str = ""
    preview: str = ""
    step_count: int = 0
    last_modified: str = ""
    last_modified_dt: Optional[datetime] = None
    workspace_uris: List[str] = None
    status: str = ""
    source: str = ""
    project_id: str = ""
    agent_name: str = ""
    parent_conversation_id: str = ""
    nesting_depth: int = 0
    killed: bool = False
    last_user_input_time: str = ""
    has_transcript: bool = False
    has_conversation_db: bool = False
    db_file_size: int = 0
    custom_title: str = ""
    is_starred: bool = False
    is_fork: bool = False
    fork_parent_id: str = ""
    fork_parent_title: str = ""

    def __post_init__(self):
        if self.workspace_uris is None:
            self.workspace_uris = []
        if self.parent_conversation_id and not self.fork_parent_id:
            self.fork_parent_id = self.parent_conversation_id
            self.is_fork = True

    @property
    def display_title(self) -> str:
        return self.custom_title or self.preview or self.title or f"Session {self.conversation_id[:8]}..."

    @property
    def original_title(self) -> str:
        return self.preview or self.title or f"Session {self.conversation_id[:8]}..."

    @property
    def short_id(self) -> str:
        return self.conversation_id[:8] if self.conversation_id else ""

    @property
    def workspace_display(self) -> str:
        if not self.workspace_uris:
            return ""
        # Decode file:// URIs
        from urllib.parse import unquote, urlparse
        paths = []
        for uri in self.workspace_uris:
            try:
                parsed = urlparse(uri)
                path = unquote(parsed.path)
                # Remove leading / on Windows paths like /c:/...
                if len(path) > 2 and path[0] == '/' and path[2] == ':':
                    path = path[1:]
                paths.append(path)
            except Exception:
                paths.append(uri)
        return ", ".join(paths)

    @property
    def last_modified_display(self) -> str:
        if self.last_modified_dt:
            return self.last_modified_dt.strftime("%Y-%m-%d %H:%M")
        return self.last_modified or ""


def discover_sessions(summaries_db: str, conversations_dir: str = "",
                      brain_dir: str = "") -> List[SessionInfo]:
    """Read all sessions from conversation_summaries.db."""
    sessions = []

    if not os.path.isfile(summaries_db):
        return sessions

    try:
        conn = sqlite3.connect(f"file:{summaries_db}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT conversation_id, title, preview, step_count,
                   last_modified_time, workspace_uris, status, source,
                   project_id, agent_name, parent_conversation_id,
                   nesting_depth, killed, last_user_input_time
            FROM conversation_summaries
            ORDER BY last_modified_time DESC
        """)

        for row in cur.fetchall():
            session = SessionInfo(
                conversation_id=row["conversation_id"] or "",
                title=row["title"] or "",
                preview=row["preview"] or "",
                step_count=row["step_count"] or 0,
                last_modified=row["last_modified_time"] or "",
                status=row["status"] or "",
                source=row["source"] or "",
                project_id=row["project_id"] or "",
                agent_name=row["agent_name"] or "",
                parent_conversation_id=row["parent_conversation_id"] or "",
                nesting_depth=row["nesting_depth"] or 0,
                killed=bool(row["killed"]),
                last_user_input_time=row["last_user_input_time"] or "",
            )

            # Parse workspace URIs
            ws = row["workspace_uris"]
            if ws:
                try:
                    session.workspace_uris = json.loads(ws)
                except (json.JSONDecodeError, TypeError):
                    session.workspace_uris = [ws]

            # Parse last_modified to datetime
            if session.last_modified:
                try:
                    # Format: "2026-05-19 17:30:20.5008124+00:00"
                    dt_str = session.last_modified
                    # Truncate fractional seconds to 6 digits for Python
                    if "." in dt_str:
                        base, frac_tz = dt_str.split(".", 1)
                        # Split fractional from timezone
                        for i, c in enumerate(frac_tz):
                            if c in ('+', '-') and i > 0:
                                frac = frac_tz[:i][:6]
                                tz = frac_tz[i:]
                                dt_str = f"{base}.{frac}{tz}"
                                break
                    session.last_modified_dt = datetime.fromisoformat(dt_str)
                except Exception:
                    pass

            # Check if conversation DB exists
            if conversations_dir:
                db_path = os.path.join(conversations_dir,
                                       f"{session.conversation_id}.db")
                if os.path.isfile(db_path):
                    session.has_conversation_db = True
                    try:
                        session.db_file_size = os.path.getsize(db_path)
                    except OSError:
                        pass

            # Check if transcript exists
            if brain_dir:
                transcript_path = os.path.join(
                    brain_dir, session.conversation_id,
                    ".system_generated", "logs", "transcript.jsonl"
                )
                session.has_transcript = os.path.isfile(transcript_path)

            sessions.append(session)

        conn.close()
    except Exception as e:
        print(f"Error reading summaries DB: {e}")

    return sessions
