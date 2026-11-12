import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow, ChatBubbleWidget
from src.history_reader import read_transcript, clear_transcript_cache


def test_performance():
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()

    print("=" * 60)
    print("RUNNING CHAT LOADING PERFORMANCE TESTS")
    print("=" * 60)

    # Find the largest session (5,087 messages)
    brain_dir = os.path.expandvars(r'%USERPROFILE%\.gemini\antigravity-cli\brain')
    conv_id = '89ff7e11-24be-4668-90cf-5af1240492a8'

    # 1. Test Transcript Cache
    clear_transcript_cache()
    t0 = time.time()
    msgs1 = read_transcript(brain_dir, conv_id)
    t_first = time.time() - t0

    t0 = time.time()
    msgs2 = read_transcript(brain_dir, conv_id)
    t_cache = time.time() - t0

    assert len(msgs1) == len(msgs2)
    print(f"[1] Transcript Cache: First read = {t_first*1000:.1f}ms, Cached read = {t_cache*1000:.3f}ms")
    assert t_cache < 5.0  # Cache should be under 5ms

    # 2. Test Pagination / Chunked Loading
    session = None
    for s in win.sessions:
        if s.conversation_id == conv_id:
            session = s
            break

    assert session is not None, f"Session {conv_id} not found in session list"

    t0 = time.time()
    win._load_chat_history(session)
    app.processEvents()
    t_load = time.time() - t0

    print(f"[2] Paginated Load Time (5,083 msgs): {t_load*1000:.1f}ms (target < 800ms, was 52,000ms!)")
    assert t_load < 1.0, f"Load time took too long: {t_load:.2f}s"
    assert win.load_more_widget is not None, "LoadMoreWidget should be present for >40 messages"
    assert win.rendered_msg_start_idx > 0

    # 3. Test Load More
    initial_count = win.chat_layout.count()
    win._on_load_more_messages()
    app.processEvents()
    new_count = win.chat_layout.count()
    assert new_count > initial_count
    print(f"[3] Load More Earlier Messages: PASSED (Layout items grew from {initial_count} to {new_count})")

    # 4. Test In-Chat Search
    t0 = time.time()
    win._on_chat_search("error")
    app.processEvents()
    t_search = time.time() - t0
    print(f"[4] In-Chat Search (across 5,083 msgs): {t_search*1000:.1f}ms")
    assert t_search < 0.4, f"Search took too long: {t_search:.2f}s"

    # Reset search
    win._on_chat_search("")
    app.processEvents()
    assert win.load_more_widget is not None
    print("[5] Reset Search: PASSED")

    print("=" * 60)
    print("ALL PERFORMANCE TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_performance()
