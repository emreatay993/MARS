"""
UI State Handler for the SolverTab.

This class encapsulates all logic related to managing the state of UI components
(enabling/disabling, showing/hiding, etc.) based on user interaction.
"""

import math
import numpy as np


class SolverUIHandler:
    """Manages the UI state for the SolverTab."""

    def __init__(self, tab):
        """
        Initialize the UI handler.

        Args:
            tab (SolverTab): The parent SolverTab instance.
        """
        self.tab = tab

    def update_output_checkboxes_state(self):
        """Enable/disable output checkboxes based on loaded files."""
        # Force/moment-related outputs (require coord + force_moment -- no stress needed)
        force_moment_enabled = (
                self.tab.coord_loaded and
                self.tab.force_moment_checkbox.isChecked() and
                self.tab.force_moment_loaded
        )
        for cb in self.tab._force_moment_outputs:
            cb.setEnabled(force_moment_enabled)
            if not force_moment_enabled:
                cb.setChecked(False)

        # When force/moment output is selected, keep it exclusive from other outputs.
        force_moment_selected = self.tab.force_moment_output_checkbox.isChecked()

        # Stress-related outputs (require coord + stress)
        stress_enabled = self.tab.coord_loaded and self.tab.stress_loaded
        for cb in self.tab._coord_stress_outputs:
            should_enable = stress_enabled and not force_moment_selected
            cb.setEnabled(should_enable)
            if not should_enable:
                cb.setChecked(False)

        # Deformation-related outputs (require coord + deformation)
        deformations_enabled = (
                self.tab.coord_loaded and
                self.tab.deformations_checkbox.isChecked() and
                self.tab.deformation_loaded
        )
        for cb in self.tab._deformation_outputs:
            should_enable = deformations_enabled and not force_moment_selected
            cb.setEnabled(should_enable)
            if not should_enable:
                cb.setChecked(False)

        # Time history mode: enabled if any data source can produce output
        any_output_possible = stress_enabled or deformations_enabled or force_moment_enabled
        self.tab.time_history_checkbox.setEnabled(any_output_possible)
        if not any_output_possible:
            self.tab.time_history_checkbox.setChecked(False)

        # Ensure dependent controls track Von Mises selection state
        self._update_plasticity_state()
        self._update_damage_index_state()

    def on_force_moment_output_toggled(self, is_checked):
        """Keep force/moment output mutually exclusive from other output selections."""
        if is_checked:
            for checkbox in self.tab._coord_stress_outputs + self.tab._deformation_outputs:
                checkbox.blockSignals(True)
                checkbox.setChecked(False)
                checkbox.blockSignals(False)

        self.update_output_checkboxes_state()
        self._update_solve_button_state()

    def toggle_steady_state_stress_inputs(self, is_checked):
        """Show/hide steady-state stress file controls."""
        self.tab.steady_state_file_button.setVisible(is_checked)
        self.tab.steady_state_file_path.setVisible(is_checked)
        if not is_checked:
            self.tab.steady_state_file_path.clear()

    def toggle_deformations_inputs(self, is_checked):
        """Show/hide deformation file controls."""
        self.tab.deformations_file_button.setVisible(is_checked)
        self.tab.deformations_file_path.setVisible(is_checked)
        self.update_output_checkboxes_state()
        if not is_checked:
            self.tab.deformations_file_path.clear()
            self.tab.deformation_loaded = False
            self.tab.deformation_data = None

    def toggle_force_moment_inputs(self, is_checked):
        """Show/hide element nodal forces & moments file controls."""
        self.tab.force_moment_file_button.setVisible(is_checked)
        self.tab.force_moment_file_path.setVisible(is_checked)
        self.update_output_checkboxes_state()
        if not is_checked:
            self.tab.force_moment_file_path.clear()
            self.tab.force_moment_loaded = False
            self.tab.force_moment_data = None

    def toggle_damage_index_checkbox_visibility(self, is_checked=None):
        """Keep damage index checkbox hidden until benchmarking completes."""
        _ = is_checked  # Maintains signal compatibility while checkbox stays hidden
        self.tab.damage_index_checkbox.setChecked(False)
        self.tab.damage_index_checkbox.setVisible(False)  # TODO: Re-enable visibility once damage index is verified

    def toggle_fatigue_params_visibility(self, checked):
        """Show/hide fatigue parameters group."""
        self.tab.fatigue_params_group.setVisible(checked)

    def toggle_plasticity_options_visibility(self, is_checked):
        """Show/hide plasticity options group based on Plasticity checkbox."""
        try:
            self.tab.plasticity_options_group.setVisible(bool(is_checked))
            if is_checked:
                self.on_plasticity_iteration_inputs_changed()
            else:
                self.clear_plasticity_warning()
        except Exception as e:
            print(f"Error toggling plasticity options visibility: {e}")

    def toggle_single_node_solution_group(self, is_checked):
        """Show/hide single node selection group."""
        try:
            if is_checked:
                # Connect exclusive handlers
                for cb in self.tab.time_history_exclusive_outputs:
                    cb.toggled.connect(
                        lambda checked, a_checkbox=cb:
                        self.on_exclusive_output_toggled(checked, a_checkbox)
                    )

                self.tab.single_node_group.setVisible(True)
                self.tab.show_output_tab_widget.setTabVisible(
                    self.tab.show_output_tab_widget.indexOf(self.tab.plot_single_node_tab),
                    True
                )
            else:
                # Disconnect exclusive handlers
                for checkbox in self.tab.time_history_exclusive_outputs:
                    try:
                        checkbox.toggled.disconnect(self.on_exclusive_output_toggled)
                    except TypeError:
                        pass

                self.tab.single_node_group.setVisible(False)
                self.tab.show_output_tab_widget.setTabVisible(
                    self.tab.show_output_tab_widget.indexOf(self.tab.plot_single_node_tab),
                    False
                )
        except Exception as e:
            print(f"Error toggling single node group visibility: {e}")

    def _on_time_history_toggled(self, is_checked):
        """Handle time history mode toggle."""
        if is_checked:
            all_output_checkboxes = (self.tab._coord_stress_outputs + self.tab._deformation_outputs
                                     + self.tab._force_moment_outputs)
            for checkbox in all_output_checkboxes:
                if checkbox is self.tab.time_history_checkbox:
                    continue
                checkbox.blockSignals(True)
                checkbox.setChecked(False)
                checkbox.blockSignals(False)
            # Ensure dependent UI reflects new states
            self._update_plasticity_state()

    def _update_damage_index_state(self, checked=False):
        """Update damage index checkbox state."""
        self.tab.damage_index_checkbox.setEnabled(False)  # TODO: Enable after damage index benchmarks
        self.tab.damage_index_checkbox.setChecked(False)
        self.tab.damage_index_checkbox.setVisible(False)

    def _update_plasticity_state(self, checked=False):
        """Enable Plasticity Correction only when Von Mises is selected.

        Remains visible at all times; disables and unchecks when Von Mises is not selected.
        """
        is_von_mises_selected = self.tab.von_mises_checkbox.isChecked()
        # Keep visible; only toggle enabled state
        self.tab.plasticity_correction_checkbox.setEnabled(is_von_mises_selected)
        if not is_von_mises_selected:
            self.tab.plasticity_correction_checkbox.setChecked(False)
            # Also hide options when dependency not satisfied
            self.toggle_plasticity_options_visibility(False)
            self.clear_plasticity_warning()

    def on_exclusive_output_toggled(self, is_checked, sender_checkbox):
        """Ensure only one output is selected in time history mode."""
        if self.tab.time_history_checkbox.isChecked() and is_checked:
            for checkbox in self.tab.time_history_exclusive_outputs:
                if checkbox is not sender_checkbox:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)

    # ========== Plot Management Methods ==========

    def update_single_node_plot(self):
        """Update placeholder plot."""
        x = np.linspace(0, 10, 100)
        y = np.zeros(100)
        self.tab.plot_single_node_tab.update_plot(x, y)

    def update_single_node_plot_based_on_checkboxes(self, checked=False):
        """Update plot based on checkbox states."""
        try:
            x_data = [1, 2, 3, 4, 5]
            y_data = [0, 0, 0, 0, 0]

            self.tab.plot_single_node_tab.update_plot(
                x_data, y_data, None,
                is_max_principal_stress=self.tab.max_principal_stress_checkbox.isChecked(),
                is_min_principal_stress=self.tab.min_principal_stress_checkbox.isChecked(),
                is_von_mises=self.tab.von_mises_checkbox.isChecked(),
                is_deformation=self.tab.deformation_checkbox.isChecked(),
                is_velocity=self.tab.velocity_checkbox.isChecked(),
                is_acceleration=self.tab.acceleration_checkbox.isChecked(),
                is_force_moment=self.tab.force_moment_output_checkbox.isChecked()
            )
        except Exception as e:
            print(f"Error updating plot based on checkbox states: {e}")

    def _update_max_min_plots(self, checked=False):
        """
        Update max/min over time plots when checkboxes are toggled.

        This method rebuilds the plots to reflect the current checkbox selections,
        hiding tabs if no relevant outputs are selected.
        """
        # Only update if solver has run and data exists
        if self.tab.analysis_engine.solver is None:
            return

        # Don't update in time history mode
        if self.tab.time_history_checkbox.isChecked():
            return

        solver = self.tab.analysis_engine.solver

        # Build max traces based on current checkbox states AND available data
        max_traces = []
        min_traces = []

        if (self.tab.von_mises_checkbox.isChecked() and
                hasattr(solver, 'max_over_time_svm') and solver.max_over_time_svm is not None):
            max_traces.append({
                'name': 'Von Mises (MPa)',
                'data': solver.max_over_time_svm
            })

        if (self.tab.max_principal_stress_checkbox.isChecked() and
                hasattr(solver, 'max_over_time_s1') and solver.max_over_time_s1 is not None):
            max_traces.append({
                'name': 'S1 (MPa)',
                'data': solver.max_over_time_s1
            })

        if (self.tab.deformation_checkbox.isChecked() and
                hasattr(solver, 'max_over_time_def') and solver.max_over_time_def is not None):
            max_traces.append({
                'name': 'Deformation (mm)',
                'data': solver.max_over_time_def
            })

        if (self.tab.velocity_checkbox.isChecked() and
                hasattr(solver, 'max_over_time_vel') and solver.max_over_time_vel is not None):
            max_traces.append({
                'name': 'Velocity (mm/s)',
                'data': solver.max_over_time_vel
            })

        if (self.tab.acceleration_checkbox.isChecked() and
                hasattr(solver, 'max_over_time_acc') and solver.max_over_time_acc is not None):
            max_traces.append({
                'name': 'Acceleration (mm/s²)',
                'data': solver.max_over_time_acc
            })

        if self.tab.force_moment_output_checkbox.isChecked():
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

        # Update or hide max tab
        if max_traces and self.tab.plot_max_over_time_tab is not None:
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

        if (self.tab.min_principal_stress_checkbox.isChecked() and
                hasattr(solver, 'min_over_time_s3') and
                solver.min_over_time_s3 is not None):
            min_traces.insert(0, {
                'name': 'S3 (MPa)',
                'data': solver.min_over_time_s3
            })

        # Update or hide min tab
        if min_traces and self.tab.plot_min_over_time_tab is not None:
            self.tab.plot_min_over_time_tab.update_plot(
                self.tab.modal_data.time_values,
                traces=min_traces
            )
            self.tab.show_output_tab_widget.setTabVisible(
                self.tab.show_output_tab_widget.indexOf(self.tab.plot_min_over_time_tab),
                True
            )
        elif self.tab.plot_min_over_time_tab is not None:
            # Min principal unchecked - hide the tab
            self.tab.plot_min_over_time_tab.clear_plot()
            self.tab.show_output_tab_widget.setTabVisible(
                self.tab.show_output_tab_widget.indexOf(self.tab.plot_min_over_time_tab),
                False
            )

    def on_plasticity_iteration_inputs_changed(self, _text=None):
        """React to iteration parameter edits and display warnings if needed."""
        if not self.tab.plasticity_options_group.isVisible():
            return
        self._update_plasticity_iteration_warning()

    def _update_plasticity_iteration_warning(self):
        warning_label = getattr(self.tab, 'plasticity_warning_label', None)
        if warning_label is None:
            return

        max_iter_text = self.tab.plasticity_max_iter_input.text().strip()
        tolerance_text = self.tab.plasticity_tolerance_input.text().strip()

        default_max_iter = 60
        default_tolerance = 1e-10

        show_warning = False

        try:
            max_iter_value = default_max_iter if max_iter_text == '' else int(max_iter_text)
        except ValueError:
            warning_label.setText("Warning: Invalid iteration count entered.")
            warning_label.setVisible(True)
            return

        try:
            tolerance_value = default_tolerance if tolerance_text == '' else float(tolerance_text)
        except ValueError:
            warning_label.setText("Warning: Invalid tolerance entered.")
            warning_label.setVisible(True)
            return

        warning_label.setText("Warning: Relaxed iteration settings may impact accuracy.")

        if max_iter_value != default_max_iter:
            show_warning = True
        if not math.isclose(tolerance_value, default_tolerance, rel_tol=0.0, abs_tol=1e-15):
            show_warning = True

        warning_label.setVisible(show_warning)

    def clear_plasticity_warning(self):
        warning_label = getattr(self.tab, 'plasticity_warning_label', None)
        if warning_label is not None:
            warning_label.setVisible(False)

    def _update_skip_modes_combo(self, num_modes):
        """Update skip modes combo box."""
        values = [str(i) for i in range(num_modes + 1)]

        self.tab.skip_modes_combo.blockSignals(True)
        self.tab.skip_modes_combo.clear()
        self.tab.skip_modes_combo.addItems(values)
        self.tab.skip_modes_combo.setCurrentIndex(0)
        self.tab.skip_modes_combo.blockSignals(False)

        self.tab.skip_last_modes_combo.blockSignals(True)
        self.tab.skip_last_modes_combo.clear()
        self.tab.skip_last_modes_combo.addItems(values)
        self.tab.skip_last_modes_combo.setCurrentIndex(0)
        self.tab.skip_last_modes_combo.blockSignals(False)

        self.tab.skip_modes_label.setVisible(True)
        self.tab.skip_modes_combo.setVisible(True)
        self.tab.skip_last_modes_label.setVisible(True)
        self.tab.skip_last_modes_combo.setVisible(True)

    def on_skip_modes_changed(self, text):
        """Handle skip modes selection change."""
        try:
            _ = text  # signal payload not used; both combos are read directly

            first_text = self.tab.skip_modes_combo.currentText()
            last_text = self.tab.skip_last_modes_combo.currentText()
            if (first_text and not first_text.isdigit()) or (last_text and not last_text.isdigit()):
                return

            num_skipped_first = int(first_text) if first_text else 0
            num_skipped_last = int(last_text) if last_text else 0

            message = (
                f"\n[INFO] Skip Modes options are set to first={num_skipped_first}, "
                f"last={num_skipped_last}. "
                f"These modes will be excluded from the next calculation.\n"
            )

            total_modes = None
            for data_source in (
                self.tab.stress_data,
                self.tab.force_moment_data,
                self.tab.deformation_data,
                self.tab.modal_data,
            ):
                if data_source is not None:
                    total_modes = data_source.num_modes
                    break

            if total_modes is not None:
                modes_used = total_modes - num_skipped_first - num_skipped_last
                message += (
                    f"       - Modes to be used: {modes_used} "
                )
                if modes_used > 0:
                    first_mode = num_skipped_first + 1
                    last_mode = total_modes - num_skipped_last
                    message += (
                        f"(from mode {first_mode} to {last_mode})\n"
                    )
                else:
                    message += (
                        "(none; adjust skip values)\n"
                    )
            else:
                message += "\n"

            if not hasattr(self.tab, 'console_textbox') or self.tab.console_textbox is None:
                return

            scroll_bar = self.tab.console_textbox.verticalScrollBar()
            self.tab.console_textbox.append(message)
            if scroll_bar is not None:
                scroll_bar.setValue(scroll_bar.maximum())
        except (ValueError, TypeError) as e:
            self.tab.console_textbox.append(
                f"\n[DEBUG] Could not parse skip modes values. Error: {e}"
            )

    def _update_solve_button_state(self):
        """Enable/disable solve button based on loaded files and selected outputs."""
        # Core requirement: modal coordinates must always be loaded
        if not self.tab.coord_loaded:
            self.tab.solve_button.setEnabled(False)
            return

        # Check if any data source is loaded that can produce results
        has_any_data = (
            self.tab.stress_loaded or
            self.tab.deformation_loaded or
            self.tab.force_moment_loaded
        )
        if not has_any_data:
            self.tab.solve_button.setEnabled(False)
            return

        # Check if at least one enabled result output is selected
        result_outputs = [
            self.tab.max_principal_stress_checkbox,
            self.tab.min_principal_stress_checkbox,
            self.tab.von_mises_checkbox,
            self.tab.deformation_checkbox,
            self.tab.velocity_checkbox,
            self.tab.acceleration_checkbox,
            self.tab.force_moment_output_checkbox,
            self.tab.damage_index_checkbox,
            self.tab.plasticity_correction_checkbox
        ]
        
        output_selected = any(cb.isChecked() and cb.isEnabled() for cb in result_outputs)
        
        self.tab.solve_button.setEnabled(output_selected)

    def _hide_plot_tabs(self):
        """Hide all plot tabs."""
        self.tab.show_output_tab_widget.setTabVisible(
            self.tab.show_output_tab_widget.indexOf(self.tab.plot_modal_coords_tab), False
        )
        if self.tab.plot_max_over_time_tab is not None:
            self.tab.plot_max_over_time_tab.clear_plot()
            self.tab.show_output_tab_widget.setTabVisible(
                self.tab.show_output_tab_widget.indexOf(self.tab.plot_max_over_time_tab), False
            )
        if self.tab.plot_min_over_time_tab is not None:
            self.tab.plot_min_over_time_tab.clear_plot()
            self.tab.show_output_tab_widget.setTabVisible(
                self.tab.show_output_tab_widget.indexOf(self.tab.plot_min_over_time_tab), False
            )

    def _show_modal_coords_tab(self):
        """Show modal coordinates plot tab."""
        self.tab.show_output_tab_widget.setTabVisible(
            self.tab.show_output_tab_widget.indexOf(self.tab.plot_modal_coords_tab), True
        )
