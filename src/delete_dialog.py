"""
delete_dialog.py - Confirmation dialogs for moving sessions to Trash and permanent deletion.
Styled with Linear x Raycast dark Brand DNA.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from src.session_discovery import SessionInfo
from src.theme import DARK
from src.icons import get_pixmap


class ConfirmTrashDialog(QDialog):
    """Confirmation modal before moving a session to the Trash."""
    def __init__(self, session: SessionInfo, child_fork_count: int = 0, parent=None):
        super().__init__(parent)
        self.session = session
        self.child_fork_count = child_fork_count

        self.setWindowTitle("Pindahkan Session ke Sampah")
        self.setFixedWidth(460)
        self.setModal(True)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header with trash icon
        header = QHBoxLayout()
        header.setSpacing(8)

        icon_label = QLabel()
        icon_label.setPixmap(get_pixmap("trash", color="#f87171", size=18))
        header.addWidget(icon_label)

        title = QLabel("Pindahkan ke Sampah?")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {DARK.ink_primary};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Session info card
        card = QFrame()
        card.setObjectName("commandBox")
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(12, 10, 12, 10)
        card_l.setSpacing(4)

        sess_title = QLabel(self.session.display_title)
        sess_title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        sess_title.setStyleSheet("color: #f7f8f8;")
        sess_title.setWordWrap(True)
        card_l.addWidget(sess_title)

        sub_info = QLabel(f"ID {self.session.short_id}  |  {self.session.step_count or 0} steps")
        sub_info.setFont(QFont("Cascadia Code", 9))
        sub_info.setStyleSheet(f"color: {DARK.ink_secondary};")
        card_l.addWidget(sub_info)

        layout.addWidget(card)

        # Explanation note
        note = QLabel(
            "Session akan dipindahkan ke menu Sampah dan disembunyikan dari daftar aktif. "
            "File percakapan tetap aman dan dapat dipulihkan kapan saja."
        )
        note.setFont(QFont("Segoe UI", 9))
        note.setStyleSheet(f"color: {DARK.ink_secondary};")
        note.setWordWrap(True)
        layout.addWidget(note)

        if self.child_fork_count > 0:
            fork_warn = QLabel(
                f"Perhatian: Session ini memiliki {self.child_fork_count} cabang (fork). "
                "Semua cabang fork juga akan ikut dipindahkan ke Sampah bersama sesi induk ini."
            )
            fork_warn.setFont(QFont("Segoe UI", 9))
            fork_warn.setStyleSheet("color: #fbbf24; background-color: #211c12; border: 1px solid #4d3c1b; border-radius: 4px; padding: 6px 8px;")
            fork_warn.setWordWrap(True)
            layout.addWidget(fork_warn)

        layout.addSpacing(4)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Batal")
        btn_cancel.setObjectName("secondaryActionBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_confirm = QPushButton("Pindahkan ke Sampah")
        btn_confirm.setObjectName("dangerActionBtn")
        btn_confirm.clicked.connect(self.accept)
        btn_row.addWidget(btn_confirm)

        layout.addLayout(btn_row)


class ConfirmPermanentDeleteDialog(QDialog):
    """Confirmation modal before permanently deleting a session from disk."""
    def __init__(self, session: SessionInfo, child_fork_count: int = 0, parent=None):
        super().__init__(parent)
        self.session = session
        self.child_fork_count = child_fork_count

        self.setWindowTitle("Hapus Permanen Session")
        self.setFixedWidth(480)
        self.setModal(True)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header with warning/trash icon
        header = QHBoxLayout()
        header.setSpacing(8)

        icon_label = QLabel()
        icon_label.setPixmap(get_pixmap("warning", color="#ef4444", size=20))
        header.addWidget(icon_label)

        title = QLabel("Hapus Permanen Session Ini?")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #ef4444;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Session info card
        card = QFrame()
        card.setObjectName("commandBox")
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(12, 10, 12, 10)
        card_l.setSpacing(4)

        sess_title = QLabel(self.session.display_title)
        sess_title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        sess_title.setStyleSheet("color: #f7f8f8;")
        sess_title.setWordWrap(True)
        card_l.addWidget(sess_title)

        sub_info = QLabel(f"ID {self.session.conversation_id}\nSteps: {self.session.step_count or 0}")
        sub_info.setFont(QFont("Cascadia Code", 9))
        sub_info.setStyleSheet(f"color: {DARK.ink_secondary};")
        card_l.addWidget(sub_info)

        layout.addWidget(card)

        # Danger Alert Box
        alert_box = QLabel(
            "PERINGATAN KERAS:\n"
            "- File database SQLite percakapan akan dihapus dari disk.\n"
            "- Direktori brain dan seluruh riwayat langkah akan dihapus.\n"
            "- Tindakan ini TIDAK DAPAT DIBATALKAN."
        )
        alert_box.setFont(QFont("Segoe UI", 9))
        alert_box.setStyleSheet(
            "color: #fca5a5; background-color: #2b1115; border: 1px solid #7f1d1d; "
            "border-radius: 6px; padding: 10px;"
        )
        alert_box.setWordWrap(True)
        layout.addWidget(alert_box)

        if self.child_fork_count > 0:
            fork_notice = QLabel(
                f"Catatan: Sesi ini memiliki {self.child_fork_count} cabang fork. "
                "Cabang fork akan dilepaskan menjadi sesi mandiri di Sampah (atau ikut dihapus jika dipilih)."
            )
            fork_notice.setFont(QFont("Segoe UI", 9))
            fork_notice.setStyleSheet("color: #cbd5e1; background-color: #17181f; border: 1px solid #282b36; border-radius: 4px; padding: 6px 8px;")
            fork_notice.setWordWrap(True)
            layout.addWidget(fork_notice)

        layout.addSpacing(4)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Batal")
        btn_cancel.setObjectName("secondaryActionBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_confirm = QPushButton("Hapus Permanen")
        btn_confirm.setObjectName("solidDangerBtn")
        btn_confirm.clicked.connect(self.accept)
        btn_row.addWidget(btn_confirm)

        layout.addLayout(btn_row)


class ConfirmEmptyTrashDialog(QDialog):
    """Confirmation modal before permanently emptying all items in Trash."""
    def __init__(self, count: int, parent=None):
        super().__init__(parent)
        self.count = count

        self.setWindowTitle("Kosongkan Semua Sampah")
        self.setFixedWidth(440)
        self.setModal(True)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        header.setSpacing(8)

        icon_label = QLabel()
        icon_label.setPixmap(get_pixmap("warning", color="#ef4444", size=20))
        header.addWidget(icon_label)

        title = QLabel("Kosongkan Semua Sampah?")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #ef4444;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        alert_box = QLabel(
            f"Anda akan menghapus permanen SEMUA {self.count} session yang berada di menu Sampah.\n\n"
            "Semua file database SQLite dan folder brain terkait akan dihapus secara fisik dari disk. "
            "Tindakan ini bersifat permanen dan tidak dapat dibatalkan."
        )
        alert_box.setFont(QFont("Segoe UI", 9))
        alert_box.setStyleSheet(
            "color: #fca5a5; background-color: #2b1115; border: 1px solid #7f1d1d; "
            "border-radius: 6px; padding: 10px;"
        )
        alert_box.setWordWrap(True)
        layout.addWidget(alert_box)

        layout.addSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Batal")
        btn_cancel.setObjectName("secondaryActionBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_confirm = QPushButton("Kosongkan Sampah")
        btn_confirm.setObjectName("solidDangerBtn")
        btn_confirm.clicked.connect(self.accept)
        btn_row.addWidget(btn_confirm)

        layout.addLayout(btn_row)
