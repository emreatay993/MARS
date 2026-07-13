r"""
Entry point for the MARS: Modal Analysis Response Solver application.

Tested with Python 3.12

--- You can build a frozen application by using the following command in the project terminal in PyCharm:
.\venv\Scripts\python.exe -m PyInstaller MARS.spec --clean --noconfirm

--- Run in Pycharm via the command:
...PycharmProjects\MARS_> .\venv\Scripts\Activate.ps1
...PycharmProjects\MARS_\src> python -m main

Initialises the Qt application and launches the main window.
"""

import sys
from pathlib import Path


def _is_batch_executable() -> bool:
    """Return whether this frozen entry point is the console batch launcher."""
    return bool(
        getattr(sys, "frozen", False)
        and Path(sys.executable).stem.casefold() == "marsbatch"
    )


def _run_gui(argv: list[str]) -> int:
    """Import and launch the Qt application only for interactive runs."""
    import os

    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication

    from ui.application_controller import ApplicationController
    from mars_solver.utils import constants
    from utils.app_settings import (
        apply_solver_runtime_settings,
        load_app_settings,
        parse_software_opengl_env,
    )

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
    app = QApplication([sys.argv[0], *argv])

    # Create and show main window
    main_window = ApplicationController()
    main_window.showMaximized()

    return app.exec_()


def main(argv: list[str] | None = None) -> int:
    """Dispatch to the GUI or the Qt-free batch command line."""
    args = list(sys.argv[1:] if argv is None else argv)
    if _is_batch_executable():
        from mars_solver.headless_runtime import cli_main

        return cli_main(args)
    if args[:1] == ["batch"]:
        from mars_solver.headless_runtime import cli_main

        return cli_main(args[1:])

    return _run_gui(args)


if __name__ == "__main__":
    raise SystemExit(main())
