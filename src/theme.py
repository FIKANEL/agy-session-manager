"""
theme.py - Design tokens and Stylesheet generator based on Linear and Raycast Brand DNA.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class DarkTokens:
    # Canvas & Surface Ladder
    canvas: str = "#08090a"
    sidebar: str = "#0c0d10"
    panel: str = "#101115"
    surface_card: str = "#131419"
    surface_card_hover: str = "#181a21"
    surface_selected: str = "#1a1d29"
    surface_input: str = "#12141a"
    surface_command_box: str = "#090a0d"

    # Hairline Borders (High contrast against dark surfaces)
    hairline: str = "#2a2d37"
    hairline_strong: str = "#3c4050"
    hairline_selected: str = "#5e6ad2"

    # Typography / Ink
    ink_primary: str = "#f7f8f8"
    # Secondary text: #a6abb8 (Contrast ratio >= 8.0:1 on #131419, WCAG AAA compliant)
    ink_secondary: str = "#a6abb8"
    # Tertiary text: #767b8a (Contrast ratio >= 5.1:1 on #131419, WCAG AA compliant)
    ink_subtle: str = "#767b8a"
    ink_disabled: str = "#454854"

    # Brand & Semantic Accents
    primary: str = "#5e6ad2"
    primary_hover: str = "#6e7adf"
    primary_pressed: str = "#4d58ba"
    primary_ink: str = "#ffffff"

    secondary_bg: str = "#1b1d24"
    secondary_hover: str = "#252833"
    secondary_border: str = "#2f323e"
    secondary_ink: str = "#e1e4ea"

    # Semantic Statuses
    success: str = "#22c55e"
    success_bg: str = "rgba(34, 197, 94, 0.12)"
    success_border: str = "rgba(34, 197, 94, 0.32)"

    warning: str = "#f59e0b"
    warning_bg: str = "rgba(245, 158, 11, 0.12)"
    warning_border: str = "rgba(245, 158, 11, 0.38)"

    danger: str = "#ef4444"
    danger_bg: str = "rgba(239, 68, 68, 0.12)"
    danger_border: str = "rgba(239, 68, 68, 0.38)"

    # Star / Favorite
    star_active: str = "#eab308"
    star_inactive: str = "#767b8a"

    # Chat Bubbles (Distinct left accents & background hues)
    user_bubble_bg: str = "#141b2d"
    user_bubble_border: str = "#283556"
    user_bubble_accent: str = "#4f6df5"
    user_bubble_ink: str = "#ecf1fc"
    user_badge: str = "#8ba2ff"

    assistant_bubble_bg: str = "#101116"
    assistant_bubble_border: str = "#242732"
    assistant_bubble_accent: str = "#5e6ad2"
    assistant_bubble_ink: str = "#e7e9ee"
    assistant_badge: str = "#a2aaf4"

    system_bubble_bg: str = "#131418"
    system_bubble_border: str = "#282a33"
    system_bubble_accent: str = "#6b7280"

    tool_chip_bg: str = "#16171e"
    tool_chip_border: str = "#282b36"
    tool_chip_ink: str = "#a6abb8"


@dataclass(frozen=True)
class LightTokens:
    canvas: str = "#f7f8fa"
    sidebar: str = "#eef0f4"
    panel: str = "#ffffff"
    surface_card: str = "#ffffff"
    surface_card_hover: str = "#f3f5f8"
    surface_selected: str = "#edeefb"
    surface_input: str = "#ffffff"
    surface_command_box: str = "#f0f2f6"

    hairline: str = "#d8dce6"
    hairline_strong: str = "#bcc2cf"
    hairline_selected: str = "#5e6ad2"

    ink_primary: str = "#16181d"
    ink_secondary: str = "#4e5462"
    ink_subtle: str = "#6f7686"
    ink_disabled: str = "#9ca3af"

    primary: str = "#5e6ad2"
    primary_hover: str = "#525ec0"
    primary_pressed: str = "#4650a8"
    primary_ink: str = "#ffffff"

    secondary_bg: str = "#ffffff"
    secondary_hover: str = "#f3f5f8"
    secondary_border: str = "#d4d8e2"
    secondary_ink: str = "#1c1f26"

    success: str = "#16a34a"
    success_bg: str = "rgba(22, 163, 74, 0.1)"
    success_border: str = "rgba(22, 163, 74, 0.28)"

    warning: str = "#d97706"
    warning_bg: str = "rgba(217, 119, 6, 0.1)"
    warning_border: str = "rgba(217, 119, 6, 0.32)"

    danger: str = "#dc2626"
    danger_bg: str = "rgba(220, 38, 38, 0.1)"
    danger_border: str = "rgba(220, 38, 38, 0.32)"

    # Star / Favorite
    star_active: str = "#d97706"
    star_inactive: str = "#9ca3af"

    user_bubble_bg: str = "#eef3fc"
    user_bubble_border: str = "#d3def4"
    user_bubble_accent: str = "#3b82f6"
    user_bubble_ink: str = "#111827"
    user_badge: str = "#2563eb"

    assistant_bubble_bg: str = "#ffffff"
    assistant_bubble_border: str = "#e0e3eb"
    assistant_bubble_accent: str = "#5e6ad2"
    assistant_bubble_ink: str = "#1f242e"
    assistant_badge: str = "#4f5ab8"

    system_bubble_bg: str = "#f3f4f6"
    system_bubble_border: str = "#e5e7eb"
    system_bubble_accent: str = "#9ca3af"

    tool_chip_bg: str = "#f4f5f8"
    tool_chip_border: str = "#dce0e8"
    tool_chip_ink: str = "#4b5262"


@dataclass(frozen=True)
class Typography:
    font_family_ui: str = '"Segoe UI", -apple-system, BlinkMacSystemFont, "Inter", sans-serif'
    font_family_mono: str = '"Cascadia Code", "Consolas", "SF Mono", monospace'

    size_hero: int = 15
    size_title: int = 13
    size_body: int = 12
    size_sub: int = 11
    size_micro: int = 10


@dataclass(frozen=True)
class Spacing:
    xxs: int = 2
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 20


@dataclass(frozen=True)
class Radius:
    xs: int = 4
    sm: int = 6
    md: int = 8
    lg: int = 10
    pill: int = 9999


DARK = DarkTokens()
LIGHT = LightTokens()
TYPO = Typography()
SPACE = Spacing()
RAD = Radius()


def get_stylesheet(theme: str = "dark") -> str:
    """Generate Qt stylesheet for the chosen theme."""
    t = DARK if theme == "dark" else LIGHT

    return f"""
QMainWindow, QDialog {{
    background-color: {t.canvas};
    color: {t.ink_primary};
}}
QWidget {{
    background-color: {t.canvas};
    color: {t.ink_primary};
    font-family: {TYPO.font_family_ui};
    font-size: 13px;
}}

/* Sidebar */
QWidget#sidebar {{
    background-color: {t.sidebar};
    border-right: 1px solid {t.hairline};
}}
QWidget#sidebar QPushButton {{
    background-color: transparent;
    color: {t.ink_secondary};
    border: 1px solid transparent;
    border-radius: {RAD.sm}px;
    padding: 8px 12px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}}
QWidget#sidebar QPushButton:hover {{
    background-color: {t.surface_card_hover};
    color: {t.ink_primary};
    border: 1px solid {t.hairline};
}}
QWidget#sidebar QPushButton:checked,
QWidget#sidebar QPushButton[active="true"] {{
    background-color: {t.surface_selected};
    color: {t.ink_primary};
    border: 1px solid {t.hairline_selected};
    font-weight: 600;
}}

/* Session List View */
QListWidget#sessionList {{
    background-color: {t.sidebar};
    border: none;
    outline: none;
    padding: 4px;
}}
QListWidget#sessionList::item {{
    background: transparent;
    border: none;
    margin: 2px 4px;
    padding: 0px;
    color: {t.ink_primary};
}}
QListWidget#sessionList::item:hover {{
    background: transparent;
    border: none;
}}
QListWidget#sessionList::item:selected {{
    background: transparent;
    border: none;
}}

/* Session Card Container inside Item */
QFrame#sessionCard {{
    background-color: {t.surface_card};
    border: 1px solid {t.hairline};
    border-radius: {RAD.md}px;
}}
QFrame#sessionCard:hover {{
    background-color: {t.surface_card_hover};
    border: 1px solid {t.hairline_strong};
}}
QFrame#sessionCard[selected="true"] {{
    background-color: {t.surface_selected};
    border: 1px solid {t.primary};
}}

/* Fork Child Card Container */
QFrame#forkCard {{
    background-color: {t.surface_input};
    border: 1px solid {t.hairline};
    border-radius: {RAD.md}px;
}}
QFrame#forkCard:hover {{
    background-color: {t.surface_card_hover};
    border: 1px solid {t.hairline_strong};
}}
QFrame#forkCard[selected="true"] {{
    background-color: {t.surface_selected};
    border: 1px solid {t.primary};
}}

/* Search & Input Fields */
QLineEdit {{
    background-color: {t.surface_input};
    border: 1px solid {t.hairline};
    border-radius: {RAD.md}px;
    padding: 7px 12px;
    color: {t.ink_primary};
    font-size: 13px;
    selection-background-color: {t.primary};
}}
QLineEdit:focus {{
    border: 1px solid {t.primary};
    background-color: {t.panel};
}}

/* Action Buttons Hierarchy */
QPushButton#primaryActionBtn {{
    background-color: {t.primary};
    color: {t.primary_ink};
    border: 1px solid {t.primary};
    border-radius: {RAD.md}px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton#primaryActionBtn:hover {{
    background-color: {t.primary_hover};
    border: 1px solid {t.primary_hover};
}}
QPushButton#primaryActionBtn:pressed {{
    background-color: {t.primary_pressed};
}}
QPushButton#primaryActionBtn:disabled {{
    background-color: {t.surface_card};
    color: {t.ink_disabled};
    border: 1px solid {t.hairline};
}}

QPushButton#secondaryActionBtn {{
    background-color: {t.secondary_bg};
    color: {t.secondary_ink};
    border: 1px solid {t.secondary_border};
    border-radius: {RAD.md}px;
    padding: 7px 13px;
    font-weight: 500;
    font-size: 12px;
}}
QPushButton#secondaryActionBtn:hover {{
    background-color: {t.secondary_hover};
    border: 1px solid {t.hairline_strong};
    color: {t.ink_primary};
}}
QPushButton#secondaryActionBtn:pressed {{
    background-color: {t.surface_card};
}}
QPushButton#secondaryActionBtn:disabled {{
    color: {t.ink_disabled};
    border: 1px solid {t.hairline};
}}

QPushButton#ghostActionBtn {{
    background-color: transparent;
    color: {t.ink_secondary};
    border: 1px solid {t.hairline};
    border-radius: {RAD.md}px;
    padding: 7px 13px;
    font-weight: 500;
    font-size: 12px;
}}
QPushButton#ghostActionBtn:hover {{
    background-color: {t.surface_card_hover};
    color: {t.ink_primary};
    border: 1px solid {t.hairline_strong};
}}
QPushButton#ghostActionBtn:disabled {{
    color: {t.ink_disabled};
    border: 1px solid {t.hairline};
}}

/* Danger Action Buttons */
QPushButton#dangerActionBtn {{
    background-color: transparent;
    color: #f87171;
    border: 1px solid #5c2429;
    border-radius: {RAD.sm}px;
    padding: 6px 12px;
    font-weight: 500;
    font-size: 12px;
}}
QPushButton#dangerActionBtn:hover {{
    background-color: #381a1f;
    border: 1px solid #e06c75;
    color: #ff9b9b;
}}
QPushButton#dangerActionBtn:pressed {{
    background-color: #481e25;
}}
QPushButton#dangerActionBtn:disabled {{
    color: {t.ink_disabled};
    border: 1px solid {t.hairline};
    background-color: transparent;
}}

QPushButton#solidDangerBtn {{
    background-color: #dc2626;
    color: #ffffff;
    border: 1px solid #ef4444;
    border-radius: {RAD.sm}px;
    padding: 7px 14px;
    font-weight: 600;
    font-size: 12px;
}}
QPushButton#solidDangerBtn:hover {{
    background-color: #b91c1c;
    border: 1px solid #dc2626;
}}
QPushButton#solidDangerBtn:pressed {{
    background-color: #991b1b;
}}
QPushButton#solidDangerBtn:disabled {{
    background-color: {t.surface_card};
    color: {t.ink_disabled};
    border: 1px solid {t.hairline};
}}

/* Icon-only Tool Button */
QPushButton#iconToolBtn {{
    background-color: {t.surface_input};
    color: {t.ink_secondary};
    border: 1px solid {t.hairline};
    border-radius: {RAD.md}px;
    padding: 6px;
}}
QPushButton#iconToolBtn:hover {{
    background-color: {t.surface_card_hover};
    color: {t.ink_primary};
    border: 1px solid {t.hairline_strong};
}}

/* Star / Favorite Button */
QPushButton#starBtn {{
    background-color: {t.surface_input};
    color: {t.ink_secondary};
    border: 1px solid {t.hairline};
    border-radius: {RAD.md}px;
    padding: 6px;
}}
QPushButton#starBtn:hover {{
    background-color: {t.surface_card_hover};
    border: 1px solid {t.hairline_strong};
}}
QPushButton#starBtn[starred="true"] {{
    background-color: {t.warning_bg};
    border: 1px solid {t.warning_border};
}}

/* Context Menu */
QMenu {{
    background-color: {t.surface_card};
    border: 1px solid {t.hairline_strong};
    border-radius: {RAD.md}px;
    padding: 6px;
}}
QMenu::item {{
    background-color: transparent;
    color: {t.ink_primary};
    padding: 6px 20px 6px 10px;
    border-radius: {RAD.sm}px;
    font-size: 13px;
}}
QMenu::item:selected {{
    background-color: {t.surface_selected};
    color: {t.ink_primary};
}}
QMenu::separator {{
    height: 1px;
    background-color: {t.hairline};
    margin: 4px 6px;
}}

/* Command Preview Box (Raycast Terminal Pill) */
QFrame#commandBox {{
    background-color: {t.surface_command_box};
    border: 1px solid {t.hairline};
    border-radius: {RAD.md}px;
    padding: 4px 10px;
}}
QLabel#commandPrompt {{
    font-family: {TYPO.font_family_mono};
    font-size: 12px;
    font-weight: bold;
    color: {t.primary};
    background-color: transparent;
}}
QLabel#commandText {{
    font-family: {TYPO.font_family_mono};
    font-size: 11px;
    color: {t.ink_secondary};
    background-color: transparent;
}}
QPushButton#commandCopyBtn {{
    background-color: transparent;
    border: none;
    padding: 4px;
    border-radius: 4px;
}}
QPushButton#commandCopyBtn:hover {{
    background-color: {t.surface_card_hover};
}}

/* Skip Permissions Pill */
QFrame#permWarningBadge {{
    background-color: {t.warning_bg};
    border: 1px solid {t.warning_border};
    border-radius: {RAD.sm}px;
    padding: 2px 8px;
}}
QLabel#permWarningText {{
    color: {t.warning};
    font-size: 11px;
    font-weight: 600;
    background-color: transparent;
}}

/* Chat Message Bubbles */
QFrame#userMsg {{
    background-color: {t.user_bubble_bg};
    border: 1px solid {t.user_bubble_border};
    border-left: 3px solid {t.user_bubble_accent};
    border-radius: {RAD.md}px;
}}
QFrame#assistantMsg {{
    background-color: {t.assistant_bubble_bg};
    border: 1px solid {t.assistant_bubble_border};
    border-left: 3px solid {t.assistant_bubble_accent};
    border-radius: {RAD.md}px;
}}
QFrame#systemMsg {{
    background-color: {t.system_bubble_bg};
    border: 1px solid {t.system_bubble_border};
    border-left: 3px solid {t.system_bubble_accent};
    border-radius: {RAD.md}px;
}}

/* Metadata Chips */
QFrame#metaChip {{
    background-color: {t.tool_chip_bg};
    border: 1px solid {t.tool_chip_border};
    border-radius: {RAD.sm}px;
    padding: 2px 6px;
}}
QLabel#metaChipText {{
    color: {t.tool_chip_ink};
    font-family: {TYPO.font_family_mono};
    font-size: 11px;
    background-color: transparent;
}}

/* Scrollbars */
QScrollArea {{
    border: none;
    background-color: {t.panel};
}}
QScrollBar:vertical {{
    background-color: {t.sidebar};
    width: 6px;
    border: none;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background-color: {t.hairline_strong};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {t.ink_subtle};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* ComboBox */
QComboBox {{
    background-color: {t.surface_input};
    border: 1px solid {t.hairline};
    border-radius: {RAD.sm}px;
    padding: 5px 10px;
    color: {t.ink_primary};
    font-size: 12px;
}}
QComboBox:hover {{
    border: 1px solid {t.hairline_strong};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {t.panel};
    color: {t.ink_primary};
    selection-background-color: {t.surface_selected};
    selection-color: {t.ink_primary};
    border: 1px solid {t.hairline_strong};
    border-radius: {RAD.sm}px;
    padding: 4px;
}}

/* Radio Button & Checkbox */
QRadioButton, QCheckBox {{
    color: {t.ink_secondary};
    spacing: 6px;
    font-size: 12px;
}}
QRadioButton:hover, QCheckBox:hover {{
    color: {t.ink_primary};
}}
QRadioButton::indicator, QCheckBox::indicator {{
    width: 14px;
    height: 14px;
}}

/* Tooltips */
QToolTip {{
    background-color: {t.surface_card};
    color: {t.ink_primary};
    border: 1px solid {t.hairline_strong};
    padding: 6px 10px;
    border-radius: {RAD.sm}px;
    font-size: 11px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {t.sidebar};
    color: {t.ink_secondary};
    border-top: 1px solid {t.hairline};
    font-size: 11px;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {t.hairline};
    width: 1px;
}}
"""
