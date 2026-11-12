"""
Agy Session Manager - Main entry point.
A desktop GUI to manage Agy CLI conversations/sessions.
"""
import sys
import os
import ctypes

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

# Set Windows explicit AppUserModelID for taskbar pinning & icon display
if sys.platform == "win32":
    try:
        myappid = "agytools.agysessionmanager.desktop.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt

from src.main_window import MainWindow


def main():
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Agy Session Manager")
    app.setOrganizationName("AgyTools")

    # Set Application & Window Icon
    icon_path = os.path.join(ROOT_DIR, "assets", "icon.ico")
    if os.path.isfile(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    # Default font
    font = QFont("Segoe UI", 11)
    app.setFont(font)

    window = MainWindow()
    if os.path.isfile(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
