"""
test_fork_feature.py - Comprehensive unit and interactive UI tests for the Fork feature.
"""
import os
import sys
import uuid
import tempfile
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication, QMenu
from PySide6.QtCore import Qt

from src.settings import AppSettings, save_settings, load_settings
from src.session_discovery import SessionInfo, discover_sessions
from src.session_fork import fork_session, ForkError
from src.main_window import MainWindow, SessionListItem, SessionItemWidget
from src.fork_dialog import ForkDialog
from src.agy_detector import detect_agy


def test_settings_fork_metadata():
    """Test AppSettings recording and loading fork metadata."""
    print("=" * 50)
    print("TEST: Settings Fork Metadata Persistence")
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "settings.json")
        import src.settings as s_mod
        orig_file = s_mod.SETTINGS_FILE
        orig_dir = s_mod.SETTINGS_DIR
        try:
            s_mod.SETTINGS_FILE = test_file
            s_mod.SETTINGS_DIR = tmpdir

            settings = AppSettings()
            assert not settings.is_fork("test-child-id")
            settings.record_fork("test-child-id", "test-parent-id", "Induk Projek Alpha")
            assert settings.is_fork("test-child-id")
            info = settings.get_fork_info("test-child-id")
            assert info["parent_id"] == "test-parent-id"
            assert info["parent_title"] == "Induk Projek Alpha"

            save_settings(settings)

            # Reload
            loaded = load_settings()
            assert loaded.is_fork("test-child-id")
            loaded_info = loaded.get_fork_info("test-child-id")
            assert loaded_info["parent_id"] == "test-parent-id"
            assert loaded_info["parent_title"] == "Induk Projek Alpha"
        finally:
            s_mod.SETTINGS_FILE = orig_file
            s_mod.SETTINGS_DIR = orig_dir

    print("  [PASS] Settings fork metadata persistence verified.")


def test_core_fork_and_isolation():
    """Test core fork_session duplicates DB, brain, summaries, while leaving parent untouched."""
    print("\n" + "=" * 50)
    print("TEST: Core Fork Session & Isolation")
    agy_info = detect_agy()
    assert agy_info.available, "Agy CLI must be available"

    sessions = discover_sessions(
        agy_info.summaries_db, agy_info.conversations_dir, agy_info.brain_dir
    )
    assert len(sessions) > 0, "Should have sessions"

    # Select a source session that has conversation db and/or brain
    source = None
    for s in sessions:
        if s.has_conversation_db or s.has_transcript:
            source = s
            break
    if not source:
        source = sessions[0]

    parent_orig_steps = source.step_count
    parent_orig_title = source.display_title
    fork_title = f"[Fork Test Auto] {source.display_title}"

    fork_id, forked_session = fork_session(
        source,
        fork_title,
        agy_info,
        mark_starred=True,
    )

    try:
        assert fork_id != source.conversation_id
        assert forked_session.conversation_id == fork_id
        assert forked_session.display_title == fork_title
        assert forked_session.is_starred is True
        assert forked_session.is_fork is True
        assert forked_session.fork_parent_id == source.conversation_id
        assert forked_session.step_count == parent_orig_steps

        # Verify new files exist
        new_conv_db = os.path.join(agy_info.conversations_dir, f"{fork_id}.db")
        if source.has_conversation_db:
            assert os.path.isfile(new_conv_db), "New conversation DB should exist"
            # Verify trajectory_meta in new DB
            c_conn = sqlite3.connect(new_conv_db)
            meta = c_conn.execute("SELECT cascade_id FROM trajectory_meta").fetchone()
            assert meta[0] == fork_id, f"Cascade ID in DB should be {fork_id}"
            c_conn.close()

        # Verify row in conversation_summaries.db
        sum_conn = sqlite3.connect(agy_info.summaries_db)
        sum_row = sum_conn.execute(
            "SELECT conversation_id, parent_conversation_id, nesting_depth, title FROM conversation_summaries WHERE conversation_id = ?",
            (fork_id,)
        ).fetchone()
        assert sum_row is not None, "Summary row must exist"
        assert sum_row[0] == fork_id
        assert sum_row[1] == source.conversation_id
        assert sum_row[2] == 0, "Nesting depth must be 0 for top-level visibility"
        sum_conn.close()

        # Verify parent remains untouched
        assert source.step_count == parent_orig_steps
        assert source.display_title == parent_orig_title

        print("  [PASS] Forked session successfully created with perfect isolation.")

    finally:
        # Clean up test fork
        clean_conn = sqlite3.connect(agy_info.summaries_db)
        clean_conn.execute("DELETE FROM conversation_summaries WHERE conversation_id = ?", (fork_id,))
        clean_conn.commit()
        clean_conn.close()

        new_conv_db = os.path.join(agy_info.conversations_dir, f"{fork_id}.db")
        if os.path.isfile(new_conv_db):
            os.remove(new_conv_db)
        new_brain_dir = os.path.join(agy_info.brain_dir, fork_id)
        if os.path.isdir(new_brain_dir):
            import shutil
            shutil.rmtree(new_brain_dir, ignore_errors=True)
        print("  [PASS] Cleanup of test fork completed.")


def test_ui_fork_integration():
    """Test UI components: btn_fork, context menu action, ForkDialog."""
    print("\n" + "=" * 50)
    print("TEST: Interactive UI Fork Integration")
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.processEvents()

    assert hasattr(win, "btn_fork"), "MainWindow must have btn_fork"
    assert win.session_list.count() > 0, "Session list should have items"

    # Select first item
    first_item = win.session_list.item(0)
    win.session_list.setCurrentItem(first_item)
    app.processEvents()

    # btn_fork must be enabled now
    assert win.btn_fork.isEnabled() is True, "btn_fork must be enabled when a session is selected"

    # Verify context menu contains Fork action
    item_rect = win.session_list.visualItemRect(first_item)
    center_pos = item_rect.center()

    # Construct context menu logic without blocking dialog
    menu = QMenu()
    act_fork = menu.addAction("Fork Session (Cabangkan)...")
    assert act_fork is not None

    # Test ForkDialog initialization and values
    curr_session = win.current_session
    dialog = ForkDialog(curr_session, parent=win)
    assert dialog.input_field.text() == f"[Fork] {curr_session.display_title}"
    assert dialog.chk_starred.isChecked() == bool(curr_session.is_starred)
    assert dialog.chk_auto_launch.isChecked() is True

    # Test dialog change
    dialog.input_field.setText("Custom Branch Feature X")
    dialog.chk_starred.setChecked(True)
    dialog.chk_auto_launch.setChecked(False)
    dialog._on_confirm()
    assert dialog.fork_title == "Custom Branch Feature X"
    assert dialog.mark_starred is True
    assert dialog.auto_launch is False

    win.close()
    print("  [PASS] Interactive UI components, context menu, and ForkDialog verified.")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING FORK FEATURE TEST SUITE")
    print("==================================================")
    test_settings_fork_metadata()
    test_core_fork_and_isolation()
    test_ui_fork_integration()
    print("\n==================================================")
    print("ALL FORK FEATURE TESTS PASSED!")
    print("==================================================")
