"""
main_window.py - Main application window for Agy Session Manager.
Re-architected with Linear x Raycast Brand DNA, zero emoji, high contrast,
manual 2-line title clamping, and dedicated monospace command bar.
"""
import os
import subprocess
from typing import List, Optional, Tuple, Dict, Set

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QLabel, QPushButton, QLineEdit,
    QScrollArea, QFrame, QComboBox, QRadioButton,
    QStatusBar, QMessageBox, QApplication, QButtonGroup,
    QCheckBox, QTextBrowser, QPlainTextEdit, QMenu,
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QFontMetrics, QPainter, QColor, QPen

from src.agy_detector import detect_agy, AgyInfo
from src.session_discovery import discover_sessions, SessionInfo
from src.history_reader import read_transcript, ChatMessage, count_messages_by_role
from src.session_search import search_sessions, filter_sessions, sort_sessions
from src.session_launcher import (
    LaunchConfig, launch_session, build_command_string, LaunchError
)
from src.settings import AppSettings, load_settings, save_settings
from src.theme import get_stylesheet, DARK, LIGHT, TYPO
from src.icons import get_icon, get_pixmap
from src.rename_dialog import RenameDialog
from src.fork_dialog import ForkDialog
from src.session_fork import fork_session, ForkError
from src.delete_dialog import (
    ConfirmTrashDialog, ConfirmPermanentDeleteDialog, ConfirmEmptyTrashDialog
)
from src.session_deletion import permanently_delete_session, DeletionError


def clamp_title_2lines(text: str, fm: QFontMetrics, width: int) -> str:
    """Manually clamp title to strictly at most 2 lines with clean word break and ellipsis."""
    if not text:
        return ""
    clean_text = " ".join(text.split())
    if width <= 30:
        return clean_text[:20] + "..."

    # If fits on 1 line
    if fm.horizontalAdvance(clean_text) <= width:
        return clean_text

    words = clean_text.split(" ")
    line1_words = []
    current_w = 0
    idx = 0

    for i, w in enumerate(words):
        space_w = fm.horizontalAdvance(" ") if line1_words else 0
        w_w = fm.horizontalAdvance(w)
        if current_w + space_w + w_w > width:
            if not line1_words:
                # Word itself exceeds width -> slice characters
                char_idx = 0
                accum_w = 0
                for c in w:
                    cw = fm.horizontalAdvance(c)
                    if accum_w + cw > width:
                        break
                    accum_w += cw
                    char_idx += 1
                line1 = w[:max(1, char_idx)]
                remaining = w[max(1, char_idx):] + (
                    " " + " ".join(words[1:]) if len(words) > 1 else ""
                )
                line2 = fm.elidedText(remaining, Qt.TextElideMode.ElideRight, width)
                return f"{line1}\n{line2}"
            idx = i
            break
        current_w += space_w + w_w
        line1_words.append(w)
    else:
        return " ".join(line1_words)

    line1 = " ".join(line1_words)
    remaining = " ".join(words[idx:])
    line2 = fm.elidedText(remaining, Qt.TextElideMode.ElideRight, width)
    return f"{line1}\n{line2}"


class BranchLineWidget(QWidget):
    """Draws an anti-aliased tree branch line connector from parent to forked session."""
    def __init__(self, is_last: bool = True, parent=None):
        super().__init__(parent)
        self.is_last = is_last
        self.setFixedWidth(24)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        mid_x = 10
        mid_y = h // 2

        # Branch line
        pen = QPen(QColor("#45495e"), 1.8)
        painter.setPen(pen)

        # Top edge to center
        painter.drawLine(mid_x, 0, mid_x, mid_y)
        # Center to right edge (into card)
        painter.drawLine(mid_x, mid_y, w, mid_y)

        # Trunk continuation downwards if more siblings follow
        if not self.is_last:
            painter.drawLine(mid_x, mid_y, mid_x, h)

        # Junction node dot (Linear purple/indigo accent)
        painter.setBrush(QColor("#5e6ad2"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(mid_x - 3, mid_y - 3, 7, 7)
        painter.end()


class SessionListItem(QListWidgetItem):
    """Custom list item that holds a SessionInfo reference and hierarchy metadata."""
    def __init__(self, session: SessionInfo, is_fork_child: bool = False, is_last_fork: bool = True):
        super().__init__()
        self.session = session
        self.is_fork_child = is_fork_child
        self.is_last_fork = is_last_fork
        self.setText("")
        self.setSizeHint(QSize(0, 72 if is_fork_child else 76))


class SessionItemWidget(QWidget):
    """Widget displayed in each session list item with card container and branch line support."""
    def __init__(self, session: SessionInfo, is_fork_child: bool = False, is_last_fork: bool = True, parent=None):
        super().__init__(parent)
        self.session = session
        self.is_fork_child = is_fork_child
        self.is_last_fork = is_last_fork
        self.raw_title = session.display_title

        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Branch line on the left if this is a child fork
        if is_fork_child:
            self.branch_widget = BranchLineWidget(is_last=is_last_fork, parent=self)
            outer_layout.addWidget(self.branch_widget)

        # Inner card container
        self.card = QFrame()
        self.card.setObjectName("forkCard" if is_fork_child else "sessionCard")
        outer_layout.addWidget(self.card, 1)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(10, 7 if is_fork_child else 8, 10, 7 if is_fork_child else 8)
        card_layout.setSpacing(4)

        # Top row: Star icon (if starred) + 2-line title label
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)

        if session.is_starred:
            star_label = QLabel()
            star_label.setPixmap(get_pixmap("star-filled", color=DARK.star_active, size=13))
            star_label.setStyleSheet("background-color: transparent;")
            star_label.setToolTip("Session Berbintang (Favorit)")
            top_row.addWidget(star_label)

        # 2-line title label
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Segoe UI", 10 if is_fork_child else 11, QFont.Weight.DemiBold))
        title_color = "#9bb2ff" if is_fork_child else "#f7f8f8"
        self.title_label.setStyleSheet(f"color: {title_color}; background-color: transparent;")
        self.title_label.setWordWrap(False)
        top_row.addWidget(self.title_label, 1)

        card_layout.addLayout(top_row)

        # Bottom row: ID chip, custom chip, fork chip, steps chip, time
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.setSpacing(6)

        # ID Chip
        id_chip = QLabel(f"ID {session.short_id}")
        id_chip.setFont(QFont("Cascadia Code", 9))
        id_chip.setStyleSheet(
            "color: #a6abb8; background-color: #17181f; border: 1px solid #282b36; "
            "border-radius: 4px; padding: 1px 5px;"
        )
        bottom.addWidget(id_chip)

        # Custom name chip (if renamed)
        if session.custom_title:
            custom_chip = QLabel("Custom")
            custom_chip.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            custom_chip.setStyleSheet(
                "color: #8ba2ff; background-color: #161a29; border: 1px solid #283556; "
                "border-radius: 4px; padding: 1px 4px;"
            )
            custom_chip.setToolTip(f"Judul Asli: {session.original_title}")
            bottom.addWidget(custom_chip)

        # Fork chip (if forked session)
        if session.is_fork:
            fork_chip = QLabel("Fork")
            fork_chip.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            fork_chip.setStyleSheet(
                "color: #82aaff; background-color: #181d2e; border: 1px solid #2b3758; "
                "border-radius: 4px; padding: 1px 4px;"
            )
            parent_tip = (
                f"Cabang (Fork) dari: {session.fork_parent_title or session.fork_parent_id[:8]}"
                if session.fork_parent_id else "Session Hasil Fork"
            )
            fork_chip.setToolTip(parent_tip)
            bottom.addWidget(fork_chip)

        # Step count chip
        if session.step_count:
            steps_chip = QLabel(f"{session.step_count} steps")
            steps_chip.setFont(QFont("Segoe UI", 9))
            steps_chip.setStyleSheet(
                "color: #a6abb8; background-color: #17181f; border: 1px solid #282b36; "
                "border-radius: 4px; padding: 1px 5px;"
            )
            bottom.addWidget(steps_chip)

        bottom.addStretch()

        # Last modified time
        time_label = QLabel(session.last_modified_display)
        time_label.setFont(QFont("Segoe UI", 9))
        time_label.setStyleSheet("color: #767b8a; background-color: transparent;")
        bottom.addWidget(time_label)

        card_layout.addLayout(bottom)

        tt_parts = [f"Title: {self.raw_title}"]
        if session.custom_title:
            tt_parts.append(f"Judul Asli: {session.original_title}")
        if session.is_fork:
            parent_info = session.fork_parent_title or session.fork_parent_id
            tt_parts.append(f"Cabang (Fork) dari: {parent_info}")
        if session.is_starred:
            tt_parts.append("Status: Berbintang (Favorit)")
        tt_parts.extend([
            f"Conversation ID: {session.conversation_id}",
            f"Steps: {session.step_count}",
            f"Workspace: {session.workspace_display}",
            f"Last Modified: {session.last_modified_display}"
        ])
        self.setToolTip("\n".join(tt_parts))

        self._update_clamped_text()

    def set_selected(self, is_selected: bool):
        self.card.setProperty("selected", "true" if is_selected else "false")
        self.card.style().unpolish(self.card)
        self.card.style().polish(self.card)

    def _update_clamped_text(self):
        star_offset = 20 if self.session.is_starred else 0
        indent_offset = 24 if self.is_fork_child else 0
        avail_w = max(80, self.width() - 24 - star_offset - indent_offset)
        fm = QFontMetrics(self.title_label.font())
        clamped = clamp_title_2lines(self.raw_title, fm, avail_w)
        self.title_label.setText(clamped)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_clamped_text()


class ChatBubbleWidget(QFrame):
    """Widget for a single chat message bubble with distinct left accent strips."""
    def __init__(self, msg: ChatMessage, parent=None):
        super().__init__(parent)
        self.msg = msg

        if msg.is_user:
            self.setObjectName("userMsg")
        elif msg.is_assistant:
            self.setObjectName("assistantMsg")
        else:
            self.setObjectName("systemMsg")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        # Header: Role badge + Icon + Timestamp
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        # Role icon & text
        icon_name = "user" if msg.is_user else ("cpu" if msg.is_assistant else "terminal")
        badge_color = DARK.user_badge if msg.is_user else (DARK.assistant_badge if msg.is_assistant else DARK.ink_subtle)
        role_text = "USER" if msg.is_user else ("AGY ASSISTANT" if msg.is_assistant else "SYSTEM")

        icon_label = QLabel()
        icon_label.setPixmap(get_pixmap(icon_name, color=badge_color, size=13))
        icon_label.setStyleSheet("background-color: transparent;")
        header.addWidget(icon_label)

        role_label = QLabel(role_text)
        role_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        role_label.setStyleSheet(f"color: {badge_color}; background-color: transparent;")
        header.addWidget(role_label)

        header.addStretch()

        if msg.time_display:
            time_label = QLabel(msg.time_display)
            time_label.setFont(QFont("Segoe UI", 9))
            time_label.setStyleSheet(f"color: {DARK.ink_subtle}; background-color: transparent;")
            header.addWidget(time_label)

        layout.addLayout(header)

        # Message Body
        content_text = msg.clean_content if msg.is_user else (msg.content or "")
        if content_text:
            display_text = content_text
            if len(display_text) > 8000:
                display_text = display_text[:8000] + "\n\n[Content truncated for display]"

            if len(display_text) <= 2500:
                content_label = QLabel(display_text)
                content_label.setWordWrap(True)
                content_label.setTextFormat(Qt.TextFormat.PlainText)
                content_label.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse |
                    Qt.TextInteractionFlag.LinksAccessibleByMouse
                )
                content_label.setStyleSheet(
                    f"background: transparent; border: none; color: {DARK.ink_primary}; "
                    f"font-family: {TYPO.font_family_ui}; font-size: 13px; line-height: 1.5;"
                )
                layout.addWidget(content_label)
            else:
                content_box = QPlainTextEdit()
                content_box.setReadOnly(True)
                content_box.setPlainText(display_text)
                content_box.setFrameShape(QFrame.Shape.NoFrame)
                content_box.setStyleSheet(
                    f"QPlainTextEdit {{ background: transparent; border: none; color: {DARK.ink_primary}; "
                    f"font-family: {TYPO.font_family_ui}; font-size: 13px; line-height: 1.5; }}"
                )
                content_box.setMaximumHeight(350)
                layout.addWidget(content_box)

        # Footer Chips: Tool calls & Tokens
        chips_row = QHBoxLayout()
        chips_row.setContentsMargins(0, 2, 0, 0)
        chips_row.setSpacing(6)

        if msg.tool_calls:
            tc_count = len(msg.tool_calls)
            tc_chip = QLabel(f"{tc_count} tool call{'s' if tc_count > 1 else ''}")
            tc_chip.setFont(QFont("Cascadia Code", 9))
            tc_chip.setStyleSheet(
                f"color: {DARK.tool_chip_ink}; background-color: {DARK.tool_chip_bg}; "
                f"border: 1px solid {DARK.tool_chip_border}; border-radius: 4px; padding: 2px 6px;"
            )
            chips_row.addWidget(tc_chip)

        if msg.is_assistant and (msg.input_tokens or msg.output_tokens):
            token_chip = QLabel(f"tokens: {msg.input_tokens:,} in / {msg.output_tokens:,} out")
            token_chip.setFont(QFont("Cascadia Code", 9))
            token_chip.setStyleSheet(
                f"color: {DARK.tool_chip_ink}; background-color: {DARK.tool_chip_bg}; "
                f"border: 1px solid {DARK.tool_chip_border}; border-radius: 4px; padding: 2px 6px;"
            )
            chips_row.addWidget(token_chip)

        chips_row.addStretch()
        if msg.tool_calls or (msg.is_assistant and (msg.input_tokens or msg.output_tokens)):
            layout.addLayout(chips_row)


class LoadMoreWidget(QFrame):
    """Pagination banner to load earlier messages without freezing the UI."""
    def __init__(self, hidden_count: int, total_count: int, on_load_more, on_load_all, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"LoadMoreWidget {{ background-color: {DARK.surface_card}; "
            f"border: 1px solid {DARK.hairline_strong}; border-radius: 6px; }}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(10)

        info_label = QLabel(f"Menampilkan pesan terbaru ({total_count - hidden_count} dari {total_count} pesan)")
        info_label.setFont(QFont("Segoe UI", 9))
        info_label.setStyleSheet(f"color: {DARK.ink_secondary}; background: transparent;")
        layout.addWidget(info_label)

        layout.addStretch()

        btn_more = QPushButton(f"Muat {min(40, hidden_count)} Pesan Sebelumnya")
        btn_more.setFont(QFont("Segoe UI", 9))
        btn_more.setStyleSheet(
            f"QPushButton {{ background-color: {DARK.secondary_bg}; color: {DARK.secondary_ink}; "
            f"border: 1px solid {DARK.secondary_border}; border-radius: 4px; padding: 4px 10px; }} "
            f"QPushButton:hover {{ background-color: {DARK.secondary_hover}; border-color: {DARK.primary}; }}"
        )
        btn_more.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_more.clicked.connect(on_load_more)
        layout.addWidget(btn_more)

        if hidden_count > 40:
            btn_all = QPushButton(f"Muat Semua ({hidden_count})")
            btn_all.setFont(QFont("Segoe UI", 9))
            btn_all.setStyleSheet(
                f"QPushButton {{ background-color: transparent; color: {DARK.primary}; "
                f"border: 1px solid {DARK.primary}; border-radius: 4px; padding: 4px 10px; }} "
                f"QPushButton:hover {{ background-color: {DARK.primary}; color: #ffffff; }}"
            )
            btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_all.clicked.connect(on_load_all)
            layout.addWidget(btn_all)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agy Session Manager")
        self.settings = load_settings()
        self.agy_info: Optional[AgyInfo] = None
        self.sessions: List[SessionInfo] = []
        self.filtered_sessions: List[SessionInfo] = []
        self.hierarchical_sessions: List[Tuple[SessionInfo, bool, bool]] = []
        self.current_session: Optional[SessionInfo] = None
        self.current_messages: List[ChatMessage] = []
        self.current_display_messages: List[ChatMessage] = []
        self.rendered_msg_start_idx: int = 0
        self.load_more_widget: Optional[LoadMoreWidget] = None
        self.PAGE_SIZE: int = 40

        self._selection_timer = QTimer(self)
        self._selection_timer.setSingleShot(True)
        self._selection_timer.setInterval(60)
        self._selection_timer.timeout.connect(self._do_load_chat_history)

        self.current_full_command: str = ""
        self.current_view: str = "all"

        self.resize(self.settings.window_width, self.settings.window_height)
        self.setMinimumWidth(800)
        self.setMinimumHeight(550)

        self._init_ui()
        self._apply_theme()
        self._detect_agy()
        self._refresh_sessions()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==========================================
        # 1. SIDEBAR
        # ==========================================
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 14, 10, 14)
        sidebar_layout.setSpacing(6)

        # Brand Header (Vector Icon + Title)
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(4, 2, 4, 6)
        brand_row.setSpacing(8)

        brand_icon = QLabel()
        brand_icon.setPixmap(get_pixmap("terminal", color=DARK.primary, size=18))
        brand_row.addWidget(brand_icon)

        app_title = QLabel("Agy Manager")
        app_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        app_title.setStyleSheet(f"color: {DARK.ink_primary};")
        brand_row.addWidget(app_title)
        brand_row.addStretch()

        sidebar_layout.addLayout(brand_row)
        sidebar_layout.addSpacing(6)

        # Navigation Buttons (Vector icons)
        self.btn_all = QPushButton("  Semua Session")
        self.btn_all.setIcon(get_icon("layers", color=DARK.ink_secondary, size=15))
        self.btn_all.setCheckable(True)
        self.btn_all.setChecked(True)
        self.btn_all.clicked.connect(lambda: self._set_view("all"))

        self.btn_starred = QPushButton("  Session Berbintang")
        self.btn_starred.setIcon(get_icon("star-filled", color=DARK.star_active, size=15))
        self.btn_starred.setCheckable(True)
        self.btn_starred.clicked.connect(lambda: self._set_view("starred"))

        self.btn_recent = QPushButton("  Session Terbaru")
        self.btn_recent.setIcon(get_icon("clock", color=DARK.ink_secondary, size=15))
        self.btn_recent.setCheckable(True)
        self.btn_recent.clicked.connect(lambda: self._set_view("recent"))

        self.btn_trash = QPushButton("  Sampah")
        self.btn_trash.setIcon(get_icon("trash", color=DARK.ink_secondary, size=15))
        self.btn_trash.setCheckable(True)
        self.btn_trash.clicked.connect(lambda: self._set_view("trash"))

        self.btn_nav_group = QButtonGroup(self)
        self.btn_nav_group.addButton(self.btn_all)
        self.btn_nav_group.addButton(self.btn_starred)
        self.btn_nav_group.addButton(self.btn_recent)
        self.btn_nav_group.addButton(self.btn_trash)

        sidebar_layout.addWidget(self.btn_all)
        sidebar_layout.addWidget(self.btn_starred)
        sidebar_layout.addWidget(self.btn_recent)
        sidebar_layout.addWidget(self.btn_trash)

        sidebar_layout.addSpacing(14)

        # Filter section
        lbl_filters = QLabel("FILTER & URUTAN")
        lbl_filters.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_filters.setStyleSheet(f"color: {DARK.ink_subtle}; letter-spacing: 0.5px;")
        lbl_filters.setContentsMargins(4, 0, 4, 2)
        sidebar_layout.addWidget(lbl_filters)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Terakhir Digunakan",
            "Terlama",
            "Judul (A-Z)",
            "Jumlah Step"
        ])
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        sidebar_layout.addWidget(self.sort_combo)

        sidebar_layout.addSpacing(4)

        self.chk_subagents = QCheckBox("Tampilkan Sub-agent")
        self.chk_subagents.setChecked(self.settings.show_subagents)
        self.chk_subagents.stateChanged.connect(self._on_filter_changed)
        sidebar_layout.addWidget(self.chk_subagents)

        sidebar_layout.addStretch()

        # Sidebar Footer
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {DARK.hairline}; max-height: 1px;")
        sidebar_layout.addWidget(sep)
        sidebar_layout.addSpacing(6)

        # Agy CLI Status indicator
        status_box = QHBoxLayout()
        status_box.setContentsMargins(4, 2, 4, 2)
        status_box.setSpacing(6)

        self.status_icon = QLabel()
        self.status_icon.setPixmap(get_pixmap("check-circle", color=DARK.success, size=13))
        status_box.addWidget(self.status_icon)

        self.lbl_agy_status = QLabel("Checking Agy CLI...")
        self.lbl_agy_status.setFont(QFont("Segoe UI", 10))
        self.lbl_agy_status.setStyleSheet(f"color: {DARK.ink_secondary};")
        status_box.addWidget(self.lbl_agy_status)
        status_box.addStretch()

        sidebar_layout.addLayout(status_box)

        # Settings & Theme Toggle
        self.btn_settings = QPushButton("  Pengaturan")
        self.btn_settings.setIcon(get_icon("settings", color=DARK.ink_secondary, size=15))
        self.btn_settings.setObjectName("ghostActionBtn")
        self.btn_settings.clicked.connect(self._show_settings_dialog)
        sidebar_layout.addWidget(self.btn_settings)

        self.btn_theme = QPushButton("  Dark Mode")
        self.btn_theme.setIcon(get_icon("moon", color=DARK.ink_secondary, size=15))
        self.btn_theme.setObjectName("ghostActionBtn")
        self.btn_theme.clicked.connect(self._toggle_theme)
        sidebar_layout.addWidget(self.btn_theme)

        main_layout.addWidget(sidebar)

        # ==========================================
        # 2. MAIN SPLITTER (Middle List + Right Viewer)
        # ==========================================
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Center Panel: Session List ---
        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)

        # Search Bar + Raycast Icon Refresh Button
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(10, 10, 10, 6)
        search_layout.setSpacing(6)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari session (ID, judul, kata kunci)...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        self.btn_refresh = QPushButton()
        self.btn_refresh.setObjectName("iconToolBtn")
        self.btn_refresh.setFixedSize(34, 34)
        self.btn_refresh.setIcon(get_icon("refresh", color=DARK.ink_secondary, size=16))
        self.btn_refresh.setToolTip("Refresh Sessions")
        self.btn_refresh.clicked.connect(self._refresh_sessions)
        search_layout.addWidget(self.btn_refresh)

        list_layout.addWidget(search_container)

        # Session Count & Empty Trash Row
        count_row = QHBoxLayout()
        count_row.setContentsMargins(12, 0, 12, 6)
        count_row.setSpacing(6)

        self.lbl_count = QLabel("0 session")
        self.lbl_count.setFont(QFont("Segoe UI", 10))
        self.lbl_count.setStyleSheet(f"color: {DARK.ink_subtle};")
        count_row.addWidget(self.lbl_count)
        count_row.addStretch()

        self.btn_empty_trash = QPushButton("  Kosongkan Sampah")
        self.btn_empty_trash.setObjectName("dangerActionBtn")
        self.btn_empty_trash.setIcon(get_icon("trash", color="#f87171", size=13))
        self.btn_empty_trash.setToolTip("Hapus permanen semua session di folder Sampah")
        self.btn_empty_trash.setVisible(False)
        self.btn_empty_trash.clicked.connect(self._prompt_empty_trash)
        count_row.addWidget(self.btn_empty_trash)

        list_layout.addLayout(count_row)

        # Session List
        self.session_list = QListWidget()
        self.session_list.setObjectName("sessionList")
        self.session_list.currentItemChanged.connect(self._on_session_selected)
        self.session_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.session_list.customContextMenuRequested.connect(self._show_session_context_menu)
        list_layout.addWidget(self.session_list)

        self.splitter.addWidget(list_panel)

        # --- Right Panel: Detail & Chat Viewer ---
        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(0)

        # Detail Header
        self.detail_header = QWidget()
        header_layout = QVBoxLayout(self.detail_header)
        header_layout.setContentsMargins(18, 14, 18, 12)
        header_layout.setSpacing(8)

        # Title Row: Star Button + Title + Rename Button
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)

        self.btn_detail_star = QPushButton()
        self.btn_detail_star.setObjectName("starBtn")
        self.btn_detail_star.setFixedSize(32, 32)
        self.btn_detail_star.setIcon(get_icon("star", color=DARK.ink_disabled, size=16))
        self.btn_detail_star.setToolTip("Beri Bintang (Pin ke Atas)")
        self.btn_detail_star.setEnabled(False)
        self.btn_detail_star.clicked.connect(self._toggle_current_star)
        title_row.addWidget(self.btn_detail_star)

        self.lbl_detail_title = QLabel("Pilih Session")
        self.lbl_detail_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lbl_detail_title.setStyleSheet(f"color: {DARK.ink_primary};")
        self.lbl_detail_title.setWordWrap(True)
        title_row.addWidget(self.lbl_detail_title, 1)

        self.btn_rename = QPushButton("  Rename")
        self.btn_rename.setObjectName("secondaryActionBtn")
        self.btn_rename.setIcon(get_icon("edit", color=DARK.ink_secondary, size=13))
        self.btn_rename.setToolTip("Ganti nama session ini agar mudah dikenali")
        self.btn_rename.setEnabled(False)
        self.btn_rename.clicked.connect(self._prompt_rename_current_session)
        title_row.addWidget(self.btn_rename)

        header_layout.addLayout(title_row)

        # Metadata Chips Row (ID, steps, workspace, time)
        self.meta_row = QHBoxLayout()
        self.meta_row.setContentsMargins(0, 0, 0, 0)
        self.meta_row.setSpacing(6)

        self.chip_id = QLabel("")
        self.chip_id.setFont(QFont("Cascadia Code", 10))
        self.chip_id.setStyleSheet(
            f"color: {DARK.ink_secondary}; background-color: {DARK.surface_input}; "
            f"border: 1px solid {DARK.hairline}; border-radius: 4px; padding: 2px 7px;"
        )
        self.chip_id.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.meta_row.addWidget(self.chip_id)

        self.chip_steps = QLabel("")
        self.chip_steps.setFont(QFont("Segoe UI", 10))
        self.chip_steps.setStyleSheet(
            f"color: {DARK.ink_secondary}; background-color: {DARK.surface_input}; "
            f"border: 1px solid {DARK.hairline}; border-radius: 4px; padding: 2px 7px;"
        )
        self.meta_row.addWidget(self.chip_steps)

        self.chip_workspace = QLabel("")
        self.chip_workspace.setFont(QFont("Segoe UI", 10))
        self.chip_workspace.setStyleSheet(
            f"color: {DARK.ink_secondary}; background-color: {DARK.surface_input}; "
            f"border: 1px solid {DARK.hairline}; border-radius: 4px; padding: 2px 7px;"
        )
        self.meta_row.addWidget(self.chip_workspace)

        self.meta_row.addStretch()
        header_layout.addLayout(self.meta_row)

        # Action Buttons Row (Clear Hierarchy)
        actions_row = QHBoxLayout()
        actions_row.setContentsMargins(0, 4, 0, 2)
        actions_row.setSpacing(8)

        # Primary Action
        self.btn_resume = QPushButton("  Resume Session")
        self.btn_resume.setObjectName("primaryActionBtn")
        self.btn_resume.setIcon(get_icon("play", color="#ffffff", size=13))
        self.btn_resume.clicked.connect(self._on_resume)
        self.btn_resume.setEnabled(False)
        actions_row.addWidget(self.btn_resume)

        # Secondary Actions
        self.btn_copy_id = QPushButton("  Copy ID")
        self.btn_copy_id.setObjectName("secondaryActionBtn")
        self.btn_copy_id.setIcon(get_icon("copy", color=DARK.ink_secondary, size=13))
        self.btn_copy_id.clicked.connect(self._copy_session_id)
        self.btn_copy_id.setEnabled(False)
        actions_row.addWidget(self.btn_copy_id)

        self.btn_copy_cmd = QPushButton("  Copy Command")
        self.btn_copy_cmd.setObjectName("secondaryActionBtn")
        self.btn_copy_cmd.setIcon(get_icon("terminal", color=DARK.ink_secondary, size=13))
        self.btn_copy_cmd.clicked.connect(self._copy_launch_command)
        self.btn_copy_cmd.setEnabled(False)
        actions_row.addWidget(self.btn_copy_cmd)

        self.btn_fork = QPushButton("  Fork")
        self.btn_fork.setObjectName("secondaryActionBtn")
        self.btn_fork.setIcon(get_icon("git-branch", color=DARK.ink_secondary, size=13))
        self.btn_fork.setToolTip("Cabangkan (Fork) session ini ke branch baru secara terisolasi")
        self.btn_fork.clicked.connect(self._prompt_fork_current_session)
        self.btn_fork.setEnabled(False)
        actions_row.addWidget(self.btn_fork)

        # Tertiary / Ghost Action
        self.btn_open_dir = QPushButton("  Open Folder")
        self.btn_open_dir.setObjectName("ghostActionBtn")
        self.btn_open_dir.setIcon(get_icon("folder", color=DARK.ink_secondary, size=13))
        self.btn_open_dir.clicked.connect(self._open_session_folder)
        self.btn_open_dir.setEnabled(False)
        actions_row.addWidget(self.btn_open_dir)

        # Trash Actions
        self.btn_move_trash = QPushButton("  Ke Sampah")
        self.btn_move_trash.setObjectName("dangerActionBtn")
        self.btn_move_trash.setIcon(get_icon("trash", color="#f87171", size=13))
        self.btn_move_trash.setToolTip("Pindahkan session ini ke Sampah (bisa dipulihkan)")
        self.btn_move_trash.clicked.connect(self._prompt_trash_current_session)
        self.btn_move_trash.setEnabled(False)
        actions_row.addWidget(self.btn_move_trash)

        self.btn_restore = QPushButton("  Pulihkan")
        self.btn_restore.setObjectName("primaryActionBtn")
        self.btn_restore.setIcon(get_icon("rotate-ccw", color="#ffffff", size=13))
        self.btn_restore.setToolTip("Pulihkan session ini kembali ke daftar aktif")
        self.btn_restore.clicked.connect(self._restore_current_session)
        self.btn_restore.setEnabled(False)
        self.btn_restore.setVisible(False)
        actions_row.addWidget(self.btn_restore)

        self.btn_perm_delete = QPushButton("  Hapus Permanen")
        self.btn_perm_delete.setObjectName("solidDangerBtn")
        self.btn_perm_delete.setIcon(get_icon("trash", color="#ffffff", size=13))
        self.btn_perm_delete.setToolTip("Hapus permanen file percakapan SQLite dan brain dari komputer")
        self.btn_perm_delete.clicked.connect(self._prompt_permanent_delete_current_session)
        self.btn_perm_delete.setEnabled(False)
        self.btn_perm_delete.setVisible(False)
        actions_row.addWidget(self.btn_perm_delete)

        actions_row.addStretch()
        header_layout.addLayout(actions_row)

        # Permissions Mode Row
        perm_row = QHBoxLayout()
        perm_row.setContentsMargins(0, 2, 0, 2)
        perm_row.setSpacing(12)

        perm_label = QLabel("Mode Permission:")
        perm_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        perm_label.setStyleSheet(f"color: {DARK.ink_secondary};")
        perm_row.addWidget(perm_label)

        self.radio_default = QRadioButton("Default")
        self.radio_default.setChecked(True)
        self.radio_default.setToolTip("Jalankan dengan izin standard interaktif")
        perm_row.addWidget(self.radio_default)

        # Skip permissions with caution pill
        self.radio_skip = QRadioButton("Skip Permissions")
        self.radio_skip.setToolTip(
            "Jalankan dengan --dangerously-skip-permissions\n"
            "PERINGATAN: Melewati konfirmasi izin tool execution"
        )
        perm_row.addWidget(self.radio_skip)

        self.perm_warning_badge = QFrame()
        self.perm_warning_badge.setObjectName("permWarningBadge")
        badge_layout = QHBoxLayout(self.perm_warning_badge)
        badge_layout.setContentsMargins(6, 2, 6, 2)
        badge_layout.setSpacing(4)

        warn_icon = QLabel()
        warn_icon.setPixmap(get_pixmap("warning", color=DARK.warning, size=12))
        warn_icon.setStyleSheet("background-color: transparent;")
        badge_layout.addWidget(warn_icon)

        warn_text = QLabel("Bypass Security")
        warn_text.setObjectName("permWarningText")
        badge_layout.addWidget(warn_text)

        perm_row.addWidget(self.perm_warning_badge)
        perm_row.addStretch()

        header_layout.addLayout(perm_row)

        self.radio_default.toggled.connect(self._update_cmd_preview)
        self.radio_skip.toggled.connect(self._update_cmd_preview)

        # Dedicated Monospace Command Box (Raycast Terminal Pill)
        self.command_box = QFrame()
        self.command_box.setObjectName("commandBox")
        cmd_box_layout = QHBoxLayout(self.command_box)
        cmd_box_layout.setContentsMargins(10, 6, 8, 6)
        cmd_box_layout.setSpacing(8)

        cmd_prompt = QLabel("$")
        cmd_prompt.setObjectName("commandPrompt")
        cmd_box_layout.addWidget(cmd_prompt)

        self.lbl_cmd_text = QLabel("Pilih session untuk melihat command peluncuran")
        self.lbl_cmd_text.setObjectName("commandText")
        self.lbl_cmd_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        cmd_box_layout.addWidget(self.lbl_cmd_text, 1)

        self.btn_copy_inline = QPushButton()
        self.btn_copy_inline.setObjectName("commandCopyBtn")
        self.btn_copy_inline.setFixedSize(26, 26)
        self.btn_copy_inline.setIcon(get_icon("copy", color=DARK.ink_secondary, size=14))
        self.btn_copy_inline.setToolTip("Copy Full Command")
        self.btn_copy_inline.clicked.connect(self._copy_launch_command)
        cmd_box_layout.addWidget(self.btn_copy_inline)

        header_layout.addWidget(self.command_box)
        detail_layout.addWidget(self.detail_header)

        # Hairline Separator
        sep_detail = QFrame()
        sep_detail.setFrameShape(QFrame.Shape.HLine)
        sep_detail.setStyleSheet(f"background-color: {DARK.hairline}; max-height: 1px;")
        detail_layout.addWidget(sep_detail)

        # Chat History Scroll Area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(18, 12, 18, 12)
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch()

        self.chat_scroll.setWidget(self.chat_container)
        detail_layout.addWidget(self.chat_scroll)

        # In-Chat Search Bar
        chat_search_container = QWidget()
        chat_search_layout = QHBoxLayout(chat_search_container)
        chat_search_layout.setContentsMargins(18, 6, 18, 10)
        chat_search_layout.setSpacing(6)

        self.chat_search_input = QLineEdit()
        self.chat_search_input.setPlaceholderText("Cari dalam percakapan...")
        self.chat_search_input.textChanged.connect(self._on_chat_search)
        chat_search_layout.addWidget(self.chat_search_input)

        detail_layout.addWidget(chat_search_container)
        self.splitter.addWidget(detail_panel)

        # Initial splitter sizes
        self.splitter.setSizes([360, 840])
        main_layout.addWidget(self.splitter)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Siap.")

        self._show_empty_state()

    def _apply_theme(self):
        stylesheet = get_stylesheet(self.settings.theme)
        self.setStyleSheet(stylesheet)
        is_dark = self.settings.theme == "dark"
        self.btn_theme.setText("  Dark Mode" if is_dark else "  Light Mode")
        self.btn_theme.setIcon(get_icon("moon" if is_dark else "sun", color=DARK.ink_secondary, size=15))
        if hasattr(self, "btn_starred"):
            self.btn_starred.setIcon(get_icon("star-filled", color=DARK.star_active, size=15))
        self._update_star_button_state()

    def _toggle_theme(self):
        self.settings.theme = "light" if self.settings.theme == "dark" else "dark"
        self._apply_theme()
        save_settings(self.settings)

    def _detect_agy(self):
        self.agy_info = detect_agy()
        if self.agy_info.available:
            self.lbl_agy_status.setText(f"Agy v{self.agy_info.version}")
            self.status_icon.setPixmap(get_pixmap("check-circle", color=DARK.success, size=13))
            if not self.settings.agy_executable:
                self.settings.agy_executable = self.agy_info.executable
            if not self.agy_info.supports_skip_permissions:
                self.radio_skip.setEnabled(False)
                self.radio_skip.setToolTip("Flag tidak didukung oleh versi CLI ini")
        else:
            self.lbl_agy_status.setText("Agy CLI Tidak Ditemukan")
            self.status_icon.setPixmap(get_pixmap("x-circle", color=DARK.danger, size=13))
            self.btn_resume.setEnabled(False)

    def _refresh_sessions(self):
        self.status_bar.showMessage("Memuat session dari disk...")
        QApplication.processEvents()

        if not self.agy_info or not self.agy_info.data_dir:
            self.status_bar.showMessage("Direktori data Agy tidak ditemukan.")
            return

        self.sessions = discover_sessions(
            self.agy_info.summaries_db,
            self.agy_info.conversations_dir,
            self.agy_info.brain_dir,
        )

        # Apply persisted starred status, custom titles, and fork info
        for s in self.sessions:
            fork_info = self.settings.get_fork_info(s.conversation_id)
            if fork_info:
                s.is_fork = True
                s.fork_parent_id = fork_info.get("parent_id", "")
                s.fork_parent_title = fork_info.get("parent_title", "")
            s.is_starred = self.settings.is_starred(s.conversation_id)
            s.custom_title = self.settings.get_custom_title(s.conversation_id) or ""

        # Fork selalu mengikuti status berbintang dari induknya
        for s in self.sessions:
            if s.is_fork and s.fork_parent_id:
                if self.settings.is_starred(s.fork_parent_id):
                    s.is_starred = True

        self._apply_filters()
        self.status_bar.showMessage(
            f"{len(self.sessions)} session terdeteksi ({len(self.filtered_sessions)} ditampilkan)."
        )

    def _apply_filters(self):
        filtered = filter_sessions(
            self.sessions,
            show_subagents=self.chk_subagents.isChecked(),
            min_steps=self.settings.min_steps_filter,
        )

        all_by_id = {s.conversation_id: s for s in self.sessions}

        # Map parent_id -> list of fork sessions in full session pool
        forks_by_parent: Dict[str, List[SessionInfo]] = {}
        for s in self.sessions:
            if s.is_fork and s.fork_parent_id:
                forks_by_parent.setdefault(s.fork_parent_id, []).append(s)

        # Separate trashed vs active views
        if self.current_view == "trash":
            filtered = [s for s in filtered if self.settings.is_trashed(s.conversation_id)]
        else:
            filtered = [s for s in filtered if not self.settings.is_trashed(s.conversation_id)]

            # Tab filter
            if self.current_view == "starred":
                starred_set = set(self.settings.starred_sessions)
                matching_ids = set()
                for s in filtered:
                    if s.conversation_id in starred_set:
                        matching_ids.add(s.conversation_id)
                        # If fork is starred, also pull in parent so hierarchy is maintained
                        if s.is_fork and s.fork_parent_id:
                            matching_ids.add(s.fork_parent_id)
                        # If parent is starred, also pull in its child forks
                        for child in forks_by_parent.get(s.conversation_id, []):
                            matching_ids.add(child.conversation_id)
                filtered = [s for s in filtered if s.conversation_id in matching_ids]

        # Search filter
        query = self.search_input.text().strip()
        if query:
            filtered = search_sessions(filtered, query)
            # If a fork matched search query, ensure parent is included
            matched_ids = {s.conversation_id for s in filtered}
            for s in list(filtered):
                if s.is_fork and s.fork_parent_id and s.fork_parent_id not in matched_ids:
                    if s.fork_parent_id in all_by_id:
                        parent_session = all_by_id[s.fork_parent_id]
                        filtered.append(parent_session)
                        matched_ids.add(parent_session.conversation_id)

        # Separate root sessions from forks that belong to an existing parent in filtered list
        current_filtered_ids = {s.conversation_id for s in filtered}
        nested_fork_ids: Set[str] = set()
        for s in filtered:
            if s.is_fork and s.fork_parent_id and s.fork_parent_id in current_filtered_ids:
                nested_fork_ids.add(s.conversation_id)

        root_sessions = [s for s in filtered if s.conversation_id not in nested_fork_ids]

        # Sort root sessions
        sort_map = {
            0: "last_modified",
            1: "created",
            2: "title",
            3: "steps",
        }
        sort_key = sort_map.get(self.sort_combo.currentIndex(), "last_modified")

        if sort_key == "last_modified":
            def thread_activity(root: SessionInfo) -> float:
                children = [c for c in forks_by_parent.get(root.conversation_id, []) if c.conversation_id in current_filtered_ids]
                times = [root.last_modified] + [c.last_modified for c in children]
                return max(times)
            root_sessions.sort(key=thread_activity, reverse=True)
        elif sort_key == "created":
            root_sessions.sort(key=lambda s: s.created_at, reverse=True)
        elif sort_key == "title":
            root_sessions.sort(key=lambda s: s.display_title.lower())
        elif sort_key == "steps":
            root_sessions.sort(key=lambda s: s.step_count, reverse=True)

        if self.current_view == "recent":
            root_sessions = root_sessions[:15]

        # Build final hierarchical list: (session, is_fork_child, is_last_fork)
        hierarchical_items: List[Tuple[SessionInfo, bool, bool]] = []
        for root in root_sessions:
            hierarchical_items.append((root, False, False))
            child_forks = [
                f for f in forks_by_parent.get(root.conversation_id, [])
                if f.conversation_id in current_filtered_ids
            ]

            child_forks.sort(key=lambda c: c.last_modified, reverse=True)
            for idx, child in enumerate(child_forks):
                is_last = (idx == len(child_forks) - 1)
                hierarchical_items.append((child, True, is_last))

        self.hierarchical_sessions = hierarchical_items
        self.filtered_sessions = [item[0] for item in hierarchical_items]
        self._populate_session_list()

    def _populate_session_list(self):
        self.session_list.clear()

        selected_item = None
        for session, is_fork_child, is_last_fork in self.hierarchical_sessions:
            item = SessionListItem(session, is_fork_child=is_fork_child, is_last_fork=is_last_fork)
            self.session_list.addItem(item)
            widget = SessionItemWidget(session, is_fork_child=is_fork_child, is_last_fork=is_last_fork)
            self.session_list.setItemWidget(item, widget)

            if self.current_session and session.conversation_id == self.current_session.conversation_id:
                selected_item = item

        if selected_item:
            self.session_list.setCurrentItem(selected_item)
            w = self.session_list.itemWidget(selected_item)
            if w and hasattr(w, "set_selected"):
                w.set_selected(True)

        total_sessions = len(self.filtered_sessions)
        fork_count = sum(1 for item in self.hierarchical_sessions if item[1])

        if self.current_view == "trash":
            count_text = f"{total_sessions} session di Sampah"
            if hasattr(self, "btn_empty_trash"):
                self.btn_empty_trash.setVisible(total_sessions > 0)
        else:
            if hasattr(self, "btn_empty_trash"):
                self.btn_empty_trash.setVisible(False)
            count_text = f"{total_sessions} session"
            if fork_count > 0:
                count_text += f" ({fork_count} fork)"
            if total_sessions != len(self.sessions):
                count_text += f" (dari {len(self.sessions)} total)"

        self.lbl_count.setText(count_text)

    def _set_view(self, view: str):
        self.current_view = view
        self.current_session = None
        if hasattr(self, "btn_all"):
            if view == "all" and not self.btn_all.isChecked():
                self.btn_all.setChecked(True)
            elif view == "starred" and not self.btn_starred.isChecked():
                self.btn_starred.setChecked(True)
            elif view == "recent" and not self.btn_recent.isChecked():
                self.btn_recent.setChecked(True)
            elif view == "trash" and not self.btn_trash.isChecked():
                self.btn_trash.setChecked(True)
        self._show_empty_state()
        self._update_header_action_buttons()
        self._apply_filters()

    def _on_search(self, text: str):
        self._apply_filters()

    def _on_sort_changed(self, index: int):
        self._apply_filters()

    def _on_filter_changed(self):
        self.settings.show_subagents = self.chk_subagents.isChecked()
        save_settings(self.settings)
        self._apply_filters()

    def _update_header_action_buttons(self):
        is_trash = (self.current_view == "trash")
        has_session = bool(self.current_session)

        # Trash action buttons
        if hasattr(self, "btn_restore"):
            self.btn_restore.setVisible(is_trash)
            self.btn_restore.setEnabled(has_session)
        if hasattr(self, "btn_perm_delete"):
            self.btn_perm_delete.setVisible(is_trash)
            self.btn_perm_delete.setEnabled(has_session)

        # Standard action buttons
        if hasattr(self, "btn_resume"):
            self.btn_resume.setVisible(not is_trash)
            self.btn_resume.setEnabled(has_session and bool(self.agy_info and self.agy_info.available))
        if hasattr(self, "btn_fork"):
            self.btn_fork.setVisible(not is_trash)
            self.btn_fork.setEnabled(has_session)
        if hasattr(self, "btn_move_trash"):
            self.btn_move_trash.setVisible(not is_trash)
            self.btn_move_trash.setEnabled(has_session)
        if hasattr(self, "btn_copy_id"):
            self.btn_copy_id.setEnabled(has_session)
        if hasattr(self, "btn_copy_cmd"):
            self.btn_copy_cmd.setEnabled(has_session and not is_trash)
        if hasattr(self, "btn_open_dir"):
            self.btn_open_dir.setEnabled(has_session)
        if hasattr(self, "btn_detail_star"):
            self.btn_detail_star.setEnabled(has_session and not is_trash)
        if hasattr(self, "btn_rename"):
            self.btn_rename.setEnabled(has_session and not is_trash)

    def _on_session_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        if previous:
            prev_widget = self.session_list.itemWidget(previous)
            if prev_widget and hasattr(prev_widget, "set_selected"):
                prev_widget.set_selected(False)
        if current:
            curr_widget = self.session_list.itemWidget(current)
            if curr_widget and hasattr(curr_widget, "set_selected"):
                curr_widget.set_selected(True)

        if not current or not isinstance(current, SessionListItem):
            self._show_empty_state()
            return

        session = current.session
        self.current_session = session

        self._update_header_action_buttons()
        self._update_star_button_state()

        self.lbl_detail_title.setText(session.display_title)
        self.chip_id.setText(f"ID: {session.conversation_id}")
        self.chip_id.setVisible(True)

        self.chip_steps.setText(f"{session.step_count} steps" if session.step_count else "0 steps")
        self.chip_steps.setVisible(True)

        if session.workspace_display:
            # Shorten workspace path for display
            ws = session.workspace_display.split(",")[0].strip()
            self.chip_workspace.setText(f"Path: {ws}")
            self.chip_workspace.setVisible(True)
        else:
            self.chip_workspace.setVisible(False)

        self._update_cmd_preview()
        self._clear_chat_layout()
        self._add_chat_notice("Memuat percakapan...")
        self._selection_timer.start(50)

    def _update_cmd_preview(self):
        """Update command bar and store the full command string for copying."""
        if not self.current_session or not self.agy_info:
            self.current_full_command = ""
            self.lbl_cmd_text.setText("Pilih session untuk melihat command peluncuran")
            self.lbl_cmd_text.setToolTip("")
            return

        config = self._build_launch_config()
        try:
            full_cmd = build_command_string(config)
            self.current_full_command = full_cmd

            # Display with Cascadia Code monospace font
            fm = QFontMetrics(self.lbl_cmd_text.font())
            avail_w = max(150, self.command_box.width() - 80)
            elided = fm.elidedText(full_cmd, Qt.TextElideMode.ElideMiddle, avail_w)
            self.lbl_cmd_text.setText(elided)
            self.lbl_cmd_text.setToolTip(full_cmd)
        except Exception as e:
            self.current_full_command = ""
            self.lbl_cmd_text.setText(f"Error: {e}")

    def _build_launch_config(self) -> LaunchConfig:
        if self.current_session:
            return self._build_launch_config_for_session(self.current_session)
        config = LaunchConfig()
        config.agy_executable = (
            self.settings.agy_executable
            or (self.agy_info.executable if self.agy_info else "")
        )
        config.skip_permissions = self.radio_skip.isChecked()
        config.terminal = self.settings.terminal_preference
        return config

    def _build_launch_config_for_session(self, session: SessionInfo) -> LaunchConfig:
        config = LaunchConfig()
        config.agy_executable = (
            self.settings.agy_executable
            or (self.agy_info.executable if self.agy_info else "")
        )
        config.conversation_id = session.conversation_id
        ws = session.workspace_display
        if ws and os.path.isdir(ws.split(",")[0].strip()):
            config.working_directory = ws.split(",")[0].strip()
        elif self.settings.default_working_directory:
            config.working_directory = self.settings.default_working_directory
        else:
            config.working_directory = os.path.expanduser("~")

        config.skip_permissions = self.radio_skip.isChecked()
        config.terminal = self.settings.terminal_preference
        return config

    def _load_chat_history(self, session: SessionInfo):
        self.current_session = session
        self._selection_timer.stop()
        self._do_load_chat_history()

    def _do_load_chat_history(self):
        session = self.current_session
        if not session:
            return

        self._clear_chat_layout()

        if not self.agy_info or not self.agy_info.brain_dir:
            self._add_chat_notice("Direktori brain tidak ditemukan.")
            return

        if not session.has_transcript:
            self._add_chat_notice(
                f"Transcript tidak tersedia untuk session ini.\n"
                f"Lokasi: {os.path.join(self.agy_info.brain_dir, session.conversation_id)}"
            )
            return

        messages = read_transcript(self.agy_info.brain_dir, session.conversation_id)
        self.current_messages = messages

        if not messages:
            self._add_chat_notice("Tidak ada pesan dalam transcript ini.")
            return

        display_messages = []
        for msg in messages:
            if msg.is_user or msg.is_assistant:
                display_messages.append(msg)
            elif msg.is_system and msg.content:
                display_messages.append(msg)

        self.current_display_messages = display_messages
        self._render_current_session_messages(initial=True)

        counts = count_messages_by_role(messages)
        self.status_bar.showMessage(
            f"{len(display_messages)} pesan dimuat (User: {counts['user']}, Assistant: {counts['assistant']}, Total steps: {len(messages)})"
        )

    def _render_current_session_messages(self, initial: bool = True):
        self._clear_chat_layout()
        total = len(self.current_display_messages)
        if total == 0:
            self._add_chat_notice("Tidak ada pesan dalam transcript ini.")
            return

        if total <= self.PAGE_SIZE:
            self.rendered_msg_start_idx = 0
            for msg in self.current_display_messages:
                bubble = ChatBubbleWidget(msg)
                self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        else:
            self.rendered_msg_start_idx = total - self.PAGE_SIZE
            hidden_count = self.rendered_msg_start_idx

            self.load_more_widget = LoadMoreWidget(
                hidden_count=hidden_count,
                total_count=total,
                on_load_more=self._on_load_more_messages,
                on_load_all=self._on_load_all_messages
            )
            self.chat_layout.insertWidget(0, self.load_more_widget)

            for msg in self.current_display_messages[self.rendered_msg_start_idx:]:
                bubble = ChatBubbleWidget(msg)
                self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

        if initial:
            QTimer.singleShot(25, self._scroll_chat_to_bottom)

    def _scroll_chat_to_bottom(self):
        vsb = self.chat_scroll.verticalScrollBar()
        if vsb:
            vsb.setValue(vsb.maximum())

    def _on_load_more_messages(self):
        if self.rendered_msg_start_idx <= 0:
            return

        new_start = max(0, self.rendered_msg_start_idx - self.PAGE_SIZE)
        messages_to_insert = self.current_display_messages[new_start:self.rendered_msg_start_idx]
        self.rendered_msg_start_idx = new_start

        vsb = self.chat_scroll.verticalScrollBar()
        old_val = vsb.value() if vsb else 0
        old_max = vsb.maximum() if vsb else 0

        if new_start == 0:
            if self.load_more_widget:
                self.chat_layout.removeWidget(self.load_more_widget)
                self.load_more_widget.deleteLater()
                self.load_more_widget = None
        else:
            if self.load_more_widget:
                self.chat_layout.removeWidget(self.load_more_widget)
                self.load_more_widget.deleteLater()
                self.load_more_widget = LoadMoreWidget(
                    hidden_count=new_start,
                    total_count=len(self.current_display_messages),
                    on_load_more=self._on_load_more_messages,
                    on_load_all=self._on_load_all_messages
                )
                self.chat_layout.insertWidget(0, self.load_more_widget)

        insert_offset = 1 if self.load_more_widget else 0
        for i, msg in enumerate(messages_to_insert):
            bubble = ChatBubbleWidget(msg)
            self.chat_layout.insertWidget(insert_offset + i, bubble)

        if vsb:
            QApplication.processEvents()
            new_max = vsb.maximum()
            vsb.setValue(old_val + (new_max - old_max))

    def _on_load_all_messages(self):
        if self.rendered_msg_start_idx <= 0:
            return

        if self.load_more_widget:
            self.chat_layout.removeWidget(self.load_more_widget)
            self.load_more_widget.deleteLater()
            self.load_more_widget = None

        messages_to_insert = self.current_display_messages[:self.rendered_msg_start_idx]
        self.rendered_msg_start_idx = 0

        for i, msg in enumerate(messages_to_insert):
            bubble = ChatBubbleWidget(msg)
            self.chat_layout.insertWidget(i, bubble)

    def _clear_chat_layout(self):
        self.load_more_widget = None
        old_container = self.chat_scroll.takeWidget()
        if old_container:
            old_container.deleteLater()
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(18, 12, 18, 12)
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch()
        self.chat_scroll.setWidget(self.chat_container)

    def _add_chat_notice(self, text: str):
        notice = QLabel(text)
        notice.setFont(QFont("Segoe UI", 11))
        notice.setStyleSheet(f"color: {DARK.ink_subtle}; background-color: transparent;")
        notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        notice.setWordWrap(True)
        notice.setContentsMargins(20, 50, 20, 50)
        self.chat_layout.insertWidget(max(0, self.chat_layout.count() - 1), notice)

    def _show_empty_state(self):
        self.current_session = None
        self.current_full_command = ""
        self._update_header_action_buttons()
        if hasattr(self, "btn_detail_star"):
            self.btn_detail_star.setEnabled(False)
            self.btn_detail_star.setIcon(get_icon("star", color=DARK.ink_disabled, size=16))
            self.btn_detail_star.setProperty("starred", False)
            self.btn_detail_star.style().unpolish(self.btn_detail_star)
            self.btn_detail_star.style().polish(self.btn_detail_star)

        self.lbl_detail_title.setText("Pilih Session")
        self.chip_id.setVisible(False)
        self.chip_steps.setVisible(False)
        self.chip_workspace.setVisible(False)
        self.lbl_cmd_text.setText("Pilih session untuk melihat command peluncuran")
        self.lbl_cmd_text.setToolTip("")

        self._clear_chat_layout()
        if not getattr(self, "sessions", []):
            if getattr(self, "agy_info", None) is not None and not self.agy_info.available:
                self._add_chat_notice(
                    "Agy CLI belum terdeteksi di sistem.\n\n"
                    "Pasang Agy CLI terlebih dahulu atau atur path executable di menu Pengaturan (ikon gear di pojok kiri bawah)."
                )
            else:
                self._add_chat_notice(
                    "Belum ada session percakapan terdeteksi.\n\n"
                    "Jalankan perintah 'agy' di terminal untuk memulai sesi percakapan pertama Anda!"
                )
        else:
            self._add_chat_notice("Pilih session di panel sebelah kiri untuk menelusuri riwayat percakapan.")

    def _on_chat_search(self, text: str):
        query = text.strip().lower()
        if not query:
            self._render_current_session_messages(initial=False)
            return

        matching = []
        for msg in self.current_display_messages:
            content = (msg.clean_content if msg.is_user else (msg.content or "")).lower()
            if query in content:
                matching.append(msg)

        self._clear_chat_layout()
        if not matching:
            self._add_chat_notice(f"Tidak ada pesan yang cocok dengan '{text.strip()}'.")
            self.status_bar.showMessage(f"0 pesan cocok dengan '{text.strip()}'")
            return

        limit = 30
        shown_count = min(len(matching), limit)
        banner_text = (
            f"Menampilkan {shown_count} dari {len(matching)} pesan yang cocok dengan '{text.strip()}'"
            if len(matching) > limit
            else f"Menampilkan {len(matching)} pesan yang cocok dengan '{text.strip()}' (dari {len(self.current_display_messages)} total)"
        )
        banner = QLabel(banner_text)
        banner.setFont(QFont("Segoe UI", 10))
        banner.setStyleSheet(
            f"color: {DARK.primary}; background: {DARK.surface_card}; "
            f"border: 1px solid {DARK.hairline_strong}; border-radius: 6px; padding: 8px 12px;"
        )
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chat_layout.insertWidget(0, banner)

        for msg in matching[:limit]:
            bubble = ChatBubbleWidget(msg)
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

        self.status_bar.showMessage(f"{len(matching)} pesan cocok dengan '{text.strip()}'")

    # === ACTIONS ===

    def _on_resume(self):
        if not self.current_session:
            return

        config = self._build_launch_config()

        if config.skip_permissions:
            reply = QMessageBox.warning(
                self,
                "Peringatan: Skip Permissions",
                "Mode ini akan melewati SEMUA pemeriksaan izin keamanan.\n"
                "Agy CLI dapat menjalankan aksi tanpa konfirmasi interaktif.\n\n"
                "Lanjutkan peluncuran?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            cmd_display = build_command_string(config)
            self.status_bar.showMessage(f"Meluncurkan: {cmd_display}")
            launch_session(config)
            self.status_bar.showMessage(f"Session {self.current_session.short_id} berhasil diluncurkan.")
        except LaunchError as e:
            QMessageBox.critical(
                self,
                "Gagal Meluncurkan Session",
                f"Terjadi kesalahan saat meluncurkan session:\n\n{e}",
            )
            self.status_bar.showMessage(f"Gagal meluncurkan: {e}")

    def _copy_session_id(self):
        if self.current_session:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.current_session.conversation_id)
            self.status_bar.showMessage(f"ID berhasil disalin: {self.current_session.conversation_id}")

    def _copy_launch_command(self):
        """Copies the FULL launch command to clipboard (not the elided display string)."""
        if not self.current_session:
            return
        # Ensure latest full command is built
        config = self._build_launch_config()
        try:
            full_cmd = build_command_string(config)
            clipboard = QApplication.clipboard()
            clipboard.setText(full_cmd)
            self.status_bar.showMessage("Command lengkap berhasil disalin ke clipboard.")
        except Exception as e:
            self.status_bar.showMessage(f"Error menyalin command: {e}")

    def _open_session_folder(self):
        if not self.current_session or not self.agy_info:
            return

        folder = os.path.join(self.agy_info.brain_dir, self.current_session.conversation_id)
        if os.path.isdir(folder):
            os.startfile(folder)
            self.status_bar.showMessage(f"Membuka folder: {folder}")
        else:
            conv_db = os.path.join(self.agy_info.conversations_dir, f"{self.current_session.conversation_id}.db")
            if os.path.isfile(conv_db):
                os.startfile(self.agy_info.conversations_dir)
            else:
                QMessageBox.information(
                    self,
                    "Folder Tidak Ditemukan",
                    f"Folder session tidak ditemukan di disk:\n{folder}",
                )

    # === STAR & RENAME ACTIONS ===

    def _update_star_button_state(self):
        if not hasattr(self, "btn_detail_star"):
            return
        if self.current_session and self.current_session.is_starred:
            self.btn_detail_star.setIcon(get_icon("star-filled", color=DARK.star_active, size=16))
            self.btn_detail_star.setToolTip("Hapus Bintang (Unpin)")
            self.btn_detail_star.setProperty("starred", True)
        else:
            color = DARK.ink_secondary if self.current_session else DARK.ink_disabled
            self.btn_detail_star.setIcon(get_icon("star", color=color, size=16))
            self.btn_detail_star.setToolTip("Beri Bintang (Pin ke Atas)")
            self.btn_detail_star.setProperty("starred", False)
        self.btn_detail_star.style().unpolish(self.btn_detail_star)
        self.btn_detail_star.style().polish(self.btn_detail_star)

    def _toggle_current_star(self):
        if not self.current_session:
            return
        self._toggle_session_star(self.current_session)

    def _toggle_session_star(self, session: SessionInfo):
        is_now_starred = self.settings.toggle_star(session.conversation_id)
        session.is_starred = is_now_starred

        # Sesi fork selalu sinkron dengan sesi induknya
        target_parent_id = session.fork_parent_id if (session.is_fork and session.fork_parent_id) else session.conversation_id
        for s in self.sessions:
            if s.conversation_id == target_parent_id or (s.is_fork and s.fork_parent_id == target_parent_id):
                s.is_starred = is_now_starred

        save_settings(self.settings)

        selected_id = self.current_session.conversation_id if self.current_session else None

        self._update_star_button_state()
        self._apply_filters()

        # Restore selection
        if selected_id:
            for i in range(self.session_list.count()):
                item = self.session_list.item(i)
                if isinstance(item, SessionListItem) and item.session.conversation_id == selected_id:
                    self.session_list.setCurrentItem(item)
                    break

        status_msg = (
            f"Session '{session.display_title}' diberi bintang (di-pin ke atas)."
            if is_now_starred else
            f"Bintang dihapus dari session '{session.display_title}'."
        )
        self.status_bar.showMessage(status_msg, 4000)

    def _prompt_rename_current_session(self):
        if not self.current_session:
            return
        self._prompt_rename_session(self.current_session)

    def _prompt_rename_session(self, session: SessionInfo):
        dialog = RenameDialog(session, theme_mode=self.settings.theme, parent=self)
        if dialog.exec():
            new_title = dialog.new_title or ""
            session.custom_title = new_title
            self.settings.set_custom_title(session.conversation_id, new_title)
            save_settings(self.settings)

            selected_id = session.conversation_id

            if self.current_session and self.current_session.conversation_id == session.conversation_id:
                self.lbl_detail_title.setText(session.display_title)

            self._apply_filters()

            # Restore selection
            for i in range(self.session_list.count()):
                item = self.session_list.item(i)
                if isinstance(item, SessionListItem) and item.session.conversation_id == selected_id:
                    self.session_list.setCurrentItem(item)
                    break

            if new_title:
                self.status_bar.showMessage(f"Nama session diubah menjadi: '{new_title}'", 4000)
            else:
                self.status_bar.showMessage("Nama session dikembalikan ke judul asli.", 4000)

    def _prompt_fork_current_session(self):
        if not self.current_session:
            return
        self._prompt_fork_session(self.current_session)

    def _prompt_fork_session(self, session: SessionInfo):
        dialog = ForkDialog(session, theme_mode=self.settings.theme, parent=self)
        if dialog.exec():
            self.status_bar.showMessage(f"Sedang mencabangkan session '{session.display_title}'...")
            QApplication.processEvents()
            try:
                new_id, new_session = fork_session(
                    session,
                    dialog.fork_title,
                    self.agy_info,
                    mark_starred=dialog.mark_starred,
                )
                self.settings.record_fork(new_id, session.conversation_id, session.display_title)
                if dialog.mark_starred or session.is_starred:
                    if new_id not in self.settings.starred_sessions:
                        self.settings.starred_sessions.append(new_id)
                self.settings.set_custom_title(new_id, dialog.fork_title)
                save_settings(self.settings)

                self._refresh_sessions()

                # Select the new forked session in the list
                for i in range(self.session_list.count()):
                    item = self.session_list.item(i)
                    if isinstance(item, SessionListItem) and item.session.conversation_id == new_id:
                        self.session_list.setCurrentItem(item)
                        break

                self.status_bar.showMessage(
                    f"Session berhasil dicabangkan: '{new_session.display_title}' (ID: {new_session.short_id})",
                    5000
                )

                if dialog.auto_launch:
                    self._on_resume_for_session(new_session)

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Gagal Fork Session",
                    f"Terjadi kesalahan saat mencabangkan session:\n\n{e}"
                )
                self.status_bar.showMessage(f"Gagal fork session: {e}", 5000)

    def _show_session_context_menu(self, pos):
        item = self.session_list.itemAt(pos)
        if not item or not isinstance(item, SessionListItem):
            return
        session = item.session

        menu = QMenu(self)

        if self.current_view == "trash":
            act_restore = menu.addAction(get_icon("rotate-ccw", color="#4ade80", size=14), "Pulihkan Session (Restore)")
            act_restore.triggered.connect(lambda: self._restore_session(session))

            act_perm = menu.addAction(get_icon("trash", color="#ef4444", size=14), "Hapus Permanen...")
            act_perm.triggered.connect(lambda: self._prompt_permanent_delete_session(session))

            menu.addSeparator()

            act_copy_id = menu.addAction(get_icon("copy", color=DARK.ink_secondary, size=14), "Copy Session ID")
            act_copy_id.triggered.connect(lambda: self._copy_id_for_session(session))

            act_folder = menu.addAction(get_icon("folder", color=DARK.ink_secondary, size=14), "Open Session Folder")
            act_folder.triggered.connect(lambda: self._open_folder_for_session(session))
        else:
            # Star / Unstar
            if session.is_starred:
                act_star = menu.addAction(get_icon("star", color=DARK.ink_secondary, size=14), "Hapus Bintang (Unpin)")
            else:
                act_star = menu.addAction(get_icon("star-filled", color=DARK.star_active, size=14), "Beri Bintang (Pin ke Atas)")
            act_star.triggered.connect(lambda: self._toggle_session_star(session))

            # Rename
            act_rename = menu.addAction(get_icon("edit", color=DARK.ink_secondary, size=14), "Ganti Nama (Rename)...")
            act_rename.triggered.connect(lambda: self._prompt_rename_session(session))

            # Fork (Cabangkan)
            act_fork = menu.addAction(get_icon("git-branch", color=DARK.ink_secondary, size=14), "Fork Session (Cabangkan)...")
            act_fork.triggered.connect(lambda: self._prompt_fork_session(session))

            menu.addSeparator()

            # Resume
            act_resume = menu.addAction(get_icon("play", color=DARK.primary, size=14), "Resume Session")
            act_resume.setEnabled(bool(self.agy_info and self.agy_info.available))
            act_resume.triggered.connect(lambda: self._on_resume_for_session(session))

            act_copy_id = menu.addAction(get_icon("copy", color=DARK.ink_secondary, size=14), "Copy Session ID")
            act_copy_id.triggered.connect(lambda: self._copy_id_for_session(session))

            act_copy_cmd = menu.addAction(get_icon("terminal", color=DARK.ink_secondary, size=14), "Copy Launch Command")
            act_copy_cmd.triggered.connect(lambda: self._copy_cmd_for_session(session))

            act_folder = menu.addAction(get_icon("folder", color=DARK.ink_secondary, size=14), "Open Session Folder")
            act_folder.triggered.connect(lambda: self._open_folder_for_session(session))

            menu.addSeparator()

            act_trash = menu.addAction(get_icon("trash", color="#f87171", size=14), "Pindahkan ke Sampah")
            act_trash.triggered.connect(lambda: self._prompt_trash_session(session))

        menu.exec(self.session_list.mapToGlobal(pos))

    # === TRASH & DELETION ACTIONS ===

    def _prompt_trash_current_session(self):
        if not self.current_session:
            return
        self._prompt_trash_session(self.current_session)

    def _prompt_trash_session(self, session: SessionInfo):
        child_count = sum(
            1 for s in self.sessions
            if s.is_fork and s.fork_parent_id == session.conversation_id
        )
        dialog = ConfirmTrashDialog(session, child_fork_count=child_count, parent=self)
        if dialog.exec():
            self.settings.move_to_trash(session.conversation_id, session.display_title)
            save_settings(self.settings)

            self.status_bar.showMessage(
                f"Session '{session.display_title}' dipindahkan ke Sampah.",
                4000
            )
            self.current_session = None
            self._show_empty_state()
            self._apply_filters()

    def _restore_current_session(self):
        if not self.current_session:
            return
        self._restore_session(self.current_session)

    def _restore_session(self, session: SessionInfo):
        self.settings.restore_from_trash(session.conversation_id)
        save_settings(self.settings)

        self.status_bar.showMessage(
            f"Session '{session.display_title}' berhasil dipulihkan dari Sampah.",
            4000
        )
        self.current_session = None
        self._show_empty_state()
        self._apply_filters()

    def _prompt_permanent_delete_current_session(self):
        if not self.current_session:
            return
        self._prompt_permanent_delete_session(self.current_session)

    def _prompt_permanent_delete_session(self, session: SessionInfo):
        if not self.settings.is_trashed(session.conversation_id):
            QMessageBox.warning(
                self,
                "Aksi Ditolak",
                "Hapus permanen hanya dapat dilakukan untuk session yang sudah berada di menu Sampah.\n"
                "Silakan pindahkan session ke Sampah terlebih dahulu."
            )
            return

        child_count = sum(
            1 for s in self.sessions
            if s.is_fork and s.fork_parent_id == session.conversation_id
        )
        dialog = ConfirmPermanentDeleteDialog(session, child_fork_count=child_count, parent=self)
        if dialog.exec():
            try:
                success, msg = permanently_delete_session(session, self.agy_info, self.settings)
                if success:
                    self.status_bar.showMessage(msg, 4000)
                else:
                    QMessageBox.warning(self, "Peringatan Hapus", msg)
                self.current_session = None
                self._show_empty_state()
                self._refresh_sessions()
            except Exception as e:
                QMessageBox.critical(self, "Gagal Hapus Permanen", f"Terjadi kesalahan:\n\n{e}")

    def _prompt_empty_trash(self):
        trashed_sessions = [s for s in self.sessions if self.settings.is_trashed(s.conversation_id)]
        if not trashed_sessions:
            return

        dialog = ConfirmEmptyTrashDialog(len(trashed_sessions), parent=self)
        if dialog.exec():
            failed = []
            for s in trashed_sessions:
                try:
                    success, msg = permanently_delete_session(s, self.agy_info, self.settings)
                    if not success:
                        failed.append(f"{s.short_id}: {msg}")
                except Exception as e:
                    failed.append(f"{s.short_id}: {e}")

            if failed:
                QMessageBox.warning(
                    self,
                    "Sebagian Session Gagal Dihapus",
                    "Terjadi kesalahan saat menghapus beberapa session:\n\n" + "\n".join(failed[:5])
                )
            else:
                self.status_bar.showMessage("Semua session di Sampah telah dihapus permanen.", 4000)

            self.current_session = None
            self._show_empty_state()
            self._refresh_sessions()

    def _copy_id_for_session(self, session: SessionInfo):
        clipboard = QApplication.clipboard()
        clipboard.setText(session.conversation_id)
        self.status_bar.showMessage(f"ID disalin: {session.conversation_id}", 3000)

    def _copy_cmd_for_session(self, session: SessionInfo):
        config = self._build_launch_config_for_session(session)
        try:
            full_cmd = build_command_string(config)
            clipboard = QApplication.clipboard()
            clipboard.setText(full_cmd)
            self.status_bar.showMessage("Command peluncuran disalin ke clipboard.", 3000)
        except Exception as e:
            self.status_bar.showMessage(f"Error menyalin command: {e}")

    def _open_folder_for_session(self, session: SessionInfo):
        if not self.agy_info:
            return
        folder = os.path.join(self.agy_info.brain_dir, session.conversation_id)
        if os.path.isdir(folder):
            os.startfile(folder)
            self.status_bar.showMessage(f"Membuka folder: {folder}", 3000)
        else:
            conv_db = os.path.join(self.agy_info.conversations_dir, f"{session.conversation_id}.db")
            if os.path.isfile(conv_db):
                os.startfile(self.agy_info.conversations_dir)
            else:
                QMessageBox.information(
                    self,
                    "Folder Tidak Ditemukan",
                    f"Tidak ada direktori brain atau DB untuk session {session.short_id}.",
                )

    def _on_resume_for_session(self, session: SessionInfo):
        config = self._build_launch_config_for_session(session)
        if config.skip_permissions:
            reply = QMessageBox.warning(
                self,
                "Peringatan: Skip Permissions",
                "Mode ini akan melewati SEMUA pemeriksaan izin keamanan.\n"
                "Agy CLI dapat menjalankan aksi tanpa konfirmasi interaktif.\n\n"
                "Lanjutkan peluncuran?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            cmd_display = build_command_string(config)
            self.status_bar.showMessage(f"Meluncurkan: {cmd_display}")
            launch_session(config)
            self.status_bar.showMessage(f"Session {session.short_id} berhasil diluncurkan.")
        except LaunchError as e:
            QMessageBox.critical(
                self,
                "Gagal Meluncurkan Session",
                f"Terjadi kesalahan saat meluncurkan session:\n\n{e}",
            )

    def _show_settings_dialog(self):
        from src.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.settings, self.agy_info, self)
        if dialog.exec():
            self.settings = dialog.get_settings()
            save_settings(self.settings)
            self._apply_theme()
            if self.settings.agy_executable:
                self.agy_info.executable = self.settings.agy_executable
                self.agy_info.available = os.path.isfile(self.settings.agy_executable)
            self._detect_agy()
            self._refresh_sessions()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_cmd_preview()
        # Trigger re-clamp on visible session items
        for i in range(self.session_list.count()):
            item = self.session_list.item(i)
            widget = self.session_list.itemWidget(item)
            if widget and isinstance(widget, SessionItemWidget):
                widget._update_clamped_text()

    def closeEvent(self, event):
        self.settings.window_width = self.width()
        self.settings.window_height = self.height()
        self.settings.splitter_sizes = self.splitter.sizes()
        save_settings(self.settings)
        super().closeEvent(event)
