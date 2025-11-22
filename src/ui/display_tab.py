"""
Refactored Display Tab for 3D visualization.

This module provides the DisplayTab widget that handles 3D visualization of FEA
results using PyVista. The class has been refactored to use UI builders and
delegate complex logic to manager classes.
"""

import numpy as np
import pyvista as pv

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMessageBox, QWidget, QStyle

# Import builders and managers
from ui.builders.display_ui import DisplayTabUIBuilder
from core.visualization import VisualizationManager, AnimationManager, HotspotDetector
from ui.handlers.display_state import DisplayState
from ui.handlers.display_file_handler import DisplayFileHandler
from ui.handlers.display_visualization_handler import DisplayVisualizationHandler
from ui.handlers.display_animation_handler import DisplayAnimationHandler
from ui.handlers.display_interaction_handler import DisplayInteractionHandler
from ui.handlers.display_export_handler import DisplayExportHandler
from ui.handlers.display_results_handler import DisplayResultsHandler


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

        # Shared state and handler scaffolding
        self.state = DisplayState()
        self.file_handler = DisplayFileHandler(self, self.state, self.viz_manager)
        self.visual_handler = DisplayVisualizationHandler(self, self.state, self.viz_manager)
        self.animation_handler = DisplayAnimationHandler(self, self.state, self.anim_manager)
        self.interaction_handler = DisplayInteractionHandler(self, self.state, self.hotspot_detector)
        self.export_handler = DisplayExportHandler(self, self.state)
        self.results_handler = DisplayResultsHandler(self, self.state, self.visual_handler)
        self.plotting_handler = None
        
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
        self.current_anim_frame_index = 0
        self.is_deformation_included_in_anim = False
        self.state.current_anim_frame_index = 0
        self.state.is_deformation_included_in_anim = False
        
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
        self.absolute_deformation_checkbox = self.components['absolute_deformation_checkbox']
        
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

        # Apply standard media icons so the playback controls are visually recognisable
        style = self.style()
        self.play_button.setIcon(style.standardIcon(QStyle.SP_MediaPlay))
        self.pause_button.setIcon(style.standardIcon(QStyle.SP_MediaPause))
        self.stop_button.setIcon(style.standardIcon(QStyle.SP_MediaStop))
    
    def set_plotting_handler(self, plotting_handler):
        """Set the plotting handler for this display tab."""
        self.plotting_handler = plotting_handler
        self.file_handler.set_plotting_handler(plotting_handler)


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
        self.state.time_values = time_values
        self.state.original_node_coords = node_coords
        
        # Update UI controls with time range
        self._update_time_controls(time_values)
        
        # Update deformation scale control
        self._update_deformation_controls(deformation_is_loaded)
        
        # Create and display initial mesh
        if node_coords is not None:
            mesh = self.viz_manager.create_mesh_from_coords(
                node_coords, df_node_ids
            )
            self.state.current_mesh = mesh
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
        # Note: Deformation controls visibility is managed by _update_deformation_controls()
    
    def _update_deformation_controls(self, deformation_loaded):
        """Update deformation scale controls based on availability."""
        if deformation_loaded:
            # Show and enable deformation controls when deformations are loaded
            self.deformation_scale_label.setVisible(True)
            self.deformation_scale_edit.setVisible(True)
            self.deformation_scale_edit.setEnabled(True)
            self.deformation_scale_edit.setText(
                str(self.last_valid_deformation_scale)
            )
            self.absolute_deformation_checkbox.setVisible(True)
        else:
            # Hide deformation controls when deformations are not loaded
            self.deformation_scale_label.setVisible(False)
            self.deformation_scale_edit.setVisible(False)
            self.deformation_scale_edit.setEnabled(False)
            self.deformation_scale_edit.setText("0")
            self.absolute_deformation_checkbox.setVisible(False)
    
    @pyqtSlot(bool)
    def load_file(self, checked=False):
        """Open file dialog and load visualization file."""
        self.file_handler.open_file_dialog()
    
    def showEvent(self, event):
        """Called when the Display tab becomes visible."""
        super().showEvent(event)
        # Ensure plotter is properly sized when tab is shown
        if hasattr(self, 'plotter'):
            self.plotter.update()
            
            # Add camera orientation widget only if tab is visible AND plotter is rendered
            # This prevents the huge widget bug
            if not self.camera_widget and self.current_mesh and self.isVisible():
                from PyQt5.QtCore import QTimer
                # Delay to ensure window is fully rendered
                QTimer.singleShot(200, self._add_camera_widget_if_ready)
    
    def _add_camera_widget_if_ready(self):
        """Add camera orientation widget only if plotter is properly initialized."""
        if self.camera_widget or not hasattr(self, 'plotter'):
            return
        
        try:
            # Check if render window is properly sized
            if self.plotter.ren_win:
                size = self.plotter.ren_win.GetSize()
                # Only add if window is reasonably sized (not tiny default)
                if size[0] >= 800 and size[1] >= 600:
                    camera_widget = self.plotter.add_camera_orientation_widget()
                    camera_widget.EnabledOn()
                    self.camera_widget = camera_widget
                    self.state.camera_widget = camera_widget
                else:
                    # Window too small, widget would be huge - skip it
                    print(f"Skipping camera widget - window size {size} too small")
        except Exception as e:
            print(f"Warning: Could not add camera orientation widget: {e}")
    
    def update_visualization(self):
        """Update the 3D visualization with current mesh."""
        self.visual_handler.update_visualization()
    
    
    @pyqtSlot(int)
    def update_point_size(self, value):
        """Update the point size of the displayed mesh."""
        self.visual_handler.update_point_size()
    
    @pyqtSlot(float)
    def _update_scalar_range(self, value):
        """Update the scalar range of the color map."""
        self.visual_handler.update_scalar_range()
    
    @pyqtSlot()
    def _validate_deformation_scale(self):
        """Validate deformation scale factor input."""
        self.visual_handler.validate_deformation_scale()
    
    @pyqtSlot(float)
    def _update_anim_range_min(self, value):
        """Ensure animation end time is not less than start time."""
        self.anim_end_spin.setMinimum(value)
    
    @pyqtSlot(float)
    def _update_anim_range_max(self, value):
        """Ensure animation start time does not exceed end time."""
        self.anim_start_spin.setMaximum(value)
    
    @pyqtSlot(str)
    def _update_step_spinbox_state(self, text):
        """Toggle between custom and actual time step modes."""
        if text == "Custom Time Step":
            self.custom_step_spin.setVisible(True)
            self.actual_interval_spin.setVisible(False)
        else:
            self.custom_step_spin.setVisible(False)
            self.actual_interval_spin.setVisible(True)
    
    @pyqtSlot(bool)
    def update_time_point_results(self, checked=False):
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
    
    @pyqtSlot(bool)
    def save_time_point_results(self, checked=False):
        """Save currently displayed results to CSV."""
        self.export_handler.save_time_point_results()
    
    @pyqtSlot(bool)
    def extract_initial_conditions(self, checked=False):
        """Extract velocity initial conditions and export to APDL format."""
        self.export_handler.extract_initial_conditions()
    
    @pyqtSlot(bool)
    def start_animation(self, checked=False):
        """Start animation playback or resume if paused."""
        self.animation_handler.start_animation()
    
    def _estimate_animation_ram(self, num_nodes, num_anim_steps, include_deformation):
        """Estimate peak RAM needed for animation precomputation in GB."""
        return self.animation_handler.estimate_animation_ram(
            num_nodes, num_anim_steps, include_deformation
        )
    
    @pyqtSlot(bool)
    def pause_animation(self, checked=False):
        """Pause animation playback."""
        self.animation_handler.pause_animation()
    
    @pyqtSlot(bool)
    def stop_animation(self, checked=False):
        """Stop animation, release precomputed data, and reset state."""
        self.animation_handler.stop_animation()
    
    @pyqtSlot(bool)
    def save_animation(self, checked=False):
        """Save animation to file (MP4 or GIF)."""
        self.animation_handler.save_animation()
    
    def _get_save_path_and_format(self):
        """Delegate to animation handler for backwards compatibility."""
        return self.animation_handler.get_save_path_and_format()

    def _write_animation_to_file(self, file_path, file_format):
        """Delegate to animation handler for backwards compatibility."""
        return self.animation_handler.write_animation_to_file(file_path, file_format)
    
    @pyqtSlot('QPoint')
    def show_context_menu(self, position):
        """Create and display the right-click context menu."""
        self.interaction_handler.show_context_menu(position)
    
    @pyqtSlot(object, str, float, float)
    def update_view_with_results(self, mesh, scalar_bar_title, data_min, data_max):
        """
        Update visualization with computed results.
        
        Args:
            mesh: PyVista mesh with results.
            scalar_bar_title: Title for the scalar bar.
            data_min: Minimum data value.
            data_max: Maximum data value.
        """
        # Update current mesh and track state
        self.current_mesh = mesh
        self.state.current_mesh = mesh
        self.data_column = scalar_bar_title
        self.state.data_column = scalar_bar_title
        
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
        self.animation_handler.set_state_attr(
            "is_deformation_included_in_anim", is_deformation_included
        )
        
        # Update data column for scalar bar title and hover annotation
        self.data_column = data_column_name
        self.state.data_column = data_column_name
        
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
        self.animation_handler.set_state_attr("current_anim_frame_index", 0)
        self.animation_handler.set_state_attr("animation_paused", False)
        
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
                    
                    self.marker_poly = pv.PolyData([point_coords])
                    self.interaction_handler.set_state_attr('marker_poly', self.marker_poly)
                    self.target_node_marker_actor = self.plotter.add_points(
                        self.marker_poly,
                        color='black',
                        point_size=self.point_size.value() * 2,
                        render_points_as_spheres=True,
                        opacity=0.3
                    )
                    self.interaction_handler.set_state_attr('target_node_marker_actor', self.target_node_marker_actor)
                    
                    self.label_point_data = pv.PolyData([point_coords])
                    self.interaction_handler.set_state_attr('label_point_data', self.label_point_data)
                    self.target_node_label_actor = self.plotter.add_point_labels(
                        self.label_point_data, [f"Node {self.target_node_id}"],
                        name="target_node_label",
                        font_size=16, text_color='red',
                        always_visible=True, show_points=False
                    )
                    self.interaction_handler.set_state_attr('target_node_label_actor', self.target_node_label_actor)
                    
                    # Hide if frozen
                    if self.freeze_tracked_node:
                        if self.target_node_marker_actor:
                            self.target_node_marker_actor.SetVisibility(False)
                        if self.target_node_label_actor:
                            self.target_node_label_actor.SetVisibility(False)
                        self.plotter.render()
                        
                except IndexError:
                    print("Warning: Could not re-create tracked node marker.")
                    self.interaction_handler.clear_goto_node_markers()
            
            # Now render the first frame with the time text
            self.animation_handler.animate_frame(update_index=False)
        except Exception as e:
            QMessageBox.critical(
                self, "Animation Error",
                f"Failed initial frame render: {str(e)}"
            )
            self.stop_animation()
            return
        
        self.anim_timer = QTimer(self)
        self.animation_handler.set_state_attr("anim_timer", self.anim_timer)
        self.anim_timer.timeout.connect(self.animation_handler.animate_frame)
        self.anim_timer.start(self.anim_interval_spin.value())
        
        # Update UI state
        self.deformation_scale_edit.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.save_anim_button.setEnabled(True)
    
    def _clear_visualization(self):
        """Properly clear existing visualization."""
        self.stop_animation()
        self.interaction_handler.clear_goto_node_markers()
        
        # Clear hover elements
        self.visual_handler.clear_hover_elements()
        
        # Clear box widget
        if self.box_widget:
            self.box_widget.Off()
            self.box_widget = None
            self.state.box_widget = None
        
        # Clear camera widget
        if self.camera_widget:
            self.camera_widget.EnabledOff()
            self.camera_widget = None
            self.state.camera_widget = None
        
        self.plotter.clear()
        
        if self.current_mesh:
            self.current_mesh.clear_data()
            self.current_mesh = None
            self.state.current_mesh = None
        
        self.current_actor = None
        self.state.current_actor = None
        self.scalar_min_spin.clear()
        self.scalar_max_spin.clear()
        self.file_path.clear()
    
    def __del__(self):
        """Cleanup when widget is destroyed."""
        if self.anim_timer is not None:
            self.anim_timer.stop()
        if hasattr(self, 'plotter'):
            self.plotter.close()
