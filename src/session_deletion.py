"""
session_deletion.py - Safe physical deletion engine for Agy Session Manager.
Enforces the strict invariant: sessions can ONLY be permanently deleted from disk
if they have first been placed in the Trash menu.
"""
import os
import shutil
import sqlite3
from typing import Tuple, Optional

from src.session_discovery import SessionInfo
from src.agy_detector import AgyInfo
from src.settings import AppSettings, save_settings


class DeletionError(Exception):
    """Raised when permanent deletion fails."""
    pass


def permanently_delete_session(
    session: SessionInfo,
    agy_info: Optional[AgyInfo],
    settings: AppSettings,
    force: bool = False
) -> Tuple[bool, str]:
    """
    Permanently deletes all data associated with a session:
    1. conversations/<id>.db
    2. brain/<id>/
    3. row from conversation_summaries.db
    4. removes metadata from settings.json

    Safety invariant: session MUST be in settings.trashed_sessions unless force=True.
    """
    cid = session.conversation_id
    if not force and not settings.is_trashed(cid):
        raise DeletionError(
            f"Sesi '{session.display_title}' belum berada di Sampah. "
            "Sesi harus dipindahkan ke Sampah terlebih dahulu sebelum dapat dihapus permanen."
        )

    errors = []

    # 1. Remove conversations/<id>.db
    if agy_info and agy_info.conversations_dir:
        conv_db = os.path.join(agy_info.conversations_dir, f"{cid}.db")
        if os.path.isfile(conv_db):
            try:
                os.remove(conv_db)
            except Exception as e:
                errors.append(f"Gagal menghapus file DB percakapan: {e}")

    # 2. Remove brain/<id>/
    if agy_info and agy_info.brain_dir:
        brain_path = os.path.join(agy_info.brain_dir, cid)
        if os.path.isdir(brain_path):
            try:
                shutil.rmtree(brain_path, ignore_errors=True)
            except Exception as e:
                errors.append(f"Gagal menghapus folder brain: {e}")

    # 3. Remove row from conversation_summaries.db
    if agy_info and agy_info.summaries_db and os.path.isfile(agy_info.summaries_db):
        try:
            conn = sqlite3.connect(agy_info.summaries_db)
            cur = conn.cursor()
            cur.execute("DELETE FROM conversation_summaries WHERE conversation_id = ?", (cid,))
            try:
                cur.execute("DELETE FROM conversation_summaries WHERE id = ?", (cid,))
            except Exception:
                pass
            conn.commit()
            conn.close()
        except Exception as e:
            errors.append(f"Gagal menghapus entri dari database summaries: {e}")

    # 4. Clean metadata in settings.json
    settings.purge_from_settings(cid)
    save_settings(settings)

    if errors:
        return False, "; ".join(errors)
    return True, f"Session '{session.display_title}' berhasil dihapus permanen."
