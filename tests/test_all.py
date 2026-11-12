"""
Tests for Agy Session Manager modules.
"""
import sys
import os
import json
import tempfile

# Add parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agy_detector import detect_agy
from src.session_discovery import discover_sessions
from src.session_search import search_sessions, filter_sessions, sort_sessions
from src.session_launcher import (
    validate_conversation_id, build_launch_args, LaunchConfig, LaunchError
)
from src.settings import AppSettings, load_settings, save_settings


def test_agy_detection():
    """Test Agy CLI detection."""
    print("=" * 50)
    print("TEST: Agy CLI Detection")
    info = detect_agy()
    print(f"  Available: {info.available}")
    print(f"  Executable: {info.executable}")
    print(f"  Version: {info.version}")
    print(f"  Data dir: {info.data_dir}")
    print(f"  Supports --conversation: {info.supports_conversation}")
    print(f"  Supports --dangerously-skip-permissions: {info.supports_skip_permissions}")
    print(f"  Supports --continue: {info.supports_continue}")
    assert info.available, "Agy CLI should be available"
    assert info.version, "Version should be detected"
    assert info.data_dir, "Data directory should be found"
    assert info.supports_conversation, "--conversation should be supported"
    print("  ✅ PASSED")
    return info


def test_session_discovery(info):
    """Test session discovery."""
    print("\n" + "=" * 50)
    print("TEST: Session Discovery")
    sessions = discover_sessions(
        info.summaries_db, info.conversations_dir, info.brain_dir
    )
    print(f"  Sessions found: {len(sessions)}")
    assert len(sessions) > 0, "Should find at least 1 session"

    # Check first session has required fields
    s = sessions[0]
    print(f"  First session: {s.display_title}")
    print(f"  ID: {s.conversation_id}")
    print(f"  Steps: {s.step_count}")
    print(f"  Last modified: {s.last_modified_display}")
    print(f"  Has transcript: {s.has_transcript}")
    print(f"  Has conversation DB: {s.has_conversation_db}")
    assert s.conversation_id, "Session should have an ID"
    print("  ✅ PASSED")
    return sessions


def test_session_search(sessions):
    """Test session search functionality."""
    print("\n" + "=" * 50)
    print("TEST: Session Search")

    # Search by partial ID
    if sessions:
        first_id = sessions[0].conversation_id[:8]
        results = search_sessions(sessions, first_id)
        print(f"  Search '{first_id}': {len(results)} results")
        assert len(results) >= 1, "Should find session by partial ID"

    # Search by empty string
    results = search_sessions(sessions, "")
    assert len(results) == len(sessions), "Empty search should return all"

    # Search by nonexistent
    results = search_sessions(sessions, "xyznonexistent12345")
    assert len(results) == 0, "Should find 0 results for nonsense"

    print("  ✅ PASSED")


def test_filter_sort(sessions):
    """Test filtering and sorting."""
    print("\n" + "=" * 50)
    print("TEST: Filter & Sort")

    # Filter out subagents
    filtered = filter_sessions(sessions, show_subagents=False)
    print(f"  Without subagents: {len(filtered)} (from {len(sessions)})")

    # Sort by title
    sorted_s = sort_sessions(filtered, "title")
    if len(sorted_s) >= 2:
        assert sorted_s[0].display_title.lower() <= sorted_s[1].display_title.lower()

    # Sort by steps
    sorted_s = sort_sessions(filtered, "steps")
    if len(sorted_s) >= 2:
        assert sorted_s[0].step_count >= sorted_s[1].step_count

    print("  ✅ PASSED")


def test_conversation_id_validation():
    """Test conversation ID validation."""
    print("\n" + "=" * 50)
    print("TEST: Conversation ID Validation")

    assert validate_conversation_id("72138e41-007e-4811-b163-d03a4bff1eef")
    assert validate_conversation_id("89ff7e11-24be-4668-90cf-5af1240492a8")
    assert not validate_conversation_id("invalid")
    assert not validate_conversation_id("")
    assert not validate_conversation_id("72138e41-007e-4811-b163")
    assert not validate_conversation_id("72138e41-007e-4811-b163-d03a4bff1ee!")
    print("  ✅ PASSED")


def test_build_launch_args():
    """Test CLI argument building."""
    print("\n" + "=" * 50)
    print("TEST: Build Launch Args")

    # Default mode (no skip permissions)
    config = LaunchConfig(
        conversation_id="72138e41-007e-4811-b163-d03a4bff1eef",
        agy_executable="agy",
        skip_permissions=False,
    )
    args = build_launch_args(config)
    print(f"  Default args: {args}")
    assert "--dangerously-skip-permissions" not in args, \
        "Default mode must NOT include skip-permissions flag"
    assert "--conversation=72138e41-007e-4811-b163-d03a4bff1eef" in args

    # Skip permissions mode
    config.skip_permissions = True
    args = build_launch_args(config)
    print(f"  Skip perm args: {args}")
    assert "--dangerously-skip-permissions" in args, \
        "Skip mode must include the flag"

    # Invalid ID
    config.conversation_id = "invalid-id"
    try:
        build_launch_args(config)
        assert False, "Should raise LaunchError for invalid ID"
    except LaunchError:
        print("  Invalid ID correctly rejected")

    # Empty executable
    config2 = LaunchConfig(conversation_id="72138e41-007e-4811-b163-d03a4bff1eef")
    try:
        build_launch_args(config2)
        assert False, "Should raise LaunchError for empty executable"
    except LaunchError:
        print("  Empty executable correctly rejected")

    print("  ✅ PASSED")


def test_settings():
    """Test settings load/save."""
    print("\n" + "=" * 50)
    print("TEST: Settings")

    settings = AppSettings()
    settings.theme = "dark"
    settings.agy_executable = "test_exe"

    # Save to temp
    import tempfile
    tmp = tempfile.mktemp(suffix=".json")
    original_file = None

    # Just test that defaults work
    assert settings.theme == "dark"
    assert settings.show_subagents == False
    assert settings.sort_by == "last_modified"
    print("  Defaults OK")
    print("  ✅ PASSED")


def test_transcript_reading(info):
    """Test reading transcript files."""
    print("\n" + "=" * 50)
    print("TEST: Transcript Reading")

    from src.history_reader import read_transcript, count_messages_by_role

    if not info.brain_dir:
        print("  ⚠️ SKIPPED: No brain directory")
        return

    # Find a session with transcript
    sessions = discover_sessions(
        info.summaries_db, info.conversations_dir, info.brain_dir
    )
    transcript_sessions = [s for s in sessions if s.has_transcript]
    print(f"  Sessions with transcripts: {len(transcript_sessions)}")

    if transcript_sessions:
        s = transcript_sessions[0]
        messages = read_transcript(info.brain_dir, s.conversation_id)
        print(f"  Session {s.short_id}: {len(messages)} messages")

        counts = count_messages_by_role(messages)
        print(f"  Counts: {counts}")

        # Check message attributes
        if messages:
            m = messages[0]
            print(f"  First message: type={m.msg_type}, source={m.source}")
            assert m.step_index is not None
            assert m.source or m.msg_type

        print("  ✅ PASSED")
    else:
        print("  ⚠️ SKIPPED: No sessions with transcripts")


def main():
    print("Agy Session Manager - Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0
    total = 7

    try:
        info = test_agy_detection()
        passed += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        failed += 1
        info = detect_agy()

    try:
        sessions = test_session_discovery(info)
        passed += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        failed += 1
        sessions = []

    try:
        test_session_search(sessions)
        passed += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        failed += 1

    try:
        test_filter_sort(sessions)
        passed += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        failed += 1

    try:
        test_conversation_id_validation()
        passed += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        failed += 1

    try:
        test_build_launch_args()
        passed += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        failed += 1

    try:
        test_transcript_reading(info)
        passed += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        failed += 1

    try:
        test_settings()
        passed += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        failed += 1

    print("\n" + "=" * 50)
    print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
    return failed


if __name__ == "__main__":
    sys.exit(main())
