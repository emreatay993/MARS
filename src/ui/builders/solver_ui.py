"""
UI Builder for the Solver Tab.

This module contains builder functions that construct UI components for the
solver tab, breaking down the massive init_ui method into manageable pieces.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QFont, QPalette, QColor, QIntValidator
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QProgressBar, QPushButton, QSizePolicy,
    QTabWidget, QVBoxLayout
)

from utils.constants import (
    WINDOW_BACKGROUND_COLOR
)
from ui.styles.style_constants import (
    BUTTON_STYLE, GROUP_BOX_STYLE, TAB_STYLE, READONLY_INPUT_STYLE,
    CHECKBOX_STYLE, CONSOLE_STYLE, PROGRESS_BAR_STYLE
)
from ui.widgets.plotting import MatplotlibWidget, PlotlyWidget


class SolverTabUIBuilder:
    """
    Builder class for constructing Solver Tab UI components.
    
    This class breaks down the UI construction into logical sections,
    making the code more maintainable and easier to understand.
    """
    
    def __init__(self):
        """Initialize the builder."""
        self.components = {}
    
    def build_file_input_section(self):
        """
        Build the file input section with buttons and path displays.
        
        Returns:
            QGroupBox: Group box containing file input controls.
        """
        # Modal Coordinate File
        coord_file_button = QPushButton('Read Modal Coordinate File (.mcf)')
        coord_file_button.setStyleSheet(BUTTON_STYLE)
        coord_file_button.setFont(QFont('Arial', 8))
        coord_file_path = QLineEdit()
        coord_file_path.setReadOnly(True)
        coord_file_path.setStyleSheet(READONLY_INPUT_STYLE)

        # Modal Stress File
        stress_file_button = QPushButton('Read Modal Stress File (.csv)')
        stress_file_button.setStyleSheet(BUTTON_STYLE)
        stress_file_button.setFont(QFont('Arial', 8))
        stress_file_path = QLineEdit()
        stress_file_path.setReadOnly(True)
        stress_file_path.setStyleSheet(READONLY_INPUT_STYLE)
        
        # Steady-State Stress (optional)
        steady_state_checkbox = QCheckBox("Include Steady-State Stress Field (Optional)")
        steady_state_checkbox.setStyleSheet(CHECKBOX_STYLE)

        steady_state_file_button = QPushButton('Read Full Stress Tensor File (.txt)')
        steady_state_file_button.setStyleSheet(BUTTON_STYLE)
        steady_state_file_button.setFont(QFont('Arial', 8))
        steady_state_file_button.setVisible(False)

        steady_state_file_path = QLineEdit()
        steady_state_file_path.setReadOnly(True)
        steady_state_file_path.setStyleSheet(READONLY_INPUT_STYLE)
        steady_state_file_path.setVisible(False)

        # Deformations (optional)
        deformations_checkbox = QCheckBox("Include Deformations (Optional)")
        deformations_checkbox.setStyleSheet(CHECKBOX_STYLE)

        deformations_file_button = QPushButton('Read Modal Deformations File (.csv)')
        deformations_file_button.setStyleSheet(BUTTON_STYLE)
        deformations_file_button.setFont(QFont('Arial', 8))
        deformations_file_button.setVisible(False)

        deformations_file_path = QLineEdit()
        deformations_file_path.setReadOnly(True)
        deformations_file_path.setStyleSheet(READONLY_INPUT_STYLE)
        deformations_file_path.setVisible(False)
        
        # Skip modes controls
        skip_modes_label = QLabel("Skip first n modes:")
        skip_modes_label.setVisible(False)
        skip_modes_combo = QComboBox()
        skip_modes_combo.setFixedWidth(80)
        skip_modes_combo.setVisible(False)
        
        # Layout
        file_layout = QGridLayout()
        file_layout.addWidget(coord_file_button, 0, 0)
        file_layout.addWidget(coord_file_path, 0, 1)
        file_layout.addWidget(stress_file_button, 1, 0)
        file_layout.addWidget(stress_file_path, 1, 1)
        file_layout.addWidget(steady_state_checkbox, 2, 0, 1, 2)
        file_layout.addWidget(steady_state_file_button, 3, 0)
        file_layout.addWidget(steady_state_file_path, 3, 1)
        file_layout.addWidget(deformations_checkbox, 4, 0, 1, 2)
        file_layout.addWidget(deformations_file_button, 5, 0)
        file_layout.addWidget(deformations_file_path, 5, 1)
        file_layout.addWidget(skip_modes_label, 1, 2)
        file_layout.addWidget(skip_modes_combo, 1, 3)
        
        file_group = QGroupBox("Input Files")
        file_group.setStyleSheet(GROUP_BOX_STYLE)
        file_group.setLayout(file_layout)
        
        # Store components for external access
        self.components['coord_file_button'] = coord_file_button
        self.components['coord_file_path'] = coord_file_path
        self.components['stress_file_button'] = stress_file_button
        self.components['stress_file_path'] = stress_file_path
        self.components['steady_state_checkbox'] = steady_state_checkbox
        self.components['steady_state_file_button'] = steady_state_file_button
        self.components['steady_state_file_path'] = steady_state_file_path
        self.components['deformations_checkbox'] = deformations_checkbox
        self.components['deformations_file_button'] = deformations_file_button
        self.components['deformations_file_path'] = deformations_file_path
        self.components['skip_modes_label'] = skip_modes_label
        self.components['skip_modes_combo'] = skip_modes_combo
        
        return file_group
    
    def build_output_selection_section(self):
        """
        Build the output selection section with checkboxes.
        
        Returns:
            QGroupBox: Group box containing output selection checkboxes.
        """
        # Create all checkboxes
        time_history_checkbox = QCheckBox('Enable Time History Mode (Single Node)')
        time_history_checkbox.setStyleSheet(CHECKBOX_STYLE)
        max_principal_stress_checkbox = QCheckBox('Max Principal Stress')
        max_principal_stress_checkbox.setStyleSheet(CHECKBOX_STYLE)
        min_principal_stress_checkbox = QCheckBox("Min Principal Stress")
        min_principal_stress_checkbox.setStyleSheet(CHECKBOX_STYLE)
        von_mises_checkbox = QCheckBox('Von-Mises Stress')
        von_mises_checkbox.setStyleSheet(CHECKBOX_STYLE)
        plasticity_correction_checkbox = QCheckBox('Enable Plasticity Correction')
        plasticity_correction_checkbox.setStyleSheet(CHECKBOX_STYLE)
        deformation_checkbox = QCheckBox('Deformation')
        deformation_checkbox.setStyleSheet(CHECKBOX_STYLE)
        velocity_checkbox = QCheckBox('Velocity')
        velocity_checkbox.setStyleSheet(CHECKBOX_STYLE)
        acceleration_checkbox = QCheckBox('Acceleration')
        acceleration_checkbox.setStyleSheet(CHECKBOX_STYLE)
        damage_index_checkbox = QCheckBox('Damage Index / Potential Damage')
        damage_index_checkbox.setStyleSheet(CHECKBOX_STYLE)
        # Layout
        output_layout = QVBoxLayout()
        output_layout.addWidget(max_principal_stress_checkbox)
        output_layout.addWidget(min_principal_stress_checkbox)
        output_layout.addWidget(von_mises_checkbox)
        output_layout.addWidget(deformation_checkbox)
        output_layout.addWidget(velocity_checkbox)
        output_layout.addWidget(acceleration_checkbox)
        output_layout.addWidget(damage_index_checkbox)
        output_layout.addWidget(time_history_checkbox)
        output_layout.addWidget(plasticity_correction_checkbox)
        
        output_group = QGroupBox("Output Options")
        output_group.setStyleSheet(GROUP_BOX_STYLE)
        output_group.setLayout(output_layout)
        
        # Store components
        self.components['time_history_checkbox'] = time_history_checkbox
        self.components['max_principal_stress_checkbox'] = max_principal_stress_checkbox
        self.components['min_principal_stress_checkbox'] = min_principal_stress_checkbox
        self.components['von_mises_checkbox'] = von_mises_checkbox
        self.components['plasticity_correction_checkbox'] = plasticity_correction_checkbox
        self.components['deformation_checkbox'] = deformation_checkbox
        self.components['velocity_checkbox'] = velocity_checkbox
        self.components['acceleration_checkbox'] = acceleration_checkbox
        self.components['damage_index_checkbox'] = damage_index_checkbox
        
        # Initially disable checkboxes until files are loaded
        for key in ['max_principal_stress_checkbox', 'min_principal_stress_checkbox',
                    'von_mises_checkbox', 'plasticity_correction_checkbox', 'deformation_checkbox', 'velocity_checkbox',
                    'acceleration_checkbox', 'damage_index_checkbox', 'time_history_checkbox']:
            self.components[key].setEnabled(False)
        
        return output_group
    
    def build_fatigue_params_section(self):
        """
        Build the fatigue parameters section.
        
        Returns:
            QGroupBox: Group box containing fatigue parameter inputs.
        """
        A_line_edit = QLineEdit()
        A_line_edit.setPlaceholderText("Enter Fatigue Strength Coefficient [MPa]")
        A_line_edit.setValidator(QDoubleValidator())
        
        m_line_edit = QLineEdit()
        m_line_edit.setPlaceholderText("Enter Fatigue Strength Exponent")
        m_line_edit.setValidator(QDoubleValidator())
        
        fatigue_inputs_layout = QVBoxLayout()
        fatigue_inputs_layout.addWidget(QLabel("σ'f"))
        fatigue_inputs_layout.addWidget(A_line_edit)
        fatigue_inputs_layout.addWidget(QLabel("b:"))
        fatigue_inputs_layout.addWidget(m_line_edit)
        
        fatigue_params_group = QGroupBox("Fatigue Parameters")
        fatigue_params_group.setStyleSheet(GROUP_BOX_STYLE)
        fatigue_params_group.setLayout(fatigue_inputs_layout)
        fatigue_params_group.setVisible(False)
        
        # Store components
        self.components['A_line_edit'] = A_line_edit
        self.components['m_line_edit'] = m_line_edit
        self.components['fatigue_params_group'] = fatigue_params_group
        
        return fatigue_params_group
    
    def build_single_node_section(self):
        """
        Build the single node selection section.
        
        Returns:
            QGroupBox: Group box containing node ID input.
        """
        single_node_label = QLabel("Select a node:")
        single_node_label.setFont(QFont('Arial', 8))
        
        node_line_edit = QLineEdit()
        node_line_edit.setPlaceholderText("Enter Node ID")
        node_line_edit.setStyleSheet(BUTTON_STYLE)
        node_line_edit.setMaximumWidth(150)
        node_line_edit.setMinimumWidth(100)

        single_node_layout = QHBoxLayout()
        single_node_layout.addWidget(single_node_label)
        single_node_layout.addWidget(node_line_edit)

        single_node_group = QGroupBox("Scoping")
        single_node_group.setStyleSheet(GROUP_BOX_STYLE)
        single_node_group.setLayout(single_node_layout)
        single_node_group.setVisible(False)
        single_node_group.setMaximumWidth(250)
        
        # Store components
        self.components['single_node_label'] = single_node_label
        self.components['node_line_edit'] = node_line_edit
        self.components['single_node_group'] = single_node_group
        
        return single_node_group

    def build_plasticity_options_section(self):
        """
        Build the plasticity correction options section.

        Returns:
            QGroupBox: Group box for plasticity options (initially hidden).
        """
        plasticity_options_group = QGroupBox("Plasticity Correction Options")
        plasticity_options_group.setStyleSheet(GROUP_BOX_STYLE)

        # Placeholder layout (extend with real options later)
        layout = QVBoxLayout()

        material_profile_button = QPushButton('Enter Material Profile')
        material_profile_button.setStyleSheet(BUTTON_STYLE)
        material_profile_button.setFont(QFont('Arial', 8))

        temperature_field_button = QPushButton('Read Temperature Field File (.txt)')
        temperature_field_button.setStyleSheet(BUTTON_STYLE)
        temperature_field_button.setFont(QFont('Arial', 8))
        temperature_field_path = QLineEdit()
        temperature_field_path.setReadOnly(True)
        temperature_field_path.setStyleSheet(READONLY_INPUT_STYLE)

        file_row = QHBoxLayout()
        file_row.addWidget(temperature_field_button)
        file_row.addWidget(temperature_field_path)
        file_row.setStretch(0, 0)
        file_row.setStretch(1, 1)

        method_row = QHBoxLayout()
        method_label = QLabel("Select Method:")
        method_combo = QComboBox()
        method_combo.addItems(["Neuber", "Glinka", "Incremental Buczynski-Glinka (IBG)"])
        method_row.addWidget(method_label)
        method_row.addWidget(method_combo)
        method_row.addStretch()

        iteration_row = QHBoxLayout()
        iteration_label = QLabel("Iteration Controls:")
        iteration_label.setMinimumWidth(120)
        max_iter_label = QLabel("Max Iterations")
        max_iter_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        max_iter_input = QLineEdit("60")
        max_iter_input.setMaximumWidth(70)
        max_iter_validator = QIntValidator(1, 10000, max_iter_input)
        max_iter_input.setValidator(max_iter_validator)
        tolerance_label = QLabel("Tolerance")
        tolerance_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        tolerance_input = QLineEdit("1e-10")
        tolerance_input.setMaximumWidth(100)
        tolerance_validator = QDoubleValidator(0.0, 1.0, 12, tolerance_input)
        tolerance_validator.setNotation(QDoubleValidator.ScientificNotation)
        tolerance_input.setValidator(tolerance_validator)
        iteration_row.addWidget(iteration_label)
        iteration_row.addWidget(max_iter_label)
        iteration_row.addWidget(max_iter_input)
        iteration_row.addWidget(tolerance_label)
        iteration_row.addWidget(tolerance_input)
        iteration_row.addStretch()

        warning_label = QLabel("Warning: Relaxed iteration settings may impact accuracy.")
        warning_label.setStyleSheet("color: #b36b00; font-style: italic;")
        warning_label.setVisible(False)

        layout.addWidget(material_profile_button)
        layout.addLayout(file_row)
        layout.addLayout(method_row)
        layout.addLayout(iteration_row)
        layout.addWidget(warning_label)
        plasticity_options_group.setLayout(layout)
        plasticity_options_group.setVisible(False)

        self.components['plasticity_options_group'] = plasticity_options_group
        self.components['material_profile_button'] = material_profile_button
        self.components['temperature_field_button'] = temperature_field_button
        self.components['temperature_field_path'] = temperature_field_path
        self.components['plasticity_method_combo'] = method_combo
        self.components['plasticity_max_iter_input'] = max_iter_input
        self.components['plasticity_tolerance_input'] = tolerance_input
        self.components['plasticity_warning_label'] = warning_label

        return plasticity_options_group
    
    def build_console_tabs_section(self):
        """
        Build the console and plotting tabs section.
        
        Returns:
            QTabWidget: Tab widget containing console and plots.
        """
        from PyQt5.QtWidgets import QTextEdit
        from PyQt5.QtGui import QFont
        
        # Console
        console_textbox = QTextEdit()
        console_textbox.setReadOnly(True)
        console_textbox.setStyleSheet(CONSOLE_STYLE)
        console_textbox.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        console_textbox.setText('Console Output:\n')

        terminal_font = QFont("Consolas", 8)
        terminal_font.setStyleHint(QFont.Monospace)
        console_textbox.setFont(terminal_font)

        # Create tab widget
        show_output_tab_widget = QTabWidget()
        show_output_tab_widget.setStyleSheet(TAB_STYLE)
        show_output_tab_widget.addTab(console_textbox, "Console")
        
        # Matplotlib plot for time history
        plot_single_node_tab = MatplotlibWidget()
        plot_single_node_tab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        show_output_tab_widget.addTab(plot_single_node_tab, "Plot (Time History)")
        show_output_tab_widget.setTabVisible(
            show_output_tab_widget.indexOf(plot_single_node_tab), False
        )
        
        # Plotly plot for modal coordinates
        plot_modal_coords_tab = PlotlyWidget()
        show_output_tab_widget.addTab(plot_modal_coords_tab, "Plot (Modal Coordinates)")
        show_output_tab_widget.setTabVisible(
            show_output_tab_widget.indexOf(plot_modal_coords_tab), False
        )
        
        # Store components
        self.components['console_textbox'] = console_textbox
        self.components['show_output_tab_widget'] = show_output_tab_widget
        self.components['plot_single_node_tab'] = plot_single_node_tab
        self.components['plot_modal_coords_tab'] = plot_modal_coords_tab
        
        return show_output_tab_widget
    
    def build_progress_section(self):
        """
        Build the progress bar.
        
        Returns:
            QProgressBar: Progress bar widget.
        """
        progress_bar = QProgressBar()
        progress_bar.setStyleSheet(PROGRESS_BAR_STYLE)
        progress_bar.setValue(0)
        progress_bar.setAlignment(Qt.AlignCenter)
        progress_bar.setTextVisible(True)
        progress_bar.setVisible(False)
        
        self.components['progress_bar'] = progress_bar
        
        return progress_bar
    
    def build_solve_button(self):
        """
        Build the solve button.
        
        Returns:
            QPushButton: Solve button.
        """
        solve_button = QPushButton('SOLVE')
        solve_button.setStyleSheet(BUTTON_STYLE)
        solve_button.setFont(QFont('Arial', 9, QFont.Bold))
        
        self.components['solve_button'] = solve_button
        
        return solve_button
    
    def set_window_palette(self, widget):
        """
        Set the window background color palette.
        
        Args:
            widget: The widget to apply the palette to.
        """
        palette = widget.palette()
        palette.setColor(QPalette.Window, QColor(*WINDOW_BACKGROUND_COLOR))
        widget.setPalette(palette)
    
    def build_complete_layout(self):
        """
        Build the complete solver tab layout with all sections.
        
        Returns:
            tuple: (main_layout, components_dict)
        """
        main_layout = QVBoxLayout()
        
        # Build all sections
        file_group = self.build_file_input_section()
        output_group = self.build_output_selection_section()
        fatigue_params_group = self.build_fatigue_params_section()
        single_node_group = self.build_single_node_section()
        plasticity_options_group = self.build_plasticity_options_section()
        solve_button = self.build_solve_button()
        console_tabs = self.build_console_tabs_section()
        progress_bar = self.build_progress_section()
        
        # Combine output sections horizontally
        hbox_user_inputs = QHBoxLayout()
        hbox_user_inputs.addWidget(output_group)
        hbox_user_inputs.addWidget(fatigue_params_group)
        hbox_user_inputs.addWidget(single_node_group)
        hbox_user_inputs.addWidget(plasticity_options_group)
        
        # Add all to main layout
        main_layout.addWidget(file_group)
        main_layout.addLayout(hbox_user_inputs)
        main_layout.addWidget(solve_button)
        main_layout.addWidget(console_tabs)
        main_layout.addWidget(progress_bar)
        
        return main_layout, self.components

