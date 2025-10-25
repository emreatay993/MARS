"""
File loading handler for the SolverTab.

This class encapsulates all logic related to opening file dialogs,
loading data using the file_io.loaders, and updating the SolverTab's
state and UI components.
"""

from PyQt5.QtWidgets import QFileDialog, QMessageBox

# Import your existing loaders
from file_io.loaders import (
    load_modal_coordinates, load_modal_stress,
    load_modal_deformations, load_steady_state_stress
)


class SolverFileHandler:
    """Manages file selection, loading, and state updates for the SolverTab."""

    def __init__(self, tab):
        """
        Initialize the file handler.

        Args:
            tab (SolverTab): The parent SolverTab instance.
        """
        self.tab = tab

    # --- Modal Coordinate File ---

    def select_coord_file(self, checked=False):
        """Open file dialog for modal coordinate file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self.tab, 'Open Modal Coordinate File', '',
            'Coordinate Files (*.mcf)'
        )
        if file_name:
            self._load_coordinate_file(file_name)

    def _load_coordinate_file(self, filename):
        """Load modal coordinate file using the loader."""
        try:
            # 1. Load data
            modal_data = load_modal_coordinates(filename)

            # 2. Set core data attributes on the main tab
            self.tab.modal_data = None  # Clear old data first
            self.tab.modal_data = modal_data
            self.tab.coord_loaded = True
            self.tab.coord_file_path.setText(filename)

            # 3. Tell the main tab "I'm done, handle the UI"
            self.tab.on_coord_file_loaded(modal_data, filename)

        except ValueError as e:
            QMessageBox.warning(
                self.tab, "Invalid File",
                f"The selected Modal Coordinate File is not valid.\n\nError: {e}"
            )

    # --- Modal Stress File ---

    def select_stress_file(self, checked=False):
        """Open file dialog for modal stress file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self.tab, 'Open Modal Stress File', '', 'CSV Files (*.csv)'
        )
        if file_name:
            self._load_stress_file(file_name)

    def _load_stress_file(self, filename):
        """Load modal stress file using the loader."""
        try:
            # 1. Load
            stress_data = load_modal_stress(filename)

            # 2. Set core data
            self.tab.stress_data = None
            self.tab.stress_data = stress_data
            self.tab.stress_file_path.setText(filename)
            self.tab.stress_loaded = True

            # 3. Callback
            self.tab.on_stress_file_loaded(stress_data, filename)

        except ValueError as e:
            QMessageBox.warning(
                self.tab, "Invalid File",
                f"The selected Modal Stress File is not valid.\n\nError: {e}"
            )

    # --- Modal Deformations File ---

    def select_deformations_file(self, checked=False):
        """Open file dialog for modal deformations file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self.tab, 'Open Modal Deformations File', '', 'CSV Files (*.csv)'
        )
        if file_name:
            self._load_deformation_file(file_name)

    def _load_deformation_file(self, filename):
        """Load modal deformations file using the loader."""
        try:
            # 1. Load
            deform_data = load_modal_deformations(filename)

            # 2. Set core data
            self.tab.deformation_data = None
            self.tab.deformation_data = deform_data
            self.tab.deformations_file_path.setText(filename)
            self.tab.deformation_loaded = True

            # 3. Callback
            self.tab.on_deformation_file_loaded(deform_data, filename)

        except ValueError as e:
            self.tab.deformation_loaded = False
            self.tab.deformations_file_path.clear()
            # 3b. Failure callback
            self.tab.on_deformation_file_failed()
            QMessageBox.warning(
                self.tab, "Invalid File",
                f"The selected Modal Deformations File is not valid.\n\nError: {e}"
            )

    # --- Steady-State Stress File ---

    def select_steady_state_file(self, checked=False):
        """Open file dialog for steady-state stress file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self.tab, 'Open Steady-State Stress File', '', 'Text Files (*.txt)'
        )
        if file_name:
            self._load_steady_state_file(file_name)

    def _load_steady_state_file(self, filename):
        """Load steady-state stress file using the loader."""
        try:
            # 1. Load
            steady_data = load_steady_state_stress(filename)

            # 2. Set core data
            self.tab.steady_state_data = steady_data
            self.tab.steady_state_file_path.setText(filename)

            # 3. Callback
            self.tab.on_steady_state_file_loaded(steady_data, filename)

        except ValueError as e:
            QMessageBox.warning(
                self.tab, "Invalid File",
                f"The selected Steady-State Stress File is not valid.\n\nError: {e}"
            )