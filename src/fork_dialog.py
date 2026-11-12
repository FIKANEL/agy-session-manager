"""
fork_dialog.py - Clean Linear x Raycast styled modal dialog for forking a session into an isolated branch.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.session_discovery import SessionInfo
from src.theme import DARK, TYPO, RAD
from src.icons import get_icon, get_pixmap


class ForkDialog(QDialog):
    """Dialog to configure and confirm forking a session into an independent branch."""
    def __init__(self, session: SessionInfo, theme_mode: str = "dark", parent=None):
        super().__init__(parent)
        self.session = session
        self.theme_mode = theme_mode

        self.fork_title: str = f"[Fork] {session.display_title}"
        self.mark_starred: bool = False
        self.auto_launch: bool = False

        self.setWindowTitle("Fork Session (Cabangkan)")
        self.setFixedWidth(500)
        self.setModal(True)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        # Header with vector icon
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        icon_label = QLabel()
        icon_label.setPixmap(get_pixmap("git-branch", color=DARK.primary, size=20))
        header_row.addWidget(icon_label)

        title_label = QLabel("Fork Session (Cabangkan)")
        title_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        header_row.addWidget(title_label)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Source Session Info Card
        info_box = QFrame()
        info_box.setObjectName("commandBox")
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(12, 10, 12, 10)
        info_layout.setSpacing(6)

        source_lbl = QLabel("Session Sumber:")
        source_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        source_lbl.setStyleSheet("color: #767b8a; background: transparent;")
        info_layout.addWidget(source_lbl)

        source_title = QLabel(self.session.display_title)
        source_title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        source_title.setStyleSheet("color: #f7f8f8; background: transparent;")
        source_title.setWordWrap(True)
        info_layout.addWidget(source_title)

        # Chips row: ID + Steps + Path
        chips_row = QHBoxLayout()
        chips_row.setContentsMargins(0, 2, 0, 0)
        chips_row.setSpacing(6)

        id_chip = QLabel(f"ID {self.session.short_id}")
        id_chip.setFont(QFont("Cascadia Code", 9))
        id_chip.setStyleSheet(
            "color: #a6abb8; background-color: #17181f; border: 1px solid #282b36; "
            "border-radius: 4px; padding: 1px 5px;"
        )
        chips_row.addWidget(id_chip)

        if self.session.step_count:
            step_chip = QLabel(f"{self.session.step_count} steps")
            step_chip.setFont(QFont("Segoe UI", 9))
            step_chip.setStyleSheet(
                "color: #a6abb8; background-color: #17181f; border: 1px solid #282b36; "
                "border-radius: 4px; padding: 1px 5px;"
            )
            chips_row.addWidget(step_chip)

        chips_row.addStretch()
        info_layout.addLayout(chips_row)

        layout.addWidget(info_box)

        # Explanation note
        note_label = QLabel(
            "Session baru akan diduplikasi secara terisolasi dengan seluruh konteks "
            "dan riwayat pesan. Anda dapat melanjutkan percakapan tanpa mengubah session aslinya."
        )
        note_label.setFont(QFont("Segoe UI", 9))
        note_label.setStyleSheet("color: #a6abb8; line-height: 1.4;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)

        # Input label & field
        input_label = QLabel("Nama Cabang / Session Baru:")
        input_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        layout.addWidget(input_label)

        self.input_field = QLineEdit()
        self.input_field.setText(self.fork_title)
        self.input_field.selectAll()
        layout.addWidget(self.input_field)

        # Options Checkboxes
        opts_layout = QVBoxLayout()
        opts_layout.setContentsMargins(0, 4, 0, 4)
        opts_layout.setSpacing(8)

        self.chk_starred = QCheckBox("Beri Bintang untuk Fork ini (Pin ke Atas)")
        self.chk_starred.setChecked(bool(self.session.is_starred))
        opts_layout.addWidget(self.chk_starred)

        self.chk_auto_launch = QCheckBox("Langsung buka / resume session baru di terminal")
        self.chk_auto_launch.setChecked(True)
        opts_layout.addWidget(self.chk_auto_launch)

        layout.addLayout(opts_layout)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 8, 0, 0)
        btn_row.setSpacing(8)

        btn_row.addStretch()

        self.btn_cancel = QPushButton("  Batal")
        self.btn_cancel.setObjectName("secondaryActionBtn")
        self.btn_cancel.setIcon(get_icon("x", color=DARK.ink_secondary, size=13))
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_cancel)

        self.btn_confirm = QPushButton("  Fork Session")
        self.btn_confirm.setObjectName("primaryActionBtn")
        self.btn_confirm.setIcon(get_icon("git-branch", color="#ffffff", size=13))
        self.btn_confirm.clicked.connect(self._on_confirm)
        btn_row.addWidget(self.btn_confirm)

        layout.addLayout(btn_row)

        self.input_field.returnPressed.connect(self._on_confirm)

    def _on_confirm(self):
        title = self.input_field.text().strip()
        if not title:
            title = f"[Fork] {self.session.display_title}"
        self.fork_title = title
        self.mark_starred = self.chk_starred.isChecked()
        self.auto_launch = self.chk_auto_launch.isChecked()
        self.accept()
