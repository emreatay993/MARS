"""
Entry point for the MSUP Smart Solver application.

This script initializes the Qt application and launches the main window.
"""

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from ui.application_controller import ApplicationController


def main():
    """Main entry point for the application."""
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Create application
    app = QApplication(sys.argv)

    # Note: Styles are applied selectively to individual widgets
    # to match legacy behavior, not globally to the application

    # Create and show main window
    main_window = ApplicationController()
    main_window.showMaximized()

    # Run application
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

