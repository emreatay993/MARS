"""Options dialog for importing modal result fields from an Ansys RST file."""

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
)

from file_io.rst_service import ALL_SCOPE, RstLoadOptions
from ui.styles.style_constants import DIALOG_STYLE


class RstImportDialog(QDialog):
    """Present the capabilities discovered during the RST inspection pass."""

    def __init__(self, metadata, parent=None):
        super().__init__(parent)
        self.metadata = metadata
        self.setWindowTitle("Import Modal Results")
        self.setMinimumWidth(560)
        self.setStyleSheet(DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.addWidget(self._build_summary())
        layout.addWidget(self._build_scope_group())
        layout.addWidget(self._build_result_group())

        messages = list(metadata.warnings or [])
        capability_errors = metadata.capability_errors or {}
        if isinstance(capability_errors, dict):
            messages.extend(
                f"{name.replace('_', ' ').title()}: {message}"
                for name, message in capability_errors.items()
                if message
            )
        else:
            messages.extend(str(message) for message in capability_errors if message)
        if messages:
            warning_label = QLabel("\n".join(f"• {message}" for message in messages))
            warning_label.setWordWrap(True)
            warning_label.setStyleSheet("color: #ffcc66;")
            layout.addWidget(warning_label)

        runtime_label = QLabel(
            "Direct RST import requires ansys-dpf-core 0.16.1 and a compatible "
            "installed Ansys 2025 R2 or newer DPF runtime."
        )
        runtime_label.setWordWrap(True)
        layout.addWidget(runtime_label)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.load_button = self.button_box.button(QDialogButtonBox.Ok)
        self.load_button.setText("Load")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        for checkbox in (
            self.stress_checkbox,
            self.deformation_checkbox,
            self.force_moment_checkbox,
        ):
            checkbox.toggled.connect(self._update_state)
        self.scope_combo.currentIndexChanged.connect(self._update_scope_capabilities)
        self._update_scope_capabilities()
        self._select_default_result()
        self._update_state()

    def _build_summary(self):
        frequencies = list(self.metadata.frequencies_hz or [])
        if frequencies:
            frequency_text = f"{frequencies[0]:.6g} to {frequencies[-1]:.6g} Hz"
        else:
            frequency_text = "not reported"
        label = QLabel(
            f"Modes to import: {self.metadata.expected_modes} of "
            f"{self.metadata.available_modes}\n"
            f"Set IDs: {', '.join(str(value) for value in self.metadata.set_ids)}\n"
            f"Frequencies: {frequency_text}"
        )
        label.setWordWrap(True)
        return label

    def _build_scope_group(self):
        group = QGroupBox("Scope")
        form = QFormLayout(group)
        self.scope_combo = QComboBox()
        for scope in self.metadata.scopes:
            details = []
            if scope.stress_node_count:
                details.append(f"stress {scope.stress_node_count}")
            if scope.deformation_node_count:
                details.append(f"deformation {scope.deformation_node_count}")
            if scope.force_moment_node_count:
                details.append(f"force/moment {scope.force_moment_node_count}")
            suffix = f" ({', '.join(details)})" if details else ""
            self.scope_combo.addItem(f"{scope.name}{suffix}", scope.name)
        form.addRow("Result scope", self.scope_combo)
        return group

    def _build_result_group(self):
        group = QGroupBox("Results")
        form = QFormLayout(group)
        capabilities = self.metadata.capabilities

        self.stress_checkbox = QCheckBox("Six-component modal stress (MPa)")
        self.stress_checkbox.setEnabled(bool(capabilities.stress))
        self.deformation_checkbox = QCheckBox("Modal deformation (mm)")
        self.deformation_checkbox.setEnabled(bool(capabilities.deformation))
        self.force_moment_checkbox = QCheckBox(
            "Element-nodal force and moment (N, N·mm)"
        )
        self.force_moment_checkbox.setEnabled(bool(capabilities.force_moment))

        form.addRow(self.stress_checkbox)
        form.addRow(self.deformation_checkbox)
        form.addRow(self.force_moment_checkbox)

        self.shell_layer_combo = QComboBox()
        for layer in self.metadata.shell_layers or ():
            self.shell_layer_combo.addItem(str(layer).title(), str(layer).lower())
        default_layer = str(self.metadata.default_shell_layer or "top").lower()
        default_index = self.shell_layer_combo.findData(default_layer)
        if default_index >= 0:
            self.shell_layer_combo.setCurrentIndex(default_index)
        self.shell_layer_label = QLabel("Shell stress layer")
        has_shell_layers = self.shell_layer_combo.count() > 0
        self.shell_layer_label.setVisible(has_shell_layers)
        self.shell_layer_combo.setVisible(has_shell_layers)
        form.addRow(self.shell_layer_label, self.shell_layer_combo)
        return group

    def _select_default_result(self):
        """Choose one useful default without starting an unexpectedly large import."""
        if any(
            checkbox.isEnabled() and checkbox.isChecked()
            for checkbox in (
                self.stress_checkbox,
                self.deformation_checkbox,
                self.force_moment_checkbox,
            )
        ):
            return
        for checkbox in (
            self.stress_checkbox,
            self.deformation_checkbox,
            self.force_moment_checkbox,
        ):
            if checkbox.isEnabled():
                checkbox.setChecked(True)
                return

    def _update_scope_capabilities(self, _index=None):
        """Restrict result selections to data supported by the chosen scope."""
        index = self.scope_combo.currentIndex()
        if index < 0 or index >= len(self.metadata.scopes):
            return
        scope = self.metadata.scopes[index]
        capabilities = self.metadata.capabilities
        availability = (
            (self.stress_checkbox, capabilities.stress and scope.stress_node_count > 0),
            (
                self.deformation_checkbox,
                capabilities.deformation and scope.deformation_node_count > 0,
            ),
            (
                self.force_moment_checkbox,
                capabilities.force_moment and scope.force_moment_node_count > 0,
            ),
        )
        for checkbox, enabled in availability:
            checkbox.setEnabled(bool(enabled))
            if not enabled:
                checkbox.setChecked(False)
        self._select_default_result()
        self._update_state()

    def _update_state(self):
        selected = any(
            checkbox.isEnabled() and checkbox.isChecked()
            for checkbox in (
                self.stress_checkbox,
                self.deformation_checkbox,
                self.force_moment_checkbox,
            )
        )
        self.load_button.setEnabled(selected)
        self.shell_layer_combo.setEnabled(
            self.stress_checkbox.isEnabled()
            and self.stress_checkbox.isChecked()
            and self.shell_layer_combo.count() > 0
        )

    def get_options(self):
        """Return immutable service options matching the current selections."""
        return RstLoadOptions(
            expected_modes=self.metadata.expected_modes,
            scope_name=self.scope_combo.currentData() or ALL_SCOPE,
            load_stress=self.stress_checkbox.isChecked(),
            load_deformation=self.deformation_checkbox.isChecked(),
            load_force_moment=self.force_moment_checkbox.isChecked(),
            shell_layer=(
                self.shell_layer_combo.currentData()
                if self.shell_layer_combo.count() > 0
                else None
            ),
        )
