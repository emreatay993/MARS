"""
File loading handler for the SolverTab.

This class encapsulates all logic related to opening file dialogs,
loading data using the file_io.loaders, and updating the SolverTab's
state and UI components.
"""

from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox, QApplication
from PyQt5.QtCore import QThread, pyqtSignal, QObject

# Import your existing loaders
from file_io.loaders import (
    load_modal_coordinates, load_modal_coordinates_pch, load_modal_stress,
    load_modal_deformations, load_element_nodal_forces_moments,
    load_steady_state_stress, load_temperature_field
)
from file_io.rst_service import inspect_modal_rst, load_modal_rst
from ui.dialogs.rst_import_dialog import RstImportDialog


class FileLoaderThread(QThread):
    """Background thread for loading large files without freezing the GUI."""
    
    # Signals
    finished = pyqtSignal(object)  # Emits loaded data
    error = pyqtSignal(str)  # Emits error message
    
    def __init__(self, loader_func, *args, **kwargs):
        """
        Initialize the loader thread.
        
        Args:
            loader_func: Function to call for loading (e.g., load_modal_stress)
            *args: Positional arguments passed to the loader.
            **kwargs: Keyword arguments passed to the loader.
        """
        super().__init__()
        self.loader_func = loader_func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        """Run the loader in background thread."""
        try:
            # Process Qt events to allow console updates
            data = self.loader_func(*self.args, **self.kwargs)
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class SolverFileHandler:
    """Manages file selection, loading, and state updates for the SolverTab."""

    def __init__(self, tab):
        """
        Initialize the file handler.

        Args:
            tab (SolverTab): The parent SolverTab instance.
        """
        self.tab = tab

    # --- Ansys Modal Results File ---

    def select_modal_rst(self, checked=False):
        """Inspect an RST, collect import options, then load selected result fields."""
        if not self.tab.coord_loaded or self.tab.modal_data is None:
            QMessageBox.warning(
                self.tab,
                "Modal Coordinates Required",
                "Load the MCF/PCH modal coordinate file before importing an RST file.",
            )
            return

        filename, _ = QFileDialog.getOpenFileName(
            self.tab,
            "Open Modal Results File",
            "",
            "Ansys Result Files (*.rst);;All Files (*)",
        )
        if filename:
            self._inspect_modal_rst(filename)

    def _inspect_modal_rst(self, filename):
        self.tab.setEnabled(False)
        self.tab.console_textbox.append("⏳ Inspecting modal RST in background...\n")
        self.rst_inspection_thread = FileLoaderThread(
            inspect_modal_rst,
            filename,
            self.tab.modal_data.num_modes,
        )
        self.rst_inspection_thread.finished.connect(
            lambda metadata: self._on_rst_inspected(metadata, filename)
        )
        self.rst_inspection_thread.error.connect(self._on_rst_inspection_error)
        self.rst_inspection_thread.start()

    def _on_rst_inspected(self, metadata, filename):
        self.tab.setEnabled(True)
        dialog = RstImportDialog(metadata, self.tab)
        if dialog.exec_() != QDialog.Accepted:
            return
        self._load_modal_rst(filename, dialog.get_options())

    def _on_rst_inspection_error(self, error):
        self.tab.setEnabled(True)
        QMessageBox.warning(
            self.tab,
            "RST Inspection Failed",
            f"The selected modal RST could not be inspected.\n\n{error}\n\n"
            "Packaged MARS includes ansys-dpf-core 0.16.1. Direct RST import "
            "additionally requires an installed Ansys 2025 R2 or newer DPF runtime.",
        )

    def _load_modal_rst(self, filename, options):
        self.tab.setEnabled(False)
        self.tab.console_textbox.append("⏳ Loading selected modal RST results in background...\n")
        self.rst_loader_thread = FileLoaderThread(load_modal_rst, filename, options)
        self.rst_loader_thread.finished.connect(
            lambda bundle: self._on_rst_loaded(bundle, filename)
        )
        self.rst_loader_thread.error.connect(self._on_rst_load_error)
        self.rst_loader_thread.start()

    def _on_rst_loaded(self, bundle, filename):
        self.tab.setEnabled(True)
        try:
            self.tab.on_modal_rst_loaded(bundle, filename)
        except Exception as exc:
            self._on_rst_load_error(str(exc))

    def _on_rst_load_error(self, error):
        self.tab.setEnabled(True)
        QMessageBox.warning(
            self.tab,
            "RST Import Failed",
            f"No existing modal result data was changed.\n\nError: {error}",
        )

    # --- Modal Coordinate File ---

    def select_coord_file(self, checked=False):
        """Open file dialog for modal coordinate file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self.tab, 'Open Modal Coordinate File', '',
            'Coordinate Files (*.mcf *.pch);;MCF Files (*.mcf);;NASTRAN Punch Files (*.pch);;All Files (*)'
        )
        if file_name:
            self._load_coordinate_file(file_name)

    def _load_coordinate_file(self, filename):
        """Load modal coordinate file using background thread."""
        # Disable UI during load
        self.tab.setEnabled(False)
        self.tab.console_textbox.append("⏳ Loading coordinate file in background...\n")

        # Select loader based on file extension
        if filename.lower().endswith('.pch'):
            loader_func = load_modal_coordinates_pch
        else:
            loader_func = load_modal_coordinates

        # Create and start loader thread
        self.coord_loader_thread = FileLoaderThread(loader_func, filename)
        self.coord_loader_thread.finished.connect(
            lambda data: self._on_coordinate_loaded(data, filename)
        )
        self.coord_loader_thread.error.connect(
            lambda error: self._on_coordinate_load_error(error)
        )
        self.coord_loader_thread.start()
    
    def _on_coordinate_loaded(self, modal_data, filename):
        """Handle successful coordinate file load."""
        # Re-enable UI
        self.tab.setEnabled(True)
        
        # Set core data attributes on the main tab
        self.tab.modal_data = None  # Clear old data first
        self.tab.modal_data = modal_data
        self.tab.coord_loaded = True
        self.tab.coord_file_path.setText(filename)

        # Tell the main tab "I'm done, handle the UI"
        self.tab.on_coord_file_loaded(modal_data, filename)
    
    def _on_coordinate_load_error(self, error):
        """Handle coordinate file load error."""
        # Re-enable UI
        self.tab.setEnabled(True)
        
        QMessageBox.warning(
            self.tab, "Invalid File",
            f"The selected Modal Coordinate File is not valid.\n\nError: {error}"
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
        """Load modal stress file using background thread."""
        # Disable UI during load
        self.tab.setEnabled(False)
        self.tab.console_textbox.append("⏳ Loading stress file in background...\n")
        
        # Create and start loader thread
        self.stress_loader_thread = FileLoaderThread(load_modal_stress, filename)
        self.stress_loader_thread.finished.connect(
            lambda data: self._on_stress_loaded(data, filename)
        )
        self.stress_loader_thread.error.connect(
            lambda error: self._on_stress_load_error(error)
        )
        self.stress_loader_thread.start()
    
    def _on_stress_loaded(self, stress_data, filename):
        """Handle successful stress file load."""
        # Re-enable UI
        self.tab.setEnabled(True)
        
        # Set core data
        self.tab.stress_data = None
        self.tab.stress_data = stress_data
        self.tab.stress_file_path.setText(filename)
        self.tab.stress_loaded = True

        # Callback
        self.tab.on_stress_file_loaded(stress_data, filename)
    
    def _on_stress_load_error(self, error):
        """Handle stress file load error."""
        # Re-enable UI
        self.tab.setEnabled(True)
        
        QMessageBox.warning(
            self.tab, "Invalid File",
            f"The selected Modal Stress File is not valid.\n\nError: {error}"
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
        """Load modal deformations file using background thread."""
        # Disable UI during load
        self.tab.setEnabled(False)
        self.tab.console_textbox.append("⏳ Loading deformation file in background...\n")
        
        # Create and start loader thread
        self.deform_loader_thread = FileLoaderThread(load_modal_deformations, filename)
        self.deform_loader_thread.finished.connect(
            lambda data: self._on_deformation_loaded(data, filename)
        )
        self.deform_loader_thread.error.connect(
            lambda error: self._on_deformation_load_error(error)
        )
        self.deform_loader_thread.start()
    
    def _on_deformation_loaded(self, deform_data, filename):
        """Handle successful deformation file load."""
        # Re-enable UI
        self.tab.setEnabled(True)
        
        # Set core data
        self.tab.deformation_data = None
        self.tab.deformation_data = deform_data
        self.tab.deformations_file_path.setText(filename)
        self.tab.deformation_loaded = True

        # Callback
        self.tab.on_deformation_file_loaded(deform_data, filename)
    
    def _on_deformation_load_error(self, error):
        """Handle deformation file load error."""
        # Re-enable UI
        self.tab.setEnabled(True)
        
        self.tab.deformation_loaded = False
        self.tab.deformations_file_path.clear()
        self.tab.on_deformation_file_failed()
        
        QMessageBox.warning(
            self.tab, "Invalid File",
            f"The selected Modal Deformations File is not valid.\n\nError: {error}"
        )

    # --- Element Nodal Forces & Moments File ---

    def select_force_moment_file(self, checked=False):
        """Open file dialog for element nodal forces & moments file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self.tab, 'Open Element Nodal Forces & Moments File', '', 'CSV Files (*.csv)'
        )
        if file_name:
            self._load_force_moment_file(file_name)

    def _load_force_moment_file(self, filename):
        """Load element nodal forces & moments file using background thread."""
        self.tab.setEnabled(False)
        self.tab.console_textbox.append("⏳ Loading element nodal forces & moments file in background...\n")

        self.fm_loader_thread = FileLoaderThread(load_element_nodal_forces_moments, filename)
        self.fm_loader_thread.finished.connect(
            lambda data: self._on_force_moment_loaded(data, filename)
        )
        self.fm_loader_thread.error.connect(
            lambda error: self._on_force_moment_load_error(error)
        )
        self.fm_loader_thread.start()

    def _on_force_moment_loaded(self, fm_data, filename):
        """Handle successful force/moment file load."""
        self.tab.setEnabled(True)
        self.tab.force_moment_data = None
        self.tab.force_moment_data = fm_data
        self.tab.force_moment_file_path.setText(filename)
        self.tab.force_moment_loaded = True
        self.tab.on_force_moment_file_loaded(fm_data, filename)

    def _on_force_moment_load_error(self, error):
        """Handle force/moment file load error."""
        self.tab.setEnabled(True)
        self.tab.force_moment_loaded = False
        self.tab.force_moment_file_path.clear()
        self.tab.on_force_moment_file_failed()
        QMessageBox.warning(
            self.tab, "Invalid File",
            f"The selected Element Nodal Forces & Moments File is not valid.\n\nError: {error}"
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

    # --- Temperature Field File ---

    def select_temperature_field_file(self, checked=False):
        """Open file dialog for temperature field file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self.tab, 'Open Temperature Field File', '',
            'Text Files (*.txt);;All Files (*)'
        )
        if file_name:
            self._load_temperature_field_file(file_name)

    def _load_temperature_field_file(self, filename):
        """Load temperature field file into a DataFrame."""
        try:
            temperature_data = load_temperature_field(filename)
            self.tab.temperature_field_file_path.setText(filename)
            self.tab.on_temperature_field_loaded(temperature_data, filename)
        except ValueError as e:
            self.tab.temperature_field_data = None
            self.tab.temperature_field_file_path.clear()
            QMessageBox.warning(
                self.tab, "Invalid File",
                f"The selected Temperature Field File is not valid.\n\nError: {e}"
            )
