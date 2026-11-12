"""
settings_dialog.py - Settings dialog for configuring Agy executable and preferences.
"""
import os
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QGroupBox, QComboBox, QFormLayout,
    QDialogButtonBox, QCheckBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.settings import AppSettings
from src.agy_detector import AgyInfo


class SettingsDialog(QDialog):
    """Settings dialog for configuring the application."""

    def __init__(self, settings: AppSettings,
                 agy_info: Optional[AgyInfo] = None,
                 parent=None):
        super().__init__(parent)
        self.settings = AppSettings(**{
            k: v for k, v in settings.__dict__.items()
        })
        self.agy_info = agy_info

        self.setWindowTitle("Pengaturan - Agy Session Manager")
        self.setMinimumWidth(500)
        self.setMinimumHeight(350)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Agy CLI group
        agy_group = QGroupBox("Agy CLI")
        agy_layout = QFormLayout(agy_group)

        # Executable path
        exe_row = QHBoxLayout()
        self.exe_input = QLineEdit(self.settings.agy_executable)
        self.exe_input.setPlaceholderText("Path ke agy.exe")
        exe_row.addWidget(self.exe_input)

        btn_browse = QPushButton("Browse...")
        btn_browse.setObjectName("secondaryBtn")
        btn_browse.clicked.connect(self._browse_executable)
        exe_row.addWidget(btn_browse)

        if self.agy_info and self.agy_info.available:
            btn_detect = QPushButton("Auto-detect")
            btn_detect.setObjectName("ghostBtn")
            btn_detect.clicked.connect(self._auto_detect)
            exe_row.addWidget(btn_detect)

        agy_layout.addRow("Executable:", exe_row)

        # Default working directory
        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit(self.settings.default_working_directory)
        self.dir_input.setPlaceholderText("Default working directory")
        dir_row.addWidget(self.dir_input)

        btn_dir = QPushButton("Browse...")
        btn_dir.setObjectName("secondaryBtn")
        btn_dir.clicked.connect(self._browse_directory)
        dir_row.addWidget(btn_dir)

        agy_layout.addRow("Working Dir:", dir_row)

        layout.addWidget(agy_group)

        # Appearance group
        appearance_group = QGroupBox("Tampilan")
        appearance_layout = QFormLayout(appearance_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentIndex(
            0 if self.settings.theme == "dark" else 1
        )
        appearance_layout.addRow("Tema:", self.theme_combo)

        layout.addWidget(appearance_group)

        # Terminal group
        terminal_group = QGroupBox("Terminal")
        terminal_layout = QFormLayout(terminal_group)

        self.terminal_combo = QComboBox()
        self.terminal_combo.addItems([
            "Auto (Windows Terminal > PowerShell)",
            "Windows Terminal",
            "PowerShell 7 (pwsh)",
            "Windows PowerShell",
        ])
        term_map = {"auto": 0, "wt": 1, "pwsh": 2, "powershell": 3}
        self.terminal_combo.setCurrentIndex(
            term_map.get(self.settings.terminal_preference, 0)
        )
        terminal_layout.addRow("Terminal:", self.terminal_combo)

        layout.addWidget(terminal_group)

        # Info
        if self.agy_info:
            cli_status = f"Ready (v{self.agy_info.version})" if self.agy_info.available else "Tidak ditemukan"
            conv_flag = "Didukung" if self.agy_info.supports_conversation else "Tidak didukung"
            skip_flag = "Didukung" if self.agy_info.supports_skip_permissions else "Tidak didukung"
            info_label = QLabel(
                f"Agy CLI: {cli_status}\n"
                f"Data: {self.agy_info.data_dir or 'N/A'}\n"
                f"Flags: --conversation [{conv_flag}] | --dangerously-skip-permissions [{skip_flag}]"
            )
            info_label.setObjectName("subtitle")
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

        layout.addStretch()

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_executable(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Pilih Agy CLI Executable",
            os.environ.get("LOCALAPPDATA", ""),
            "Executable (*.exe);;All Files (*)"
        )
        if path:
            self.exe_input.setText(path)

    def _browse_directory(self):
        path = QFileDialog.getExistingDirectory(
            self, "Pilih Working Directory",
            self.dir_input.text() or os.path.expanduser("~")
        )
        if path:
            self.dir_input.setText(path)

    def _auto_detect(self):
        if self.agy_info and self.agy_info.executable:
            self.exe_input.setText(self.agy_info.executable)

    def get_settings(self) -> AppSettings:
        self.settings.agy_executable = self.exe_input.text().strip()
        self.settings.default_working_directory = self.dir_input.text().strip()
        self.settings.theme = (
            "dark" if self.theme_combo.currentIndex() == 0 else "light"
        )
        term_values = ["auto", "wt", "pwsh", "powershell"]
        self.settings.terminal_preference = term_values[
            self.terminal_combo.currentIndex()
        ]
        return self.settings
