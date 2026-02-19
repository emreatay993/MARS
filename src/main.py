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
from utils import constants
from utils.app_settings import (
    apply_solver_runtime_settings,
    load_app_settings,
    parse_software_opengl_env,
)


def main():
    """Main entry point for the application."""
    app_settings = load_app_settings()
    apply_solver_runtime_settings(app_settings, constants)

    env_software_gl = parse_software_opengl_env()
    if env_software_gl is None:
        use_software_opengl = bool(app_settings.get("software_opengl", False))
        software_gl_source = "advanced settings"
    else:
        use_software_opengl = env_software_gl
        software_gl_source = "MARS_SOFTWARE_OPENGL"

    if use_software_opengl:
        os.environ.setdefault("QT_OPENGL", "software")
        QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)
        print(
            f"MARS: software OpenGL mode enabled via {software_gl_source}."
        )

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
