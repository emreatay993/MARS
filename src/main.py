"""
Entry point for the MARS: Modal Analysis Response Solver application.

Tested with Python 3.11

--- You can build a frozen application by using the following command in the project terminal in PyCharm:
.\venv\Scripts\python.exe -m PyInstaller MARS.spec --clean --noconfirm

--- Run in Pycharm via the command:
...PycharmProjects\MARS_> .\venv\Scripts\Activate.ps1
...PycharmProjects\MARS_\src> python -m main

Initialises the Qt application and launches the main window.
"""

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from ui.application_controller import ApplicationController


def main():
    """Main entry point for the application."""
    use_software_opengl = os.getenv("MARS_SOFTWARE_OPENGL", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if use_software_opengl:
        os.environ.setdefault("QT_OPENGL", "software")
        QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)
        print("MARS: software OpenGL mode enabled via MARS_SOFTWARE_OPENGL.")

    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Create application
    app = QApplication(sys.argv)

    # Create and show main window
    main_window = ApplicationController()
    main_window.showMaximized()

    # Run application
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
