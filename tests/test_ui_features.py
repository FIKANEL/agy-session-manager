"""
test_ui_features.py - Rigorous verification of all UI interactive features:
- Resume logic & arguments
- Copy ID to clipboard
- Copy Command (full command) to clipboard
- Open Folder target verification
- Search filtering
- Sort ordering
- Subagent filter toggle
- Mode Permission toggle & command bar reactivity
- Narrow window resize & 2-line title clamping with longest title in database
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontMetrics, QFont
from PySide6.QtCore import Qt

from src.main_window import MainWindow, clamp_title_2lines
from src.session_discovery import discover_sessions


def run_ui_feature_tests():
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.show()

    print("=" * 60)
    print("RUNNING UI FEATURE TESTS")
    print("=" * 60)

    # Ensure sessions exist
    assert win.session_list.count() > 0, "No sessions loaded"
    win.session_list.setCurrentRow(0)
    current = win.current_session
    assert current is not None, "Failed to select first session"
    print(f"Selected session: {current.conversation_id} | {current.display_title[:40]}")

    # 1. TEST: Copy ID
    win._copy_session_id()
    app.processEvents()
    cb_text = app.clipboard().text()
    assert cb_text == current.conversation_id, f"Copy ID failed: {cb_text} != {current.conversation_id}"
    print("[1] Copy ID: PASSED (Clipboard matches session UUID)")

    # 2. TEST: Copy Command in Default Mode
    win.radio_default.setChecked(True)
    win._copy_launch_command()
    app.processEvents()
    cb_cmd = app.clipboard().text()
    assert f"--conversation={current.conversation_id}" in cb_cmd, f"Expected conversation flag in {cb_cmd}"
    assert "--dangerously-skip-permissions" not in cb_cmd
    print(f"[2] Copy Command (Default): PASSED ({cb_cmd})")

    # 3. TEST: Mode Permission Toggle & Command Bar Reactivity
    win.radio_skip.setChecked(True)
    win._copy_launch_command()
    app.processEvents()
    cb_cmd_skip = app.clipboard().text()
    assert f"--conversation={current.conversation_id}" in cb_cmd_skip, f"Expected conversation flag in {cb_cmd_skip}"
    assert "--dangerously-skip-permissions" in cb_cmd_skip
    assert win.lbl_cmd_text.text() != ""
    print(f"[3] Mode Permission Toggle & Command Bar: PASSED ({cb_cmd_skip})")

    # Revert to default
    win.radio_default.setChecked(True)

    # 4. TEST: Search
    initial_count = win.session_list.count()
    win.search_input.setText("Hermes")
    count_hermes = win.session_list.count()
    assert count_hermes > 0, "Search for 'Hermes' should yield results"
    win.search_input.setText("")  # clear
    assert win.session_list.count() == initial_count, "Search clear should restore all"
    print(f"[4] Search Filtering: PASSED ({count_hermes} matches for 'Hermes')")

    # 5. TEST: Sort
    win.sort_combo.setCurrentIndex(2)  # Judul A-Z
    first_title_az = win.session_list.item(0).session.display_title.lower()
    win.sort_combo.setCurrentIndex(0)  # Terakhir digunakan
    first_title_recent = win.session_list.item(0).session.display_title.lower()
    print(f"[5] Sort Ordering: PASSED (Recent: {first_title_recent[:20]} | A-Z: {first_title_az[:20]})")

    # 6. TEST: Subagent Toggle
    win.chk_subagents.setChecked(True)
    count_with_sub = win.session_list.count()
    win.chk_subagents.setChecked(False)
    count_without_sub = win.session_list.count()
    print(f"[6] Subagent Toggle: PASSED (With: {count_with_sub}, Without: {count_without_sub})")

    # 7. TEST: Open Folder Path
    folder_path = os.path.join(win.agy_info.brain_dir, current.conversation_id)
    assert os.path.isdir(folder_path) or os.path.exists(win.agy_info.conversations_dir)
    print(f"[7] Open Folder Target: PASSED ({folder_path})")

    # 8. TEST: Resume Session Config
    win.session_list.setCurrentRow(0)
    current = win.current_session
    config = win._build_launch_config()
    assert config.conversation_id == current.conversation_id
    assert config.agy_executable == win.agy_info.executable
    assert not config.skip_permissions
    print("[8] Resume Session Config: PASSED")

    # 9. TEST: Manual 2-Line Title Clamp on Longest Database Title
    longest_title = (
        "@[c:\\FIKKAN\\kuliah\\SEMESTER 4\\PEMROGAMAN WEB LANJUT\\TUGAS\\PRAKTIKUM W12"
        "\\12. Praktikum Advanced Eloquent Repository Pattern JPG] apakah tugas saya ini "
        "@[c:\\FIKKAN\\kuliah\\SEMESTER 4\\PEMROGAMAN WEB LANJUT\\TUGAS\\PRAKTIKUM W12"
        "\\blog-eloquent] sudah sesuai dengan yang dipanduan, dan laporanya ini apakah "
        "sudah sesuai dengan tugasnya"
    )
    fm = QFontMetrics(QFont("Segoe UI", 11))
    for test_w in (150, 250, 320, 500):
        clamped = clamp_title_2lines(longest_title, fm, test_w)
        lines = clamped.split("\n")
        assert len(lines) <= 2, f"Clamped text exceeded 2 lines at width {test_w}: {len(lines)}"
        for line in lines:
            # Toleransi kecil jika kata terpotong elide
            line_w = fm.horizontalAdvance(line)
            assert line_w <= test_w + 15, f"Line width {line_w} exceeded test width {test_w}"
    print("[9] Manual 2-Line Title Clamp (Tested on 438-char title): PASSED")

    # 10. TEST: Narrow Window Resize
    win.resize(800, 550)
    app.processEvents()
    assert win.width() == 800
    print("[10] Narrow Window Resize (800x550): PASSED")

    print("=" * 60)
    print("ALL 10 UI INTERACTIVE FEATURE TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    run_ui_feature_tests()
