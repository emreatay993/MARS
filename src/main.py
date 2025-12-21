"""
Entry point for the MARS: Modal Analysis Response Solver application.

Tested with Python 3.11 + torch==2.8.0

--- You can build a frozen application by using the following command in the project terminal in PyCharm:
.\venv\Scripts\python.exe -m PyInstaller MARS.spec --clean --noconfirm

--- Run in Pycharm via the command:
...PycharmProjects\MARS_> .\venv\Scripts\Activate.ps1
...PycharmProjects\MARS_\src> python -m main

Initialises the Qt application and launches the main window.
"""

import sys

# Initialize PyTorch with CUDA DLL fix (must be first import)
# import utils.torch_setup  # noqa: F401

import os
import platform
if platform.system() == "Windows":
    import ctypes
    from importlib.util import find_spec
    try:
        if (spec := find_spec("torch")) and spec.origin and os.path.exists(
            dll_path := os.path.join(os.path.dirname(spec.origin), "lib", "c10.dll")
        ):
            ctypes.CDLL(os.path.normpath(dll_path))
    except Exception:
        pass

# Testing
import torch

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

    # Create and show main window
    main_window = ApplicationController()
    main_window.showMaximized()

    # Run application
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
