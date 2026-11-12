"""
session_fork.py - Core logic for safely forking Agy CLI sessions into independent branches.
Preserves the original session completely untouched by duplicating the conversation database,
brain transcript/artifacts, and registering a new entry in conversation_summaries.db.
"""
import os
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from src.session_discovery import SessionInfo
from src.agy_detector import AgyInfo


class ForkError(Exception):
    """Raised when session forking fails."""
    pass


def fork_session(
    orig_session: SessionInfo,
    new_title: str,
    agy_info: AgyInfo,
    mark_starred: bool = False,
) -> Tuple[str, SessionInfo]:
    """
    Fork an existing session into a new independent session.
    
    Args:
        orig_session: The source SessionInfo to fork.
        new_title: Custom title for the new forked session.
        agy_info: AgyInfo containing data directory paths.
        mark_starred: Whether to mark the new session as starred.

    Returns:
        (new_conversation_id, new_session_info)

    Raises:
        ForkError: If database operations or file copies fail.
    """
    if not agy_info or not agy_info.summaries_db:
        raise ForkError("Direktori database Agy tidak valid atau tidak ditemukan.")

    if not os.path.isfile(agy_info.summaries_db):
        raise ForkError(f"Database summaries tidak ditemukan di: {agy_info.summaries_db}")

    orig_id = orig_session.conversation_id
    if not orig_id:
        raise ForkError("Session sumber tidak memiliki Conversation ID.")

    new_id = str(uuid.uuid4())
    clean_title = new_title.strip() or f"[Fork] {orig_session.display_title}"

    # 1. Duplicate conversation SQLite DB if exists
    orig_conv_db = os.path.join(agy_info.conversations_dir, f"{orig_id}.db")
    new_conv_db = os.path.join(agy_info.conversations_dir, f"{new_id}.db")
    has_conv_db = False
    db_file_size = 0

    if os.path.isfile(orig_conv_db):
        try:
            os.makedirs(agy_info.conversations_dir, exist_ok=True)
            shutil.copy2(orig_conv_db, new_conv_db)
            has_conv_db = True
            db_file_size = os.path.getsize(new_conv_db)

            # Update trajectory_meta inside the new conversation DB
            c_conn = sqlite3.connect(new_conv_db)
            new_traj_id = str(uuid.uuid4())
            c_conn.execute(
                "UPDATE trajectory_meta SET trajectory_id = ?, cascade_id = ?",
                (new_traj_id, new_id)
            )
            c_conn.commit()
            c_conn.close()
        except Exception as e:
            if os.path.isfile(new_conv_db):
                try:
                    os.remove(new_conv_db)
                except OSError:
                    pass
            raise ForkError(f"Gagal menyalin database percakapan: {e}")

    # 2. Duplicate brain directory (transcripts, steps, logs, artifacts) if exists
    orig_brain_dir = os.path.join(agy_info.brain_dir, orig_id)
    new_brain_dir = os.path.join(agy_info.brain_dir, new_id)
    has_transcript = False

    if os.path.isdir(orig_brain_dir):
        try:
            os.makedirs(agy_info.brain_dir, exist_ok=True)
            shutil.copytree(orig_brain_dir, new_brain_dir, dirs_exist_ok=True)

            # Replace occurrences of old conversation_id with new_id in transcript logs
            logs_dir = os.path.join(new_brain_dir, ".system_generated", "logs")
            for fname in ["transcript.jsonl", "transcript_full.jsonl"]:
                fpath = os.path.join(logs_dir, fname)
                if os.path.isfile(fpath):
                    has_transcript = True
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        content = content.replace(orig_id, new_id)
                        with open(fpath, "w", encoding="utf-8") as f:
                            f.write(content)
                    except Exception:
                        pass
        except Exception as e:
            # Clean up copied brain on error
            if os.path.isdir(new_brain_dir):
                shutil.rmtree(new_brain_dir, ignore_errors=True)
            if os.path.isfile(new_conv_db):
                try:
                    os.remove(new_conv_db)
                except OSError:
                    pass
            raise ForkError(f"Gagal menduplikasi direktori brain: {e}")

    # 3. Insert new row into conversation_summaries.db
    try:
        conn = sqlite3.connect(agy_info.summaries_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Fetch original row
        cur.execute(
            "SELECT * FROM conversation_summaries WHERE conversation_id = ?",
            (orig_id,)
        )
        row = cur.fetchone()

        now_utc = datetime.now(timezone.utc)
        now_str = now_utc.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "+00:00"

        if row:
            cols = list(row.keys())
            val_map = dict(row)
            val_map["conversation_id"] = new_id
            val_map["title"] = clean_title
            val_map["preview"] = clean_title
            val_map["last_modified_time"] = now_str
            val_map["last_user_input_time"] = now_str
            val_map["parent_conversation_id"] = orig_id
            val_map["nesting_depth"] = 0  # Top-level session so it shows up in main session list
            val_map["killed"] = 0
            val_map["not_fully_idle"] = 0

            placeholders = ", ".join(["?"] * len(cols))
            col_names = ", ".join([f"`{c}`" for c in cols])
            values = [val_map[c] for c in cols]

            cur.execute(
                f"INSERT INTO conversation_summaries ({col_names}) VALUES ({placeholders})",
                values
            )
        else:
            # Fallback insertion if original row wasn't found in DB
            cur.execute("""
                INSERT INTO conversation_summaries (
                    conversation_id, title, preview, step_count,
                    last_modified_time, workspace_uris, status, source,
                    project_id, agent_name, parent_conversation_id,
                    nesting_depth, last_user_input_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_id, clean_title, clean_title, orig_session.step_count,
                now_str, "[]", "CASCADE_RUN_STATUS_IDLE", orig_session.source or "",
                orig_session.project_id or "", orig_session.agent_name or "",
                orig_id, 0, now_str
            ))

        conn.commit()
        conn.close()
    except Exception as e:
        # Rollback copied files
        if os.path.isfile(new_conv_db):
            try:
                os.remove(new_conv_db)
            except OSError:
                pass
        if os.path.isdir(new_brain_dir):
            shutil.rmtree(new_brain_dir, ignore_errors=True)
        raise ForkError(f"Gagal mendaftarkan session baru ke database: {e}")

    # Build new SessionInfo
    new_session = SessionInfo(
        conversation_id=new_id,
        title=clean_title,
        preview=clean_title,
        step_count=orig_session.step_count,
        last_modified=now_str,
        last_modified_dt=now_utc,
        workspace_uris=list(orig_session.workspace_uris),
        status="CASCADE_RUN_STATUS_IDLE",
        source=orig_session.source,
        project_id=orig_session.project_id,
        agent_name=orig_session.agent_name,
        parent_conversation_id=orig_id,
        nesting_depth=0,
        has_transcript=has_transcript,
        has_conversation_db=has_conv_db,
        db_file_size=db_file_size,
        custom_title=clean_title,
        is_starred=mark_starred,
        is_fork=True,
        fork_parent_id=orig_id,
        fork_parent_title=orig_session.display_title,
    )

    return new_id, new_session
