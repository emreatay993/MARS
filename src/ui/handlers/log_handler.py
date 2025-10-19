"""
Log Handler for the SolverTab.

This class encapsulates all logic related to formatting log messages
and appending them to the UI's console.
"""

import os


class SolverLogHandler:
    """Manages formatting and writing log messages to the console."""

    def __init__(self, tab):
        """
        Initialize the log handler.

        Args:
            tab (SolverTab): The parent SolverTab instance (to access console).
        """
        self.tab = tab

    def _log_coordinate_load(self, filename, modal_data):
        """Log successful coordinate file load."""
        self.tab.console_textbox.append(
            f"Successfully validated and loaded modal coordinate file: "
            f"{os.path.basename(filename)}\n"
        )
        self.tab.console_textbox.append(
            f"Modal coordinates tensor shape (m x n): {modal_data.modal_coord.shape}\n"
        )

    def _log_stress_load(self, filename, stress_data):
        """Log successful stress file load."""
        self.tab.console_textbox.append(
            f"Successfully validated and loaded modal stress file: "
            f"{os.path.basename(filename)}\n"
        )
        self.tab.console_textbox.append(f"Node IDs tensor shape: {stress_data.node_ids.shape}\n")
        self.tab.console_textbox.append("Normal stress components extracted: SX, SY, SZ, SXY, SYZ, SXZ")
        self.tab.console_textbox.append(
            f"SX shape: {stress_data.modal_sx.shape}, "
            f"SY shape: {stress_data.modal_sy.shape}, "
            f"SZ shape: {stress_data.modal_sz.shape}"
        )
        self.tab.console_textbox.append(
            f"SXY shape: {stress_data.modal_sxy.shape}, "
            f"SYZ shape: {stress_data.modal_syz.shape}, "
            f"SXZ shape: {stress_data.modal_sxz.shape}\n"
        )
        self.tab.console_textbox.verticalScrollBar().setValue(
            self.tab.console_textbox.verticalScrollBar().maximum()
        )

    def _log_deformation_load(self, filename, deform_data):
        """Log successful deformation file load."""
        self.tab.console_textbox.append(
            f"Successfully validated and loaded modal deformations file: "
            f"{os.path.basename(filename)}\n"
        )
        self.tab.console_textbox.append(
            f"Deformations array shapes: "
            f"UX {deform_data.modal_ux.shape}, "
            f"UY {deform_data.modal_uy.shape}, "
            f"UZ {deform_data.modal_uz.shape}"
        )

    def _log_steady_state_load(self, filename, steady_data):
        """Log successful steady-state file load."""
        self.tab.console_textbox.append(
            f"Successfully validated and loaded steady-state stress file: "
            f"{os.path.basename(filename)}\n"
        )
        self.tab.console_textbox.append(
            f"Steady-state stress data shape: {steady_data.node_ids.shape}"
        )