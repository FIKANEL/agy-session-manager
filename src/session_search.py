"""
session_search.py - Search sessions by ID, title, content, keywords.
"""
from typing import List
from src.session_discovery import SessionInfo


def search_sessions(sessions: List[SessionInfo], query: str) -> List[SessionInfo]:
    """Search sessions by query string across multiple fields."""
    if not query or not query.strip():
        return sessions

    query_lower = query.strip().lower()
    results = []

    for session in sessions:
        # Search in conversation ID
        if query_lower in session.conversation_id.lower():
            results.append(session)
            continue

        # Search in title/preview or custom title or original title
        if query_lower in session.display_title.lower() or query_lower in session.original_title.lower():
            results.append(session)
            continue

        # Search in workspace paths
        if query_lower in session.workspace_display.lower():
            results.append(session)
            continue

        # Search in project_id
        if session.project_id and query_lower in session.project_id.lower():
            results.append(session)
            continue

        # Search in agent name
        if session.agent_name and query_lower in session.agent_name.lower():
            results.append(session)
            continue

    return results


def filter_sessions(sessions: List[SessionInfo],
                    show_subagents: bool = False,
                    min_steps: int = 0) -> List[SessionInfo]:
    """Filter sessions based on criteria."""
    filtered = []
    for s in sessions:
        # Optionally hide subagent sessions
        if not show_subagents and s.nesting_depth > 0:
            continue
        # Filter by minimum step count
        if s.step_count < min_steps:
            continue
        filtered.append(s)
    return filtered


def sort_sessions(sessions: List[SessionInfo],
                  sort_by: str = "last_modified") -> List[SessionInfo]:
    """Sort sessions by given criteria, with starred sessions pinned to the top."""
    if sort_by == "last_modified":
        res = sorted(
            sessions,
            key=lambda s: s.last_modified or "",
            reverse=True
        )
    elif sort_by == "created":
        res = sorted(
            sessions,
            key=lambda s: s.last_modified or "",
            reverse=False
        )
    elif sort_by == "title":
        res = sorted(
            sessions,
            key=lambda s: s.display_title.lower()
        )
    elif sort_by == "steps":
        res = sorted(
            sessions,
            key=lambda s: s.step_count,
            reverse=True
        )
    else:
        res = list(sessions)

    # Pin starred sessions to the top (stable sort preserves ordering within each group)
    return sorted(res, key=lambda s: not s.is_starred)
