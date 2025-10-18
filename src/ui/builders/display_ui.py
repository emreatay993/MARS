"""
UI Builder for the Display Tab.

This module contains builder functions that construct UI components for the
display tab, organizing the 3D visualization controls.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QFont
from PyQt5.QtWidgets import (
    QComboBox, QDoubleSpinBox, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSpinBox, QVBoxLayout
)
from pyvistaqt import QtInteractor

from utils.constants import (
    BUTTON_STYLE, GROUP_BOX_STYLE, READONLY_LINE_EDIT_STYLE,
    DEFAULT_POINT_SIZE, DEFAULT_BACKGROUND_COLOR, DEFAULT_ANIMATION_INTERVAL_MS
)


class DisplayTabUIBuilder:
    """
    Builder class for constructing Display Tab UI components.
    
    This class breaks down the UI construction into logical sections
    for better maintainability.
    """
    
    def __init__(self):
        """Initialize the builder."""
        self.components = {}
    
    def build_file_controls(self):
        """
        Build the file loading controls.
        
        Returns:
            QHBoxLayout: Layout containing file controls.
        """
        file_button = QPushButton('Load Visualization File')
        file_button.setStyleSheet(BUTTON_STYLE)
        
        file_path = QLineEdit()
        file_path.setReadOnly(True)
        file_path.setStyleSheet(READONLY_LINE_EDIT_STYLE)
        
        file_layout = QHBoxLayout()
        file_layout.addWidget(file_button)
        file_layout.addWidget(file_path)
        
        # Store components
        self.components['file_button'] = file_button
        self.components['file_path'] = file_path
        
        return file_layout
    
    def build_visualization_controls(self):
        """
        Build the visualization control widgets.
        
        Returns:
            QGroupBox: Group box containing visualization controls.
        """
        # Point size control
        point_size = QSpinBox()
        point_size.setRange(1, 100)
        point_size.setValue(DEFAULT_POINT_SIZE)
        point_size.setPrefix("Size: ")
        
        # Scalar range controls
        scalar_min_spin = QDoubleSpinBox()
        scalar_max_spin = QDoubleSpinBox()
        scalar_min_spin.setPrefix("Min: ")
        scalar_max_spin.setPrefix("Max: ")
        scalar_min_spin.setDecimals(3)
        scalar_max_spin.setDecimals(3)
        
        # Deformation scale factor
        deformation_scale_label = QLabel("Deformation Scale Factor:")
        deformation_scale_edit = QLineEdit("1")
        validator = QDoubleValidator()
        validator.setNotation(QDoubleValidator.StandardNotation)
        deformation_scale_edit.setValidator(validator)
        deformation_scale_label.setVisible(False)
        deformation_scale_edit.setVisible(False)
        
        # Layout
        graphics_control_layout = QHBoxLayout()
        graphics_control_layout.addWidget(QLabel("Node Point Size:"))
        graphics_control_layout.addWidget(point_size)
        graphics_control_layout.addWidget(QLabel("Legend Range:"))
        graphics_control_layout.addWidget(scalar_min_spin)
        graphics_control_layout.addWidget(scalar_max_spin)
        graphics_control_layout.addWidget(deformation_scale_label)
        graphics_control_layout.addWidget(deformation_scale_edit)
        graphics_control_layout.addStretch()
        
        graphics_control_group = QGroupBox("Visualization Controls")
        graphics_control_group.setStyleSheet(GROUP_BOX_STYLE)
        graphics_control_group.setLayout(graphics_control_layout)
        
        # Store components
        self.components['point_size'] = point_size
        self.components['scalar_min_spin'] = scalar_min_spin
        self.components['scalar_max_spin'] = scalar_max_spin
        self.components['deformation_scale_label'] = deformation_scale_label
        self.components['deformation_scale_edit'] = deformation_scale_edit
        self.components['graphics_control_layout'] = graphics_control_layout
        self.components['graphics_control_group'] = graphics_control_group
        
        return graphics_control_group
    
    def build_time_point_controls(self):
        """
        Build the time point selection controls.
        
        Returns:
            QGroupBox: Group box containing time point controls.
        """
        selected_time_label = QLabel("Initialize / Display results for a selected time point:")
        selected_time_label.setStyleSheet("margin: 10px;")
        
        time_point_spinbox = QDoubleSpinBox()
        time_point_spinbox.setDecimals(5)
        time_point_spinbox.setPrefix("Time (seconds): ")
        time_point_spinbox.setRange(0, 0)
        
        update_time_button = QPushButton("Update")
        save_time_button = QPushButton("Save Time Point as CSV")
        
        extract_ic_button = QPushButton("Export Velocity as Initial Condition in APDL")
        extract_ic_button.setStyleSheet(BUTTON_STYLE)
        extract_ic_button.setVisible(False)
        
        # Layout
        time_point_layout = QHBoxLayout()
        time_point_layout.addWidget(selected_time_label)
        time_point_layout.addWidget(time_point_spinbox)
        time_point_layout.addWidget(update_time_button)
        time_point_layout.addWidget(save_time_button)
        time_point_layout.addWidget(extract_ic_button)
        time_point_layout.addStretch()
        
        time_point_group = QGroupBox("Initialization & Time Point Controls")
        time_point_group.setStyleSheet(GROUP_BOX_STYLE)
        time_point_group.setLayout(time_point_layout)
        time_point_group.setVisible(False)
        
        # Store components
        self.components['selected_time_label'] = selected_time_label
        self.components['time_point_spinbox'] = time_point_spinbox
        self.components['update_time_button'] = update_time_button
        self.components['save_time_button'] = save_time_button
        self.components['extract_ic_button'] = extract_ic_button
        self.components['time_point_layout'] = time_point_layout
        self.components['time_point_group'] = time_point_group
        
        return time_point_group
    
    def build_animation_controls(self):
        """
        Build the animation control widgets.
        
        Returns:
            QGroupBox: Group box containing animation controls.
        """
        # Animation interval
        anim_interval_spin = QSpinBox()
        anim_interval_spin.setRange(5, 10000)
        anim_interval_spin.setValue(DEFAULT_ANIMATION_INTERVAL_MS)
        anim_interval_spin.setPrefix("Interval (ms): ")
        
        # Time range
        anim_start_label = QLabel("Time Range:")
        anim_start_spin = QDoubleSpinBox()
        anim_start_spin.setPrefix("Start: ")
        anim_start_spin.setDecimals(5)
        anim_start_spin.setMinimum(0)
        anim_start_spin.setValue(0)
        
        anim_end_spin = QDoubleSpinBox()
        anim_end_spin.setPrefix("End: ")
        anim_end_spin.setDecimals(5)
        anim_end_spin.setMinimum(0)
        anim_end_spin.setValue(1)
        
        # Playback buttons
        play_button = QPushButton("Play")
        pause_button = QPushButton("Pause")
        stop_button = QPushButton("Stop")
        pause_button.setEnabled(False)
        stop_button.setEnabled(False)
        
        # Time step mode
        time_step_mode_combo = QComboBox()
        time_step_mode_combo.addItems(["Custom Time Step", "Actual Data Time Steps"])
        time_step_mode_combo.setCurrentIndex(1)
        
        custom_step_spin = QDoubleSpinBox()
        custom_step_spin.setDecimals(5)
        custom_step_spin.setRange(0.000001, 10)
        custom_step_spin.setValue(0.01)
        custom_step_spin.setPrefix("Step (secs): ")
        
        actual_interval_spin = QSpinBox()
        actual_interval_spin.setRange(1, 1)
        actual_interval_spin.setValue(1)
        actual_interval_spin.setPrefix("Every nth: ")
        actual_interval_spin.setVisible(False)
        
        # Save animation button
        save_anim_button = QPushButton("Save as Video/GIF")
        save_anim_button.setStyleSheet(BUTTON_STYLE)
        save_anim_button.setEnabled(False)
        save_anim_button.setToolTip(
            "Save the precomputed animation frames as MP4 or GIF.\n"
            "Requires 'imageio' and 'ffmpeg' (for MP4)."
        )
        
        # Layout
        anim_layout = QHBoxLayout()
        anim_layout.addWidget(time_step_mode_combo)
        anim_layout.addWidget(custom_step_spin)
        anim_layout.addWidget(actual_interval_spin)
        anim_layout.addWidget(anim_interval_spin)
        anim_layout.addWidget(anim_start_label)
        anim_layout.addWidget(anim_start_spin)
        anim_layout.addWidget(anim_end_spin)
        anim_layout.addWidget(play_button)
        anim_layout.addWidget(pause_button)
        anim_layout.addWidget(stop_button)
        anim_layout.addWidget(save_anim_button)
        
        anim_group = QGroupBox("Animation Controls")
        anim_group.setStyleSheet(GROUP_BOX_STYLE)
        anim_group.setLayout(anim_layout)
        anim_group.setVisible(False)
        
        # Store components
        self.components['anim_interval_spin'] = anim_interval_spin
        self.components['anim_start_label'] = anim_start_label
        self.components['anim_start_spin'] = anim_start_spin
        self.components['anim_end_spin'] = anim_end_spin
        self.components['play_button'] = play_button
        self.components['pause_button'] = pause_button
        self.components['stop_button'] = stop_button
        self.components['time_step_mode_combo'] = time_step_mode_combo
        self.components['custom_step_spin'] = custom_step_spin
        self.components['actual_interval_spin'] = actual_interval_spin
        self.components['save_anim_button'] = save_anim_button
        self.components['anim_layout'] = anim_layout
        self.components['anim_group'] = anim_group
        
        return anim_group
    
    def build_plotter(self, parent):
        """
        Build the PyVista plotter widget.
        
        Args:
            parent: Parent widget for the plotter.
        
        Returns:
            QtInteractor: PyVista plotter widget.
        """
        plotter = QtInteractor(parent=parent)
        plotter.set_background(DEFAULT_BACKGROUND_COLOR)
        plotter.setContextMenuPolicy(Qt.CustomContextMenu)
        
        self.components['plotter'] = plotter
        
        return plotter
    
    def build_complete_layout(self, parent):
        """
        Build the complete display tab layout with all sections.
        
        Args:
            parent: Parent widget for components that need it.
        
        Returns:
            tuple: (main_layout, components_dict)
        """
        main_layout = QVBoxLayout()
        
        # Build all sections
        file_layout = self.build_file_controls()
        graphics_control_group = self.build_visualization_controls()
        time_point_group = self.build_time_point_controls()
        anim_group = self.build_animation_controls()
        plotter = self.build_plotter(parent)
        
        # Add all to main layout
        main_layout.addLayout(file_layout)
        main_layout.addWidget(graphics_control_group)
        main_layout.addWidget(time_point_group)
        main_layout.addWidget(anim_group)
        main_layout.addWidget(plotter)
        
        return main_layout, self.components

