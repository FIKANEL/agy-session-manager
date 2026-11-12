"""
styles.py - Dark/Light theme stylesheets for the application.
"""

DARK_THEME = """
QMainWindow, QDialog {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

/* Sidebar */
QWidget#sidebar {
    background-color: #181825;
    border-right: 1px solid #313244;
}
QWidget#sidebar QPushButton {
    background-color: transparent;
    color: #cdd6f4;
    border: none;
    border-radius: 6px;
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
}
QWidget#sidebar QPushButton:hover {
    background-color: #313244;
}
QWidget#sidebar QPushButton:checked,
QWidget#sidebar QPushButton[active="true"] {
    background-color: #45475a;
    color: #89b4fa;
    font-weight: bold;
}

/* Session List */
QListWidget {
    background-color: #181825;
    border: none;
    outline: none;
}
QListWidget::item {
    background-color: transparent;
    border-bottom: 1px solid #313244;
    padding: 10px 12px;
    color: #cdd6f4;
}
QListWidget::item:selected {
    background-color: #313244;
    border-left: 3px solid #89b4fa;
}
QListWidget::item:hover {
    background-color: #27273a;
}

/* Search box */
QLineEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 8px 12px;
    color: #cdd6f4;
    font-size: 13px;
    selection-background-color: #89b4fa;
}
QLineEdit:focus {
    border: 1px solid #89b4fa;
}

/* Buttons */
QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #74c7ec;
}
QPushButton:pressed {
    background-color: #585b70;
}
QPushButton:disabled {
    background-color: #45475a;
    color: #6c7086;
}
QPushButton#dangerBtn {
    background-color: #f38ba8;
    color: #1e1e2e;
}
QPushButton#dangerBtn:hover {
    background-color: #eba0ac;
}
QPushButton#secondaryBtn {
    background-color: #45475a;
    color: #cdd6f4;
}
QPushButton#secondaryBtn:hover {
    background-color: #585b70;
}
QPushButton#ghostBtn {
    background-color: transparent;
    color: #89b4fa;
    font-weight: normal;
}
QPushButton#ghostBtn:hover {
    background-color: #313244;
}

/* Scroll areas */
QScrollArea {
    border: none;
    background-color: #1e1e2e;
}
QScrollBar:vertical {
    background-color: #181825;
    width: 8px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background-color: #181825;
    height: 8px;
    border: none;
}
QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 4px;
    min-width: 30px;
}

/* Labels */
QLabel {
    color: #cdd6f4;
    background-color: transparent;
}
QLabel#title {
    font-size: 18px;
    font-weight: bold;
    color: #cdd6f4;
}
QLabel#subtitle {
    font-size: 12px;
    color: #6c7086;
}
QLabel#sectionTitle {
    font-size: 14px;
    font-weight: bold;
    color: #a6adc8;
}

/* Chat bubbles */
QFrame#userMsg {
    background-color: #313244;
    border-radius: 12px;
    border: none;
}
QFrame#assistantMsg {
    background-color: #1e1e2e;
    border-radius: 12px;
    border: 1px solid #313244;
}
QFrame#systemMsg {
    background-color: #181825;
    border-radius: 8px;
    border: 1px solid #45475a;
}
QFrame#toolMsg {
    background-color: #1a1a2e;
    border-radius: 8px;
    border: 1px solid #313244;
}

/* Combo box */
QComboBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
    color: #cdd6f4;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #45475a;
    border: 1px solid #45475a;
}

/* Splitter */
QSplitter::handle {
    background-color: #313244;
    width: 1px;
}

/* Tab Widget */
QTabWidget::pane {
    border: none;
    background-color: #1e1e2e;
}
QTabBar::tab {
    background-color: #181825;
    color: #6c7086;
    padding: 8px 16px;
    border: none;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:selected {
    color: #89b4fa;
    border-bottom: 2px solid #89b4fa;
}
QTabBar::tab:hover {
    color: #cdd6f4;
}

/* Tooltips */
QToolTip {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    padding: 6px;
    border-radius: 4px;
    font-size: 12px;
}

/* Radio buttons */
QRadioButton {
    color: #cdd6f4;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

/* Check boxes */
QCheckBox {
    color: #cdd6f4;
    spacing: 8px;
}

/* Group Box */
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
    color: #a6adc8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

/* Status bar */
QStatusBar {
    background-color: #181825;
    color: #6c7086;
    border-top: 1px solid #313244;
}

/* Menu bar */
QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
}
QMenuBar::item:selected {
    background-color: #313244;
}
QMenu {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #45475a;
}
QMenu::item:selected {
    background-color: #313244;
}

/* Progress bar */
QProgressBar {
    background-color: #313244;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #cdd6f4;
    height: 6px;
}
QProgressBar::chunk {
    background-color: #89b4fa;
    border-radius: 4px;
}
"""

LIGHT_THEME = """
QMainWindow, QDialog {
    background-color: #eff1f5;
    color: #4c4f69;
}
QWidget {
    background-color: #eff1f5;
    color: #4c4f69;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}
QWidget#sidebar {
    background-color: #e6e9ef;
    border-right: 1px solid #ccd0da;
}
QWidget#sidebar QPushButton {
    background-color: transparent;
    color: #4c4f69;
    border: none;
    border-radius: 6px;
    padding: 10px 14px;
    text-align: left;
}
QWidget#sidebar QPushButton:hover {
    background-color: #ccd0da;
}
QWidget#sidebar QPushButton:checked {
    background-color: #bcc0cc;
    color: #1e66f5;
    font-weight: bold;
}
QListWidget {
    background-color: #e6e9ef;
    border: none;
}
QListWidget::item {
    border-bottom: 1px solid #ccd0da;
    padding: 10px 12px;
}
QListWidget::item:selected {
    background-color: #ccd0da;
    border-left: 3px solid #1e66f5;
}
QLineEdit {
    background-color: #ccd0da;
    border: 1px solid #bcc0cc;
    border-radius: 8px;
    padding: 8px 12px;
    color: #4c4f69;
}
QLineEdit:focus {
    border: 1px solid #1e66f5;
}
QPushButton {
    background-color: #1e66f5;
    color: #eff1f5;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #2e7df7;
}
QPushButton#secondaryBtn {
    background-color: #bcc0cc;
    color: #4c4f69;
}
QPushButton#ghostBtn {
    background-color: transparent;
    color: #1e66f5;
}
QFrame#userMsg {
    background-color: #ccd0da;
    border-radius: 12px;
}
QFrame#assistantMsg {
    background-color: #eff1f5;
    border-radius: 12px;
    border: 1px solid #ccd0da;
}
QScrollBar:vertical {
    background-color: #e6e9ef;
    width: 8px;
}
QScrollBar::handle:vertical {
    background-color: #bcc0cc;
    border-radius: 4px;
}
QSplitter::handle {
    background-color: #ccd0da;
}
QStatusBar {
    background-color: #e6e9ef;
    color: #6c6f85;
    border-top: 1px solid #ccd0da;
}
QComboBox {
    background-color: #ccd0da;
    border: 1px solid #bcc0cc;
    border-radius: 6px;
    padding: 6px 10px;
}
QLabel {
    background-color: transparent;
}
QLabel#subtitle {
    color: #6c6f85;
}
QToolTip {
    background-color: #e6e9ef;
    color: #4c4f69;
    border: 1px solid #ccd0da;
}
"""
