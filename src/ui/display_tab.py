"""
Refactored Display Tab for 3D visualization.

This module provides the DisplayTab widget that handles 3D visualization of FEA
results using PyVista. The class has been refactored to use UI builders and
delegate complex logic to manager classes.
"""

import os
import time
import gc
import numpy as np
import pandas as pd
import pyvista as pv
import vtk

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QWidget

# Import builders and managers
from ui.builders.display_ui import DisplayTabUIBuilder
from core.visualization import VisualizationManager, AnimationManager, HotspotDetector
from ui.widgets.dialogs import HotspotDialog
from file_io.exporters import export_mesh_to_csv, export_apdl_ic
from utils.constants import NP_DTYPE


class DisplayTab(QWidget):
    """
    Refactored Display Tab for 3D visualization of FEA results.
    
    This class uses UI builders for construction and delegates complex logic
    to manager classes (VisualizationManager, AnimationManager, HotspotDetector).
    
    Signals:
        node_picked_signal: Emitted when a node is picked (int: node_id)
        time_point_update_requested: Emitted when time point update is needed
        animation_precomputation_requested: Emitted when animation precomputation is needed
    """
    
    # Signals
    node_picked_signal = pyqtSignal(int)
    time_point_update_requested = pyqtSignal(float, dict)
    animation_precomputation_requested = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize the Display Tab."""
        super().__init__(parent)
        
        # Managers for complex logic
        self.viz_manager = VisualizationManager()
        self.anim_manager = AnimationManager()
        self.hotspot_detector = HotspotDetector()
        
        # Build UI using builder
        builder = DisplayTabUIBuilder()
        layout, self.components = builder.build_complete_layout(self)
        self.setLayout(layout)
        
        # Store commonly used components as direct attributes
        self._setup_component_references()
        
        # State tracking
        self.current_mesh = None
        self.current_actor = None
        self.camera_state = None
        self.camera_widget = None
        self.hover_annotation = None
        self.hover_observer = None
        self.last_hover_time = 0  # For frame rate throttling
        self.data_column = "Result"  # Track current data column name
        self.anim_timer = None
        self.time_text_actor = None
        self.current_anim_time = 0.0
        self.animation_paused = False
        self.temp_solver = None
        self.time_values = None
        self.original_node_coords = None
        self.last_valid_deformation_scale = 1.0
        
        # Hotspot and picking state
        self.highlight_actor = None
        self.box_widget = None
        self.hotspot_dialog = None
        self.is_point_picking_active = False
        
        # Node tracking state
        self.target_node_index = None
        self.target_node_id = None
        self.target_node_label_actor = None
        self.label_point_data = None
        self.marker_poly = None
        self.target_node_marker_actor = None
        self.last_goto_node_id = None
        self.freeze_tracked_node = False
        self.freeze_baseline = None
        
        # Connect signals
        self._connect_signals()
    
    def _setup_component_references(self):
        """Create direct references to frequently used components."""
        # File controls
        self.file_button = self.components['file_button']
        self.file_path = self.components['file_path']
        
        # Visualization controls
        self.plotter = self.components['plotter']
        self.point_size = self.components['point_size']
        self.scalar_min_spin = self.components['scalar_min_spin']
        self.scalar_max_spin = self.components['scalar_max_spin']
        self.deformation_scale_label = self.components['deformation_scale_label']
        self.deformation_scale_edit = self.components['deformation_scale_edit']
        
        # Time point controls
        self.time_point_spinbox = self.components['time_point_spinbox']
        self.update_time_button = self.components['update_time_button']
        self.save_time_button = self.components['save_time_button']
        self.extract_ic_button = self.components['extract_ic_button']
        self.time_point_group = self.components['time_point_group']
        
        # Animation controls
        self.anim_interval_spin = self.components['anim_interval_spin']
        self.anim_start_spin = self.components['anim_start_spin']
        self.anim_end_spin = self.components['anim_end_spin']
        self.play_button = self.components['play_button']
        self.pause_button = self.components['pause_button']
        self.stop_button = self.components['stop_button']
        self.time_step_mode_combo = self.components['time_step_mode_combo']
        self.custom_step_spin = self.components['custom_step_spin']
        self.actual_interval_spin = self.components['actual_interval_spin']
        self.save_anim_button = self.components['save_anim_button']
        self.anim_group = self.components['anim_group']
    
    def set_plotting_handler(self, plotting_handler):
        """Set the plotting handler for this display tab."""
        self.plotting_handler = plotting_handler

    def _connect_signals(self):
        """Connect UI signals to their handlers."""
        # File controls
        self.file_button.clicked.connect(self.load_file)
        
        # Visualization controls
        self.point_size.valueChanged.connect(self.update_point_size)
        self.scalar_min_spin.valueChanged.connect(self._update_scalar_range)
        self.scalar_max_spin.valueChanged.connect(self._update_scalar_range)
        self.scalar_min_spin.valueChanged.connect(
            lambda v: self.scalar_max_spin.setMinimum(v)
        )
        self.scalar_max_spin.valueChanged.connect(
            lambda v: self.scalar_min_spin.setMaximum(v)
        )
        self.deformation_scale_edit.editingFinished.connect(
            self._validate_deformation_scale
        )
        
        # Time point controls
        self.update_time_button.clicked.connect(self.update_time_point_results)
        self.save_time_button.clicked.connect(self.save_time_point_results)
        self.extract_ic_button.clicked.connect(self.extract_initial_conditions)
        
        # Animation controls
        self.anim_start_spin.valueChanged.connect(self._update_anim_range_min)
        self.anim_end_spin.valueChanged.connect(self._update_anim_range_max)
        self.play_button.clicked.connect(self.start_animation)
        self.pause_button.clicked.connect(self.pause_animation)
        self.stop_button.clicked.connect(self.stop_animation)
        self.time_step_mode_combo.currentTextChanged.connect(
            self._update_step_spinbox_state
        )
        self.save_anim_button.clicked.connect(self.save_animation)
        
        # Context menu
        self.plotter.customContextMenuRequested.connect(self.show_context_menu)
    
    @pyqtSlot(object)
    def _setup_initial_view(self, initial_data):
        """
        Setup initial view with loaded data.
        
        Args:
            initial_data: Tuple of (time_values, node_coords, node_ids, deformation_loaded)
        """
        time_values, node_coords, df_node_ids, deformation_is_loaded = initial_data
        
        # Store data
        self.time_values = time_values
        self.original_node_coords = node_coords
        
        # Update UI controls with time range
        self._update_time_controls(time_values)
        
        # Update deformation scale control
        self._update_deformation_controls(deformation_is_loaded)
        
        # Create and display initial mesh
        if node_coords is not None:
            mesh = self.viz_manager.create_mesh_from_coords(
                node_coords, df_node_ids
            )
            self.current_mesh = mesh
            self.update_visualization()
            self.plotter.reset_camera()
    
    def _update_time_controls(self, time_values):
        """Update time-related UI controls with time range."""
        min_time, max_time = np.min(time_values), np.max(time_values)
        
        # Time point spinbox
        self.time_point_spinbox.setRange(min_time, max_time)
        self.time_point_spinbox.setValue(min_time)
        
        # Compute average sampling interval
        if len(time_values) > 1:
            avg_dt = np.mean(np.diff(time_values))
        else:
            avg_dt = 1.0
        self.time_point_spinbox.setSingleStep(avg_dt)
        
        # Animation time range
        self.anim_start_spin.setRange(min_time, max_time)
        self.anim_end_spin.setRange(min_time, max_time)
        self.anim_start_spin.setValue(min_time)
        self.anim_end_spin.setValue(max_time)
        self.actual_interval_spin.setMaximum(len(time_values))
        self.actual_interval_spin.setValue(1)
        
        # Show controls
        self.anim_group.setVisible(True)
        self.time_point_group.setVisible(True)
        self.deformation_scale_label.setVisible(True)
        self.deformation_scale_edit.setVisible(True)
    
    def _update_deformation_controls(self, deformation_loaded):
        """Update deformation scale controls based on availability."""
        if deformation_loaded:
            self.deformation_scale_edit.setEnabled(True)
            self.deformation_scale_edit.setText(
                str(self.last_valid_deformation_scale)
            )
        else:
            self.deformation_scale_edit.setEnabled(False)
            self.deformation_scale_edit.setText("0")
    
    def load_file(self):
        """Open file dialog and load visualization file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, 'Open Visualization File', '', 'CSV Files (*.csv)'
        )
        if file_name:
            self._visualize_data(file_name)
    
    def _visualize_data(self, filename):
        """
        Load and visualize data from file.
        
        Args:
            filename: Path to the CSV file to load.
        """
        try:
            df = pd.read_csv(filename)
            
            # Extract coordinates
            if not {'X', 'Y', 'Z'}.issubset(df.columns):
                QMessageBox.warning(
                    self, "Invalid File",
                    "File must contain X, Y, Z coordinate columns."
                )
                return
            
            coords = df[['X', 'Y', 'Z']].to_numpy()
            
            # Extract node IDs if available
            node_ids = None
            if 'NodeID' in df.columns:
                node_ids = df['NodeID'].to_numpy()
            
            # Create mesh
            mesh = self.viz_manager.create_mesh_from_coords(coords, node_ids)
            
            # Add scalar data (all remaining columns)
            scalar_cols = [
                col for col in df.columns 
                if col not in ['X', 'Y', 'Z', 'NodeID', 'Index']
            ]
            
            if scalar_cols:
                # Use first scalar column as active
                scalar_name = scalar_cols[0]
                scalar_data = df[scalar_name].to_numpy()
                mesh = self.viz_manager.update_mesh_scalars(
                    mesh, scalar_data, scalar_name
                )
                self.data_column = scalar_name
            
            self.current_mesh = mesh
            self.file_path.setText(filename)
            self.update_visualization()
            self.plotter.reset_camera()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Error Loading File",
                f"Failed to load file:\n{str(e)}"
            )
    
    def update_visualization(self):
        """Update the 3D visualization with current mesh."""
        if self.current_mesh is None:
            return
        
        # Clear existing actors
        self.plotter.clear()
        
        # Update data column name from active scalars
        if self.current_mesh.active_scalars_name:
            self.data_column = self.current_mesh.active_scalars_name
        
        # Add mesh to plotter
        self.current_actor = self.plotter.add_mesh(
            self.current_mesh,
            scalars=self.current_mesh.active_scalars_name,
            point_size=self.point_size.value(),
            render_points_as_spheres=True,
            show_scalar_bar=True,
            cmap='jet',
            below_color='gray',
            above_color='magenta',
            scalar_bar_args={
                'title': self.data_column,
                'fmt': '%.4f',
                'position_x': 0.04,  # Left edge (5% from left)
                'position_y': 0.35,  # Vertical position (35% from bottom)
                'width': 0.05,  # Width of the scalar bar (5% of window)
                'height': 0.5,  # Height of the scalar bar (50% of window)
                'vertical': True,  # Force vertical orientation
                'title_font_size': 14,
                'label_font_size': 12,
                'shadow': True,  # Optional: Add shadow for readability
                'n_labels': 10  # Number of labels to display
            }
        )
        
        # Update scalar range if set
        if (self.scalar_min_spin.value() != self.scalar_max_spin.value()):
            self.current_actor.mapper.scalar_range = (
                self.scalar_min_spin.value(),
                self.scalar_max_spin.value()
            )
        
        # Setup hover annotation
        self._setup_hover_annotation()
        
        # Add camera widget if not present
        if not self.camera_widget:
            self.camera_widget = self.plotter.add_camera_orientation_widget()
            self.camera_widget.EnabledOn()
        
        self.plotter.reset_camera()
    
    def _setup_hover_annotation(self):
        """Set up hover callback to display node ID and value."""
        if not self.current_mesh or 'NodeID' not in self.current_mesh.array_names:
            return
        
        # Clean up previous hover elements
        self._clear_hover_elements()
        
        # Create new annotation
        self.hover_annotation = self.plotter.add_text(
            "", position='upper_right', font_size=8,
            color='black', name='hover_annotation'
        )
        
        # Create picker and callback with throttling
        picker = vtk.vtkPointPicker()
        picker.SetTolerance(0.01)
        
        def hover_callback(obj, event):
            now = time.time()
            if (now - self.last_hover_time) < 0.033:  # 30 FPS throttle
                return
            
            iren = obj
            pos = iren.GetEventPosition()
            picker.Pick(pos[0], pos[1], 0, self.plotter.renderer)
            point_id = picker.GetPointId()
            
            if point_id != -1 and point_id < self.current_mesh.n_points:
                node_id = self.current_mesh['NodeID'][point_id]
                value = self.current_mesh[self.data_column][point_id]
                self.hover_annotation.SetText(2, f"Node ID: {node_id}\n{self.data_column}: {value:.5f}")
            else:
                self.hover_annotation.SetText(2, "")
            
            iren.GetRenderWindow().Render()
            self.last_hover_time = now
        
        # Add and track new observer
        self.hover_observer = self.plotter.iren.add_observer('MouseMoveEvent', hover_callback)
    
    def _clear_hover_elements(self):
        """Dedicated hover element cleanup."""
        if self.hover_annotation:
            self.plotter.remove_actor(self.hover_annotation)
            self.hover_annotation = None
        
        if self.hover_observer:
            self.plotter.iren.remove_observer(self.hover_observer)
            self.hover_observer = None
    
    def update_point_size(self):
        """Update the point size of the displayed mesh."""
        if self.current_actor is not None:
            # Clear and re-setup hover annotation for updated point size
            self._clear_hover_elements()
            self.current_actor.GetProperty().SetPointSize(
                self.point_size.value()
            )
            self._setup_hover_annotation()
            self.plotter.render()
    
    def _update_scalar_range(self):
        """Update the scalar range of the color map."""
        if self.current_actor is not None:
            self.current_actor.mapper.scalar_range = (
                self.scalar_min_spin.value(),
                self.scalar_max_spin.value()
            )
            self.plotter.render()
    
    def _validate_deformation_scale(self):
        """Validate deformation scale factor input."""
        text = self.deformation_scale_edit.text()
        try:
            value = float(text)
            self.last_valid_deformation_scale = value
        except ValueError:
            # Revert to last valid value
            self.deformation_scale_edit.setText(
                str(self.last_valid_deformation_scale)
            )
    
    def _update_anim_range_min(self, value):
        """Ensure animation end time is not less than start time."""
        self.anim_end_spin.setMinimum(value)
    
    def _update_anim_range_max(self, value):
        """Ensure animation start time does not exceed end time."""
        self.anim_start_spin.setMaximum(value)
    
    def _update_step_spinbox_state(self, text):
        """Toggle between custom and actual time step modes."""
        if text == "Custom Time Step":
            self.custom_step_spin.setVisible(True)
            self.actual_interval_spin.setVisible(False)
        else:
            self.custom_step_spin.setVisible(False)
            self.actual_interval_spin.setVisible(True)
    
    def update_time_point_results(self):
        """Request time point calculation and update visualization."""
        # Get main tab (solver tab) to check which outputs are selected
        main_tab = self.window().solver_tab
        if main_tab is None:
            QMessageBox.warning(
                self, "Not Ready",
                "Solver tab not initialized."
            )
            return
        
        # Gather options
        options = {
            'compute_von_mises': main_tab.von_mises_checkbox.isChecked(),
            'compute_max_principal': main_tab.max_principal_stress_checkbox.isChecked(),
            'compute_min_principal': main_tab.min_principal_stress_checkbox.isChecked(),
            'compute_deformation_contour': main_tab.deformation_checkbox.isChecked(),
            'compute_velocity': main_tab.velocity_checkbox.isChecked(),
            'compute_acceleration': main_tab.acceleration_checkbox.isChecked(),
            'display_deformed_shape': main_tab.deformations_checkbox.isChecked(),
            'include_steady': main_tab.steady_state_checkbox.isChecked(),
            'skip_n_modes': int(main_tab.skip_modes_combo.currentText()) if main_tab.skip_modes_combo.currentText() else 0,
            'scale_factor': float(self.deformation_scale_edit.text())
        }
        
        selected_time = self.time_point_spinbox.value()
        
        # Emit signal to request computation
        print(f"DisplayTab: Requesting time point update for time {selected_time}")
        self.time_point_update_requested.emit(selected_time, options)
    
    def save_time_point_results(self):
        """Save currently displayed results to CSV."""
        if self.current_mesh is None:
            QMessageBox.warning(self, "No Data", "No visualization data to save.")
            return
        
        active_scalar_name = self.current_mesh.active_scalars_name
        if not active_scalar_name:
            QMessageBox.warning(
                self, "No Active Data",
                "The current mesh does not have an active scalar field to save."
            )
            return
        
        # Create default filename
        base_name = active_scalar_name.split(' ')[0]
        selected_time = self.time_point_spinbox.value()
        default_filename = f"{base_name}_T_{selected_time:.5f}.csv".replace('.', '_')
        
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Time Point Results", default_filename, "CSV Files (*.csv)"
        )
        
        if file_name:
            try:
                export_mesh_to_csv(
                    self.current_mesh, active_scalar_name, file_name
                )
                QMessageBox.information(
                    self, "Save Successful",
                    f"Time point results saved successfully to:\n{file_name}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Save Error",
                    f"An error occurred while saving the file: {e}"
                )
    
    def extract_initial_conditions(self):
        """Extract velocity initial conditions and export to APDL format."""
        # Check if velocity data is available in the current mesh
        if self.current_mesh is None:
            QMessageBox.warning(
                self, "No Data",
                "No visualization data available. Please compute velocity at a time point first."
            )
            return
        
        # Check if velocity components are in the mesh
        if not all(key in self.current_mesh.array_names for key in ['vel_x', 'vel_y', 'vel_z']):
            QMessageBox.warning(
                self, "Missing Velocity Data",
                "Velocity components not found in current mesh.\n\n"
                "Please compute velocity for a time point first using the Update button."
            )
            return
        
        # Get node IDs
        if 'NodeID' not in self.current_mesh.array_names:
            QMessageBox.warning(
                self, "Missing Node IDs",
                "Node IDs not found in mesh. Cannot export initial conditions."
            )
            return
        
        # Extract data
        node_ids = self.current_mesh['NodeID']
        vel_x = self.current_mesh['vel_x'].flatten()
        vel_y = self.current_mesh['vel_y'].flatten()
        vel_z = self.current_mesh['vel_z'].flatten()
        
        # Open file dialog
        from PyQt5.QtWidgets import QFileDialog
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Initial Conditions",
            "initial_conditions.inp",
            "APDL Files (*.inp);;All Files (*)"
        )
        
        if file_name:
            try:
                export_apdl_ic(node_ids, vel_x, vel_y, vel_z, file_name)
                QMessageBox.information(
                    self, "Export Successful",
                    f"Initial conditions exported successfully to:\n{file_name}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error",
                    f"Failed to export initial conditions:\n{str(e)}"
                )
    
    def start_animation(self):
        """Start animation playback or resume if paused."""
        if self.current_mesh is None:
            QMessageBox.warning(
                self, "No Data",
                "Please load or initialize the mesh before animating."
            )
            return
        
        # Preserve tracked node state before cleanup
        tracked_node_index = self.target_node_index
        tracked_node_id = self.target_node_id
        is_frozen = self.freeze_tracked_node
        
        # Hide marker/label if frozen mode is active
        if tracked_node_index is not None and is_frozen:
            if self.target_node_marker_actor:
                self.target_node_marker_actor.SetVisibility(False)
            if self.target_node_label_actor:
                self.target_node_label_actor.SetVisibility(False)
            self.plotter.render()
        
        # Handle resume logic
        if self.animation_paused:
            if self.anim_manager.precomputed_scalars is None:
                QMessageBox.warning(
                    self, "Resume Error",
                    "Cannot resume. Precomputed data is missing. Please stop and start again."
                )
                self.stop_animation()
                return
            
            print("Resuming animation...")
            self.animation_paused = False
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.play_button.setEnabled(False)
            self.deformation_scale_edit.setEnabled(False)
            
            if self.anim_timer:
                self.anim_timer.start(self.anim_interval_spin.value())
            else:
                self.anim_timer = QTimer(self)
                self.anim_timer.timeout.connect(self._animate_frame)
                self.anim_timer.start(self.anim_interval_spin.value())
            return
        
        # Start fresh
        self.stop_animation()
        self.play_button.setEnabled(False)
        
        # Restore tracked node state
        if tracked_node_index is not None:
            self.target_node_index = tracked_node_index
            self.target_node_id = tracked_node_id
            self.freeze_tracked_node = is_frozen
            
            # Set freeze baseline
            if self.freeze_tracked_node and self.original_node_coords is not None:
                if self.current_mesh is not None and self.current_mesh.n_points > tracked_node_index:
                    self.freeze_baseline = self.current_mesh.points[self.target_node_index].copy()
                else:
                    print("Warning: Cannot set freeze_baseline")
                    self.freeze_tracked_node = False
        
        # Get animation time steps
        anim_times, anim_indices, error_msg = self._get_animation_time_steps()
        if error_msg:
            QMessageBox.warning(self, "Animation Setup Error", error_msg)
            return
        if anim_times is None or len(anim_times) == 0:
            QMessageBox.warning(self, "Animation Setup Error", "No time steps generated.")
            return
        
        # Gather UI selections
        main_tab = self.window().solver_tab

        # Count selected outputs
        selected_outputs = [
            main_tab.von_mises_checkbox.isChecked(),
            main_tab.max_principal_stress_checkbox.isChecked(),
            main_tab.min_principal_stress_checkbox.isChecked(),
            main_tab.deformation_checkbox.isChecked(),
            main_tab.velocity_checkbox.isChecked(),
            main_tab.acceleration_checkbox.isChecked()
        ]
        num_selected = sum(selected_outputs)

        if num_selected == 0:
            QMessageBox.warning(self, "No Selection", "No valid output is selected for animation.")
            self.play_button.setEnabled(True)
            return
        elif num_selected > 1:
            QMessageBox.warning(
                self, "Error - Multiple Selections",
                "Please select only one output type for animation playback.\n\n"
                "Animation currently supports displaying one output at a time for clarity.\n"
                "You can switch between different outputs using the checkboxes and run separate animations."
            )
            self.play_button.setEnabled(True)
            return
        
        # Gather parameters
        params = {
            'compute_von_mises': main_tab.von_mises_checkbox.isChecked(),
            'compute_max_principal': main_tab.max_principal_stress_checkbox.isChecked(),
            'compute_min_principal': main_tab.min_principal_stress_checkbox.isChecked(),
            'compute_deformation_anim': main_tab.deformations_checkbox.isChecked(),
            'compute_deformation_contour': main_tab.deformation_checkbox.isChecked(),
            'compute_velocity': main_tab.velocity_checkbox.isChecked(),
            'compute_acceleration': main_tab.acceleration_checkbox.isChecked(),
            'include_steady': main_tab.steady_state_checkbox.isChecked(),
            'skip_n_modes': int(main_tab.skip_modes_combo.currentText()) if main_tab.skip_modes_combo.currentText() else 0,
            'scale_factor': float(self.deformation_scale_edit.text()),
            'anim_indices': anim_indices
        }
        
        # Show wait cursor and request precomputation
        from PyQt5.QtWidgets import QApplication
        QApplication.setOverrideCursor(Qt.WaitCursor)
        print("DisplayTab: Delegating animation precomputation...")
        self.animation_precomputation_requested.emit(params)
    
    def _get_animation_time_steps(self):
        """
        Determine animation time steps based on user settings.
        
        Returns:
            tuple: (anim_times, anim_indices, error_message)
        """
        if self.time_values is None or len(self.time_values) == 0:
            return None, None, "Time values not loaded."
        
        start_time = self.anim_start_spin.value()
        end_time = self.anim_end_spin.value()
        
        if start_time >= end_time:
            return None, None, "Animation start time must be less than end time."
        
        anim_times_list = []
        anim_indices_list = []
        
        if self.time_step_mode_combo.currentText() == "Custom Time Step":
            step = self.custom_step_spin.value()
            if step <= 0:
                return None, None, "Custom time step must be positive."
            
            current_t = start_time
            last_added_idx = -1
            
            while current_t <= end_time:
                idx = np.argmin(np.abs(self.time_values - current_t))
                
                if (self.time_values[idx] >= start_time and 
                    self.time_values[idx] <= end_time and 
                    idx != last_added_idx):
                    anim_indices_list.append(idx)
                    anim_times_list.append(self.time_values[idx])
                    last_added_idx = idx
                
                if current_t + step <= current_t:
                    print("Warning: Custom time step too small, breaking loop.")
                    break
                current_t += step
            
            # Ensure end point is included
            end_idx = np.argmin(np.abs(self.time_values - end_time))
            if (self.time_values[end_idx] >= start_time and 
                self.time_values[end_idx] <= end_time):
                if not anim_indices_list or end_idx != anim_indices_list[-1]:
                    anim_indices_list.append(end_idx)
                    anim_times_list.append(self.time_values[end_idx])
        
        else:  # "Actual Data Time Steps"
            nth = self.actual_interval_spin.value()
            if nth <= 0:
                return None, None, "Actual data step interval must be positive."
            
            valid_indices = np.where(
                (self.time_values >= start_time) & (self.time_values <= end_time)
            )[0]
            
            if len(valid_indices) == 0:
                return None, None, "No data time steps found in specified range."
            
            selected_indices = valid_indices[::nth].tolist()
            
            # Ensure first and last points included
            first_idx = valid_indices[0]
            if first_idx not in selected_indices:
                selected_indices.insert(0, first_idx)
            
            last_idx = valid_indices[-1]
            if not selected_indices or last_idx != selected_indices[-1]:
                selected_indices.append(last_idx)
            
            anim_indices_list = selected_indices
            anim_times_list = self.time_values[anim_indices_list].tolist()
        
        if not anim_times_list:
            return None, None, "No animation frames generated."
        
        # Remove duplicates while preserving order
        unique_indices, order_indices = np.unique(anim_indices_list, return_index=True)
        final_indices = unique_indices[np.argsort(order_indices)]
        final_times = self.time_values[final_indices]
        
        return np.array(final_times), np.array(final_indices, dtype=int), None
    
    def _estimate_animation_ram(self, num_nodes, num_anim_steps, include_deformation):
        """Estimate peak RAM needed for animation precomputation in GB."""
        element_size = np.dtype(NP_DTYPE).itemsize
        
        # Intermediate stress arrays (6 components)
        normal_stress_ram = num_nodes * 6 * num_anim_steps * element_size
        
        # Final scalar array
        scalar_ram = num_nodes * 1 * num_anim_steps * element_size
        
        # Deformation arrays if needed
        intermediate_displacement_ram = 0
        final_coordinate_ram = 0
        if include_deformation:
            intermediate_displacement_ram = num_nodes * 3 * num_anim_steps * element_size
            final_coordinate_ram = num_nodes * 3 * num_anim_steps * element_size
        
        total_ram_bytes = (normal_stress_ram + scalar_ram + 
                          intermediate_displacement_ram + final_coordinate_ram)
        total_ram_bytes *= 1.20  # 20% safety buffer
        
        return total_ram_bytes / (1024 ** 3)
    
    def pause_animation(self):
        """Pause animation playback."""
        if self.anim_timer is not None and self.anim_timer.isActive():
            self.anim_timer.stop()
            self.animation_paused = True
            self.play_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            
            # Show marker/label when paused if tracking and frozen
            if self.target_node_index is not None and self.freeze_tracked_node:
                if self.target_node_marker_actor:
                    self.target_node_marker_actor.SetVisibility(True)
                if self.target_node_label_actor:
                    self.target_node_label_actor.SetVisibility(True)
                self.plotter.render()
            
            print("\nAnimation paused.")
        else:
            print("\nPause command ignored: Animation timer not active.")
    
    def stop_animation(self):
        """Stop animation, release precomputed data, and reset state."""
        # Check if there's anything to stop
        is_stoppable = (self.anim_timer is not None or 
                       self.anim_manager.precomputed_scalars is not None)
        
        # Clear markers
        self._clear_goto_node_markers()
        
        if is_stoppable:
            print("\nStopping animation and releasing resources...")
        
        # Stop timer
        if self.anim_timer is not None:
            self.anim_timer.stop()
            try:
                self.anim_timer.timeout.disconnect(self._animate_frame)
            except TypeError:
                pass
            self.anim_timer = None
        
        # Release precomputed data
        if self.anim_manager.precomputed_scalars is not None:
            print("Released precomputed scalars.")
        self.anim_manager.reset()
        gc.collect()
        
        # Reset state
        self.current_anim_frame_index = 0
        self.animation_paused = False
        self.is_deformation_included_in_anim = False
        
        # Reset UI
        self.deformation_scale_edit.setEnabled(True)
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.save_anim_button.setEnabled(False)
        
        # Remove time text actor
        if self.time_text_actor is not None:
            self.plotter.remove_actor(self.time_text_actor)
            self.time_text_actor = None
        
        # Reset mesh to original state
        if self.current_mesh and self.original_node_coords is not None:
            print("Resetting mesh to original coordinates.")
            try:
                if self.current_mesh.n_points == self.original_node_coords.shape[0]:
                    self.current_mesh.points = self.original_node_coords.copy()
                    try:
                        self.current_mesh.points_modified()
                    except AttributeError:
                        self.current_mesh.GetPoints().Modified()
                    self.plotter.render()
            except Exception as e:
                print(f"Error resetting mesh points: {e}")
        
        if is_stoppable:
            print("\nAnimation stopped.")
    
    def _animate_frame(self, update_index=True):
        """Update display using next precomputed animation frame."""
        if (self.anim_manager.precomputed_scalars is None or 
            self.anim_manager.precomputed_anim_times is None):
            print("Animation frame skipped: Precomputed data not available.")
            self.stop_animation()
            return
        
        if not self._update_mesh_for_frame(self.current_anim_frame_index):
            print(f"Animation frame skipped: Failed to update mesh.")
            self.stop_animation()
            return
        
        self.plotter.render()
        
        if update_index:
            num_frames = self.anim_manager.get_num_frames()
            if num_frames > 0:
                self.current_anim_frame_index += 1
                if self.current_anim_frame_index >= num_frames:
                    self.current_anim_frame_index = 0  # Loop
            else:
                self.stop_animation()
    
    def _update_mesh_for_frame(self, frame_index):
        """Update mesh data for given animation frame."""
        if (self.anim_manager.precomputed_scalars is None or 
            self.anim_manager.precomputed_anim_times is None or 
            self.current_mesh is None):
            return False
        
        num_frames = self.anim_manager.get_num_frames()
        if frame_index < 0 or frame_index >= num_frames:
            return False
        
        try:
            # Get frame data
            scalars, coords, time_val = self.anim_manager.get_frame_data(frame_index)
            
            # Update coordinates
            if coords is not None:
                current_coords = coords.copy()
                
                # Apply freeze node tracking
                if self.freeze_tracked_node and self.freeze_baseline is not None:
                    tracked_now = current_coords[self.target_node_index]
                    shift = tracked_now - self.freeze_baseline
                    if np.any(shift):
                        current_coords -= shift
                        if self.marker_poly is not None:
                            self.marker_poly.points[:] -= shift
                            self.marker_poly.Modified()
                
                self.current_mesh.points = current_coords
                try:
                    self.current_mesh.points_modified()
                except AttributeError:
                    self.current_mesh.GetPoints().Modified()
            
            # Update scalars
            data_column = self.anim_manager.data_column_name
            self.current_mesh[data_column] = scalars
            if self.current_mesh.active_scalars_name != data_column:
                self.current_mesh.set_active_scalars(data_column)
            
            # Update time text
            time_text = f"Time: {time_val:.5f} s"
            if self.time_text_actor is not None:
                try:
                    self.time_text_actor.SetInput(time_text)
                except:
                    self.plotter.remove_actor(self.time_text_actor, render=False)
                    self.time_text_actor = self.plotter.add_text(
                        time_text, position=(0.8, 0.9), viewport=False, font_size=10
                    )
            else:
                self.time_text_actor = self.plotter.add_text(
                    time_text, position=(0.8, 0.9), viewport=False, font_size=10
                )
            
            # Update tracked node marker position
            if self.target_node_index is not None:
                new_coords = self.current_mesh.points[self.target_node_index]
                if not self.freeze_tracked_node and self.target_node_label_actor and self.label_point_data:
                    self.label_point_data.points[0, :] = new_coords
                    self.label_point_data.Modified()
                if self.target_node_marker_actor and self.marker_poly:
                    self.marker_poly.points[0] = new_coords
                    self.marker_poly.Modified()
            
            return True
            
        except Exception as e:
            print(f"Error updating mesh for frame {frame_index}: {e}")
            return False
    
    def save_animation(self):
        """Save animation to file (MP4 or GIF)."""
        if self.anim_manager.precomputed_scalars is None:
            QMessageBox.warning(
                self, "No Animation",
                "No animation has been precomputed. Please play the animation first."
            )
            return
        
        # Get save path and format
        file_path, file_format = self._get_save_path_and_format()
        if not file_path:
            return
        
        # Save animation
        try:
            success = self._write_animation_to_file(file_path, file_format)
            if success:
                QMessageBox.information(
                    self, "Save Successful",
                    f"Animation saved successfully to:\n{file_path}"
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Save Error",
                f"Failed to save animation:\n{str(e)}"
            )
    
    def _get_save_path_and_format(self):
        """Open file dialog to choose save location and format."""
        default_dir = ""
        if hasattr(self.window(), 'project_directory') and self.window().project_directory:
            default_dir = self.window().project_directory
        
        file_name, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Animation",
            default_dir,
            "MP4 Video (*.mp4);;Animated GIF (*.gif)",
            "MP4 Video (*.mp4)"
        )
        
        if not file_name:
            return None, None
        
        if "MP4" in selected_filter:
            file_format = "MP4"
            if not file_name.lower().endswith(".mp4"):
                file_name += ".mp4"
        elif "GIF" in selected_filter:
            file_format = "GIF"
            if not file_name.lower().endswith(".gif"):
                file_name += ".gif"
        else:
            QMessageBox.warning(
                self, "Cannot Determine Format",
                "Could not determine file format. Please use .mp4 or .gif extension."
            )
            return None, None
        
        return file_name, file_format
    
    def _write_animation_to_file(self, file_path, file_format):
        """Write animation frames to file."""
        import imageio
        from PyQt5.QtWidgets import QProgressDialog
        
        num_frames = self.anim_manager.get_num_frames()
        fps = 1000.0 / self.anim_interval_spin.value()
        
        print(f"Saving {num_frames} frames to '{file_path}' as {file_format} at {fps:.2f} FPS.")
        
        progress = QProgressDialog(
            "Saving animation frames...", "Cancel", 0, num_frames, self.window()
        )
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Saving Animation")
        progress.setMinimumDuration(1000)
        
        writer_kwargs = {'fps': fps, 'macro_block_size': None}
        if file_format == 'MP4':
            writer_kwargs.update({'pixelformat': 'yuv420p', 'quality': 7})
        else:  # GIF
            writer_kwargs.update({'loop': 0, 'palettesize': 256})
        
        writer = imageio.get_writer(file_path, format=file_format, mode='I', **writer_kwargs)
        
        try:
            for i in range(num_frames):
                if progress.wasCanceled():
                    print("Animation save cancelled by user.")
                    return False
                
                # Update mesh for this frame
                if not self._update_mesh_for_frame(i):
                    print(f"Failed to update frame {i}")
                    continue
                
                self.plotter.render()
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
                time.sleep(0.01)
                
                # Capture screenshot
                frame_image = self.plotter.screenshot(
                    transparent_background=False, 
                    return_img=True
                )
                if frame_image is not None:
                    writer.append_data(frame_image)
                
                progress.setValue(i + 1)
            
            writer.close()
            progress.setValue(num_frames)
            print(f"Animation saved successfully to {file_path}")
            return True
            
        except Exception as e:
            print(f"Error during animation save: {e}")
            if writer:
                writer.close()
            raise
        finally:
            progress.close()
    
    def _clear_goto_node_markers(self):
        """Remove all actors and reset state for 'Go To Node' feature."""
        if self.target_node_marker_actor:
            self.plotter.remove_actor(self.target_node_marker_actor)
        if self.target_node_label_actor:
            self.plotter.remove_actor(self.target_node_label_actor)
        
        self.target_node_index = None
        self.target_node_id = None
        self.marker_poly = None
        self.target_node_marker_actor = None
        self.target_node_label_actor = None
        self.freeze_tracked_node = False
        self.freeze_baseline = None
    
    def show_context_menu(self, position):
        """Create and display the right-click context menu."""
        if self.current_mesh is None:
            return
        
        from PyQt5.QtWidgets import QMenu, QWidgetAction
        from PyQt5.QtGui import QCursor
        context_menu = QMenu(self)
        
        context_menu.setStyleSheet("""
            QMenu {
                background-color: #e7f0fd;
                color: black;
                border: 1px solid #5b9bd5;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 5px 25px 5px 20px;
                margin: 2px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #cce4ff;
                color: black;
            }
            QMenu::item:disabled {
                color: #808080;
                background-color: transparent;
            }
            QMenu::separator {
                height: 1px;
                background-color: #5b9bd5;
                margin: 5px 0px;
            }
        """)
        
        title_style = "font-weight: bold; color: #333; text-decoration: underline; padding: 4px 0px 6px 7px;"
        
        # Selection Tools section
        from PyQt5.QtWidgets import QLabel, QAction
        box_title_label = QLabel("Selection Tools")
        box_title_label.setStyleSheet(title_style)
        box_title_action = QWidgetAction(context_menu)
        box_title_action.setDefaultWidget(box_title_label)
        context_menu.addAction(box_title_action)
        
        # Toggle box
        box_action_text = "Remove Selection Box" if self.box_widget else "Add Selection Box"
        toggle_box_action = QAction(box_action_text, self)
        toggle_box_action.triggered.connect(self.toggle_selection_box)
        context_menu.addAction(toggle_box_action)
        
        # Pick box center
        pick_action = QAction("Pick Box Center", self)
        pick_action.setCheckable(True)
        pick_action.setChecked(self.is_point_picking_active)
        pick_action.setEnabled(self.current_mesh is not None)
        pick_action.triggered.connect(self.toggle_point_picking_mode)
        context_menu.addAction(pick_action)
        
        context_menu.addSeparator()
        
        # Hotspot Analysis section
        hotspot_title_label = QLabel("Hotspot Analysis")
        hotspot_title_label.setStyleSheet(title_style)
        hotspot_title_action = QWidgetAction(context_menu)
        hotspot_title_action.setDefaultWidget(hotspot_title_label)
        context_menu.addAction(hotspot_title_action)
        
        # Find hotspots
        hotspot_action = QAction("Find Hotspots (on current view)", self)
        hotspot_action.setEnabled(
            self.current_mesh and self.current_mesh.active_scalars is not None
        )
        hotspot_action.triggered.connect(self._find_hotspots_on_view)
        context_menu.addAction(hotspot_action)
        
        # Find in box
        find_in_box_action = QAction("Find Hotspots in Selection", self)
        find_in_box_action.setEnabled(self.box_widget is not None)
        find_in_box_action.triggered.connect(self.find_hotspots_in_box)
        context_menu.addAction(find_in_box_action)
        
        context_menu.addSeparator()
        
        # Point-Based Analysis section
        point_analysis_title_label = QLabel("Point-Based Analysis")
        point_analysis_title_label.setStyleSheet(title_style)
        point_analysis_title_action = QWidgetAction(context_menu)
        point_analysis_title_action.setDefaultWidget(point_analysis_title_label)
        context_menu.addAction(point_analysis_title_action)
        
        # Plot time history
        plot_point_history_action = QAction("Plot Time History for Selected Node", self)
        plot_point_history_action.triggered.connect(self.enable_time_history_picking)
        context_menu.addAction(plot_point_history_action)
        
        context_menu.addSeparator()
        
        # View Control section
        view_title_label = QLabel("View Control")
        view_title_label.setStyleSheet(title_style)
        view_title_action = QWidgetAction(context_menu)
        view_title_action.setDefaultWidget(view_title_label)
        context_menu.addAction(view_title_action)
        
        # Go to node
        go_to_node_action = QAction("Go To Node", self)
        has_mesh_and_node_ids = (
            self.current_mesh is not None and 
            'NodeID' in self.current_mesh.array_names
        )
        is_animation_running_and_frozen = (
            self.anim_timer is not None and 
            self.anim_timer.isActive() and 
            self.freeze_tracked_node
        )
        can_go_to_node = has_mesh_and_node_ids and not is_animation_running_and_frozen
        go_to_node_action.setEnabled(can_go_to_node)
        go_to_node_action.triggered.connect(self.go_to_node)
        context_menu.addAction(go_to_node_action)
        
        # Lock camera
        freeze_action = QAction("Lock Camera for Animation (freeze node)", self)
        freeze_action.setCheckable(True)
        freeze_action.setChecked(self.freeze_tracked_node)
        freeze_action.setEnabled(self.target_node_index is not None)
        freeze_action.triggered.connect(self.toggle_freeze_node)
        context_menu.addAction(freeze_action)
        
        # Reset camera
        reset_camera_action = QAction("Reset Camera", self)
        reset_camera_action.triggered.connect(self.plotter.reset_camera)
        context_menu.addAction(reset_camera_action)
        
        context_menu.exec_(self.plotter.mapToGlobal(position))
    
    def update_view_with_results(self, mesh, scalar_bar_title, data_min, data_max):
        """
        Update visualization with computed results.
        
        Args:
            mesh: PyVista mesh with results.
            scalar_bar_title: Title for the scalar bar.
            data_min: Minimum data value.
            data_max: Maximum data value.
        """
        # Update current mesh and data column
        self.current_mesh = mesh
        self.data_column = scalar_bar_title
        
        # Update scalar range spin boxes
        self.scalar_min_spin.blockSignals(True)
        self.scalar_max_spin.blockSignals(True)
        self.scalar_min_spin.setRange(data_min, data_max)
        self.scalar_max_spin.setRange(data_min, 1e30)
        self.scalar_min_spin.setValue(data_min)
        self.scalar_max_spin.setValue(data_max)
        self.scalar_min_spin.blockSignals(False)
        self.scalar_max_spin.blockSignals(False)
        
        # Update the visualization
        self.update_visualization()
        
        # Clear file path since this is computed data, not loaded from file
        self.file_path.clear()
        
        # Show IC export button if velocity components are present
        if all(key in mesh.array_names for key in ['vel_x', 'vel_y', 'vel_z']):
            self.extract_ic_button.setVisible(True)
        else:
            self.extract_ic_button.setVisible(False)
    
    @pyqtSlot(object)
    def on_animation_data_ready(self, precomputed_data):
        """Receive precomputed animation data and start playback."""
        from PyQt5.QtWidgets import QApplication
        QApplication.restoreOverrideCursor()
        
        if precomputed_data is None:
            print("Animation precomputation failed. See console for details.")
            self.stop_animation()
            return
        
        print("DisplayTab: Received precomputed animation data. Starting playback.")
        
        # Unpack data
        (precomputed_scalars, precomputed_coords, precomputed_anim_times, 
         data_column_name, is_deformation_included) = precomputed_data
        
        # Store in animation manager
        self.anim_manager.precomputed_scalars = precomputed_scalars
        self.anim_manager.precomputed_coords = precomputed_coords
        self.anim_manager.precomputed_anim_times = precomputed_anim_times
        self.anim_manager.data_column_name = data_column_name
        self.anim_manager.is_deformation_included = is_deformation_included
        self.is_deformation_included_in_anim = is_deformation_included
        
        # Update data column for scalar bar title and hover annotation
        self.data_column = data_column_name
        
        # Update scalar range spinboxes based on precomputed data
        data_min = np.min(precomputed_scalars)
        data_max = np.max(precomputed_scalars)
        self.scalar_min_spin.blockSignals(True)
        self.scalar_max_spin.blockSignals(True)
        self.scalar_min_spin.setRange(data_min, data_max)
        self.scalar_max_spin.setRange(data_min, 1e30)
        self.scalar_min_spin.setValue(data_min)
        self.scalar_max_spin.setValue(data_max)
        self.scalar_min_spin.blockSignals(False)
        self.scalar_max_spin.blockSignals(False)
        
        # Update the current mesh with first frame data and rebuild visualization
        # This ensures scalar bar title and range are updated
        self.current_anim_frame_index = 0
        self.animation_paused = False
        
        try:
            # Get first frame data
            scalars, coords, time_val = self.anim_manager.get_frame_data(0)
            
            # Update mesh scalars
            if self.current_mesh is not None:
                self.current_mesh[data_column_name] = scalars
                self.current_mesh.set_active_scalars(data_column_name)
                
                # Update coordinates if deformation is included
                if coords is not None:
                    self.current_mesh.points = coords.copy()
                    try:
                        self.current_mesh.points_modified()
                    except AttributeError:
                        self.current_mesh.GetPoints().Modified()
                
                # Rebuild visualization with new scalar bar title and range
                self.update_visualization()
            
            # Re-create tracked node markers AFTER update_visualization (which clears the plotter)
            if self.target_node_index is not None:
                try:
                    point_coords = (precomputed_coords[self.target_node_index, :, 0] 
                                   if precomputed_coords is not None 
                                   else self.current_mesh.points[self.target_node_index])
                    
                    import pyvista as pv
                    self.marker_poly = pv.PolyData([point_coords])
                    self.target_node_marker_actor = self.plotter.add_points(
                        self.marker_poly,
                        color='black',
                        point_size=self.point_size.value() * 2,
                        render_points_as_spheres=True,
                        opacity=0.3
                    )
                    
                    self.label_point_data = pv.PolyData([point_coords])
                    self.target_node_label_actor = self.plotter.add_point_labels(
                        self.label_point_data, [f"Node {self.target_node_id}"],
                        name="target_node_label",
                        font_size=16, text_color='red',
                        always_visible=True, show_points=False
                    )
                    
                    # Hide if frozen
                    if self.freeze_tracked_node:
                        if self.target_node_marker_actor:
                            self.target_node_marker_actor.SetVisibility(False)
                        if self.target_node_label_actor:
                            self.target_node_label_actor.SetVisibility(False)
                        self.plotter.render()
                        
                except IndexError:
                    print("Warning: Could not re-create tracked node marker.")
                    self._clear_goto_node_markers()
            
            # Now render the first frame with the time text
            self._animate_frame(update_index=False)
        except Exception as e:
            QMessageBox.critical(
                self, "Animation Error",
                f"Failed initial frame render: {str(e)}"
            )
            self.stop_animation()
            return
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate_frame)
        self.anim_timer.start(self.anim_interval_spin.value())
        
        # Update UI state
        self.deformation_scale_edit.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.save_anim_button.setEnabled(True)
    
    def toggle_selection_box(self):
        """Add or remove the box widget from the plotter."""
        if self.box_widget is None:
            import vtk
            self.box_widget = self.plotter.add_box_widget(callback=self._dummy_callback)
            self.box_widget.SetPlaceFactor(0.75)
            
            # Style the handles
            handle_property = self.box_widget.GetHandleProperty()
            handle_property.SetColor(0.8, 0.4, 0.2)
            handle_property.SetPointSize(1)
            
            selected_handle_property = self.box_widget.GetSelectedHandleProperty()
            selected_handle_property.SetColor(1.0, 0.5, 0.0)
        else:
            self.plotter.clear_box_widgets()
            self.box_widget = None
        
        self.plotter.render()
    
    def _dummy_callback(self, *args):
        """Do-nothing callback for box widget."""
        pass
    
    def toggle_point_picking_mode(self, checked):
        """Toggle point picking mode on the plotter."""
        self.is_point_picking_active = checked
        if checked:
            self.plotter.enable_point_picking(
                callback=self._on_point_picked_for_box,
                show_message=False,
                use_picker=True,
                left_clicking=True
            )
            self.plotter.setCursor(Qt.CrossCursor)
        else:
            self.plotter.disable_picking()
            self.plotter.setCursor(Qt.ArrowCursor)
    
    def _on_point_picked_for_box(self, *args):
        """Callback when point is picked for box positioning."""
        if not args or args[0].size == 0:
            return
        
        center = args[0]
        import vtk
        
        if self.box_widget is None:
            self.box_widget = self.plotter.add_box_widget(callback=self._dummy_callback)
            self.box_widget.GetHandleProperty().SetColor(0.8, 0.4, 0.2)
            self.box_widget.GetSelectedHandleProperty().SetColor(1.0, 0.5, 0.0)
            self.box_widget.GetHandleProperty().SetPointSize(10)
            self.box_widget.GetSelectedHandleProperty().SetPointSize(15)
            
            size = self.current_mesh.length * 0.1
            bounds = [
                center[0] - size / 2.0, center[0] + size / 2.0,
                center[1] - size / 2.0, center[1] + size / 2.0,
                center[2] - size / 2.0, center[2] + size / 2.0,
            ]
        else:
            box_geometry = vtk.vtkPolyData()
            self.box_widget.GetPolyData(box_geometry)
            current_bounds = box_geometry.GetBounds()
            
            x_size = current_bounds[1] - current_bounds[0]
            y_size = current_bounds[3] - current_bounds[2]
            z_size = current_bounds[5] - current_bounds[4]
            bounds = [
                center[0] - x_size / 2.0, center[0] + x_size / 2.0,
                center[1] - y_size / 2.0, center[1] + y_size / 2.0,
                center[2] - z_size / 2.0, center[2] + z_size / 2.0,
            ]
        
        self.box_widget.PlaceWidget(bounds)
        self.plotter.render()
        self.toggle_point_picking_mode(False)
    
    def _find_hotspots_on_view(self):
        """Find hotspots on currently visible points."""
        if not self.current_mesh:
            QMessageBox.warning(
                self, "No Data",
                "There is no mesh loaded to find hotspots on."
            )
            return
        
        import vtk
        selector = vtk.vtkSelectVisiblePoints()
        selector.SetInputData(self.current_mesh)
        selector.SetRenderer(self.plotter.renderer)
        selector.Update()
        
        import pyvista as pv
        visible_mesh = pv.wrap(selector.GetOutput())
        
        if visible_mesh.n_points == 0:
            QMessageBox.information(
                self, "No Visible Points",
                "No points are visible in the current camera view."
            )
            return
        
        self._find_and_show_hotspots(visible_mesh)
    
    def _find_and_show_hotspots(self, mesh_to_analyze):
        """Run hotspot analysis on given mesh."""
        if not mesh_to_analyze or mesh_to_analyze.n_points == 0:
            QMessageBox.information(
                self, "No Nodes Found",
                "No nodes were found in the selected area."
            )
            return
        
        num_hotspots, ok = QInputDialog.getInt(
            self, "Number of Hotspots",
            "How many top nodes to find?", 10, 1, 1000
        )
        if not ok:
            return
        
        try:
            node_ids = mesh_to_analyze['NodeID']
            scalar_values = mesh_to_analyze.active_scalars
            scalar_name = mesh_to_analyze.active_scalars_name or "Result"
            
            df = pd.DataFrame({'NodeID': node_ids, scalar_name: scalar_values})
            df_hotspots = df.sort_values(by=scalar_name, ascending=False).head(num_hotspots).copy()
            df_hotspots.insert(0, 'Rank', range(1, 1 + len(df_hotspots)))
            df_hotspots.reset_index(drop=True, inplace=True)
            
            if self.hotspot_dialog is not None:
                self.hotspot_dialog.close()
            
            dialog = HotspotDialog(df_hotspots, self)
            dialog.node_selected.connect(self._highlight_and_focus_on_node)
            dialog.finished.connect(self._cleanup_hotspot_analysis)
            
            if self.box_widget is not None:
                self.box_widget.Off()
            
            self.hotspot_dialog = dialog
            self.hotspot_dialog.show()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to find hotspots: {e}")
    
    def find_hotspots_in_box(self):
        """Clip mesh to box bounds and run hotspot analysis."""
        if self.box_widget is None:
            return
        
        import vtk
        box_geometry = vtk.vtkPolyData()
        self.box_widget.GetPolyData(box_geometry)
        bounds = box_geometry.GetBounds()
        
        clipped_mesh = self.current_mesh.clip_box(bounds, invert=False)
        self._find_and_show_hotspots(clipped_mesh)
    
    def _highlight_and_focus_on_node(self, node_id):
        """Highlight and focus camera on specific node."""
        if self.current_mesh is None:
            QMessageBox.warning(self, "No Mesh", "Cannot highlight node - no mesh loaded.")
            return
        
        if self.highlight_actor:
            self.plotter.renderer.RemoveActor(self.highlight_actor)
            self.highlight_actor = None
        
        try:
            node_indices = np.where(self.current_mesh['NodeID'] == node_id)[0]
            if len(node_indices) == 0:
                print(f"Node ID {node_id} not found in current mesh.")
                return
            
            point_index = node_indices[0]
            point_coords = self.current_mesh.points[point_index]
            label_text = f"Node {node_id}"
            
            self.highlight_actor = self.plotter.add_point_labels(
                point_coords, [label_text],
                name="hotspot_label",
                font_size=16,
                point_color='black',
                shape_opacity=0.5,
                point_size=self.point_size.value() * 2,
                text_color='purple',
                always_visible=True
            )
            
            self.plotter.fly_to(point_coords)
            
        except Exception as e:
            QMessageBox.critical(
                self, "Visualization Error",
                f"Could not highlight node {node_id}: {e}"
            )
    
    def _cleanup_hotspot_analysis(self):
        """Remove highlight labels and re-enable box widget."""
        if hasattr(self, 'highlight_actor') and self.highlight_actor:
            self.plotter.remove_actor("hotspot_label", reset_camera=False)
            self.highlight_actor = None
        
        self._clear_goto_node_markers()
        
        if self.box_widget:
            self.box_widget.On()
        
        self.hotspot_dialog = None
        self.plotter.render()
    
    def enable_time_history_picking(self):
        """Activate point-history plotting."""
        # Offer tracked node if available
        if self.target_node_index is not None and self.target_node_id is not None:
            reply = QMessageBox.question(
                self,
                "Use Tracked Node?",
                f"Plot time history for tracked node {self.target_node_id}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.node_picked_signal.emit(self.target_node_id)
                return
        
        # Fall back to normal picking
        if not self.current_mesh or 'NodeID' not in self.current_mesh.array_names:
            QMessageBox.warning(
                self, "No Data",
                "Cannot pick a point. Please load data with NodeIDs first."
            )
            return
        
        print("Picking mode enabled: Click on a node to plot its time history.")
        self.plotter.enable_point_picking(
            callback=self._on_point_picked_for_history,
            show_message=False,
            use_picker=True,
            left_clicking=True
        )
        self.plotter.setCursor(Qt.CrossCursor)
    
    def _on_point_picked_for_history(self, *args):
        """Callback when point is picked for time history."""
        self.plotter.disable_picking()
        self.plotter.setCursor(Qt.ArrowCursor)
        
        if not args or len(args) == 0 or not isinstance(args[0], (np.ndarray, list, tuple)):
            print("Picking cancelled or missed the mesh.")
            return
        
        picked_coords = args[0]
        if len(picked_coords) == 0:
            print("Picking cancelled or missed the mesh.")
            return
        
        picked_point_index = self.current_mesh.find_closest_point(picked_coords)
        
        if picked_point_index != -1 and picked_point_index < self.current_mesh.n_points:
            try:
                node_id = self.current_mesh['NodeID'][picked_point_index]
                print(f"Node {node_id} picked. Emitting signal...")
                self.node_picked_signal.emit(node_id)
            except (KeyError, IndexError) as e:
                print(f"Could not retrieve NodeID: {e}")
        else:
            print("Picking cancelled or missed the mesh.")
    
    def go_to_node(self):
        """Prompt for Node ID and fly camera to it."""
        if not self.current_mesh or 'NodeID' not in self.current_mesh.array_names:
            QMessageBox.warning(
                self, "Action Unavailable",
                "No mesh with NodeIDs is currently loaded."
            )
            return
        
        default_val = self.last_goto_node_id if self.last_goto_node_id is not None else 0
        node_id, ok = QInputDialog.getInt(
            self, "Go To Node", "Enter Node ID:", value=default_val
        )
        if not ok:
            return
        
        try:
            self._clear_goto_node_markers()
            
            node_indices = np.where(self.current_mesh['NodeID'] == node_id)[0]
            if not node_indices.size:
                QMessageBox.warning(self, "Not Found", f"Node ID {node_id} was not found.")
                return
            
            self.last_goto_node_id = node_id
            self.target_node_index = node_indices[0]
            self.target_node_id = node_id
            point_coords = self.current_mesh.points[self.target_node_index]
            
            # Create marker
            import pyvista as pv
            self.marker_poly = pv.PolyData([point_coords])
            self.target_node_marker_actor = self.plotter.add_points(
                self.marker_poly,
                color='black',
                point_size=self.point_size.value() * 2,
                render_points_as_spheres=True,
                opacity=0.3,
            )
            
            # Create label
            self.label_point_data = pv.PolyData([point_coords])
            self.target_node_label_actor = self.plotter.add_point_labels(
                self.label_point_data, [f"Node {self.target_node_id}"],
                name="target_node_label",
                font_size=16, text_color='red',
                always_visible=True, show_points=False
            )
            
            self.plotter.fly_to(point_coords)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not go to node {node_id}: {e}")
    
    def toggle_freeze_node(self, checked):
        """Toggle freeze node tracking for animation."""
        if self.target_node_index is None or self.current_mesh is None:
            QMessageBox.warning(
                self, "No Tracked Node",
                "Use 'Go To Node' first, then lock the camera."
            )
            return
        
        self.freeze_tracked_node = checked
        if checked:
            self.freeze_baseline = self.current_mesh.points[self.target_node_index].copy()
            
            # Hide label/marker if animation is active
            if self.anim_timer is not None and self.anim_timer.isActive():
                if self.target_node_label_actor:
                    self.target_node_label_actor.SetVisibility(False)
                if self.target_node_marker_actor:
                    self.target_node_marker_actor.SetVisibility(False)
        else:
            self.freeze_baseline = None
            
            # Show label/marker when unfreezing
            if self.target_node_label_actor:
                self.target_node_label_actor.SetVisibility(True)
            if self.target_node_marker_actor:
                self.target_node_marker_actor.SetVisibility(True)
        
        self.plotter.render()
    
    def _clear_visualization(self):
        """Properly clear existing visualization."""
        self.stop_animation()
        
        # Clear hover elements
        self._clear_hover_elements()
        
        # Clear box widget
        if self.box_widget:
            self.box_widget.Off()
            self.box_widget = None
        
        # Clear camera widget
        if self.camera_widget:
            self.camera_widget.EnabledOff()
            self.camera_widget = None
        
        self.plotter.clear()
        
        if self.current_mesh:
            self.current_mesh.clear_data()
            self.current_mesh = None
        
        self.current_actor = None
        self.scalar_min_spin.clear()
        self.scalar_max_spin.clear()
        self.file_path.clear()
    
    def __del__(self):
        """Cleanup when widget is destroyed."""
        if self.anim_timer is not None:
            self.anim_timer.stop()
        if hasattr(self, 'plotter'):
            self.plotter.close()
