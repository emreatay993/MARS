"""
Analysis Handler for the SolverTab.

This class encapsulates all logic related to:
1. Validating UI inputs for analysis.
2. Building the SolverConfig.
3. Executing the analysis via the AnalysisEngine.
4. Handling and plotting the results.
"""

import os
import traceback
import  gc
import psutil
from datetime import datetime
from typing import Optional
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal
import numpy as np
from PyQt5.QtWidgets import QMessageBox, QApplication
import pyvista as pv

from solver import engine as solver_engine
from utils import constants
from utils.node_utils import get_node_index_from_id
from core.data_models import PlasticityConfig, SolverConfig
from ui.widgets.plotting import PlotlyMaxWidget


class SolverThread(QThread):
    """Background thread for running solver without freezing the GUI."""
    
    # Signals
    finished = pyqtSignal(object, object)  # Emits (result, config)
    error = pyqtSignal(str)  # Emits error message
    
    def __init__(self, analysis_handler, config):
        """
        Initialize the solver thread.
        
        Args:
            analysis_handler: SolverAnalysisHandler instance
            config: SolverConfig with analysis settings
        """
        super().__init__()
        self.analysis_handler = analysis_handler
        self.config = config
    
    def run(self):
        """Run the solver in background thread (computation only)."""
        try:
            # Configure analysis engine
            self.analysis_handler._configure_analysis_engine()
            
            # Execute analysis (computation only - no Qt widget operations)
            result = self.analysis_handler._execute_analysis(self.config)
            
            # Emit success signal with result and config
            self.finished.emit(result, self.config)
            
        except Exception as e:
            # Emit error signal
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.error.emit(error_msg)


class SolverAnalysisHandler:
    """Manages the analysis execution and result handling for the SolverTab."""

    def __init__(self, tab):
        """
        Initialize the analysis handler.

        Args:
            tab (SolverTab): The parent SolverTab instance.
        """
        self.tab = tab
        self._solve_start_time: Optional[datetime] = None

    @pyqtSlot()
    def solve(self, force_time_history_for_node_id=None):
        """Run analysis in background thread."""
        # Validate and build config
        config = self._validate_and_build_config(force_time_history_for_node_id)
        if config is None:
            return None
        
        # Get current tab index to restore later
        current_tab_index = self.tab.show_output_tab_widget.currentIndex()
        
        # Log solve start
        self._log_solve_start(config)
        
        # Disable UI during solve
        self.tab.setEnabled(False)
        self.tab.console_textbox.append("⏳ Running analysis in background...\n")
        
        # Store tab index for completion handler
        self._current_tab_index = current_tab_index
        
        # Show progress bar
        self.tab.progress_bar.setVisible(True)
        self.tab.progress_bar.setValue(0)
        
        # Create and start solver thread
        self.solver_thread = SolverThread(self, config)
        self.solver_thread.finished.connect(self._on_solve_complete)
        self.solver_thread.error.connect(self._on_solve_error)
        self.solver_thread.start()
        
        return None  # Result will be handled in completion callback
    
    def _on_solve_complete(self, result, config):
        """
        Handle successful solve completion (runs on main thread).
        This is where all Qt widget operations happen safely.
        
        Args:
            result: Analysis result (for time history mode)
            config: SolverConfig used for the analysis
        """
        # Re-enable UI
        self.tab.setEnabled(True)
        
        # Hide progress bar
        self.tab.progress_bar.setVisible(False)
        
        # Handle results based on mode (NOW on main thread - safe for Qt widgets!)
        if config.time_history_mode:
            self._handle_time_history_result(result, config)
            
            # Check if we should also show a popup dialog (when triggered from Display tab)
            if getattr(self.tab, '_show_popup_after_solve', False):
                self.tab._show_plot_in_new_dialog(result)
                self.tab._show_popup_after_solve = False  # Reset flag
        else:
            self._handle_batch_results(config)
        
        # Log completion
        self._log_solve_complete()
        
        # Restore tab index
        self.tab.show_output_tab_widget.setCurrentIndex(self._current_tab_index)
    
    def _on_solve_error(self, error_msg):
        """Handle solve error."""
        # Re-enable UI
        self.tab.setEnabled(True)
        
        # Log error
        self.tab.console_textbox.append(f"\n❌ Solver Error:\n{error_msg}\n")
        
        # Show error dialog
        QMessageBox.critical(
            self.tab, "Solver Error",
            f"An error occurred during analysis:\n\n{error_msg}"
        )
        
        # Hide progress bar
        self.tab.progress_bar.setVisible(False)

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
                self.tab.time_history_checkbox.isChecked() or
                force_node_id is not None
        )

        # Get output selections
        config = SolverConfig(
            calculate_von_mises=self.tab.von_mises_checkbox.isChecked(),
            calculate_max_principal_stress=self.tab.max_principal_stress_checkbox.isChecked(),
            calculate_min_principal_stress=self.tab.min_principal_stress_checkbox.isChecked(),
            calculate_deformation=self.tab.deformation_checkbox.isChecked(),
            calculate_velocity=self.tab.velocity_checkbox.isChecked(),
            calculate_acceleration=self.tab.acceleration_checkbox.isChecked(),
            calculate_force_moment=self.tab.force_moment_output_checkbox.isChecked(),
            calculate_damage=self.tab.damage_index_checkbox.isChecked(),
            time_history_mode=is_time_history,
            include_steady_state=self.tab.steady_state_checkbox.isChecked(),
            output_directory=self._get_output_directory()
        )

        # Get skip modes
        config.skip_n_modes = self._get_skip_n_modes()
        config.skip_last_n_modes = self._get_skip_last_n_modes()

        # Force/moment output must remain exclusive to avoid mixed-result visualization.
        if config.calculate_force_moment and any([
            config.calculate_von_mises,
            config.calculate_max_principal_stress,
            config.calculate_min_principal_stress,
            config.calculate_deformation,
            config.calculate_velocity,
            config.calculate_acceleration,
            config.calculate_damage,
        ]):
            QMessageBox.warning(
                self.tab,
                "Invalid Output Selection",
                "Element Nodal Forces & Moments cannot be combined with other output types."
            )
            self.tab.progress_bar.setVisible(False)
            return None

        # Validate time history mode
        if is_time_history:
            node_id = self._validate_time_history_mode(force_node_id)
            if node_id is None:
                return None
            config.selected_node_id = node_id

        # Validate steady state if selected
        if config.include_steady_state and self.tab.steady_state_data is None:
            self.tab.console_textbox.append(
                "Error: Steady-state stress data is not loaded yet."
            )
            self.tab.progress_bar.setVisible(False)
            return None

        # Validate skip modes against all loaded datasets
        total_skipped = config.skip_n_modes + config.skip_last_n_modes
        for data_source, label in [
            (self.tab.stress_data, "stress"),
            (self.tab.force_moment_data, "force/moment"),
        ]:
            if data_source and total_skipped >= data_source.num_modes:
                QMessageBox.critical(
                    self.tab, "Calculation Error",
                    f"Cannot skip first={config.skip_n_modes} and last={config.skip_last_n_modes} "
                    f"modes as only {data_source.num_modes} are available in {label} data."
                )
                self.tab.progress_bar.setVisible(False)
                return None

        # Get fatigue parameters if needed
        if config.calculate_damage:
            fatigue_params = self._get_fatigue_parameters()
            if fatigue_params is None:
                return None
            config.fatigue_A, config.fatigue_m = fatigue_params

        try:
            plasticity_cfg = self._build_plasticity_config(config)
        except ValueError as exc:
            self.tab.console_textbox.append(f"Plasticity configuration error: {exc}")
            QMessageBox.warning(self.tab, "Plasticity Configuration", str(exc))
            return None

        config.plasticity = plasticity_cfg

        return config

    def _node_exists_in_any_dataset(self, node_id):
        """Check if a node ID exists in any loaded dataset relevant to selected outputs."""
        # If force or moment output is selected, check those datasets
        if self.tab.force_moment_output_checkbox.isChecked() and self.tab.force_moment_data is not None:
            if get_node_index_from_id(node_id, self.tab.force_moment_data.node_ids, log_missing=False) is not None:
                return True
        # Otherwise check stress data
        if (
            self.tab.stress_data is not None and
            get_node_index_from_id(node_id, self.tab.stress_data.node_ids, log_missing=False) is not None
        ):
            return True
        return False

    def _validate_time_history_mode(self, force_node_id):
        """
        Validate time history mode inputs.

        Args:
            force_node_id: Optional forced node ID.

        Returns:
            int: Validated node ID, or None if validation fails.
        """
        if force_node_id is not None:
            if not self._node_exists_in_any_dataset(force_node_id):
                QMessageBox.warning(
                    self.tab, "Invalid Node ID",
                    f"Node ID {force_node_id} was not found."
                )
                return None
            return force_node_id

        # Get from UI
        node_id_text = self.tab.node_line_edit.text()
        if not node_id_text:
            QMessageBox.warning(
                self.tab, "Missing Input",
                "Please enter a Node ID for Time History mode."
            )
            return None

        try:
            node_id = int(node_id_text)
            if not self._node_exists_in_any_dataset(node_id):
                QMessageBox.warning(
                    self.tab, "Invalid Node ID",
                    f"Node ID {node_id} was not found in any loaded data file."
                )
                return None

            # Validate at least one output is selected
            if not self._any_time_history_output_selected():
                QMessageBox.warning(
                    self.tab, "No Output Selected",
                    "Please select an output to plot for the time history analysis."
                )
                return None

            return node_id

        except ValueError:
            QMessageBox.warning(
                self.tab, "Invalid Input",
                "The entered Node ID is not a valid integer."
            )
            return None

    def _any_time_history_output_selected(self):
        """Check if any time history output is selected."""
        return any([
            self.tab.von_mises_checkbox.isChecked(),
            self.tab.max_principal_stress_checkbox.isChecked(),
            self.tab.min_principal_stress_checkbox.isChecked(),
            self.tab.deformation_checkbox.isChecked(),
            self.tab.velocity_checkbox.isChecked(),
            self.tab.acceleration_checkbox.isChecked(),
            self.tab.force_moment_output_checkbox.isChecked()
        ])

    def _get_fatigue_parameters(self):
        """Get and validate fatigue parameters."""
        try:
            fatigue_A = float(self.tab.A_line_edit.text())
            fatigue_m = float(self.tab.m_line_edit.text())
            return fatigue_A, fatigue_m
        except ValueError:
            QMessageBox.warning(
                self.tab, "Invalid Input",
                "Please enter valid numbers for fatigue parameters A and m."
            )
            return None

    def _build_plasticity_config(self, solver_config: SolverConfig) -> Optional[PlasticityConfig]:
        """Assemble plasticity configuration or return ``None`` when disabled."""
        if not self.tab.plasticity_correction_checkbox.isChecked():
            return None

        if not self.tab.von_mises_checkbox.isChecked():
            raise ValueError("Von Mises output must be enabled when plasticity correction is selected.")

        method_text = self.tab.plasticity_method_combo.currentText().strip().lower()
        method_map = {
            "neuber": "neuber",
            "glinka": "glinka",
            "incremental buczynski-glinka (ibg)": "ibg",
        }
        if method_text not in method_map:
            raise ValueError(f"Unsupported plasticity method '{self.tab.plasticity_method_combo.currentText()}'.")
        method = method_map[method_text]

        if method == "ibg" and not solver_config.time_history_mode:
            raise ValueError("Incremental Buczynski-Glinka (IBG) correction requires Time History mode.")

        material_profile = self.tab.material_profile_data
        if material_profile is None or not material_profile.has_data:
            raise ValueError("Please enter a material profile with plastic curves before enabling plasticity.")

        temperature_data = self.tab.temperature_field_data
        if method in {"neuber", "glinka"} and temperature_data is None:
            raise ValueError("Neuber and Glinka corrections require a temperature field file.")

        max_iter_text = self.tab.plasticity_max_iter_input.text().strip()
        tol_text = self.tab.plasticity_tolerance_input.text().strip()

        try:
            max_iterations = int(max_iter_text) if max_iter_text else 60
        except ValueError as exc:
            raise ValueError("Invalid maximum iteration count for plasticity correction.") from exc

        try:
            tolerance = float(tol_text) if tol_text else 1e-10
        except ValueError as exc:
            raise ValueError("Invalid tolerance value for plasticity correction.") from exc

        default_temperature = 22.0 if temperature_data is None else None

        return PlasticityConfig(
            enabled=True,
            method=method,
            max_iterations=max_iterations,
            tolerance=tolerance,
            material_profile=material_profile,
            temperature_field=temperature_data,
            default_temperature=default_temperature,
            extrapolation_mode=(self.tab.plasticity_extrapolation_combo.currentText().strip().lower()
                                if getattr(self.tab, 'plasticity_extrapolation_combo', None) else 'linear'),
        )

    def _get_skip_n_modes(self):
        """Get number of modes to skip from UI."""
        try:
            text = self.tab.skip_modes_combo.currentText()
            return int(text) if text else 0
        except (ValueError, TypeError):
            return 0

    def _get_skip_last_n_modes(self):
        """Get number of trailing modes to skip from UI."""
        try:
            text = self.tab.skip_last_modes_combo.currentText()
            return int(text) if text else 0
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _build_mode_slice(skip_first, skip_last):
        """Build mode slice for skipping leading/trailing modes."""
        mode_stop = -skip_last if skip_last > 0 else None
        return slice(skip_first, mode_stop)

    def _get_output_directory(self):
        """Get output directory for results."""
        base_path = self.tab.project_directory or os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.abspath(base_path)

        if os.path.isfile(base_path):
            base_path = os.path.dirname(base_path)

        try:
            os.makedirs(base_path, exist_ok=True)
        except OSError:
            # Fall back to a safe location beside this module
            fallback = os.path.dirname(os.path.abspath(__file__))
            os.makedirs(fallback, exist_ok=True)
            base_path = fallback

        return base_path

    def _configure_analysis_engine(self):
        """Configure the analysis engine with loaded data."""
        self.tab.analysis_engine.configure_data(
            self.tab.modal_data,
            self.tab.stress_data,
            self.tab.deformation_data,
            self.tab.steady_state_data,
            force_moment_data=self.tab.force_moment_data
        )

    def _execute_analysis(self, config):
        """
        Execute ONLY the computation (no UI updates).
        Safe to call from background thread.

        Args:
            config: SolverConfig with analysis settings.
            
        Returns:
            Result object for time history mode, None for batch mode.
        """
        # Create solver
        self.tab.analysis_engine.create_solver(config)

        # Connect progress signal (Qt signals are thread-safe)
        if self.tab.analysis_engine.solver:
            self.tab.analysis_engine.solver.progress_signal.connect(
                self.tab.update_progress_bar
            )

        # Run analysis (computation only - no Qt widget operations)
        if config.time_history_mode:
            result = self.tab.analysis_engine.run_single_node_analysis(
                config.selected_node_id, config
            )
        else:
            self.tab.analysis_engine.run_batch_analysis(config)
            result = None

        return result

    def _handle_time_history_result(self, result, config):
        """Handle results from time history analysis."""
        # Update plot
        plasticity_overlay = result.metadata.get('plasticity') if result.metadata else None
        # Add diagnostics toggle request if available
        try:
            show_diag = bool(getattr(self.tab, 'plasticity_diag_checkbox', None) and self.tab.plasticity_diag_checkbox.isChecked())
        except Exception:
            show_diag = False
        if plasticity_overlay is not None:
            plasticity_overlay['show_diagnostics'] = show_diag
        self.tab.plot_single_node_tab.update_plot(
            result.time_values,
            result.stress_values,
            node_id=result.node_id,
            is_max_principal_stress=config.calculate_max_principal_stress,
            is_min_principal_stress=config.calculate_min_principal_stress,
            is_von_mises=config.calculate_von_mises,
            is_deformation=config.calculate_deformation,
            is_velocity=config.calculate_velocity,
            is_acceleration=config.calculate_acceleration,
            is_force_moment=config.calculate_force_moment,
            plasticity_overlay=plasticity_overlay
        )

        # Console messaging for plasticity in time-history mode
        if config.plasticity and config.plasticity.enabled:
            if plasticity_overlay and 'plastic_strain' in plasticity_overlay:
                method_name = config.plasticity.method.upper()
                self.tab.console_textbox.append(
                    f"Plasticity correction applied ({method_name}) for node {result.node_id}."
                )
                final_strain = plasticity_overlay['plastic_strain'][-1]
                self.tab.console_textbox.append(
                    f"Final cumulative plastic strain: {final_strain:.6e}"
                )
            else:
                if (config.plasticity.method or '').lower() != 'ibg':
                    self.tab.console_textbox.append(
                        "Plasticity correction was enabled, but no Neuber/Glinka overlay "
                        "data was produced for this result."
                    )

        # Ensure the time history plot tab is visible
        plot_tab_index = self.tab.show_output_tab_widget.indexOf(self.tab.plot_single_node_tab)
        if plot_tab_index >= 0:
            self.tab.show_output_tab_widget.setTabVisible(plot_tab_index, True)
            # Switch to the plot tab to show the results
            self.tab.show_output_tab_widget.setCurrentIndex(plot_tab_index)

        # Log completion
        self.tab.console_textbox.append(
            f"\n✓ Time history plot updated for Node {result.node_id}\n"
        )

    def _handle_batch_results(self, config):
        """Handle results from batch analysis."""
        # Create maximum over time plots
        max_traces = []
        min_traces = []
        solver = self.tab.analysis_engine.solver  # Shortcut

        if config.calculate_von_mises and hasattr(solver, 'max_over_time_svm'):
            max_traces.append({
                'name': 'Von Mises (MPa)',
                'data': solver.max_over_time_svm
            })

        plasticity_ctx = getattr(solver, 'plasticity_context', None)
        if plasticity_ctx and plasticity_ctx.method in {'neuber', 'glinka'}:
            corrected_trace = getattr(solver, 'max_over_time_svm_corrected', None)
            if corrected_trace is not None:
                corrected_copy = np.array(corrected_trace, dtype=float)
                corrected_copy[~np.isfinite(corrected_copy)] = np.nan
                if not np.all(np.isnan(corrected_copy)):
                    max_traces.append({
                        'name': 'Corrected Von Mises (MPa)',
                        'data': corrected_copy
                    })
            self.tab.console_textbox.append(
                f"Plasticity correction applied ({plasticity_ctx.method.title()})"
            )

        if config.calculate_max_principal_stress and hasattr(solver, 'max_over_time_s1'):
            max_traces.append({
                'name': 'S1 (MPa)',
                'data': solver.max_over_time_s1
            })

        if config.calculate_min_principal_stress and hasattr(solver, 'min_over_time_s3'):
            min_traces.append({
                'name': 'S3 (MPa)',
                'data': solver.min_over_time_s3
            })

        if config.calculate_deformation and hasattr(solver, 'max_over_time_def'):
            max_traces.append({
                'name': 'Deformation (mm)',
                'data': solver.max_over_time_def
            })
            if hasattr(solver, 'min_over_time_def') and solver.min_over_time_def is not None:
                min_traces.append({
                    'name': 'Deformation (mm)',
                    'data': solver.min_over_time_def
                })

        if config.calculate_velocity and hasattr(solver, 'max_over_time_vel'):
            max_traces.append({
                'name': 'Velocity (mm/s)',
                'data': solver.max_over_time_vel
            })
            if hasattr(solver, 'min_over_time_vel') and solver.min_over_time_vel is not None:
                min_traces.append({
                    'name': 'Velocity (mm/s)',
                    'data': solver.min_over_time_vel
                })

        if config.calculate_acceleration and hasattr(solver, 'max_over_time_acc'):
            max_traces.append({
                'name': 'Acceleration (mm/s²)',
                'data': solver.max_over_time_acc
            })
            if hasattr(solver, 'min_over_time_acc') and solver.min_over_time_acc is not None:
                min_traces.append({
                    'name': 'Acceleration (mm/s²)',
                    'data': solver.min_over_time_acc
                })

        if config.calculate_force_moment:
            if hasattr(solver, 'max_over_time_force_mag') and solver.max_over_time_force_mag is not None:
                max_traces.append({
                    'name': '|F| (N)',
                    'data': solver.max_over_time_force_mag
                })
            if hasattr(solver, 'max_over_time_force_fx') and solver.max_over_time_force_fx is not None:
                max_traces.append({'name': 'Fx (N)', 'data': solver.max_over_time_force_fx})
            if hasattr(solver, 'max_over_time_force_fy') and solver.max_over_time_force_fy is not None:
                max_traces.append({'name': 'Fy (N)', 'data': solver.max_over_time_force_fy})
            if hasattr(solver, 'max_over_time_force_fz') and solver.max_over_time_force_fz is not None:
                max_traces.append({'name': 'Fz (N)', 'data': solver.max_over_time_force_fz})
            if hasattr(solver, 'max_over_time_moment_mag') and solver.max_over_time_moment_mag is not None:
                max_traces.append({
                    'name': '|M| (N·mm)',
                    'data': solver.max_over_time_moment_mag
                })
            if hasattr(solver, 'max_over_time_moment_mx') and solver.max_over_time_moment_mx is not None:
                max_traces.append({'name': 'Mx (N·mm)', 'data': solver.max_over_time_moment_mx})
            if hasattr(solver, 'max_over_time_moment_my') and solver.max_over_time_moment_my is not None:
                max_traces.append({'name': 'My (N·mm)', 'data': solver.max_over_time_moment_my})
            if hasattr(solver, 'max_over_time_moment_mz') and solver.max_over_time_moment_mz is not None:
                max_traces.append({'name': 'Mz (N·mm)', 'data': solver.max_over_time_moment_mz})

            if hasattr(solver, 'min_over_time_force_mag') and solver.min_over_time_force_mag is not None:
                min_traces.append({'name': '|F| (N)', 'data': solver.min_over_time_force_mag})
            if hasattr(solver, 'min_over_time_force_fx') and solver.min_over_time_force_fx is not None:
                min_traces.append({'name': 'Fx (N)', 'data': solver.min_over_time_force_fx})
            if hasattr(solver, 'min_over_time_force_fy') and solver.min_over_time_force_fy is not None:
                min_traces.append({'name': 'Fy (N)', 'data': solver.min_over_time_force_fy})
            if hasattr(solver, 'min_over_time_force_fz') and solver.min_over_time_force_fz is not None:
                min_traces.append({'name': 'Fz (N)', 'data': solver.min_over_time_force_fz})
            if hasattr(solver, 'min_over_time_moment_mag') and solver.min_over_time_moment_mag is not None:
                min_traces.append({'name': '|M| (N·mm)', 'data': solver.min_over_time_moment_mag})
            if hasattr(solver, 'min_over_time_moment_mx') and solver.min_over_time_moment_mx is not None:
                min_traces.append({'name': 'Mx (N·mm)', 'data': solver.min_over_time_moment_mx})
            if hasattr(solver, 'min_over_time_moment_my') and solver.min_over_time_moment_my is not None:
                min_traces.append({'name': 'My (N·mm)', 'data': solver.min_over_time_moment_my})
            if hasattr(solver, 'min_over_time_moment_mz') and solver.min_over_time_moment_mz is not None:
                min_traces.append({'name': 'Mz (N·mm)', 'data': solver.min_over_time_moment_mz})

        # Show maximum over time tab if there are traces
        if max_traces:
            if self.tab.plot_max_over_time_tab is None:
                self.tab.plot_max_over_time_tab = PlotlyMaxWidget()
                modal_tab_index = self.tab.show_output_tab_widget.indexOf(self.tab.plot_modal_coords_tab)
                self.tab.show_output_tab_widget.insertTab(
                    modal_tab_index + 1,
                    self.tab.plot_max_over_time_tab,
                    "Maximum Over Time"
                )

            self.tab.plot_max_over_time_tab.update_plot(
                self.tab.modal_data.time_values,
                traces=max_traces
            )
            self.tab.show_output_tab_widget.setTabVisible(
                self.tab.show_output_tab_widget.indexOf(self.tab.plot_max_over_time_tab),
                True
            )
        elif self.tab.plot_max_over_time_tab is not None:
            self.tab.plot_max_over_time_tab.clear_plot()
            self.tab.show_output_tab_widget.setTabVisible(
                self.tab.show_output_tab_widget.indexOf(self.tab.plot_max_over_time_tab),
                False
            )

        # Show minimum over time tab if minimum traces are available
        if min_traces:
            if self.tab.plot_min_over_time_tab is None:
                self.tab.plot_min_over_time_tab = PlotlyMaxWidget()
                if self.tab.plot_max_over_time_tab is not None:
                    idx = self.tab.show_output_tab_widget.indexOf(self.tab.plot_max_over_time_tab)
                    self.tab.show_output_tab_widget.insertTab(idx + 1, self.tab.plot_min_over_time_tab,
                                                              "Minimum Over Time")
                else:
                    modal_tab_index = self.tab.show_output_tab_widget.indexOf(self.tab.plot_modal_coords_tab)
                    self.tab.show_output_tab_widget.insertTab(modal_tab_index + 1, self.tab.plot_min_over_time_tab,
                                                              "Minimum Over Time")

            self.tab.plot_min_over_time_tab.update_plot(
                self.tab.modal_data.time_values,
                traces=min_traces
            )
            self.tab.show_output_tab_widget.setTabVisible(
                self.tab.show_output_tab_widget.indexOf(self.tab.plot_min_over_time_tab),
                True
            )
        elif self.tab.plot_min_over_time_tab is not None:
            self.tab.plot_min_over_time_tab.clear_plot()
            self.tab.show_output_tab_widget.setTabVisible(
                self.tab.show_output_tab_widget.indexOf(self.tab.plot_min_over_time_tab),
                False
            )

        dataset_catalog = self._build_display_dataset_catalog(
            solver=solver,
            config=config,
            plasticity_ctx=plasticity_ctx,
        )

        # Update display tab scalar controls and selector catalog
        self._update_display_tab_scalar_range(solver, dataset_catalog)

    def _build_display_dataset_catalog(self, solver, config, plasticity_ctx):
        """Build catalog[group][component][mode] for Display selector controls."""
        catalog = {}
        output_dir = getattr(solver, 'output_directory', None)
        if not output_dir:
            return catalog

        def _file_exists(file_name):
            return bool(file_name) and os.path.exists(os.path.join(output_dir, file_name))

        def _add_entry(group, component, mode, field_name, csv_filename, units):
            if not _file_exists(csv_filename):
                return
            catalog.setdefault(group, {}).setdefault(component, {})[mode] = {
                "field_name": field_name,
                "csv_filename": csv_filename,
                "units": units,
            }

        mode_labels = {
            "max_over_time": "Max over Time",
            "min_over_time": "Min over Time",
            "time_of_max": "Time of Max",
            "time_of_min": "Time of Min",
        }

        def _add_component_modes(group, component, base_filename, value_label, value_unit):
            _add_entry(
                group,
                component,
                "max_over_time",
                f"{value_label} ({value_unit}) - {mode_labels['max_over_time']}",
                f"max_{base_filename}.csv",
                value_unit,
            )
            _add_entry(
                group,
                component,
                "min_over_time",
                f"{value_label} ({value_unit}) - {mode_labels['min_over_time']}",
                f"min_{base_filename}.csv",
                value_unit,
            )
            _add_entry(
                group,
                component,
                "time_of_max",
                f"{mode_labels['time_of_max']}: {value_label} (s)",
                f"time_of_max_{base_filename}.csv",
                "s",
            )
            _add_entry(
                group,
                component,
                "time_of_min",
                f"{mode_labels['time_of_min']}: {value_label} (s)",
                f"time_of_min_{base_filename}.csv",
                "s",
            )

        if config.calculate_von_mises:
            _add_component_modes("Von Mises", "Magnitude", "von_mises_stress", "SVM", "MPa")

        if config.calculate_max_principal_stress:
            _add_component_modes("Max Principal", "S1", "s1_stress", "S1", "MPa")

        if config.calculate_min_principal_stress:
            _add_component_modes("Min Principal", "S3", "s3_stress", "S3", "MPa")

        if config.calculate_deformation:
            for component, suffix, label in [
                ("|U|", "", "Deformation"),
                ("UX", "_x", "UX"),
                ("UY", "_y", "UY"),
                ("UZ", "_z", "UZ"),
            ]:
                _add_component_modes(
                    "Deformation",
                    component,
                    f"deformation{suffix}",
                    label,
                    "mm",
                )

        if config.calculate_velocity:
            for component, suffix, label in [
                ("|V|", "", "Velocity"),
                ("VX", "_x", "VX"),
                ("VY", "_y", "VY"),
                ("VZ", "_z", "VZ"),
            ]:
                _add_component_modes(
                    "Velocity",
                    component,
                    f"velocity{suffix}",
                    label,
                    "mm/s",
                )

        if config.calculate_acceleration:
            for component, suffix, label in [
                ("|A|", "", "Acceleration"),
                ("AX", "_x", "AX"),
                ("AY", "_y", "AY"),
                ("AZ", "_z", "AZ"),
            ]:
                _add_component_modes(
                    "Acceleration",
                    component,
                    f"acceleration{suffix}",
                    label,
                    "mm/s²",
                )

        if config.calculate_force_moment:
            for component, base_filename, label, unit in [
                ("|F|", "element_nodal_force", "Force", "N"),
                ("FX", "element_nodal_force_fx", "FX", "N"),
                ("FY", "element_nodal_force_fy", "FY", "N"),
                ("FZ", "element_nodal_force_fz", "FZ", "N"),
                ("|M|", "element_nodal_moment", "Moment", "N·mm"),
                ("MX", "element_nodal_moment_mx", "MX", "N·mm"),
                ("MY", "element_nodal_moment_my", "MY", "N·mm"),
                ("MZ", "element_nodal_moment_mz", "MZ", "N·mm"),
            ]:
                _add_component_modes("Force/Moment", component, base_filename, label, unit)

        if plasticity_ctx and plasticity_ctx.method in {'neuber', 'glinka'}:
            _add_entry(
                "Corrected Von Mises",
                "Magnitude",
                "max_over_time",
                "Corrected SVM (MPa) - Max over Time",
                "corrected_von_mises.csv",
                "MPa",
            )
            _add_entry(
                "Corrected Von Mises",
                "Magnitude",
                "time_of_max",
                "Time of Max: Corrected SVM (s)",
                "time_of_max_corrected_von_mises.csv",
                "s",
            )
            _add_entry(
                "Plastic Strain",
                "Equivalent",
                "max_over_time",
                "Plastic Strain",
                "plastic_strain.csv",
                "",
            )

        return catalog

    def _update_display_tab_scalar_range(self, solver, dataset_catalog):
        """Update the display tab with solver-generated dataset catalog."""
        if not dataset_catalog:
            return

        try:
            display_tab = self.tab.window().display_tab
        except Exception:
            return

        current_field = getattr(display_tab, 'data_column', None)
        display_tab.results_handler.apply_solver_results(
            solver,
            dataset_catalog,
            current_field
        )

    def _log_solve_start(self, config):
        """Log solve start information."""
        current_time = datetime.now()
        self._solve_start_time = current_time
        self.tab.console_textbox.append(
            f"\n******************* BEGIN SOLVE ********************\n"
            f"Datetime: {current_time}\n\n"
        )

    def _log_solve_complete(self):
        """Log solve completion."""
        end_time = datetime.now()
        elapsed_seconds = None
        if self._solve_start_time is not None:
            elapsed_seconds = (end_time - self._solve_start_time).total_seconds()

        complete_message = "\n******************* SOLVE COMPLETE ********************\n\n"
        if elapsed_seconds is not None:
            complete_message += f"Elapsed time: {elapsed_seconds:.3f} seconds\n\n"

        self.tab.console_textbox.append(complete_message)
        self._solve_start_time = None

    def _handle_solve_error(self, error):
        """Handle errors during solve."""
        error_msg = f"Error during solve:\n{str(error)}\n\n{traceback.format_exc()}"
        self.tab.console_textbox.append(error_msg)
        QMessageBox.critical(self.tab, "Solve Error", str(error))
        self.tab.progress_bar.setVisible(False)

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
            # Validate data is loaded -- at minimum, modal coordinates must be loaded,
            # plus at least one data source (stress, force, or moment)
            if not self.tab.coord_loaded:
                QMessageBox.warning(self.tab, "Missing Data", "Modal coordinate file is not loaded.")
                return
            if not (self.tab.stress_loaded or self.tab.force_moment_loaded):
                QMessageBox.warning(self.tab, "Missing Data", "No data files loaded (stress or force/moment).")
                return

            # Validate single output selection
            num_outputs = sum([
                options.get('compute_von_mises', False),
                options.get('compute_max_principal', False),
                options.get('compute_min_principal', False),
                options.get('compute_deformation_contour', False),
                options.get('compute_velocity', False),
                options.get('compute_acceleration', False),
                options.get('compute_force_moment', False)
            ])

            if num_outputs > 1:
                QMessageBox.warning(
                    self.tab, "Multiple Outputs",
                    "Please select only one output type for time point visualization."
                )
                return
            if num_outputs == 0:
                QMessageBox.warning(
                    self.tab, "No Selection",
                    "No valid output is selected. Please select a valid output type."
                )
                return

            # Find nearest time index
            time_index = np.argmin(np.abs(self.tab.modal_data.time_values - selected_time))
            skip_first = int(options.get('skip_n_modes', 0) or 0)
            skip_last = int(options.get('skip_last_n_modes', 0) or 0)
            if skip_first + skip_last >= self.tab.modal_data.num_modes:
                QMessageBox.warning(
                    self.tab,
                    "Invalid Skip Modes",
                    "Skip first/last mode values exclude all available modes. "
                    "Reduce one of the skip values and try again."
                )
                return
            mode_slice = self._build_mode_slice(skip_first, skip_last)

            # Prepare modal deformations if needed
            modal_deformations_filtered = None
            if options.get('display_deformed_shape', False) and self.tab.deformation_data:
                modal_deformations_filtered = (
                    self.tab.deformation_data.modal_ux[:, mode_slice],
                    self.tab.deformation_data.modal_uy[:, mode_slice],
                    self.tab.deformation_data.modal_uz[:, mode_slice]
                )

            # Handle velocity/acceleration (need time window)
            is_vel_or_accel = options.get('compute_velocity', False) or options.get('compute_acceleration', False)
            if is_vel_or_accel:
                half = 3  # Use 3 points on either side
                idx0 = max(0, time_index - half)
                idx1 = min(self.tab.modal_data.num_time_points, time_index + half + 1)

                if idx1 - idx0 < 2:
                    QMessageBox.warning(
                        self.tab, "Too Few Samples",
                        "Velocity/acceleration need at least two time steps."
                    )
                    return

                selected_modal_coord = self.tab.modal_data.modal_coord[mode_slice, idx0:idx1]
                dt_window = self.tab.modal_data.time_values[idx0:idx1]
                centre_offset = time_index - idx0
            else:
                selected_modal_coord = self.tab.modal_data.modal_coord[mode_slice, time_index:time_index + 1]
                dt_window = self.tab.modal_data.time_values[time_index:time_index + 1]
                centre_offset = 0

            # Prepare steady-state kwargs
            steady_kwargs = {}
            if options.get('include_steady', False) and self.tab.steady_state_data:
                steady_kwargs = {
                    'steady_sx': self.tab.steady_state_data.steady_sx,
                    'steady_sy': self.tab.steady_state_data.steady_sy,
                    'steady_sz': self.tab.steady_state_data.steady_sz,
                    'steady_sxy': self.tab.steady_state_data.steady_sxy,
                    'steady_syz': self.tab.steady_state_data.steady_syz,
                    'steady_sxz': self.tab.steady_state_data.steady_sxz,
                    'steady_node_ids': self.tab.steady_state_data.node_ids
                }

            # Prepare force/moment data for temp solver
            modal_fm_filtered = None
            fm_node_ids = None
            fm_node_coords = None
            if options.get('compute_force_moment', False) and self.tab.force_moment_data:
                fmd = self.tab.force_moment_data
                modal_fm_filtered = (
                    fmd.modal_fx[:, mode_slice], fmd.modal_fy[:, mode_slice], fmd.modal_fz[:, mode_slice],
                    fmd.modal_mx[:, mode_slice], fmd.modal_my[:, mode_slice], fmd.modal_mz[:, mode_slice]
                )
                fm_node_ids = fmd.node_ids
                fm_node_coords = fmd.node_coords

            # Prepare stress arrays for temp solver (optional)
            stress_sx = self.tab.stress_data.modal_sx[:, mode_slice] if self.tab.stress_data else None
            stress_sy = self.tab.stress_data.modal_sy[:, mode_slice] if self.tab.stress_data else None
            stress_sz = self.tab.stress_data.modal_sz[:, mode_slice] if self.tab.stress_data else None
            stress_sxy = self.tab.stress_data.modal_sxy[:, mode_slice] if self.tab.stress_data else None
            stress_syz = self.tab.stress_data.modal_syz[:, mode_slice] if self.tab.stress_data else None
            stress_sxz = self.tab.stress_data.modal_sxz[:, mode_slice] if self.tab.stress_data else None

            # Create temporary solver for this time point
            temp_solver = solver_engine.MSUPSmartSolverTransient(
                modal_sx=stress_sx, modal_sy=stress_sy, modal_sz=stress_sz,
                modal_sxy=stress_sxy, modal_syz=stress_syz, modal_sxz=stress_sxz,
                modal_coord=selected_modal_coord,
                time_values=dt_window,
                modal_node_ids=self.tab.stress_data.node_ids if self.tab.stress_data else None,
                modal_deformations=modal_deformations_filtered,
                modal_force_moment=modal_fm_filtered,
                force_moment_node_ids=fm_node_ids,
                force_moment_node_coords=fm_node_coords,
                **steady_kwargs
            )

            num_nodes = self.tab.stress_data.num_nodes if self.tab.stress_data else 0
            display_coords = self.tab.stress_data.node_coords if self.tab.stress_data else None
            ux_tp, uy_tp, uz_tp = None, None, None

            # Apply deformation to coordinates if requested
            if options.get('display_deformed_shape', False) and self.tab.deformation_data and num_nodes > 0:
                ux_tp, uy_tp, uz_tp = temp_solver.compute_deformations(0, num_nodes)
                if is_vel_or_accel:
                    ux_tp = ux_tp[:, [centre_offset]]
                    uy_tp = uy_tp[:, [centre_offset]]
                    uz_tp = uz_tp[:, [centre_offset]]
                displacement_vector = np.hstack((ux_tp, uy_tp, uz_tp))
                display_coords = self.tab.stress_data.node_coords + (
                        displacement_vector * options.get('scale_factor', 1.0)
                )

            # Compute stresses only when stress data is available and stress outputs selected
            actual_sx = actual_sy = actual_sz = actual_sxy = actual_syz = actual_sxz = None
            is_stress_output = any([
                options.get('compute_von_mises', False),
                options.get('compute_max_principal', False),
                options.get('compute_min_principal', False),
            ])
            if is_stress_output and num_nodes > 0:
                actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz = \
                    temp_solver.compute_normal_stresses(0, num_nodes)

            # Create mesh (will be overridden for force/moment which have their own coords)
            mesh = None
            if display_coords is not None:
                mesh = pv.PolyData(display_coords)
                if self.tab.stress_data and self.tab.stress_data.node_ids is not None:
                    mesh["NodeID"] = self.tab.stress_data.node_ids.astype(int)

            # Compute requested scalar field
            scalar_field, display_name = None, "Result"

            def _to_1d(values):
                return np.asarray(values, dtype=float).reshape(-1)

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
                if not self.tab.deformation_data:
                    QMessageBox.warning(
                        self.tab, "Missing Data",
                        "Modal deformations must be loaded for this calculation."
                    )
                    return
                if ux_tp is None:
                    ux_tp, uy_tp, uz_tp = temp_solver.compute_deformations(0, num_nodes)
                def_x = _to_1d(ux_tp)
                def_y = _to_1d(uy_tp)
                def_z = _to_1d(uz_tp)
                def_mag = np.sqrt(def_x ** 2 + def_y ** 2 + def_z ** 2)
                mesh["def_x"] = def_x
                mesh["def_y"] = def_y
                mesh["def_z"] = def_z
                mesh["def_mag"] = def_mag
                mesh["UX (mm)"] = def_x
                mesh["UY (mm)"] = def_y
                mesh["UZ (mm)"] = def_z
                mesh["Deformation (mm)"] = def_mag
                scalar_field = def_mag
                display_name = "Deformation (mm)"

            elif is_vel_or_accel:
                if not self.tab.deformation_data:
                    QMessageBox.warning(
                        self.tab, "Missing Data",
                        "Modal deformations must be loaded for this calculation."
                    )
                    return
                ux_blk, uy_blk, uz_blk = temp_solver.compute_deformations(0, num_nodes)
                vel_mag, acc_mag, vel_x, vel_y, vel_z, acc_x, acc_y, acc_z = \
                    temp_solver._vel_acc_from_disp(ux_blk, uy_blk, uz_blk, dt_window.astype(temp_solver.NP_DTYPE))

                if options.get('compute_velocity', False):
                    vel_x_tp = _to_1d(vel_x[:, [centre_offset]])
                    vel_y_tp = _to_1d(vel_y[:, [centre_offset]])
                    vel_z_tp = _to_1d(vel_z[:, [centre_offset]])
                    vel_mag_tp = _to_1d(vel_mag[:, [centre_offset]])
                    scalar_field = vel_mag_tp
                    display_name = "Velocity (mm/s)"
                    # Keep lowercase component names for APDL IC export compatibility.
                    mesh["vel_x"] = vel_x_tp
                    mesh["vel_y"] = vel_y_tp
                    mesh["vel_z"] = vel_z_tp
                    mesh["vel_mag"] = vel_mag_tp
                    mesh["VX (mm/s)"] = vel_x_tp
                    mesh["VY (mm/s)"] = vel_y_tp
                    mesh["VZ (mm/s)"] = vel_z_tp
                    mesh["Velocity (mm/s)"] = vel_mag_tp
                else:  # Acceleration
                    acc_x_tp = _to_1d(acc_x[:, [centre_offset]])
                    acc_y_tp = _to_1d(acc_y[:, [centre_offset]])
                    acc_z_tp = _to_1d(acc_z[:, [centre_offset]])
                    acc_mag_tp = _to_1d(acc_mag[:, [centre_offset]])
                    scalar_field = acc_mag_tp
                    display_name = "Acceleration (mm/s²)"
                    mesh["acc_x"] = acc_x_tp
                    mesh["acc_y"] = acc_y_tp
                    mesh["acc_z"] = acc_z_tp
                    mesh["acc_mag"] = acc_mag_tp
                    mesh["AX (mm/s²)"] = acc_x_tp
                    mesh["AY (mm/s²)"] = acc_y_tp
                    mesh["AZ (mm/s²)"] = acc_z_tp
                    mesh["Acceleration (mm/s²)"] = acc_mag_tp

            elif options.get('compute_force_moment', False):
                if not self.tab.force_moment_data:
                    QMessageBox.warning(
                        self.tab, "Missing Data",
                        "Element nodal forces & moments must be loaded for this calculation."
                    )
                    return
                fm_result = temp_solver.compute_forces_moments(0, temp_solver.modal_forces_fx.shape[0])
                if fm_result is not None:
                    fx_tp, fy_tp, fz_tp, mx_tp, my_tp, mz_tp = fm_result
                    # Use force/moment node coords for mesh
                    mesh = pv.PolyData(self.tab.force_moment_data.node_coords)
                    if self.tab.force_moment_data.node_ids is not None:
                        mesh["NodeID"] = self.tab.force_moment_data.node_ids.astype(int)
                    fx = _to_1d(fx_tp)
                    fy = _to_1d(fy_tp)
                    fz = _to_1d(fz_tp)
                    mx = _to_1d(mx_tp)
                    my = _to_1d(my_tp)
                    mz = _to_1d(mz_tp)
                    f_mag = np.sqrt(fx ** 2 + fy ** 2 + fz ** 2)
                    m_mag = np.sqrt(mx ** 2 + my ** 2 + mz ** 2)
                    mesh["fx"] = fx
                    mesh["fy"] = fy
                    mesh["fz"] = fz
                    mesh["f_mag"] = f_mag
                    mesh["mx"] = mx
                    mesh["my"] = my
                    mesh["mz"] = mz
                    mesh["m_mag"] = m_mag
                    mesh["FX (N)"] = fx
                    mesh["FY (N)"] = fy
                    mesh["FZ (N)"] = fz
                    mesh["Force (N)"] = f_mag
                    mesh["MX (N·mm)"] = mx
                    mesh["MY (N·mm)"] = my
                    mesh["MZ (N·mm)"] = mz
                    mesh["Moment (N·mm)"] = m_mag
                    scalar_field = f_mag
                    display_name = "Force (N)"

            if scalar_field is None:
                print("No valid output was calculated.")
                return

            if mesh is None:
                print("No mesh was prepared for display.")
                return

            scalar_field = _to_1d(scalar_field)

            # Add scalar field to mesh
            mesh[display_name] = scalar_field
            mesh.set_active_scalars(display_name)

            # Compute data range
            data_min, data_max = np.min(scalar_field), np.max(scalar_field)

            # Emit results to Display tab
            self.tab.time_point_result_ready.emit(mesh, display_name, data_min, data_max)

        except Exception as e:
            print(f"ERROR during time point calculation: {e}")
            traceback.print_exc()

    def _validate_animation_request(self, params):
        """
        Validate core and request-specific preconditions for animation.

        Returns:
            (bool, str): Tuple of ok flag and error message (if not ok).
        """
        # Core data requirements
        if not self.tab.coord_loaded:
            return False, "Modal coordinate file is not loaded."
        if not (self.tab.stress_loaded or self.tab.force_moment_loaded):
            return False, "No data files loaded (stress or force/moment)."

        # Frames to compute
        anim_indices = params.get('anim_indices', [])
        if len(anim_indices) == 0:
            return False, "No animation frames to compute."

        # At least one output selected
        if not any([
            params.get('compute_von_mises', False),
            params.get('compute_max_principal', False),
            params.get('compute_min_principal', False),
            params.get('compute_deformation_contour', False),
            params.get('compute_velocity', False),
            params.get('compute_acceleration', False),
            params.get('compute_force_moment', False)
        ]):
            return False, "No valid output selected for animation."

        # Deformation dependency
        if params.get('compute_deformation_anim', False) and not self.tab.deformation_data:
            return False, (
                "Deformation animation is selected but deformation data is not loaded.\n\n"
                "Please either:\n"
                "• Load a deformation file using the 'Modal Deformations File' button\n"
                "• Or uncheck 'Include Deformations' in the solver tab"
            )

        # Steady-state dependency
        if params.get('include_steady', False) and not self.tab.steady_state_data:
            return False, (
                "Steady-state inclusion is selected but steady-state data is not loaded.\n\n"
                "Please either:\n"
                "• Load a steady-state stress file using the 'Read Full Stress Tensor File (.txt)' button\n"
                "• Or uncheck 'Include Steady-State Stress Field' in the solver tab"
            )

        # Skip-mode validation
        try:
            skip_first = int(params.get('skip_n_modes', 0) or 0)
            skip_last = int(params.get('skip_last_n_modes', 0) or 0)
        except (TypeError, ValueError):
            return False, "Skip mode values are invalid."

        if skip_first < 0 or skip_last < 0:
            return False, "Skip mode values cannot be negative."
        if skip_first + skip_last >= self.tab.modal_data.num_modes:
            return False, (
                f"Invalid skip settings: first={skip_first}, last={skip_last}, "
                f"available={self.tab.modal_data.num_modes}. Reduce skip values."
            )

        return True, ""

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
            display_tab = self.tab.window().display_tab

            # Validate core and request-specific preconditions
            ok, error_msg = self._validate_animation_request(params)
            if not ok:
                # Emit failure and let UI decide how to present the error
                QApplication.restoreOverrideCursor()
                # Emit explicit failure signal with message
                try:
                    self.tab.animation_precomputation_failed.emit(error_msg)
                except Exception:
                    pass
                self.tab.animation_data_ready.emit(None)
                # Log to console
                print(f"Animation cancelled: {error_msg}")
                return

            # Get animation indices
            anim_indices = params.get('anim_indices', [])
            if len(anim_indices) == 0:
                QMessageBox.warning(self.tab, "No Frames", "No animation frames to compute.")
                QApplication.restoreOverrideCursor()
                self.tab.animation_data_ready.emit(None)
                return

            anim_times = self.tab.modal_data.time_values[anim_indices]
            num_anim_steps = len(anim_times)
            print(f"Precomputing {num_anim_steps} animation frames...")

            # Deformation usage for RAM estimate
            compute_deformation_anim = params.get('compute_deformation_anim', False)

            # RAM check - use the largest node set that will be processed
            num_nodes = self.tab.stress_data.num_nodes if self.tab.stress_data else 0
            if params.get('compute_force_moment', False) and self.tab.force_moment_data:
                num_nodes = max(num_nodes, self.tab.force_moment_data.num_nodes)
            estimated_gb = display_tab._estimate_animation_ram(
                num_nodes, num_anim_steps, compute_deformation_anim
            )

            available_gb = psutil.virtual_memory().available / (1024 ** 3)
            safe_available_gb = available_gb * constants.RAM_PERCENT

            print(f"Estimated RAM: {estimated_gb:.3f} GB")
            print(f"Available RAM: {available_gb:.3f} GB (Safe: {safe_available_gb:.3f} GB)")

            if estimated_gb > safe_available_gb:
                QMessageBox.warning(
                    self.tab, "Insufficient Memory",
                    f"Estimated RAM ({estimated_gb:.3f} GB) exceeds safe limit "
                    f"({safe_available_gb:.3f} GB). Adjust time range or step."
                )
                QApplication.restoreOverrideCursor()
                self.tab.animation_data_ready.emit(None)
                return

            # Create temporary solver for animation
            skip_first = int(params.get('skip_n_modes', 0) or 0)
            skip_last = int(params.get('skip_last_n_modes', 0) or 0)
            mode_slice = self._build_mode_slice(skip_first, skip_last)
            selected_modal_coord = self.tab.modal_data.modal_coord[mode_slice, anim_indices]

            steady_kwargs = {}
            if params.get('include_steady', False) and self.tab.steady_state_data:
                steady_kwargs = {
                    'steady_sx': self.tab.steady_state_data.steady_sx,
                    'steady_sy': self.tab.steady_state_data.steady_sy,
                    'steady_sz': self.tab.steady_state_data.steady_sz,
                    'steady_sxy': self.tab.steady_state_data.steady_sxy,
                    'steady_syz': self.tab.steady_state_data.steady_syz,
                    'steady_sxz': self.tab.steady_state_data.steady_sxz,
                    'steady_node_ids': self.tab.steady_state_data.node_ids
                }

            modal_deformations_filtered = None
            if compute_deformation_anim and self.tab.deformation_data:
                modal_deformations_filtered = (
                    self.tab.deformation_data.modal_ux[:, mode_slice],
                    self.tab.deformation_data.modal_uy[:, mode_slice],
                    self.tab.deformation_data.modal_uz[:, mode_slice]
                )

            # Prepare force/moment data for animation solver
            modal_fm_anim = None
            fm_node_ids_anim = None
            fm_node_coords_anim = None
            if params.get('compute_force_moment', False) and self.tab.force_moment_data:
                fmd = self.tab.force_moment_data
                modal_fm_anim = (
                    fmd.modal_fx[:, mode_slice], fmd.modal_fy[:, mode_slice], fmd.modal_fz[:, mode_slice],
                    fmd.modal_mx[:, mode_slice], fmd.modal_my[:, mode_slice], fmd.modal_mz[:, mode_slice]
                )
                fm_node_ids_anim = fmd.node_ids
                fm_node_coords_anim = fmd.node_coords

            # Prepare stress arrays (optional)
            anim_stress_sx = self.tab.stress_data.modal_sx[:, mode_slice] if self.tab.stress_data else None
            anim_stress_sy = self.tab.stress_data.modal_sy[:, mode_slice] if self.tab.stress_data else None
            anim_stress_sz = self.tab.stress_data.modal_sz[:, mode_slice] if self.tab.stress_data else None
            anim_stress_sxy = self.tab.stress_data.modal_sxy[:, mode_slice] if self.tab.stress_data else None
            anim_stress_syz = self.tab.stress_data.modal_syz[:, mode_slice] if self.tab.stress_data else None
            anim_stress_sxz = self.tab.stress_data.modal_sxz[:, mode_slice] if self.tab.stress_data else None

            temp_solver = solver_engine.MSUPSmartSolverTransient(
                modal_sx=anim_stress_sx, modal_sy=anim_stress_sy, modal_sz=anim_stress_sz,
                modal_sxy=anim_stress_sxy, modal_syz=anim_stress_syz, modal_sxz=anim_stress_sxz,
                modal_coord=selected_modal_coord,
                time_values=anim_times,
                modal_node_ids=self.tab.stress_data.node_ids if self.tab.stress_data else None,
                modal_deformations=modal_deformations_filtered,
                modal_force_moment=modal_fm_anim,
                force_moment_node_ids=fm_node_ids_anim,
                force_moment_node_coords=fm_node_coords_anim,
                **steady_kwargs
            )

            # Only compute stresses if stress-based outputs are selected and data is available
            is_stress_anim = any([
                params.get('compute_von_mises', False),
                params.get('compute_max_principal', False),
                params.get('compute_min_principal', False),
            ])
            actual_sx = actual_sy = actual_sz = actual_sxy = actual_syz = actual_sxz = None
            if self.tab.stress_data and (is_stress_anim or any([
                params.get('compute_deformation_contour', False),
                params.get('compute_velocity', False),
                params.get('compute_acceleration', False),
            ])):
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
                if not self.tab.deformation_data:
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

            if params.get('compute_force_moment', False):
                if not self.tab.force_moment_data:
                    raise ValueError("Force/moment data not loaded.")
                n_fm = temp_solver.modal_forces_fx.shape[0]
                fx_a, fy_a, fz_a, mx_a, my_a, mz_a = temp_solver.compute_forces_moments(0, n_fm)
                precomputed_scalars = np.sqrt(fx_a ** 2 + fy_a ** 2 + fz_a ** 2)
                data_column_name = "Force (N)"

            # Compute deformed coordinates if requested
            precomputed_coords = None
            if compute_deformation_anim and self.tab.deformation_data and self.tab.stress_data and num_nodes > 0:
                print("Computing deformations for animation...")
                deformations = temp_solver.compute_deformations(0, num_nodes)
                if deformations is not None:
                    ux_anim, uy_anim, uz_anim = deformations
                    scale_factor = params.get('scale_factor', 1.0)

                    original_coords_reshaped = self.tab.stress_data.node_coords[:, :, np.newaxis]
                    
                    # Apply zero-referencing based on user preference
                    # By default (show_absolute_deformation=False), animations show relative motion
                    # from the start frame, making the first frame appear at "zero" deformation.
                    # When show_absolute_deformation=True, animations preserve absolute deformation
                    # values from the undeformed geometry.
                    show_absolute = params.get('show_absolute_deformation', False)
                    if not show_absolute:
                        # Zero-reference to first animation frame (relative motion mode)
                        ux_anim -= ux_anim[:, [0]]
                        uy_anim -= uy_anim[:, [0]]
                        uz_anim -= uz_anim[:, [0]]
                        print("Animation mode: Relative deformations (zero-referenced to start frame)")
                    else:
                        print("Animation mode: Absolute deformations (from undeformed geometry)")

                    displacements_stacked = np.stack([ux_anim, uy_anim, uz_anim], axis=1)
                    precomputed_coords = original_coords_reshaped + scale_factor * displacements_stacked

            print("Cleaning up temporary animation data...")
            del temp_solver, actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz
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
            self.tab.animation_data_ready.emit(results)

        except Exception as e:
            print(f"ERROR during animation precomputation: {e}")
            traceback.print_exc()
            QApplication.restoreOverrideCursor()
            self.tab.animation_data_ready.emit(None)
