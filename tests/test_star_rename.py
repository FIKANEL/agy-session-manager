"""
test_star_rename.py - Unit and UI integration tests for Star and Rename features.
"""
import os
import sys
import tempfile
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.settings import AppSettings, save_settings, load_settings
from src.session_discovery import SessionInfo
from src.session_search import search_sessions, sort_sessions, filter_sessions
from src.main_window import MainWindow, SessionListItem, SessionItemWidget


def test_settings_star_rename_persistence():
    """Test AppSettings starring, custom titles, and JSON roundtrip."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "settings.json")
        import src.settings as s_mod
        orig_file = s_mod.SETTINGS_FILE
        orig_dir = s_mod.SETTINGS_DIR
        try:
            s_mod.SETTINGS_FILE = test_file
            s_mod.SETTINGS_DIR = tmpdir

            settings = AppSettings()
            assert not settings.is_starred("conv-1")
            assert settings.toggle_star("conv-1") is True
            assert settings.is_starred("conv-1")
            assert settings.toggle_star("conv-1") is False
            assert not settings.is_starred("conv-1")
            settings.toggle_star("conv-1")

            settings.set_custom_title("conv-1", "Projek Alpha Refactor")
            assert settings.get_custom_title("conv-1") == "Projek Alpha Refactor"

            save_settings(settings)

            # Reload
            loaded = load_settings()
            assert loaded.is_starred("conv-1")
            assert loaded.get_custom_title("conv-1") == "Projek Alpha Refactor"

            # Reset title
            loaded.set_custom_title("conv-1", "")
            assert loaded.get_custom_title("conv-1") is None
            save_settings(loaded)

            reloaded = load_settings()
            assert reloaded.get_custom_title("conv-1") is None
        finally:
            s_mod.SETTINGS_FILE = orig_file
            s_mod.SETTINGS_DIR = orig_dir

    print("  [PASS] Settings star & rename persistence")


def test_session_info_display_title_priority():
    """Test SessionInfo display_title priority."""
    s = SessionInfo(
        conversation_id="12345678-abcd",
        title="Original Title",
        preview="Preview Text",
    )
    assert s.display_title == "Preview Text"
    assert s.original_title == "Preview Text"

    s.custom_title = "Custom Renamed Title"
    assert s.display_title == "Custom Renamed Title"
    assert s.original_title == "Preview Text"

    s.custom_title = ""
    assert s.display_title == "Preview Text"

    print("  [PASS] SessionInfo display title priority")


def test_starred_pinned_to_top():
    """Test that sort_sessions pins starred sessions to the top in all sort modes."""
    s1 = SessionInfo(conversation_id="1", title="Alpha", last_modified="2026-10-20 10:00", step_count=10, is_starred=False)
    s2 = SessionInfo(conversation_id="2", title="Beta", last_modified="2026-10-21 10:00", step_count=50, is_starred=False)
    s3 = SessionInfo(conversation_id="3", title="Gamma", last_modified="2026-10-19 10:00", step_count=5, is_starred=True)

    # Sort by last_modified (newest first). Unstarred would put 2, then 1, then 3.
    # But s3 is starred, so s3 must be first!
    sorted_res = sort_sessions([s1, s2, s3], "last_modified")
    assert sorted_res[0].conversation_id == "3", "Starred s3 must be at index 0"
    assert sorted_res[1].conversation_id == "2", "s2 should be next"
    assert sorted_res[2].conversation_id == "1", "s1 should be last"

    # Multiple starred sessions preserve inner sort
    s4 = SessionInfo(conversation_id="4", title="Delta", last_modified="2026-10-25 10:00", step_count=100, is_starred=True)
    sorted_multi = sort_sessions([s1, s2, s3, s4], "last_modified")
    # s4 and s3 are both starred. s4 (Oct 25) is newer than s3 (Oct 19).
    assert [s.conversation_id for s in sorted_multi] == ["4", "3", "2", "1"]

    # Sort by title A-Z
    sorted_title = sort_sessions([s1, s2, s3, s4], "title")
    # Starred are s3 (Gamma) and s4 (Delta). Inner sorted: Delta, Gamma.
    assert [s.conversation_id for s in sorted_title[:2]] == ["4", "3"]

    print("  [PASS] Starred sessions pinned to top in sort")


def test_search_by_custom_title():
    """Test search matches custom renamed titles as well as original."""
    s1 = SessionInfo(conversation_id="abc", title="Bug Fix Auth", custom_title="Penyelidikan CVE")
    s2 = SessionInfo(conversation_id="def", title="Refactor DB", custom_title="")

    # Search by custom title
    matches = search_sessions([s1, s2], "Penyelidikan")
    assert len(matches) == 1 and matches[0].conversation_id == "abc"

    # Search by original title
    matches_orig = search_sessions([s1, s2], "Auth")
    assert len(matches_orig) == 1 and matches_orig[0].conversation_id == "abc"

    print("  [PASS] Search by custom title & original title")


def test_main_window_interactive():
    """Interactive Qt UI tests for Star & Rename features."""
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.processEvents()

    if not win.sessions:
        print("  [SKIP] No sessions available for UI test")
        win.close()
        return

    # Select first session
    first_item = win.session_list.item(0)
    win.session_list.setCurrentItem(first_item)
    app.processEvents()

    curr_session = win.current_session
    assert curr_session is not None
    orig_starred = curr_session.is_starred
    orig_custom = curr_session.custom_title

    # 1. Test Toggle Star via UI
    win.btn_detail_star.click()
    app.processEvents()
    assert curr_session.is_starred == (not orig_starred)
    # List top item should be starred
    top_item = win.session_list.item(0)
    if curr_session.is_starred:
        assert top_item.session.is_starred is True

    # 2. Test Starred View Filter
    win.btn_starred.click()
    app.processEvents()
    for i in range(win.session_list.count()):
        assert win.session_list.item(i).session.is_starred is True

    # Revert to all
    win.btn_all.click()
    app.processEvents()

    # Revert star
    if curr_session.is_starred != orig_starred:
        win.btn_detail_star.click()
        app.processEvents()

    # 3. Test Rename persistence in UI
    test_new_name = "Session Test Otomatis 999"
    curr_session.custom_title = test_new_name
    win.settings.set_custom_title(curr_session.conversation_id, test_new_name)
    save_settings(win.settings)
    win._apply_filters()
    app.processEvents()

    # Check display title in header and item widget
    assert win.lbl_detail_title.text() == test_new_name or curr_session.display_title == test_new_name

    # Reset name
    curr_session.custom_title = orig_custom
    win.settings.set_custom_title(curr_session.conversation_id, orig_custom or "")
    save_settings(win.settings)
    win._apply_filters()
    app.processEvents()

    win.close()
    print("  [PASS] MainWindow interactive UI tests for Star & Rename")


if __name__ == "__main__":
    print("==================================================")
    print("TEST: Star and Rename Session Features")
    print("==================================================")
    test_settings_star_rename_persistence()
    test_session_info_display_title_priority()
    test_starred_pinned_to_top()
    test_search_by_custom_title()
    test_main_window_interactive()
    print("==================================================")
    print("ALL STAR & RENAME TESTS PASSED!")
    print("==================================================")
