"""
test_trash_delete.py - Unit and integration tests for Trash & Deletion feature.
Verifies:
1. Two-stage deletion: Soft delete to Trash first, then permanent deletion.
2. Invariant: Permanent deletion is blocked unless session is already in Trash.
3. Settings persistence and fork synchronization for Trash.
4. UI views and button adaptability.
"""
import sys
import os
import shutil
import sqlite3
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication

from src.settings import AppSettings
from src.session_discovery import SessionInfo
from src.session_deletion import permanently_delete_session, DeletionError
from src.agy_detector import AgyInfo
from src.main_window import MainWindow, SessionListItem


class TestTrashAndDelete(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="agy_trash_test_")
        self.conv_dir = os.path.join(self.tmp_dir, "conversations")
        self.brain_dir = os.path.join(self.tmp_dir, "brain")
        os.makedirs(self.conv_dir, exist_ok=True)
        os.makedirs(self.brain_dir, exist_ok=True)

        self.summaries_db = os.path.join(self.tmp_dir, "conversation_summaries.db")
        conn = sqlite3.connect(self.summaries_db)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE conversation_summaries (
                conversation_id TEXT PRIMARY KEY,
                title TEXT,
                nesting_depth INTEGER,
                parent_conversation_id TEXT
            )
        """)
        conn.commit()
        conn.close()

        self.agy_info = AgyInfo(
            available=True,
            executable="agy.exe",
            version="1.0.0",
            data_dir=self.tmp_dir,
            conversations_dir=self.conv_dir,
            brain_dir=self.brain_dir,
            summaries_db=self.summaries_db,
        )

        import src.settings as s_mod
        self.orig_settings_file = s_mod.SETTINGS_FILE
        self.orig_settings_dir = s_mod.SETTINGS_DIR
        s_mod.SETTINGS_FILE = os.path.join(self.tmp_dir, "test_settings.json")
        s_mod.SETTINGS_DIR = self.tmp_dir

        self.settings = AppSettings()

    def tearDown(self):
        import src.settings as s_mod
        s_mod.SETTINGS_FILE = self.orig_settings_file
        s_mod.SETTINGS_DIR = self.orig_settings_dir
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_settings_trash_lifecycle(self):
        """Verify move_to_trash, is_trashed, and restore_from_trash."""
        cid = "test-session-1234"
        self.assertFalse(self.settings.is_trashed(cid))

        self.settings.move_to_trash(cid, "Test Title")
        self.assertTrue(self.settings.is_trashed(cid))
        self.assertIn(cid, self.settings.trashed_sessions)

        self.settings.restore_from_trash(cid)
        self.assertFalse(self.settings.is_trashed(cid))
        self.assertNotIn(cid, self.settings.trashed_sessions)

    def test_fork_sync_in_trash(self):
        """Verify trashing a parent automatically trashes its child forks."""
        parent_id = "parent-1111"
        child_id = "child-2222"

        self.settings.record_fork(child_id, parent_id, "Parent Title")
        self.assertFalse(self.settings.is_trashed(parent_id))
        self.assertFalse(self.settings.is_trashed(child_id))

        # Trash parent -> child should follow
        self.settings.move_to_trash(parent_id, "Parent Session")
        self.assertTrue(self.settings.is_trashed(parent_id))
        self.assertTrue(self.settings.is_trashed(child_id))

        # Restore parent -> child should restore
        self.settings.restore_from_trash(parent_id)
        self.assertFalse(self.settings.is_trashed(parent_id))
        self.assertFalse(self.settings.is_trashed(child_id))

    def test_permanent_delete_safety_invariant(self):
        """Verify permanent delete fails with DeletionError if session is NOT in trash."""
        dummy_session = SessionInfo(
            conversation_id="not-in-trash-uuid",
            title="Active Session",
        )

        with self.assertRaises(DeletionError):
            permanently_delete_session(dummy_session, self.agy_info, self.settings, force=False)

    def test_physical_permanent_deletion(self):
        """Verify physical deletion removes sqlite file, brain folder, summaries row, and settings."""
        cid = "real-delete-uuid-5678"
        dummy_session = SessionInfo(
            conversation_id=cid,
            title="Session To Delete",
        )

        # 1. Create physical conversation DB
        conv_file = os.path.join(self.conv_dir, f"{cid}.db")
        with open(conv_file, "w") as f:
            f.write("dummy db content")

        # 2. Create physical brain folder
        brain_sub = os.path.join(self.brain_dir, cid)
        os.makedirs(brain_sub, exist_ok=True)
        with open(os.path.join(brain_sub, "transcript.jsonl"), "w") as f:
            f.write("{}")

        # 3. Create row in summaries db
        conn = sqlite3.connect(self.summaries_db)
        cur = conn.cursor()
        cur.execute("INSERT INTO conversation_summaries VALUES (?, ?, 0, '')", (cid, "Session To Delete"))
        conn.commit()
        conn.close()

        # 4. Put into settings
        self.settings.starred_sessions.append(cid)
        self.settings.custom_titles[cid] = "Renamed Title"
        self.settings.move_to_trash(cid, "Session To Delete")

        # Verify files exist
        self.assertTrue(os.path.isfile(conv_file))
        self.assertTrue(os.path.isdir(brain_sub))

        # Execute permanent deletion
        success, msg = permanently_delete_session(dummy_session, self.agy_info, self.settings, force=False)
        self.assertTrue(success)

        # Verify physical files are GONE
        self.assertFalse(os.path.isfile(conv_file))
        self.assertFalse(os.path.isdir(brain_sub))

        # Verify database row is GONE
        conn = sqlite3.connect(self.summaries_db)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM conversation_summaries WHERE conversation_id = ?", (cid,))
        count = cur.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0)

        # Verify settings are purged
        self.assertNotIn(cid, self.settings.trashed_sessions)
        self.assertNotIn(cid, self.settings.starred_sessions)
        self.assertNotIn(cid, self.settings.custom_titles)

    def test_main_window_trash_tab_and_buttons(self):
        """Verify MainWindow trash navigation, empty trash button, and button state adaptation."""
        win = MainWindow()
        try:
            # Switch to trash view
            win._set_view("trash")
            self.assertEqual(win.current_view, "trash")

            # Header buttons must adapt for Trash view
            self.assertFalse(win.btn_restore.isHidden())
            self.assertFalse(win.btn_perm_delete.isHidden())
            self.assertTrue(win.btn_resume.isHidden())
            self.assertTrue(win.btn_fork.isHidden())
            self.assertTrue(win.btn_move_trash.isHidden())

            # Switch back to all view
            win._set_view("all")
            self.assertEqual(win.current_view, "all")
            self.assertTrue(win.btn_restore.isHidden())
            self.assertTrue(win.btn_perm_delete.isHidden())
            self.assertFalse(win.btn_resume.isHidden())
            self.assertFalse(win.btn_fork.isHidden())
            self.assertFalse(win.btn_move_trash.isHidden())
        finally:
            win.close()


if __name__ == "__main__":
    unittest.main()
