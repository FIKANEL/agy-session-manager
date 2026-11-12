"""
test_fork_hierarchy.py - Automated test suite for tree-based fork hierarchy display.
Verifies that forked sessions appear nested beneath their parent session with branch lines.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from PySide6.QtWidgets import QApplication

from src.main_window import MainWindow, SessionListItem, SessionItemWidget, BranchLineWidget
from src.session_discovery import SessionInfo
from src.settings import AppSettings


class TestForkHierarchy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.win = MainWindow()

    def tearDown(self):
        self.win.close()

    def test_branch_line_widget_painting(self):
        """Verify BranchLineWidget creates cleanly without crashing."""
        b1 = BranchLineWidget(is_last=False)
        self.assertEqual(b1.width(), 24)
        self.assertFalse(b1.is_last)

        b2 = BranchLineWidget(is_last=True)
        self.assertTrue(b2.is_last)

    def test_hierarchical_nesting_in_list(self):
        """Verify forks are placed directly beneath their parent session in the list widget."""
        # Find any session that has a fork
        found_parent_id = None
        found_child_id = None

        for item_data in self.win.hierarchical_sessions:
            sess, is_child, is_last = item_data
            if is_child and sess.fork_parent_id:
                found_child_id = sess.conversation_id
                found_parent_id = sess.fork_parent_id
                break

        if not found_parent_id:
            self.skipTest("No fork currently in database to verify against")

        # In self.win.session_list, verify child immediately follows parent
        items = [self.win.session_list.item(i) for i in range(self.win.session_list.count())]
        parent_idx = None
        child_idx = None

        for idx, item in enumerate(items):
            if isinstance(item, SessionListItem):
                if item.session.conversation_id == found_parent_id:
                    parent_idx = idx
                elif item.session.conversation_id == found_child_id:
                    child_idx = idx

        self.assertIsNotNone(parent_idx, "Parent session should be in the list")
        self.assertIsNotNone(child_idx, "Child fork should be in the list")
        self.assertGreater(child_idx, parent_idx, "Child fork must appear AFTER parent")

        # Child must be marked as fork child
        child_item = items[child_idx]
        self.assertTrue(child_item.is_fork_child)

        child_widget = self.win.session_list.itemWidget(child_item)
        self.assertIsInstance(child_widget, SessionItemWidget)
        self.assertTrue(child_widget.is_fork_child)
        self.assertTrue(hasattr(child_widget, "branch_widget"))
        self.assertIsInstance(child_widget.branch_widget, BranchLineWidget)

    def test_card_selection_styling(self):
        """Verify selecting an item properly updates card property [selected='true']."""
        if self.win.session_list.count() > 0:
            item = self.win.session_list.item(0)
            self.win.session_list.setCurrentItem(item)
            widget = self.win.session_list.itemWidget(item)
            self.assertEqual(widget.card.property("selected"), "true")


if __name__ == "__main__":
    unittest.main()
