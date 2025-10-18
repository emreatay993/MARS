"""
Refactored Solver Tab for MSUP Smart Solver.

This module provides the main solver interface that has been refactored from
MSUPSmartSolverGUI to use UI builders, data models, and the AnalysisEngine.
"""

import os
import sys
from datetime import datetime

import numpy as np
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QMessageBox, QWidget

# Import builders and managers
from ui.builders.solver_ui import SolverTabUIBuilder
from ui.widgets.console import Logger
from ui.widgets.plotting import PlotlyMaxWidget
from core.computation import AnalysisEngine
from core.data_models import (
    ModalData, ModalStressData, DeformationData, 
    SteadyStateData, SolverConfig
)
from file_io.loaders import (
    load_modal_coordinates, load_modal_stress,
    load_modal_deformations, load_steady_state_stress
)
from utils.constants import NP_DTYPE
from utils.node_utils import get_node_index_from_id


class SolverTab(QWidget):
    """
    Refactored Solver Tab for MSUP transient analysis.
    
    This class manages file loading, solver configuration, and analysis execution.
    It has been refactored to use UI builders, data models, and delegate
    computation to the AnalysisEngine.
    
    Signals:
        initial_data_loaded: Emitted when initial data is loaded
        time_point_result_ready: Emitted when time point results are ready
        animation_data_ready: Emitted when animation data is ready
    """
    
    # Signals
    initial_data_loaded = pyqtSignal(object)
    time_point_result_ready = pyqtSignal(object, str, float, float)
    animation_data_ready = pyqtSignal(object)
    
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
        self._update_solve_button_state()
    
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
        self.coord_file_button.clicked.connect(self.select_coord_file)
        self.stress_file_button.clicked.connect(self.select_stress_file)
        self.deformations_file_button.clicked.connect(self.select_deformations_file)
        self.steady_state_file_button.clicked.connect(self.select_steady_state_file)
        
        # Checkboxes
        self.steady_state_checkbox.toggled.connect(self.toggle_steady_state_stress_inputs)
        self.deformations_checkbox.toggled.connect(self.toggle_deformations_inputs)
        self.time_history_checkbox.toggled.connect(self.toggle_single_node_solution_group)
        self.time_history_checkbox.toggled.connect(self._on_time_history_toggled)
        self.von_mises_checkbox.toggled.connect(self.toggle_damage_index_checkbox_visibility)
        self.von_mises_checkbox.toggled.connect(self._update_damage_index_state)
        self.time_history_checkbox.toggled.connect(self._update_damage_index_state)
        self.damage_index_checkbox.toggled.connect(self.toggle_fatigue_params_visibility)
        
        # Plot updates
        self.max_principal_stress_checkbox.toggled.connect(
            self.update_single_node_plot_based_on_checkboxes
        )
        self.min_principal_stress_checkbox.toggled.connect(
            self.update_single_node_plot_based_on_checkboxes
        )
        self.von_mises_checkbox.toggled.connect(
            self.update_single_node_plot_based_on_checkboxes
        )
        
        # Connect checkboxes to update max/min over time plots
        self.von_mises_checkbox.toggled.connect(self._update_max_min_plots)
        self.max_principal_stress_checkbox.toggled.connect(self._update_max_min_plots)
        self.min_principal_stress_checkbox.toggled.connect(self._update_max_min_plots)
        self.deformation_checkbox.toggled.connect(self._update_max_min_plots)
        self.velocity_checkbox.toggled.connect(self._update_max_min_plots)
        self.acceleration_checkbox.toggled.connect(self._update_max_min_plots)
        
        # Skip modes
        self.skip_modes_combo.currentTextChanged.connect(self.on_skip_modes_changed)
        
        # Node entry
        self.node_line_edit.returnPressed.connect(self.on_node_entered)
        
        # Solve button
        self.solve_button.clicked.connect(lambda: self.solve())
        
        # Progress bar
        # Will be connected to solver signal when solver is created
    
    def _setup_initial_state(self):
        """Setup initial widget states."""
        self.toggle_damage_index_checkbox_visibility()
        self.update_single_node_plot()
    
    def select_coord_file(self):
        """Open file dialog for modal coordinate file."""
        from PyQt5.QtWidgets import QFileDialog
        file_name, _ = QFileDialog.getOpenFileName(
            self, 'Open Modal Coordinate File', '', 
            'Coordinate Files (*.mcf)'
        )
        if file_name:
            self._load_coordinate_file(file_name)
    
    def _load_coordinate_file(self, filename):
        """Load modal coordinate file using the loader."""
        try:
            # Load using loader
            modal_data = load_modal_coordinates(filename)
            
            # Clear old data and plots
            self.modal_data = None
            self.plot_modal_coords_tab.clear_plot()
            self._hide_plot_tabs()
            
            # Store new data
            self.modal_data = modal_data
            self.coord_file_path.setText(filename)
            
            # Update UI
            self._log_coordinate_load(filename, modal_data)
            self.plot_modal_coords_tab.update_plot(
                modal_data.time_values, modal_data.modal_coord
            )
            self._show_modal_coords_tab()
            
            self.coord_loaded = True
            self.update_output_checkboxes_state()
            self._check_and_emit_initial_data()
            self._update_solve_button_state()
            
        except ValueError as e:
            QMessageBox.warning(
                self, "Invalid File",
                f"The selected Modal Coordinate File is not valid.\n\nError: {e}"
            )
    
    def select_stress_file(self):
        """Open file dialog for modal stress file."""
        from PyQt5.QtWidgets import QFileDialog
        file_name, _ = QFileDialog.getOpenFileName(
            self, 'Open Modal Stress File', '', 'CSV Files (*.csv)'
        )
        if file_name:
            self._load_stress_file(file_name)
    
    def _load_stress_file(self, filename):
        """Load modal stress file using the loader."""
        try:
            # Load using loader
            stress_data = load_modal_stress(filename)
            
            # Clear old data
            self.stress_data = None
            self.plot_single_node_tab.clear_plot()
            if hasattr(self, 'window') and self.window() is not None:
                if hasattr(self.window(), 'display_tab'):
                    self.window().display_tab._clear_visualization()
            
            # Store new data
            self.stress_data = stress_data
            self.stress_file_path.setText(filename)
            
            # Update skip modes combo
            self._update_skip_modes_combo(stress_data.num_modes)
            
            # Log success
            self._log_stress_load(filename, stress_data)
            
            self.stress_loaded = True
            self.update_output_checkboxes_state()
            self._check_and_emit_initial_data()
            self._update_solve_button_state()
            
        except ValueError as e:
            QMessageBox.warning(
                self, "Invalid File",
                f"The selected Modal Stress File is not valid.\n\nError: {e}"
            )
    
    def select_deformations_file(self):
        """Open file dialog for modal deformations file."""
        from PyQt5.QtWidgets import QFileDialog
        file_name, _ = QFileDialog.getOpenFileName(
            self, 'Open Modal Deformations File', '', 'CSV Files (*.csv)'
        )
        if file_name:
            self._load_deformation_file(file_name)
    
    def _load_deformation_file(self, filename):
        """Load modal deformations file using the loader."""
        try:
            # Load using loader
            deform_data = load_modal_deformations(filename)
            
            # Clear old data
            self.deformation_data = None
            self.skip_modes_combo.clear()
            
            # Store new data
            self.deformation_data = deform_data
            self.deformations_file_path.setText(filename)
            
            # Update skip modes combo
            self._update_skip_modes_combo(deform_data.num_modes)
            
            # Log success
            self._log_deformation_load(filename, deform_data)
            
            self.deformation_loaded = True
            self.toggle_deformations_inputs()
            self.update_output_checkboxes_state()
            self._check_and_emit_initial_data()
            sys.stdout.flush()
            
        except ValueError as e:
            self.deformation_loaded = False
            self.deformations_file_path.clear()
            self.toggle_deformations_inputs()
            QMessageBox.warning(
                self, "Invalid File",
                f"The selected Modal Deformations File is not valid.\n\nError: {e}"
            )
    
    def select_steady_state_file(self):
        """Open file dialog for steady-state stress file."""
        from PyQt5.QtWidgets import QFileDialog
        file_name, _ = QFileDialog.getOpenFileName(
            self, 'Open Steady-State Stress File', '', 'Text Files (*.txt)'
        )
        if file_name:
            self._load_steady_state_file(file_name)
    
    def _load_steady_state_file(self, filename):
        """Load steady-state stress file using the loader."""
        try:
            # Load using loader
            steady_data = load_steady_state_stress(filename)
            
            # Store data
            self.steady_state_data = steady_data
            self.steady_state_file_path.setText(filename)
            
            # Log success
            self._log_steady_state_load(filename, steady_data)
            sys.stdout.flush()
            
        except ValueError as e:
            QMessageBox.warning(
                self, "Invalid File",
                f"The selected Steady-State Stress File is not valid.\n\nError: {e}"
            )
    
    def solve(self, force_time_history_for_node_id=None):
        """
        Main solve method - orchestrates the analysis.
        
        Args:
            force_time_history_for_node_id: Optional node ID to force time history mode.
        """
        try:
            # Save current tab index
            current_tab_index = self.show_output_tab_widget.currentIndex()
            
            # Validate inputs and get configuration
            config = self._validate_and_build_config(force_time_history_for_node_id)
            if config is None:
                return
            
            # Log start
            self._log_solve_start(config)
            
            # Configure analysis engine with data
            self._configure_analysis_engine()
            
            # Execute analysis
            self._execute_analysis(config)
            
            # Log completion
            self._log_solve_complete()
            
            # Restore tab
            self.show_output_tab_widget.setCurrentIndex(current_tab_index)
            
        except Exception as e:
            self._handle_solve_error(e)
    
    def _validate_and_build_config(self, force_node_id):
        """
        Validate inputs and build solver configuration.
        
        Args:
            force_node_id: Optional node ID to force time history mode.
        
        Returns:
            SolverConfig or None if validation fails.
        """
        # Check if in time history mode
        is_time_history = (
            self.time_history_checkbox.isChecked() or 
            force_node_id is not None
        )
        
        # Get output selections
        config = SolverConfig(
            calculate_von_mises=self.von_mises_checkbox.isChecked(),
            calculate_max_principal_stress=self.max_principal_stress_checkbox.isChecked(),
            calculate_min_principal_stress=self.min_principal_stress_checkbox.isChecked(),
            calculate_deformation=self.deformation_checkbox.isChecked(),
            calculate_velocity=self.velocity_checkbox.isChecked(),
            calculate_acceleration=self.acceleration_checkbox.isChecked(),
            calculate_damage=self.damage_index_checkbox.isChecked(),
            time_history_mode=is_time_history,
            include_steady_state=self.steady_state_checkbox.isChecked(),
            output_directory=self._get_output_directory()
        )
        
        # Get skip modes
        config.skip_n_modes = self._get_skip_n_modes()
        
        # Validate time history mode
        if is_time_history:
            node_id = self._validate_time_history_mode(force_node_id)
            if node_id is None:
                return None
            config.selected_node_id = node_id
        
        # Validate steady state if selected
        if config.include_steady_state and self.steady_state_data is None:
            self.console_textbox.append(
                "Error: Steady-state stress data is not loaded yet."
            )
            self.progress_bar.setVisible(False)
            return None
        
        # Validate skip modes
        if self.stress_data and config.skip_n_modes >= self.stress_data.num_modes:
            QMessageBox.critical(
                self, "Calculation Error",
                f"Cannot skip {config.skip_n_modes} modes as only "
                f"{self.stress_data.num_modes} are available."
            )
            self.progress_bar.setVisible(False)
            return None
        
        # Get fatigue parameters if needed
        if config.calculate_damage:
            fatigue_params = self._get_fatigue_parameters()
            if fatigue_params is None:
                return None
            config.fatigue_A, config.fatigue_m = fatigue_params
        
        return config
    
    def _validate_time_history_mode(self, force_node_id):
        """
        Validate time history mode inputs.
        
        Args:
            force_node_id: Optional forced node ID.
        
        Returns:
            int: Validated node ID, or None if validation fails.
        """
        if force_node_id is not None:
            if force_node_id not in self.stress_data.node_ids:
                QMessageBox.warning(
                    self, "Invalid Node ID",
                    f"Node ID {force_node_id} was not found."
                )
                return None
            return force_node_id
        
        # Get from UI
        node_id_text = self.node_line_edit.text()
        if not node_id_text:
            QMessageBox.warning(
                self, "Missing Input",
                "Please enter a Node ID for Time History mode."
            )
            return None
        
        try:
            node_id = int(node_id_text)
            if node_id not in self.stress_data.node_ids:
                QMessageBox.warning(
                    self, "Invalid Node ID",
                    f"Node ID {node_id} was not found in the loaded modal stress file."
                )
                return None
            
            # Validate at least one output is selected
            if not self._any_time_history_output_selected():
                QMessageBox.warning(
                    self, "No Output Selected",
                    "Please select an output to plot for the time history analysis."
                )
                return None
            
            return node_id
            
        except ValueError:
            QMessageBox.warning(
                self, "Invalid Input",
                "The entered Node ID is not a valid integer."
            )
            return None
    
    def _any_time_history_output_selected(self):
        """Check if any time history output is selected."""
        return any([
            self.von_mises_checkbox.isChecked(),
            self.max_principal_stress_checkbox.isChecked(),
            self.min_principal_stress_checkbox.isChecked(),
            self.deformation_checkbox.isChecked(),
            self.velocity_checkbox.isChecked(),
            self.acceleration_checkbox.isChecked()
        ])
    
    def _get_fatigue_parameters(self):
        """Get and validate fatigue parameters."""
        try:
            fatigue_A = float(self.A_line_edit.text())
            fatigue_m = float(self.m_line_edit.text())
            return fatigue_A, fatigue_m
        except ValueError:
            QMessageBox.warning(
                self, "Invalid Input",
                "Please enter valid numbers for fatigue parameters A and m."
            )
            return None
    
    def _get_skip_n_modes(self):
        """Get number of modes to skip from UI."""
        if not self.skip_modes_combo.isVisible():
            return 0
        try:
            return int(self.skip_modes_combo.currentText())
        except (ValueError, TypeError):
            return 0
    
    def _get_output_directory(self):
        """Get output directory for results."""
        if self.project_directory:
            return self.project_directory
        return os.path.dirname(os.path.abspath(__file__))
    
    def _configure_analysis_engine(self):
        """Configure the analysis engine with loaded data."""
        self.analysis_engine.configure_data(
            self.modal_data,
            self.stress_data,
            self.deformation_data,
            self.steady_state_data
        )
    
    def _execute_analysis(self, config):
        """
        Execute the analysis based on configuration.
        
        Args:
            config: SolverConfig with analysis settings.
        """
        # Create solver
        self.analysis_engine.create_solver(config)
        
        # Connect progress signal
        if self.analysis_engine.solver:
            self.analysis_engine.solver.progress_signal.connect(
                self.update_progress_bar
            )
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        if config.time_history_mode:
            # Run single-node analysis
            result = self.analysis_engine.run_single_node_analysis(
                config.selected_node_id, config
            )
            self._handle_time_history_result(result, config)
        else:
            # Run batch analysis
            self.analysis_engine.run_batch_analysis(config)
            self._handle_batch_results(config)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
    
    def _handle_time_history_result(self, result, config):
        """Handle results from time history analysis."""
        # Update plot
        self.plot_single_node_tab.update_plot(
            result.time_values,
            result.stress_values,
            node_id=result.node_id,
            is_max_principal_stress=config.calculate_max_principal_stress,
            is_min_principal_stress=config.calculate_min_principal_stress,
            is_von_mises=config.calculate_von_mises,
            is_deformation=config.calculate_deformation,
            is_velocity=config.calculate_velocity,
            is_acceleration=config.calculate_acceleration
        )
        
        # Ensure the time history plot tab is visible
        plot_tab_index = self.show_output_tab_widget.indexOf(self.plot_single_node_tab)
        if plot_tab_index >= 0:
            self.show_output_tab_widget.setTabVisible(plot_tab_index, True)
            # Switch to the plot tab to show the results
            self.show_output_tab_widget.setCurrentIndex(plot_tab_index)
        
        # Log completion
        self.console_textbox.append(
            f"\n✓ Time history plot updated for Node {result.node_id}\n"
        )
    
    def _handle_batch_results(self, config):
        """Handle results from batch analysis."""
        # Create maximum over time plots
        max_traces = []
        
        if config.calculate_von_mises and hasattr(self.analysis_engine.solver, 'max_over_time_svm'):
            max_traces.append({
                'name': 'Von Mises (MPa)',
                'data': self.analysis_engine.solver.max_over_time_svm
            })
            von_mises_max = self.analysis_engine.solver.max_over_time_svm
        else:
            von_mises_max = None
        
        if config.calculate_max_principal_stress and hasattr(self.analysis_engine.solver, 'max_over_time_s1'):
            max_traces.append({
                'name': 'S1 (MPa)',
                'data': self.analysis_engine.solver.max_over_time_s1
            })
            s1_max = self.analysis_engine.solver.max_over_time_s1
        else:
            s1_max = None
        
        if config.calculate_deformation and hasattr(self.analysis_engine.solver, 'max_over_time_def'):
            max_traces.append({
                'name': 'Deformation (mm)',
                'data': self.analysis_engine.solver.max_over_time_def
            })
            def_max = self.analysis_engine.solver.max_over_time_def
        else:
            def_max = None
        
        if config.calculate_velocity and hasattr(self.analysis_engine.solver, 'max_over_time_vel'):
            max_traces.append({
                'name': 'Velocity (mm/s)',
                'data': self.analysis_engine.solver.max_over_time_vel
            })
            vel_max = self.analysis_engine.solver.max_over_time_vel
        else:
            vel_max = None
        
        if config.calculate_acceleration and hasattr(self.analysis_engine.solver, 'max_over_time_acc'):
            max_traces.append({
                'name': 'Acceleration (mm/s²)',
                'data': self.analysis_engine.solver.max_over_time_acc
            })
            acc_max = self.analysis_engine.solver.max_over_time_acc
        else:
            acc_max = None
        
        # Show maximum over time tab if there are traces
        if max_traces:
            if self.plot_max_over_time_tab is None:
                from ui.widgets.plotting import PlotlyMaxWidget
                self.plot_max_over_time_tab = PlotlyMaxWidget()
                modal_tab_index = self.show_output_tab_widget.indexOf(self.plot_modal_coords_tab)
                self.show_output_tab_widget.insertTab(
                    modal_tab_index + 1,
                    self.plot_max_over_time_tab,
                    "Maximum Over Time"
                )
            
            self.plot_max_over_time_tab.update_plot(
                self.modal_data.time_values,
                traces=max_traces
            )
            self.show_output_tab_widget.setTabVisible(
                self.show_output_tab_widget.indexOf(self.plot_max_over_time_tab),
                True
            )
        
        # Show minimum over time tab if min principal stress was calculated
        if config.calculate_min_principal_stress and hasattr(self.analysis_engine.solver, 'min_over_time_s3'):
            min_traces = [{
                'name': 'S3 (MPa)',
                'data': self.analysis_engine.solver.min_over_time_s3
            }]
            
            if self.plot_min_over_time_tab is None:
                from ui.widgets.plotting import PlotlyMaxWidget
                self.plot_min_over_time_tab = PlotlyMaxWidget()
                if self.plot_max_over_time_tab is not None:
                    idx = self.show_output_tab_widget.indexOf(self.plot_max_over_time_tab)
                    self.show_output_tab_widget.insertTab(idx + 1, self.plot_min_over_time_tab, "Minimum Over Time")
                else:
                    modal_tab_index = self.show_output_tab_widget.indexOf(self.plot_modal_coords_tab)
                    self.show_output_tab_widget.insertTab(modal_tab_index + 1, self.plot_min_over_time_tab, "Minimum Over Time")
            
            self.plot_min_over_time_tab.update_plot(
                self.modal_data.time_values,
                traces=min_traces
            )
            self.show_output_tab_widget.setTabVisible(
                self.show_output_tab_widget.indexOf(self.plot_min_over_time_tab),
                True
            )
        
        # Update display tab scalar range controls
        self._update_display_tab_scalar_range(
            von_mises_max, s1_max, def_max, vel_max, acc_max
        )
    
    def _update_display_tab_scalar_range(self, von_mises_max, s1_max, def_max, vel_max, acc_max):
        """
        Update display tab scalar range controls based on calculated max values.
        
        Args:
            von_mises_max: Max von Mises data over time.
            s1_max: Max S1 data over time.
            def_max: Max deformation data over time.
            vel_max: Max velocity data over time.
            acc_max: Max acceleration data over time.
        """
        # Determine scalar min/max from available data
        scalar_min, scalar_max = None, None
        
        if von_mises_max is not None:
            scalar_min = np.min(von_mises_max)
            scalar_max = np.max(von_mises_max)
        elif s1_max is not None:
            scalar_min = np.min(s1_max)
            scalar_max = np.max(s1_max)
        elif def_max is not None:
            scalar_min = np.min(def_max)
            scalar_max = np.max(def_max)
        elif vel_max is not None:
            scalar_min = np.min(vel_max)
            scalar_max = np.max(vel_max)
        elif acc_max is not None:
            scalar_min = np.min(acc_max)
            scalar_max = np.max(acc_max)
        
        # Update display tab if values available
        if scalar_min is not None and scalar_max is not None:
            try:
                display_tab = self.window().display_tab
                display_tab.scalar_min_spin.blockSignals(True)
                display_tab.scalar_max_spin.blockSignals(True)
                display_tab.scalar_min_spin.setRange(scalar_min, scalar_max)
                display_tab.scalar_max_spin.setRange(scalar_min, 1e30)
                display_tab.scalar_min_spin.setValue(scalar_min)
                display_tab.scalar_max_spin.setValue(scalar_max)
                display_tab.scalar_min_spin.blockSignals(False)
                display_tab.scalar_max_spin.blockSignals(False)
            except Exception as e:
                print(f"Could not update display tab scalar range: {e}")
    
    def update_progress_bar(self, value):
        """
        Update progress bar value.
        
        Args:
            value: Progress percentage (0-100).
        """
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"Progress: {value}%")
    
    def _log_solve_start(self, config):
        """Log solve start information."""
        current_time = datetime.now()
        self.console_textbox.append(
            f"\n******************* BEGIN SOLVE ********************\n"
            f"Datetime: {current_time}\n\n"
        )
    
    def _log_solve_complete(self):
        """Log solve completion."""
        self.console_textbox.append(
            "\n******************* SOLVE COMPLETE ********************\n\n"
        )
    
    def _handle_solve_error(self, error):
        """Handle errors during solve."""
        import traceback
        error_msg = f"Error during solve:\n{str(error)}\n\n{traceback.format_exc()}"
        self.console_textbox.append(error_msg)
        QMessageBox.critical(self, "Solve Error", str(error))
        self.progress_bar.setVisible(False)
    
    # ========== UI State Management Methods ==========
    
    def update_output_checkboxes_state(self):
        """Enable/disable output checkboxes based on loaded files."""
        # Stress-related outputs
        stress_enabled = self.coord_loaded and self.stress_loaded
        for cb in self._coord_stress_outputs:
            cb.setEnabled(stress_enabled)
            if not stress_enabled:
                cb.setChecked(False)
        
        # Deformation-related outputs
        deformations_enabled = (
            self.coord_loaded and
            self.deformations_checkbox.isChecked() and
            self.deformation_loaded
        )
        for cb in self._deformation_outputs:
            cb.setEnabled(deformations_enabled)
            if not deformations_enabled:
                cb.setChecked(False)
    
    def toggle_steady_state_stress_inputs(self):
        """Show/hide steady-state stress file controls."""
        is_checked = self.steady_state_checkbox.isChecked()
        self.steady_state_file_button.setVisible(is_checked)
        self.steady_state_file_path.setVisible(is_checked)
        if not is_checked:
            self.steady_state_file_path.clear()
    
    def toggle_deformations_inputs(self):
        """Show/hide deformation file controls."""
        is_checked = self.deformations_checkbox.isChecked()
        self.deformations_file_button.setVisible(is_checked)
        self.deformations_file_path.setVisible(is_checked)
        self.update_output_checkboxes_state()
        if not is_checked:
            self.deformations_file_path.clear()
            self.deformation_loaded = False
    
    def toggle_damage_index_checkbox_visibility(self):
        """Show/hide damage index checkbox based on von Mises selection."""
        if self.von_mises_checkbox.isChecked():
            self.damage_index_checkbox.setVisible(True)
        else:
            self.damage_index_checkbox.setVisible(False)
    
    def toggle_fatigue_params_visibility(self, checked):
        """Show/hide fatigue parameters group."""
        self.fatigue_params_group.setVisible(checked)
    
    def toggle_single_node_solution_group(self):
        """Show/hide single node selection group."""
        try:
            if self.time_history_checkbox.isChecked():
                # Connect exclusive handlers
                for cb in self.time_history_exclusive_outputs:
                    cb.toggled.connect(
                        lambda checked, a_checkbox=cb: 
                        self.on_exclusive_output_toggled(checked, a_checkbox)
                    )
                
                self.single_node_group.setVisible(True)
                self.show_output_tab_widget.setTabVisible(
                    self.show_output_tab_widget.indexOf(self.plot_single_node_tab), 
                    True
                )
            else:
                # Disconnect exclusive handlers
                for checkbox in self.time_history_exclusive_outputs:
                    try:
                        checkbox.toggled.disconnect(self.on_exclusive_output_toggled)
                    except TypeError:
                        pass
                
                self.single_node_group.setVisible(False)
                self.show_output_tab_widget.setTabVisible(
                    self.show_output_tab_widget.indexOf(self.plot_single_node_tab), 
                    False
                )
        except Exception as e:
            print(f"Error toggling single node group visibility: {e}")
    
    def _on_time_history_toggled(self, is_checked):
        """Handle time history mode toggle."""
        if is_checked:
            all_output_checkboxes = self._coord_stress_outputs + self._deformation_outputs
            for checkbox in all_output_checkboxes:
                if checkbox is self.time_history_checkbox:
                    continue
                checkbox.blockSignals(True)
                checkbox.setChecked(False)
                checkbox.blockSignals(False)
    
    def _update_damage_index_state(self):
        """Update damage index checkbox state."""
        is_time_history_checked = self.time_history_checkbox.isChecked()
        is_von_mises_checked = self.von_mises_checkbox.isChecked()
        is_enabled = is_von_mises_checked and not is_time_history_checked
        self.damage_index_checkbox.setEnabled(False)  # TODO: Enable after benchmarks
        if not is_enabled:
            self.damage_index_checkbox.setChecked(False)
            self.damage_index_checkbox.setVisible(False)
    
    def on_exclusive_output_toggled(self, is_checked, sender_checkbox):
        """Ensure only one output is selected in time history mode."""
        if self.time_history_checkbox.isChecked() and is_checked:
            for checkbox in self.time_history_exclusive_outputs:
                if checkbox is not sender_checkbox:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)
    
    # ========== Plot Management Methods ==========
    
    def update_single_node_plot(self):
        """Update placeholder plot."""
        x = np.linspace(0, 10, 100)
        y = np.zeros(100)
        self.plot_single_node_tab.update_plot(x, y)
    
    def update_single_node_plot_based_on_checkboxes(self):
        """Update plot based on checkbox states."""
        try:
            x_data = [1, 2, 3, 4, 5]
            y_data = [0, 0, 0, 0, 0]
            
            self.plot_single_node_tab.update_plot(
                x_data, y_data, None,
                is_max_principal_stress=self.max_principal_stress_checkbox.isChecked(),
                is_min_principal_stress=self.min_principal_stress_checkbox.isChecked(),
                is_von_mises=self.von_mises_checkbox.isChecked(),
                is_deformation=self.deformation_checkbox.isChecked(),
                is_velocity=self.velocity_checkbox.isChecked(),
                is_acceleration=self.acceleration_checkbox.isChecked()
            )
        except Exception as e:
            print(f"Error updating plot based on checkbox states: {e}")
    
    def _update_max_min_plots(self):
        """
        Update max/min over time plots when checkboxes are toggled.
        
        This method rebuilds the plots to reflect the current checkbox selections,
        hiding tabs if no relevant outputs are selected.
        """
        # Only update if solver has run and data exists
        if self.analysis_engine.solver is None:
            return
        
        # Don't update in time history mode
        if self.time_history_checkbox.isChecked():
            return
        
        # Build max traces based on current checkbox states AND available data
        max_traces = []
        
        if (self.von_mises_checkbox.isChecked() and 
            hasattr(self.analysis_engine.solver, 'max_over_time_svm') and
            self.analysis_engine.solver.max_over_time_svm is not None):
            max_traces.append({
                'name': 'Von Mises (MPa)',
                'data': self.analysis_engine.solver.max_over_time_svm
            })
        
        if (self.max_principal_stress_checkbox.isChecked() and 
            hasattr(self.analysis_engine.solver, 'max_over_time_s1') and
            self.analysis_engine.solver.max_over_time_s1 is not None):
            max_traces.append({
                'name': 'S1 (MPa)',
                'data': self.analysis_engine.solver.max_over_time_s1
            })
        
        if (self.deformation_checkbox.isChecked() and 
            hasattr(self.analysis_engine.solver, 'max_over_time_def') and
            self.analysis_engine.solver.max_over_time_def is not None):
            max_traces.append({
                'name': 'Deformation (mm)',
                'data': self.analysis_engine.solver.max_over_time_def
            })
        
        if (self.velocity_checkbox.isChecked() and 
            hasattr(self.analysis_engine.solver, 'max_over_time_vel') and
            self.analysis_engine.solver.max_over_time_vel is not None):
            max_traces.append({
                'name': 'Velocity (mm/s)',
                'data': self.analysis_engine.solver.max_over_time_vel
            })
        
        if (self.acceleration_checkbox.isChecked() and 
            hasattr(self.analysis_engine.solver, 'max_over_time_acc') and
            self.analysis_engine.solver.max_over_time_acc is not None):
            max_traces.append({
                'name': 'Acceleration (mm/s²)',
                'data': self.analysis_engine.solver.max_over_time_acc
            })
        
        # Update or hide max tab
        if max_traces and self.plot_max_over_time_tab is not None:
            self.plot_max_over_time_tab.update_plot(
                self.modal_data.time_values,
                traces=max_traces
            )
            self.show_output_tab_widget.setTabVisible(
                self.show_output_tab_widget.indexOf(self.plot_max_over_time_tab),
                True
            )
        elif self.plot_max_over_time_tab is not None:
            # No max traces - hide the tab
            self.plot_max_over_time_tab.clear_plot()
            self.show_output_tab_widget.setTabVisible(
                self.show_output_tab_widget.indexOf(self.plot_max_over_time_tab),
                False
            )
        
        # Update or hide min tab
        if (self.min_principal_stress_checkbox.isChecked() and 
            hasattr(self.analysis_engine.solver, 'min_over_time_s3') and
            self.analysis_engine.solver.min_over_time_s3 is not None and
            self.plot_min_over_time_tab is not None):
            min_traces = [{
                'name': 'S3 (MPa)',
                'data': self.analysis_engine.solver.min_over_time_s3
            }]
            self.plot_min_over_time_tab.update_plot(
                self.modal_data.time_values,
                traces=min_traces
            )
            self.show_output_tab_widget.setTabVisible(
                self.show_output_tab_widget.indexOf(self.plot_min_over_time_tab),
                True
            )
        elif self.plot_min_over_time_tab is not None:
            # Min principal unchecked - hide the tab
            self.plot_min_over_time_tab.clear_plot()
            self.show_output_tab_widget.setTabVisible(
                self.show_output_tab_widget.indexOf(self.plot_min_over_time_tab),
                False
            )
    
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
    
    def handle_node_selection(self, node_id):
        """
        Handle node selection from display tab or manual entry.
        
        Triggers time history calculation for the selected node.
        
        Args:
            node_id: Node ID to handle.
        """
        try:
            # Validate node exists
            if not self.stress_data or node_id not in self.stress_data.node_ids:
                QMessageBox.warning(
                    self, "Node Not Found",
                    f"Node ID {node_id} not found in loaded data."
                )
                return
            
            # Validate that at least one output is selected
            if not any([
                self.max_principal_stress_checkbox.isChecked(),
                self.min_principal_stress_checkbox.isChecked(),
                self.von_mises_checkbox.isChecked(),
                self.deformation_checkbox.isChecked(),
                self.velocity_checkbox.isChecked(),
                self.acceleration_checkbox.isChecked()
            ]):
                QMessageBox.warning(
                    self, "No Output Selected",
                    "Please select at least one output type (Von Mises, Principal Stress, "
                    "Deformation, Velocity, or Acceleration) before computing time history."
                )
                return
            
            # Log selection
            self.console_textbox.append(
                f"\n{'='*60}\n"
                f"Computing time history for Node ID: {node_id}\n"
                f"{'='*60}"
            )
            self.console_textbox.verticalScrollBar().setValue(
                self.console_textbox.verticalScrollBar().maximum()
            )
            
            # Trigger solve with time history mode for this node
            self.solve(force_time_history_for_node_id=node_id)
            
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"An error occurred while selecting node: {e}"
            )
    
    def perform_time_point_calculation(self, selected_time, options):
        """
        Perform time-point calculation for all nodes at a specific time.
        
        This method creates a temporary solver for a single time point (or small window
        for velocity/acceleration) and computes the requested output field. Results are
        packaged into a PyVista mesh and emitted to the Display tab.
        
        Args:
            selected_time: Time value requested by user.
            options: Dict with flags (compute_von_mises, scale_factor, etc.).
        """
        print("SolverTab: Received request for time point calculation.")
        
        try:
            # Validate data is loaded
            if not (self.coord_loaded and self.stress_loaded):
                QMessageBox.warning(self, "Missing Data", "Core data files are not loaded.")
                return
            
            # Validate single output selection
            num_outputs = sum([
                options.get('compute_von_mises', False),
                options.get('compute_max_principal', False),
                options.get('compute_min_principal', False),
                options.get('compute_deformation_contour', False),
                options.get('compute_velocity', False),
                options.get('compute_acceleration', False)
            ])
            
            if num_outputs > 1:
                QMessageBox.warning(
                    self, "Multiple Outputs",
                    "Please select only one output type for time point visualization."
                )
                return
            if num_outputs == 0:
                QMessageBox.warning(
                    self, "No Selection",
                    "No valid output is selected. Please select a valid output type."
                )
                return
            
            # Find nearest time index
            time_index = np.argmin(np.abs(self.modal_data.time_values - selected_time))
            mode_slice = slice(options.get('skip_n_modes', 0), None)
            
            # Prepare modal deformations if needed
            modal_deformations_filtered = None
            if options.get('display_deformed_shape', False) and self.deformation_data:
                modal_deformations_filtered = (
                    self.deformation_data.modal_ux[:, mode_slice],
                    self.deformation_data.modal_uy[:, mode_slice],
                    self.deformation_data.modal_uz[:, mode_slice]
                )
            
            # Handle velocity/acceleration (need time window)
            is_vel_or_accel = options.get('compute_velocity', False) or options.get('compute_acceleration', False)
            if is_vel_or_accel:
                half = 3  # Use 3 points on either side
                idx0 = max(0, time_index - half)
                idx1 = min(self.modal_data.num_time_points, time_index + half + 1)
                
                if idx1 - idx0 < 2:
                    QMessageBox.warning(
                        self, "Too Few Samples",
                        "Velocity/acceleration need at least two time steps."
                    )
                    return
                
                selected_modal_coord = self.modal_data.modal_coord[mode_slice, idx0:idx1]
                dt_window = self.modal_data.time_values[idx0:idx1]
                centre_offset = time_index - idx0
            else:
                selected_modal_coord = self.modal_data.modal_coord[mode_slice, time_index:time_index + 1]
                dt_window = self.modal_data.time_values[time_index:time_index + 1]
                centre_offset = 0
            
            # Prepare steady-state kwargs
            steady_kwargs = {}
            if options.get('include_steady', False) and self.steady_state_data:
                steady_kwargs = {
                    'steady_sx': self.steady_state_data.steady_sx,
                    'steady_sy': self.steady_state_data.steady_sy,
                    'steady_sz': self.steady_state_data.steady_sz,
                    'steady_sxy': self.steady_state_data.steady_sxy,
                    'steady_syz': self.steady_state_data.steady_syz,
                    'steady_sxz': self.steady_state_data.steady_sxz,
                    'steady_node_ids': self.steady_state_data.node_ids
                }
            
            # Create temporary solver for this time point
            from solver.engine import MSUPSmartSolverTransient
            temp_solver = MSUPSmartSolverTransient(
                self.stress_data.modal_sx[:, mode_slice],
                self.stress_data.modal_sy[:, mode_slice],
                self.stress_data.modal_sz[:, mode_slice],
                self.stress_data.modal_sxy[:, mode_slice],
                self.stress_data.modal_syz[:, mode_slice],
                self.stress_data.modal_sxz[:, mode_slice],
                selected_modal_coord,
                dt_window,
                modal_node_ids=self.stress_data.node_ids,
                modal_deformations=modal_deformations_filtered,
                **steady_kwargs
            )
            
            num_nodes = self.stress_data.num_nodes
            display_coords = self.stress_data.node_coords
            ux_tp, uy_tp, uz_tp = None, None, None
            
            # Apply deformation to coordinates if requested
            if options.get('display_deformed_shape', False) and self.deformation_data:
                ux_tp, uy_tp, uz_tp = temp_solver.compute_deformations(0, num_nodes)
                if is_vel_or_accel:
                    ux_tp = ux_tp[:, [centre_offset]]
                    uy_tp = uy_tp[:, [centre_offset]]
                    uz_tp = uz_tp[:, [centre_offset]]
                displacement_vector = np.hstack((ux_tp, uy_tp, uz_tp))
                display_coords = self.stress_data.node_coords + (
                    displacement_vector * options.get('scale_factor', 1.0)
                )
            
            # Compute stresses
            actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz = \
                temp_solver.compute_normal_stresses(0, num_nodes)
            
            # Create mesh
            import pyvista as pv
            mesh = pv.PolyData(display_coords)
            if self.stress_data.node_ids is not None:
                mesh["NodeID"] = self.stress_data.node_ids.astype(int)
            
            # Compute requested scalar field
            scalar_field, display_name = None, "Result"
            
            if options.get('compute_von_mises', False):
                scalar_field = temp_solver.compute_von_mises_stress(
                    actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz
                )
                display_name = "SVM (MPa)"
            
            elif options.get('compute_max_principal', False):
                s1, _, _ = temp_solver.compute_principal_stresses(
                    actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz
                )
                scalar_field = s1
                display_name = "S1 (MPa)"
            
            elif options.get('compute_min_principal', False):
                _, _, s3 = temp_solver.compute_principal_stresses(
                    actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz
                )
                scalar_field = s3
                display_name = "S3 (MPa)"
            
            elif options.get('compute_deformation_contour', False):
                if not self.deformation_data:
                    QMessageBox.warning(
                        self, "Missing Data",
                        "Modal deformations must be loaded for this calculation."
                    )
                    return
                if ux_tp is None:
                    ux_tp, uy_tp, uz_tp = temp_solver.compute_deformations(0, num_nodes)
                scalar_field = np.sqrt(ux_tp ** 2 + uy_tp ** 2 + uz_tp ** 2)
                display_name = "Deformation (mm)"
            
            elif is_vel_or_accel:
                if not self.deformation_data:
                    QMessageBox.warning(
                        self, "Missing Data",
                        "Modal deformations must be loaded for this calculation."
                    )
                    return
                ux_blk, uy_blk, uz_blk = temp_solver.compute_deformations(0, num_nodes)
                vel_mag, acc_mag, vel_x, vel_y, vel_z, _acc_x, _acc_y, _acc_z = \
                    temp_solver._vel_acc_from_disp(ux_blk, uy_blk, uz_blk, dt_window.astype(temp_solver.NP_DTYPE))
                
                if options.get('compute_velocity', False):
                    scalar_field = vel_mag[:, [centre_offset]]
                    display_name = "Velocity (mm/s)"
                    # Add components for IC export
                    mesh["vel_x"] = vel_x[:, [centre_offset]]
                    mesh["vel_y"] = vel_y[:, [centre_offset]]
                    mesh["vel_z"] = vel_z[:, [centre_offset]]
                else:  # Acceleration
                    scalar_field = acc_mag[:, [centre_offset]]
                    display_name = "Acceleration (mm/s²)"
            
            if scalar_field is None:
                print("No valid output was calculated.")
                return
            
            # Add scalar field to mesh
            mesh[display_name] = scalar_field
            mesh.set_active_scalars(display_name)
            
            # Compute data range
            data_min, data_max = np.min(scalar_field), np.max(scalar_field)
            
            # Emit results to Display tab
            self.time_point_result_ready.emit(mesh, display_name, data_min, data_max)
            
        except Exception as e:
            import traceback
            print(f"ERROR during time point calculation: {e}")
            traceback.print_exc()
    
    def perform_animation_precomputation(self, params):
        """
        Precompute animation frames and emit results.
        
        This method receives animation parameters, computes scalar and coordinate
        data for all frames, and emits the results back to the Display tab.
        
        Args:
            params: Dict with animation parameters (compute flags, indices, etc.).
        """
        try:
            # Get display tab for helper methods
            display_tab = self.window().display_tab
            
            # Validate data loaded
            if not (self.coord_loaded and self.stress_loaded):
                QMessageBox.warning(self, "Missing Data", "Core data files are not loaded.")
                from PyQt5.QtWidgets import QApplication
                QApplication.restoreOverrideCursor()
                self.animation_data_ready.emit(None)
                return
            
            # Get animation indices
            anim_indices = params.get('anim_indices', [])
            if len(anim_indices) == 0:
                QMessageBox.warning(self, "No Frames", "No animation frames to compute.")
                QApplication.restoreOverrideCursor()
                self.animation_data_ready.emit(None)
                return
            
            anim_times = self.modal_data.time_values[anim_indices]
            num_anim_steps = len(anim_times)
            print(f"Precomputing {num_anim_steps} animation frames...")
            
            # Validate at least one output selected
            if not any([
                params.get('compute_von_mises', False),
                params.get('compute_max_principal', False),
                params.get('compute_min_principal', False),
                params.get('compute_deformation_contour', False),
                params.get('compute_velocity', False),
                params.get('compute_acceleration', False)
            ]):
                QMessageBox.warning(self, "No Selection", "No valid output selected for animation.")
                QApplication.restoreOverrideCursor()
                self.animation_data_ready.emit(None)
                return
            
            # Check deformation
            compute_deformation_anim = params.get('compute_deformation_anim', False)
            if compute_deformation_anim and not self.deformation_data:
                QMessageBox.warning(
                    self, "Deformation Error",
                    "Deformation is checked, but deformation data is not loaded."
                )
                compute_deformation_anim = False
            
            # RAM check
            num_nodes = self.stress_data.num_nodes
            estimated_gb = display_tab._estimate_animation_ram(
                num_nodes, num_anim_steps, compute_deformation_anim
            )
            
            import psutil
            available_gb = psutil.virtual_memory().available / (1024 ** 3)
            import solver.engine as solver_engine
            safe_available_gb = available_gb * solver_engine.RAM_PERCENT
            
            print(f"Estimated RAM: {estimated_gb:.3f} GB")
            print(f"Available RAM: {available_gb:.3f} GB (Safe: {safe_available_gb:.3f} GB)")
            
            if estimated_gb > safe_available_gb:
                QMessageBox.warning(
                    self, "Insufficient Memory",
                    f"Estimated RAM ({estimated_gb:.3f} GB) exceeds safe limit "
                    f"({safe_available_gb:.3f} GB). Adjust time range or step."
                )
                QApplication.restoreOverrideCursor()
                self.animation_data_ready.emit(None)
                return
            
            # Create temporary solver for animation
            mode_slice = slice(params.get('skip_n_modes', 0), None)
            selected_modal_coord = self.modal_data.modal_coord[mode_slice, anim_indices]
            
            steady_kwargs = {}
            if params.get('include_steady', False) and self.steady_state_data:
                steady_kwargs = {
                    'steady_sx': self.steady_state_data.steady_sx,
                    'steady_sy': self.steady_state_data.steady_sy,
                    'steady_sz': self.steady_state_data.steady_sz,
                    'steady_sxy': self.steady_state_data.steady_sxy,
                    'steady_syz': self.steady_state_data.steady_syz,
                    'steady_sxz': self.steady_state_data.steady_sxz,
                    'steady_node_ids': self.steady_state_data.node_ids
                }
            
            modal_deformations_filtered = None
            if compute_deformation_anim and self.deformation_data:
                modal_deformations_filtered = (
                    self.deformation_data.modal_ux[:, mode_slice],
                    self.deformation_data.modal_uy[:, mode_slice],
                    self.deformation_data.modal_uz[:, mode_slice]
                )
            
            from solver.engine import MSUPSmartSolverTransient
            temp_solver = MSUPSmartSolverTransient(
                self.stress_data.modal_sx[:, mode_slice],
                self.stress_data.modal_sy[:, mode_slice],
                self.stress_data.modal_sz[:, mode_slice],
                self.stress_data.modal_sxy[:, mode_slice],
                self.stress_data.modal_syz[:, mode_slice],
                self.stress_data.modal_sxz[:, mode_slice],
                selected_modal_coord,
                anim_times,
                modal_node_ids=self.stress_data.node_ids,
                modal_deformations=modal_deformations_filtered,
                **steady_kwargs
            )
            
            print("Computing normal stresses for animation...")
            actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz = \
                temp_solver.compute_normal_stresses(0, num_nodes)
            
            print("Computing scalar field for animation...")
            precomputed_scalars = None
            data_column_name = "Result"
            
            if params.get('compute_von_mises', False):
                precomputed_scalars = temp_solver.compute_von_mises_stress(
                    actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz
                )
                data_column_name = "SVM (MPa)"
            elif params.get('compute_max_principal', False):
                s1_anim, _, _ = temp_solver.compute_principal_stresses(
                    actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz
                )
                precomputed_scalars = s1_anim
                data_column_name = "S1 (MPa)"
            elif params.get('compute_min_principal', False):
                _, _, s3_anim = temp_solver.compute_principal_stresses(
                    actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz
                )
                precomputed_scalars = s3_anim
                data_column_name = "S3 (MPa)"
            elif any([
                params.get('compute_velocity', False),
                params.get('compute_acceleration', False),
                params.get('compute_deformation_contour', False)
            ]):
                if not self.deformation_data:
                    raise ValueError("Deformation data not loaded.")
                
                ux_anim, uy_anim, uz_anim = temp_solver.compute_deformations(0, num_nodes)
                
                if params.get('compute_deformation_contour', False):
                    precomputed_scalars = np.sqrt(ux_anim ** 2 + uy_anim ** 2 + uz_anim ** 2)
                    data_column_name = "Deformation (mm)"
                
                if params.get('compute_velocity', False) or params.get('compute_acceleration', False):
                    vel_mag, acc_mag, _, _, _, _, _, _ = temp_solver._vel_acc_from_disp(
                        ux_anim, uy_anim, uz_anim, anim_times.astype(temp_solver.NP_DTYPE)
                    )
                    if params.get('compute_velocity', False):
                        precomputed_scalars = vel_mag
                        data_column_name = "Velocity (mm/s)"
                    else:
                        precomputed_scalars = acc_mag
                        data_column_name = "Acceleration (mm/s²)"
            
            # Compute deformed coordinates if requested
            precomputed_coords = None
            if compute_deformation_anim and self.deformation_data:
                print("Computing deformations for animation...")
                deformations = temp_solver.compute_deformations(0, num_nodes)
                if deformations is not None:
                    ux_anim, uy_anim, uz_anim = deformations
                    scale_factor = params.get('scale_factor', 1.0)
                    
                    original_coords_reshaped = self.stress_data.node_coords[:, :, np.newaxis]
                    ux_anim -= ux_anim[:, [0]]
                    uy_anim -= uy_anim[:, [0]]
                    uz_anim -= uz_anim[:, [0]]
                    
                    displacements_stacked = np.stack([ux_anim, uy_anim, uz_anim], axis=1)
                    precomputed_coords = original_coords_reshaped + scale_factor * displacements_stacked
            
            print("Cleaning up temporary animation data...")
            del temp_solver, actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz
            import gc
            gc.collect()
            print("---Precomputation complete.---")
            
            # Package results
            results = (
                precomputed_scalars,
                precomputed_coords,
                anim_times,
                data_column_name,
                compute_deformation_anim
            )
            
            # Emit to display tab
            self.animation_data_ready.emit(results)
            
        except Exception as e:
            print(f"ERROR during animation precomputation: {e}")
            import traceback
            traceback.print_exc()
            QApplication.restoreOverrideCursor()
            self.animation_data_ready.emit(None)
    
    # ========== Logging Helper Methods ==========
    
    def _log_coordinate_load(self, filename, modal_data):
        """Log successful coordinate file load."""
        self.console_textbox.append(
            f"Successfully validated and loaded modal coordinate file: "
            f"{os.path.basename(filename)}\n"
        )
        self.console_textbox.append(
            f"Modal coordinates tensor shape (m x n): {modal_data.modal_coord.shape}\n"
        )
    
    def _log_stress_load(self, filename, stress_data):
        """Log successful stress file load."""
        self.console_textbox.append(
            f"Successfully validated and loaded modal stress file: "
            f"{os.path.basename(filename)}\n"
        )
        self.console_textbox.append(f"Node IDs tensor shape: {stress_data.node_ids.shape}\n")
        self.console_textbox.append("Normal stress components extracted: SX, SY, SZ, SXY, SYZ, SXZ")
        self.console_textbox.append(
            f"SX shape: {stress_data.modal_sx.shape}, "
            f"SY shape: {stress_data.modal_sy.shape}, "
            f"SZ shape: {stress_data.modal_sz.shape}"
        )
        self.console_textbox.append(
            f"SXY shape: {stress_data.modal_sxy.shape}, "
            f"SYZ shape: {stress_data.modal_syz.shape}, "
            f"SXZ shape: {stress_data.modal_sxz.shape}\n"
        )
        self.console_textbox.verticalScrollBar().setValue(
            self.console_textbox.verticalScrollBar().maximum()
        )
    
    def _log_deformation_load(self, filename, deform_data):
        """Log successful deformation file load."""
        self.console_textbox.append(
            f"Successfully validated and loaded modal deformations file: "
            f"{os.path.basename(filename)}\n"
        )
        self.console_textbox.append(
            f"Deformations array shapes: "
            f"UX {deform_data.modal_ux.shape}, "
            f"UY {deform_data.modal_uy.shape}, "
            f"UZ {deform_data.modal_uz.shape}"
        )
    
    def _log_steady_state_load(self, filename, steady_data):
        """Log successful steady-state file load."""
        self.console_textbox.append(
            f"Successfully validated and loaded steady-state stress file: "
            f"{os.path.basename(filename)}\n"
        )
        self.console_textbox.append(
            f"Steady-state stress data shape: {steady_data.node_ids.shape}"
        )
    
    def _update_skip_modes_combo(self, num_modes):
        """Update skip modes combo box."""
        self.skip_modes_combo.clear()
        self.skip_modes_combo.addItems([str(i) for i in range(num_modes + 1)])
        self.skip_modes_label.setVisible(True)
        self.skip_modes_combo.setVisible(True)
    
    def on_skip_modes_changed(self, text):
        """Handle skip modes selection change."""
        try:
            if not text or not text.isdigit():
                return
            num_skipped = int(text)
            message = (
                f"\n[INFO] Skip Modes option is set to {num_skipped}. "
                f"The first {num_skipped} modes will be excluded from the next calculation.\n"
            )
            if self.stress_data and self.stress_data.modal_sx is not None:
                total_modes = self.stress_data.num_modes
                modes_used = total_modes - num_skipped
                message += (
                    f"       - Modes to be used: {modes_used} "
                    f"(from mode {num_skipped + 1} to {total_modes})\n"
                )
            self.console_textbox.append(message)
            self.console_textbox.verticalScrollBar().setValue(
                self.console_textbox.verticalScrollBar().maximum()
            )
        except (ValueError, TypeError) as e:
            self.console_textbox.append(
                f"\n[DEBUG] Could not parse skip modes value: {text}. Error: {e}"
            )
    
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
    
    def _update_solve_button_state(self):
        """Enable/disable solve button based on loaded files."""
        can_solve = self.coord_loaded and self.stress_loaded
        self.solve_button.setEnabled(can_solve)
    
    def _hide_plot_tabs(self):
        """Hide all plot tabs."""
        self.show_output_tab_widget.setTabVisible(
            self.show_output_tab_widget.indexOf(self.plot_modal_coords_tab), False
        )
        if self.plot_max_over_time_tab is not None:
            self.plot_max_over_time_tab.clear_plot()
            self.show_output_tab_widget.setTabVisible(
                self.show_output_tab_widget.indexOf(self.plot_max_over_time_tab), False
            )
        if self.plot_min_over_time_tab is not None:
            self.plot_min_over_time_tab.clear_plot()
            self.show_output_tab_widget.setTabVisible(
                self.show_output_tab_widget.indexOf(self.plot_min_over_time_tab), False
            )
    
    def _show_modal_coords_tab(self):
        """Show modal coordinates plot tab."""
        self.show_output_tab_widget.setTabVisible(
            self.show_output_tab_widget.indexOf(self.plot_modal_coords_tab), True
        )
    
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

