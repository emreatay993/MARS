"""
Solver tab implementation for MARS (Modal Analysis Response Solver).

Refactored from the legacy MSUPSmartSolverGUI to use UI builders, data models,
and the AnalysisEngine facade.
"""

import os
import sys

import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QMessageBox, QWidget, QDialog, QVBoxLayout

# Import builders and managers
from ui.builders.solver_ui import SolverTabUIBuilder
from ui.handlers.file_handler import SolverFileHandler
from ui.handlers.ui_state_handler import SolverUIHandler
from ui.handlers.analysis_handler import SolverAnalysisHandler
from ui.handlers.log_handler import SolverLogHandler
from ui.widgets.console import Logger
from ui.widgets.plotting import MatplotlibWidget
from core.computation import AnalysisEngine
from core.data_models import (
    ModalData, ModalStressData, DeformationData, 
    SteadyStateData, SolverConfig
)


class SolverTab(QWidget):
    """
    Solver tab for MARS transient analysis.

    Manages file loading, solver configuration, and analysis execution using UI
    builders, data models, and the AnalysisEngine.

    Signals:
        initial_data_loaded: Emitted when initial data is loaded
        time_point_result_ready: Emitted when time point results are ready
        animation_data_ready: Emitted when animation data is ready
    """
    
    # Signals
    initial_data_loaded = pyqtSignal(object)
    time_point_result_ready = pyqtSignal(object, str, float, float)
    animation_data_ready = pyqtSignal(object)
    animation_precomputation_failed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize the Solver Tab."""
        super().__init__(parent)
        
        # Initialize state
        self.project_directory = None
        self.modal_data = None
        self.stress_data = None
        self.deformation_data = None
        self.steady_state_data = None

        self.analysis_engine = AnalysisEngine()
        self.file_handler = SolverFileHandler(self)
        self.ui_handler = SolverUIHandler(self)
        self.analysis_handler = SolverAnalysisHandler(self)
        self.log_handler = SolverLogHandler(self)
        
        # Flags for loaded data
        self.coord_loaded = False
        self.stress_loaded = False
        self.deformation_loaded = False
        
        # For plotting
        self.plot_dialog = None
        self.modal_plot_window = None
        self.plot_min_over_time_tab = None
        self.plot_max_over_time_tab = None
        
        # Build UI
        self._build_ui()
        
        # Setup logger
        self.logger = Logger(self.console_textbox)
        sys.stdout = self.logger
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Initial state
        self.ui_handler._update_solve_button_state()
    
    def _build_ui(self):
        """Build the UI using the UI builder."""
        builder = SolverTabUIBuilder()
        
        # Set window palette
        builder.set_window_palette(self)
        
        # Build layout and get components
        layout, self.components = builder.build_complete_layout()
        self.setLayout(layout)
        
        # Store commonly used components as direct attributes
        self._setup_component_references()
        
        # Connect signals
        self._connect_signals()
        
        # Setup initial state
        self._setup_initial_state()
    
    def _setup_component_references(self):
        """Create direct references to frequently used components."""
        # File controls
        self.coord_file_button = self.components['coord_file_button']
        self.coord_file_path = self.components['coord_file_path']
        self.stress_file_button = self.components['stress_file_button']
        self.stress_file_path = self.components['stress_file_path']
        self.steady_state_checkbox = self.components['steady_state_checkbox']
        self.steady_state_file_button = self.components['steady_state_file_button']
        self.steady_state_file_path = self.components['steady_state_file_path']
        self.deformations_checkbox = self.components['deformations_checkbox']
        self.deformations_file_button = self.components['deformations_file_button']
        self.deformations_file_path = self.components['deformations_file_path']
        self.skip_modes_label = self.components['skip_modes_label']
        self.skip_modes_combo = self.components['skip_modes_combo']
        
        # Output checkboxes
        self.time_history_checkbox = self.components['time_history_checkbox']
        self.max_principal_stress_checkbox = self.components['max_principal_stress_checkbox']
        self.min_principal_stress_checkbox = self.components['min_principal_stress_checkbox']
        self.von_mises_checkbox = self.components['von_mises_checkbox']
        self.deformation_checkbox = self.components['deformation_checkbox']
        self.velocity_checkbox = self.components['velocity_checkbox']
        self.acceleration_checkbox = self.components['acceleration_checkbox']
        self.damage_index_checkbox = self.components['damage_index_checkbox']
        
        # Fatigue parameters
        self.A_line_edit = self.components['A_line_edit']
        self.m_line_edit = self.components['m_line_edit']
        self.fatigue_params_group = self.components['fatigue_params_group']
        
        # Single node controls
        self.node_line_edit = self.components['node_line_edit']
        self.single_node_group = self.components['single_node_group']
        
        # Console and plots
        self.console_textbox = self.components['console_textbox']
        self.show_output_tab_widget = self.components['show_output_tab_widget']
        self.plot_single_node_tab = self.components['plot_single_node_tab']
        self.plot_modal_coords_tab = self.components['plot_modal_coords_tab']
        
        # Progress and solve
        self.progress_bar = self.components['progress_bar']
        self.solve_button = self.components['solve_button']
        
        # Lists of output checkboxes
        self._deformation_outputs = [
            self.deformation_checkbox,
            self.velocity_checkbox,
            self.acceleration_checkbox
        ]
        
        self._coord_stress_outputs = [
            self.time_history_checkbox,
            self.max_principal_stress_checkbox,
            self.min_principal_stress_checkbox,
            self.von_mises_checkbox,
            self.damage_index_checkbox
        ]
        
        self.time_history_exclusive_outputs = [
            self.max_principal_stress_checkbox,
            self.min_principal_stress_checkbox,
            self.von_mises_checkbox,
            self.deformation_checkbox,
            self.velocity_checkbox,
            self.acceleration_checkbox
        ]
    
    def _connect_signals(self):
        """Connect UI signals to their handlers."""
        # File loading
        self.coord_file_button.clicked.connect(self.file_handler.select_coord_file)
        self.stress_file_button.clicked.connect(self.file_handler.select_stress_file)
        self.deformations_file_button.clicked.connect(self.file_handler.select_deformations_file)
        self.steady_state_file_button.clicked.connect(self.file_handler.select_steady_state_file)
        
        # Checkboxes
        self.steady_state_checkbox.toggled.connect(self.ui_handler.toggle_steady_state_stress_inputs)
        self.deformations_checkbox.toggled.connect(self.ui_handler.toggle_deformations_inputs)
        self.time_history_checkbox.toggled.connect(self.ui_handler.toggle_single_node_solution_group)
        self.time_history_checkbox.toggled.connect(self.ui_handler._on_time_history_toggled)
        self.von_mises_checkbox.toggled.connect(self.ui_handler.toggle_damage_index_checkbox_visibility)
        self.von_mises_checkbox.toggled.connect(self.ui_handler._update_damage_index_state)
        self.time_history_checkbox.toggled.connect(self.ui_handler._update_damage_index_state)
        self.damage_index_checkbox.toggled.connect(self.ui_handler.toggle_fatigue_params_visibility)
        
        # Plot updates
        self.max_principal_stress_checkbox.toggled.connect(
            self.ui_handler.update_single_node_plot_based_on_checkboxes
        )
        self.min_principal_stress_checkbox.toggled.connect(
            self.ui_handler.update_single_node_plot_based_on_checkboxes
        )
        self.von_mises_checkbox.toggled.connect(
            self.ui_handler.update_single_node_plot_based_on_checkboxes
        )
        
        # Connect checkboxes to update max/min over time plots
        self.von_mises_checkbox.toggled.connect(self.ui_handler._update_max_min_plots)
        self.max_principal_stress_checkbox.toggled.connect(self.ui_handler._update_max_min_plots)
        self.min_principal_stress_checkbox.toggled.connect(self.ui_handler._update_max_min_plots)
        self.deformation_checkbox.toggled.connect(self.ui_handler._update_max_min_plots)
        self.velocity_checkbox.toggled.connect(self.ui_handler._update_max_min_plots)
        self.acceleration_checkbox.toggled.connect(self.ui_handler._update_max_min_plots)
        
        # Skip modes
        self.skip_modes_combo.currentTextChanged.connect(self.ui_handler.on_skip_modes_changed)
        
        # Node entry
        self.node_line_edit.returnPressed.connect(self.on_node_entered)
        
        # Solve button
        self.solve_button.clicked.connect(lambda: self.analysis_handler.solve())
        
        # Progress bar
        # Will be connected to solver signal when solver is created
    
    def _setup_initial_state(self):
        """Setup initial widget states."""
        self.ui_handler.toggle_damage_index_checkbox_visibility()
        self.ui_handler.update_single_node_plot()

    def on_coord_file_loaded(self, modal_data, filename):
        """Handle all UI and state updates after a coord file is loaded."""

        # 1. Clear old plot data
        self.plot_modal_coords_tab.clear_plot()

        # 2. Tell UI Handler to update tabs
        self.ui_handler._hide_plot_tabs()

        # 3. Log the success
        self.log_handler._log_coordinate_load(filename, modal_data)

        # 4. Update the plot widget
        self.plot_modal_coords_tab.update_plot(
            modal_data.time_values, modal_data.modal_coord
        )

        # 5. Tell UI Handler to show the correct tab
        self.ui_handler._show_modal_coords_tab()

        # 6. Update all other UI states
        self.ui_handler.update_output_checkboxes_state()
        self.ui_handler._update_solve_button_state()

        # 7. Emit data for other tabs
        self._check_and_emit_initial_data()

    def on_stress_file_loaded(self, stress_data, filename):
        """Handle all UI and state updates after a stress file is loaded."""
        # 1. Clear plots
        self.plot_single_node_tab.clear_plot()
        if hasattr(self, 'window') and self.window() is not None:
            if hasattr(self.window(), 'display_tab'):
                self.window().display_tab._clear_visualization()

        # 2. Update UI
        self.ui_handler._update_skip_modes_combo(stress_data.num_modes)
        self.ui_handler.update_output_checkboxes_state()
        self.ui_handler._update_solve_button_state()

        # 3. Log
        self.log_handler._log_stress_load(filename, stress_data)

        # 4. Emit data
        self._check_and_emit_initial_data()

    def on_deformation_file_loaded(self, deform_data, filename):
        """Handle all UI and state updates after a deformation file is loaded."""
        # 1. Clear/Update UI
        self.skip_modes_combo.clear()
        self.ui_handler._update_skip_modes_combo(deform_data.num_modes)
        # Note: toggle_deformations_inputs() is already connected to the checkbox
        # which is checked, so the UI is already correct. We just update state.
        self.ui_handler.update_output_checkboxes_state()

        # 2. Log
        self.log_handler._log_deformation_load(filename, deform_data)
        sys.stdout.flush()

        # 3. Emit data
        self._check_and_emit_initial_data()

    def on_deformation_file_failed(self):
        """Handle UI updates when deformation file fails to load."""
        # This just resets the UI state
        self.ui_handler.toggle_deformations_inputs()

    def on_steady_state_file_loaded(self, steady_data, filename):
        """Handle all UI and state updates after a steady-state file is loaded."""
        # 1. Log
        self.log_handler._log_steady_state_load(filename, steady_data)
        sys.stdout.flush()

    def _check_and_emit_initial_data(self):
        """Check if data is loaded and emit signal."""
        if self.coord_loaded and self.stress_loaded:
            initial_data = (
                self.modal_data.time_values,
                self.stress_data.node_coords,
                self.stress_data.node_ids,
                self.deformation_loaded
            )
            self.initial_data_loaded.emit(initial_data)

    @pyqtSlot(int)
    def update_progress_bar(self, value):
        """
        Update progress bar value.
        
        Args:
            value: Progress percentage (0-100).
        """
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"Progress: {value}%")
    
    # ========== Plot Management Methods ==========

    @pyqtSlot()
    def on_node_entered(self):
        """Handle Enter key press in node ID field."""
        try:
            entered_text = self.node_line_edit.text()
            if not entered_text.isdigit():
                QMessageBox.warning(
                    self, "Invalid Input",
                    "Please enter a valid integer Node ID."
                )
                return
            
            node_id = int(entered_text)
            self.handle_node_selection(node_id)
            
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Error processing entered Node ID: {e}"
            )
    
    @pyqtSlot(int)
    def handle_node_selection(self, node_id):
        """Handle node selection from within the solver tab."""
        try:
            self._compute_time_history_for_node(node_id, require_single_output=True)
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"An error occurred while selecting node: {e}"
            )

    @pyqtSlot(int)
    def plot_history_for_node(self, node_id):
        """Trigger time history calculation and show results in a dialog."""
        try:
            result = self._compute_time_history_for_node(node_id, require_single_output=True)
            if result is not None:
                self._show_plot_in_new_dialog(result)
        except Exception as e:
            QMessageBox.critical(
                self, "Plot Error",
                f"Failed to plot time history for node {node_id}: {e}"
            )

    def _compute_time_history_for_node(self, node_id, require_single_output=True):
        """Validate selection and run time-history analysis."""
        if not self.stress_data or node_id not in self.stress_data.node_ids:
            QMessageBox.warning(self, "Node Not Found", f"Node ID {node_id} not found in loaded data.")
            return None

        outputs = {
            'Von-Mises Stress': self.von_mises_checkbox.isChecked(),
            'Max Principal Stress': self.max_principal_stress_checkbox.isChecked(),
            'Min Principal Stress': self.min_principal_stress_checkbox.isChecked(),
            'Deformation': self.deformation_checkbox.isChecked(),
            'Velocity': self.velocity_checkbox.isChecked(),
            'Acceleration': self.acceleration_checkbox.isChecked(),
        }

        selected = [name for name, is_checked in outputs.items() if is_checked]

        if not selected:
            QMessageBox.warning(self, "No Output Selected",
                                "Select an output (Von Mises, Principal Stress, Deformation, Velocity, or Acceleration) before plotting time history.")
            return None

        if require_single_output and len(selected) > 1:
            QMessageBox.warning(
                self,
                "Multiple Outputs Selected",
                "Select only one output before plotting time history."
            )
            return None

        needs_deformation = any(outputs[name] for name in ['Deformation', 'Velocity', 'Acceleration'])
        if needs_deformation and not self.deformation_loaded:
            QMessageBox.warning(
                self,
                "Missing Deformation Data",
                "Plotting deformation, velocity, or acceleration requires the modal deformations file."
            )
            return None

        self.console_textbox.append(
            f"\n{'=' * 60}\nComputing time history for Node ID: {node_id}\nSelected Output: {selected[0]}\n{'=' * 60}"
        )
        self.console_textbox.verticalScrollBar().setValue(
            self.console_textbox.verticalScrollBar().maximum()
        )

        result = self.analysis_handler.solve(force_time_history_for_node_id=node_id)
        return result

    def _show_plot_in_new_dialog(self, result):
        """Display the time-history result in a Matplotlib dialog."""
        if self.plot_dialog:
            self.plot_dialog.close()

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Time History for Node {result.node_id}")
        dialog.resize(900, 600)

        widget = MatplotlibWidget()
        widget.update_plot(
            result.time_values,
            result.stress_values,
            node_id=result.node_id,
            is_max_principal_stress=(result.result_type == 'max_principal'),
            is_min_principal_stress=(result.result_type == 'min_principal'),
            is_von_mises=(result.result_type == 'von_mises'),
            is_deformation=(result.result_type == 'deformation'),
            is_velocity=(result.result_type == 'velocity'),
            is_acceleration=(result.result_type == 'acceleration')
        )

        layout = QVBoxLayout(dialog)
        layout.addWidget(widget)

        flags = dialog.windowFlags()
        flags |= Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint
        dialog.setWindowFlags(flags)

        dialog.show()
        self.plot_dialog = dialog
    
    # ========== Drag and Drop Support ==========

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop event."""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.handle_dropped_file(event.source(), files[0])
    
    def handle_dropped_file(self, target_widget, file_path):
        """
        Handle dropped file based on target widget.

        Args:
            target_widget: Widget where file was dropped.
            file_path: Path to the dropped file.
        """
        # Determine which file type based on target
        if target_widget == self.coord_file_path:
            self._load_coordinate_file(file_path)
        elif target_widget == self.stress_file_path:
            self._load_stress_file(file_path)
        elif target_widget == self.deformations_file_path:
            self._load_deformation_file(file_path)
        elif target_widget == self.steady_state_file_path:
            self._load_steady_state_file(file_path)

    # ========== External Request Interface ==========

    @pyqtSlot(float, object)
    def request_time_point_calculation(self, selected_time, options):
        """
        Handle external request for time point calculation.

        This is the public interface method that external components (like main_window)
        should call to request time point calculations. It delegates to the analysis handler.

        Args:
            selected_time: Time value requested by user.
            options: Dict with calculation options (compute_von_mises, scale_factor, etc.).
        """
        self.analysis_handler.perform_time_point_calculation(selected_time, options)

    @pyqtSlot(object)
    def request_animation_precomputation(self, params):
        """
        Handle external request for animation precomputation.

        This is the public interface method that external components (like main_window)
        should call to request animation precomputations. It delegates to the analysis handler.

        Args:
            params: Dict with animation parameters (compute flags, indices, etc.).
        """
        self.analysis_handler.perform_animation_precomputation(params)
