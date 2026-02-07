#!/usr/bin/env python3
"""
SHOTER — Discord Username Checker
One-click launcher.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from ui import MainWindow, STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SHOTER")
    app.setStyle("Fusion")

    # Apply dark theme
    app.setStyleSheet(STYLESHEET)

    # Default font
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
