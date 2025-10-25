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
from PyQt5.QtCore import pyqtSlot
import numpy as np
from PyQt5.QtWidgets import QMessageBox, QApplication
import pyvista as pv

from solver import engine as solver_engine
from core.data_models import SolverConfig
from ui.widgets.plotting import PlotlyMaxWidget


class SolverAnalysisHandler:
    """Manages the analysis execution and result handling for the SolverTab."""

    def __init__(self, tab):
        """
        Initialize the analysis handler.

        Args:
            tab (SolverTab): The parent SolverTab instance.
        """
        self.tab = tab

    @pyqtSlot()
    def solve(self, force_time_history_for_node_id=None):
        """
        Main solve method - orchestrates the analysis.

        Args:
            force_time_history_for_node_id: Optional node ID to force time history mode.
        """
        try:
            # Save current tab index
            current_tab_index = self.tab.show_output_tab_widget.currentIndex()

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
            self.tab.show_output_tab_widget.setCurrentIndex(current_tab_index)

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
            calculate_damage=self.tab.damage_index_checkbox.isChecked(),
            time_history_mode=is_time_history,
            include_steady_state=self.tab.steady_state_checkbox.isChecked(),
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
        if config.include_steady_state and self.tab.steady_state_data is None:
            self.tab.console_textbox.append(
                "Error: Steady-state stress data is not loaded yet."
            )
            self.tab.progress_bar.setVisible(False)
            return None

        # Validate skip modes
        if self.tab.stress_data and config.skip_n_modes >= self.tab.stress_data.num_modes:
            QMessageBox.critical(
                self.tab, "Calculation Error",
                f"Cannot skip {config.skip_n_modes} modes as only "
                f"{self.tab.stress_data.num_modes} are available."
            )
            self.tab.progress_bar.setVisible(False)
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
            if force_node_id not in self.tab.stress_data.node_ids:
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
            if node_id not in self.tab.stress_data.node_ids:
                QMessageBox.warning(
                    self.tab, "Invalid Node ID",
                    f"Node ID {node_id} was not found in the loaded modal stress file."
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
            self.tab.acceleration_checkbox.isChecked()
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

    def _get_skip_n_modes(self):
        """Get number of modes to skip from UI."""
        if not self.tab.skip_modes_combo.isVisible():
            return 0
        try:
            return int(self.tab.skip_modes_combo.currentText())
        except (ValueError, TypeError):
            return 0

    def _get_output_directory(self):
        """Get output directory for results."""
        if self.tab.project_directory:
            return self.tab.project_directory
        return os.path.dirname(os.path.abspath(__file__))

    def _configure_analysis_engine(self):
        """Configure the analysis engine with loaded data."""
        self.tab.analysis_engine.configure_data(
            self.tab.modal_data,
            self.tab.stress_data,
            self.tab.deformation_data,
            self.tab.steady_state_data
        )

    def _execute_analysis(self, config):
        """
        Execute the analysis based on configuration.

        Args:
            config: SolverConfig with analysis settings.
        """
        # Create solver
        self.tab.analysis_engine.create_solver(config)

        # Connect progress signal
        if self.tab.analysis_engine.solver:
            self.tab.analysis_engine.solver.progress_signal.connect(
                self.tab.update_progress_bar  # Connects to the method on SolverTab
            )

        # Show progress bar
        self.tab.progress_bar.setVisible(True)
        self.tab.progress_bar.setValue(0)

        if config.time_history_mode:
            # Run single-node analysis
            result = self.tab.analysis_engine.run_single_node_analysis(
                config.selected_node_id, config
            )
            self._handle_time_history_result(result, config)
        else:
            # Run batch analysis
            self.tab.analysis_engine.run_batch_analysis(config)
            self._handle_batch_results(config)

        # Hide progress bar
        self.tab.progress_bar.setVisible(False)

    def _handle_time_history_result(self, result, config):
        """Handle results from time history analysis."""
        # Update plot
        self.tab.plot_single_node_tab.update_plot(
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
        solver = self.tab.analysis_engine.solver  # Shortcut

        if config.calculate_von_mises and hasattr(solver, 'max_over_time_svm'):
            max_traces.append({
                'name': 'Von Mises (MPa)',
                'data': solver.max_over_time_svm
            })
            von_mises_max = solver.max_over_time_svm
        else:
            von_mises_max = None

        if config.calculate_max_principal_stress and hasattr(solver, 'max_over_time_s1'):
            max_traces.append({
                'name': 'S1 (MPa)',
                'data': solver.max_over_time_s1
            })
            s1_max = solver.max_over_time_s1
        else:
            s1_max = None

        if config.calculate_deformation and hasattr(solver, 'max_over_time_def'):
            max_traces.append({
                'name': 'Deformation (mm)',
                'data': solver.max_over_time_def
            })
            def_max = solver.max_over_time_def
        else:
            def_max = None

        if config.calculate_velocity and hasattr(solver, 'max_over_time_vel'):
            max_traces.append({
                'name': 'Velocity (mm/s)',
                'data': solver.max_over_time_vel
            })
            vel_max = solver.max_over_time_vel
        else:
            vel_max = None

        if config.calculate_acceleration and hasattr(solver, 'max_over_time_acc'):
            max_traces.append({
                'name': 'Acceleration (mm/s²)',
                'data': solver.max_over_time_acc
            })
            acc_max = solver.max_over_time_acc
        else:
            acc_max = None

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

        # Show minimum over time tab if min principal stress was calculated
        if config.calculate_min_principal_stress and hasattr(solver, 'min_over_time_s3'):
            min_traces = [{
                'name': 'S3 (MPa)',
                'data': solver.min_over_time_s3
            }]

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
                display_tab = self.tab.window().display_tab
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

    def _log_solve_start(self, config):
        """Log solve start information."""
        current_time = datetime.now()
        self.tab.console_textbox.append(
            f"\n******************* BEGIN SOLVE ********************\n"
            f"Datetime: {current_time}\n\n"
        )

    def _log_solve_complete(self):
        """Log solve completion."""
        self.tab.console_textbox.append(
            "\n******************* SOLVE COMPLETE ********************\n\n"
        )

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
            # Validate data is loaded
            if not (self.tab.coord_loaded and self.tab.stress_loaded):
                QMessageBox.warning(self.tab, "Missing Data", "Core data files are not loaded.")
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
            mode_slice = slice(options.get('skip_n_modes', 0), None)

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

            # Create temporary solver for this time point
            temp_solver = solver_engine.MSUPSmartSolverTransient(
                self.tab.stress_data.modal_sx[:, mode_slice],
                self.tab.stress_data.modal_sy[:, mode_slice],
                self.tab.stress_data.modal_sz[:, mode_slice],
                self.tab.stress_data.modal_sxy[:, mode_slice],
                self.tab.stress_data.modal_syz[:, mode_slice],
                self.tab.stress_data.modal_sxz[:, mode_slice],
                selected_modal_coord,
                dt_window,
                modal_node_ids=self.tab.stress_data.node_ids,
                modal_deformations=modal_deformations_filtered,
                **steady_kwargs
            )

            num_nodes = self.tab.stress_data.num_nodes
            display_coords = self.tab.stress_data.node_coords
            ux_tp, uy_tp, uz_tp = None, None, None

            # Apply deformation to coordinates if requested
            if options.get('display_deformed_shape', False) and self.tab.deformation_data:
                ux_tp, uy_tp, uz_tp = temp_solver.compute_deformations(0, num_nodes)
                if is_vel_or_accel:
                    ux_tp = ux_tp[:, [centre_offset]]
                    uy_tp = uy_tp[:, [centre_offset]]
                    uz_tp = uz_tp[:, [centre_offset]]
                displacement_vector = np.hstack((ux_tp, uy_tp, uz_tp))
                display_coords = self.tab.stress_data.node_coords + (
                        displacement_vector * options.get('scale_factor', 1.0)
                )

            # Compute stresses
            actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz = \
                temp_solver.compute_normal_stresses(0, num_nodes)

            # Create mesh
            mesh = pv.PolyData(display_coords)
            if self.tab.stress_data.node_ids is not None:
                mesh["NodeID"] = self.tab.stress_data.node_ids.astype(int)

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
                if not self.tab.deformation_data:
                    QMessageBox.warning(
                        self.tab, "Missing Data",
                        "Modal deformations must be loaded for this calculation."
                    )
                    return
                if ux_tp is None:
                    ux_tp, uy_tp, uz_tp = temp_solver.compute_deformations(0, num_nodes)
                scalar_field = np.sqrt(ux_tp ** 2 + uy_tp ** 2 + uz_tp ** 2)
                display_name = "Deformation (mm)"

            elif is_vel_or_accel:
                if not self.tab.deformation_data:
                    QMessageBox.warning(
                        self.tab, "Missing Data",
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
        if not (self.tab.coord_loaded and self.tab.stress_loaded):
            return False, "Core data files are not loaded."

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
            params.get('compute_acceleration', False)
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

            # RAM check
            num_nodes = self.tab.stress_data.num_nodes
            estimated_gb = display_tab._estimate_animation_ram(
                num_nodes, num_anim_steps, compute_deformation_anim
            )

            available_gb = psutil.virtual_memory().available / (1024 ** 3)
            safe_available_gb = available_gb * solver_engine.RAM_PERCENT

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
            mode_slice = slice(params.get('skip_n_modes', 0), None)
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

            temp_solver = solver_engine.MSUPSmartSolverTransient(
                self.tab.stress_data.modal_sx[:, mode_slice],
                self.tab.stress_data.modal_sy[:, mode_slice],
                self.tab.stress_data.modal_sz[:, mode_slice],
                self.tab.stress_data.modal_sxy[:, mode_slice],
                self.tab.stress_data.modal_syz[:, mode_slice],
                self.tab.stress_data.modal_sxz[:, mode_slice],
                selected_modal_coord,
                anim_times,
                modal_node_ids=self.tab.stress_data.node_ids,
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

            # Compute deformed coordinates if requested
            precomputed_coords = None
            if compute_deformation_anim and self.tab.deformation_data:
                print("Computing deformations for animation...")
                deformations = temp_solver.compute_deformations(0, num_nodes)
                if deformations is not None:
                    ux_anim, uy_anim, uz_anim = deformations
                    scale_factor = params.get('scale_factor', 1.0)

                    original_coords_reshaped = self.tab.stress_data.node_coords[:, :, np.newaxis]
                    ux_anim -= ux_anim[:, [0]]
                    uy_anim -= uy_anim[:, [0]]
                    uz_anim -= uz_anim[:, [0]]

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