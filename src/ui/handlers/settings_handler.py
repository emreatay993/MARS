"""
Handles the application and management of advanced settings.
"""

import os

import utils.constants as constants
from utils.app_settings import (
    apply_solver_runtime_settings,
    save_app_settings,
)


class SettingsHandler:
    """Manages applying advanced settings to the solver engine."""

    def __init__(self):
        """Initialize the settings handler."""
        pass

    def apply_advanced_settings(self, settings):
        """Apply advanced settings to global constants."""
        apply_solver_runtime_settings(settings, constants)

        software_opengl_enabled = bool(settings.get("software_opengl", False))
        os.environ["MARS_SOFTWARE_OPENGL"] = "1" if software_opengl_enabled else "0"

        save_app_settings(
            {
                "ram_percent": constants.RAM_PERCENT,
                "precision": constants.DEFAULT_PRECISION,
                "software_opengl": software_opengl_enabled,
            }
        )

        print("\n--- Advanced settings updated ---")
        print(f"  RAM Allocation: {constants.RAM_PERCENT * 100:.0f}%")
        print(f"  Solver Precision: {constants.DEFAULT_PRECISION}")
        print(
            f"  Software OpenGL (next launch): "
            f"{'On' if software_opengl_enabled else 'Off'}"
        )
        print("---------------------------------")
