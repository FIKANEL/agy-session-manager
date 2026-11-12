"""
rename_dialog.py - Clean Linear-styled modal dialog for renaming sessions.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.session_discovery import SessionInfo
from src.theme import DARK, TYPO, RAD
from src.icons import get_icon, get_pixmap


class RenameDialog(QDialog):
    """Dialog to set or reset a custom name for a session."""
    def __init__(self, session: SessionInfo, theme_mode: str = "dark", parent=None):
        super().__init__(parent)
        self.session = session
        self.theme_mode = theme_mode
        self.new_title: Optional[str] = None
        self.is_reset: bool = False

        self.setWindowTitle("Ganti Nama Session")
        self.setFixedWidth(460)
        self.setModal(True)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header with vector icon
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        icon_label = QLabel()
        icon_label.setPixmap(get_pixmap("edit", color=DARK.primary, size=18))
        header_row.addWidget(icon_label)

        title_label = QLabel("Ganti Nama Session")
        title_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        header_row.addWidget(title_label)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Session Original info box
        info_box = QFrame()
        info_box.setObjectName("commandBox")
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(10, 8, 10, 8)
        info_layout.setSpacing(4)

        orig_label = QLabel("Judul Asli:")
        orig_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        orig_label.setStyleSheet("color: #767b8a; background: transparent;")
        info_layout.addWidget(orig_label)

        orig_text = QLabel(self.session.original_title)
        orig_text.setFont(QFont("Segoe UI", 10))
        orig_text.setStyleSheet("color: #a6abb8; background: transparent;")
        orig_text.setWordWrap(True)
        info_layout.addWidget(orig_text)

        id_text = QLabel(f"ID: {self.session.conversation_id}")
        id_text.setFont(QFont("Cascadia Code", 9))
        id_text.setStyleSheet("color: #767b8a; background: transparent;")
        info_layout.addWidget(id_text)

        layout.addWidget(info_box)

        # Input label & line edit
        input_label = QLabel("Nama Baru Session:")
        input_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        layout.addWidget(input_label)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Contoh: Audit Smart Contract, Fix Bug Auth, dll...")
        current_name = self.session.custom_title or self.session.display_title
        self.input_field.setText(current_name)
        self.input_field.selectAll()
        layout.addWidget(self.input_field)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 6, 0, 0)
        btn_row.setSpacing(8)

        # Reset button (only active if custom title exists)
        self.btn_reset = QPushButton("  Reset ke Asli")
        self.btn_reset.setObjectName("ghostActionBtn")
        self.btn_reset.setIcon(get_icon("refresh", color=DARK.ink_secondary, size=13))
        self.btn_reset.setToolTip("Kembalikan nama ke judul asli bawaan sistem")
        self.btn_reset.clicked.connect(self._on_reset)
        if not self.session.custom_title:
            self.btn_reset.setEnabled(False)
        btn_row.addWidget(self.btn_reset)

        btn_row.addStretch()

        self.btn_cancel = QPushButton("  Batal")
        self.btn_cancel.setObjectName("secondaryActionBtn")
        self.btn_cancel.setIcon(get_icon("x", color=DARK.ink_secondary, size=13))
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("  Simpan")
        self.btn_save.setObjectName("primaryActionBtn")
        self.btn_save.setIcon(get_icon("check", color="#ffffff", size=13))
        self.btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(self.btn_save)

        layout.addLayout(btn_row)

        self.input_field.returnPressed.connect(self._on_save)

    def _on_save(self):
        text = self.input_field.text().strip()
        if text:
            self.new_title = text
            self.is_reset = False
            self.accept()
        else:
            # If user submitted empty string, treat as reset to original
            self._on_reset()

    def _on_reset(self):
        self.new_title = ""
        self.is_reset = True
        self.accept()
