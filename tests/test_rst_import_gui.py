"""Focused GUI-state tests for the two-stage modal RST importer."""

import os
import sys
from types import SimpleNamespace

import numpy as np

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PyQt5.QtWidgets import QApplication, QComboBox, QMessageBox

from mars_solver.core.data_models import DeformationData, ModalData
from ui.builders.solver_ui import SolverTabUIBuilder
from ui.dialogs.rst_import_dialog import RstImportDialog
from ui.handlers.file_handler import FileLoaderThread, SolverFileHandler
from ui.handlers.ui_state_handler import SolverUIHandler
from ui.solver_tab import SolverTab
from ui import tooltips


_QT_APP = None


def _app():
    global _QT_APP
    _QT_APP = QApplication.instance() or QApplication([])
    return _QT_APP


class _Path:
    def __init__(self):
        self.text = None

    def setText(self, text):
        self.text = text

    def clear(self):
        self.text = ""


class _Checkbox:
    def __init__(self):
        self.checked = False

    def setChecked(self, checked):
        self.checked = bool(checked)


class _Console:
    def __init__(self):
        self.lines = []

    def append(self, text):
        self.lines.append(text)


class _Counter:
    def __init__(self):
        self.calls = 0

    def __call__(self, *_args):
        self.calls += 1


def test_file_loader_thread_forwards_positional_and_keyword_arguments():
    _app()
    received = []
    thread = FileLoaderThread(lambda left, right=0: left + right, 4, right=7)
    thread.finished.connect(received.append)

    thread.run()

    assert received == [11]


def test_rst_first_launch_help_distinguishes_prerequisite_from_bundled_client():
    _app()
    builder = SolverTabUIBuilder()
    file_group = builder.build_file_input_section()

    assert file_group is not None
    assert builder.components["rst_file_button"].isEnabled() is False
    assert builder.components["rst_file_button"].isHidden() is True
    assert builder.components["stress_file_button"].isHidden() is False
    assert "Load modal coordinates" in builder.components[
        "rst_file_path"
    ].placeholderText()
    assert "Why this is initially disabled" in tooltips.RST_FILE_BUTTON
    assert ".mcf/.pch first" in tooltips.RST_FILE_BUTTON
    assert "includes ansys-dpf-core 0.16.1" in tooltips.RST_FILE_BUTTON
    assert "Load modal coordinates" in tooltips.RST_FILE_PATH


def test_modal_result_modes_show_only_their_own_controls():
    _app()
    builder = SolverTabUIBuilder()
    file_group = builder.build_file_input_section()
    tab = SimpleNamespace(**builder.components, _modal_input_mode="csv")
    handler = SolverUIHandler(tab)
    handler.update_modal_input_mode()

    assert file_group is not None
    assert tab.modal_input_mode_combo.currentData() == "csv"
    assert tab.stress_file_button.isHidden() is False
    assert tab.rst_file_button.isHidden() is True
    assert tab.deformations_checkbox.isHidden() is False

    tab.modal_input_mode_combo.setCurrentIndex(
        tab.modal_input_mode_combo.findData("rst")
    )
    tab._modal_input_mode = "rst"
    handler.update_modal_input_mode()

    assert tab.rst_file_button.isHidden() is False
    assert tab.stress_file_button.isHidden() is True
    assert tab.deformations_checkbox.isHidden() is True
    assert tab.force_moment_checkbox.isHidden() is True
    assert "one modal .rst file" in tab.modal_input_mode_help.text()


def test_switching_modal_result_source_confirms_before_clearing(monkeypatch):
    _app()
    combo = QComboBox()
    combo.addItem("CSV", "csv")
    combo.addItem("RST", "rst")
    combo.setCurrentIndex(1)
    clear_results = _Counter()
    refresh_mode = _Counter()
    tab = SimpleNamespace(
        modal_input_mode_combo=combo,
        _modal_input_mode="csv",
        stress_loaded=True,
        deformation_loaded=False,
        force_moment_loaded=False,
        _clear_modal_result_inputs=clear_results,
        ui_handler=SimpleNamespace(update_modal_input_mode=refresh_mode),
    )
    monkeypatch.setattr(
        "ui.solver_tab.QMessageBox.question",
        lambda *_args: QMessageBox.Yes,
    )

    SolverTab.on_modal_input_mode_changed(tab, 1)

    assert clear_results.calls == 1
    assert refresh_mode.calls == 1
    assert tab._modal_input_mode == "rst"


def test_cancel_and_load_error_preserve_existing_modal_state(monkeypatch):
    _app()
    old_stress = object()
    tab = SimpleNamespace(
        stress_data=old_stress,
        setEnabled=lambda _enabled: None,
    )
    handler = SolverFileHandler(tab)
    load_calls = []

    class _CancelledDialog:
        def __init__(self, *_args):
            pass

        def exec_(self):
            return 0

    monkeypatch.setattr("ui.handlers.file_handler.RstImportDialog", _CancelledDialog)
    monkeypatch.setattr(handler, "_load_modal_rst", lambda *args: load_calls.append(args))
    monkeypatch.setattr("ui.handlers.file_handler.QMessageBox.warning", lambda *_args: None)

    handler._on_rst_inspected(object(), "modal.rst")
    handler._on_rst_load_error("failed")

    assert tab.stress_data is old_stress
    assert load_calls == []


def test_rst_dialog_maps_capabilities_scope_and_shell_layer_to_options():
    _app()
    metadata = SimpleNamespace(
        expected_modes=2,
        available_modes=3,
        set_ids=(1, 4, 7),
        frequencies_hz=(12.0, 24.0, 36.0),
        warnings=("One extra mode will be ignored.",),
        capability_errors={},
        capabilities=SimpleNamespace(
            stress=True,
            deformation=True,
            force_moment=False,
        ),
        scopes=(
            SimpleNamespace(
                name="All result-support nodes",
                stress_node_count=10,
                deformation_node_count=8,
                force_moment_node_count=0,
            ),
            SimpleNamespace(
                name="DEFORMATION_ONLY",
                stress_node_count=0,
                deformation_node_count=4,
                force_moment_node_count=0,
            ),
        ),
        shell_layers=("top", "bottom", "mid"),
        default_shell_layer="top",
    )
    dialog = RstImportDialog(metadata)
    dialog.stress_checkbox.setChecked(False)
    dialog.deformation_checkbox.setChecked(True)

    options = dialog.get_options()

    assert options.expected_modes == 2
    assert options.scope_name == "All result-support nodes"
    assert options.load_stress is False
    assert options.load_deformation is True
    assert options.load_force_moment is False
    assert options.shell_layer == "top"
    assert dialog.force_moment_checkbox.isEnabled() is False

    dialog.scope_combo.setCurrentIndex(1)
    assert dialog.stress_checkbox.isEnabled() is False
    assert dialog.deformation_checkbox.isEnabled() is True
    assert dialog.deformation_checkbox.isChecked() is True
    dialog.close()


def test_rst_bundle_replaces_modal_fields_atomically_and_resets_stale_results():
    reset = _Counter()
    clear_plot = _Counter()
    hide_tabs = _Counter()
    show_modal_tab = _Counter()
    clear_display = _Counter()
    update_skip = _Counter()
    update_outputs = _Counter()
    update_solve = _Counter()
    emit_initial = _Counter()

    tab = SimpleNamespace(
        stress_data=object(),
        deformation_data=None,
        force_moment_data=object(),
        stress_loaded=True,
        deformation_loaded=False,
        force_moment_loaded=True,
        rst_file_path=_Path(),
        stress_file_path=_Path(),
        deformations_file_path=_Path(),
        force_moment_file_path=_Path(),
        deformations_checkbox=_Checkbox(),
        force_moment_checkbox=_Checkbox(),
        analysis_engine=SimpleNamespace(reset=reset),
        plot_single_node_tab=SimpleNamespace(clear_plot=clear_plot),
        ui_handler=SimpleNamespace(
            _hide_plot_tabs=hide_tabs,
            _show_modal_coords_tab=show_modal_tab,
            _update_skip_modes_combo=update_skip,
            update_output_checkboxes_state=update_outputs,
            _update_solve_button_state=update_solve,
        ),
        modal_data=ModalData(
            modal_coord=np.ones((2, 3)),
            time_values=np.arange(3, dtype=float),
        ),
        console_textbox=_Console(),
        window=lambda: SimpleNamespace(
            display_tab=SimpleNamespace(_clear_visualization=clear_display)
        ),
        _check_and_emit_initial_data=emit_initial,
    )
    deformation = DeformationData(
        node_ids=np.array([2]),
        modal_ux=np.ones((1, 2)),
        modal_uy=np.ones((1, 2)),
        modal_uz=np.ones((1, 2)),
        node_coords=np.zeros((1, 3)),
    )
    bundle = SimpleNamespace(
        stress_data=None,
        deformation_data=deformation,
        force_moment_data=None,
        warnings=("warning",),
    )

    SolverTab.on_modal_rst_loaded(tab, bundle, "modal.rst")

    assert tab.stress_data is None
    assert tab.deformation_data is deformation
    assert tab.force_moment_data is None
    assert tab.stress_loaded is False
    assert tab.deformation_loaded is True
    assert tab.force_moment_loaded is False
    assert tab.rst_file_path.text == "modal.rst"
    assert tab.stress_file_path.text == ""
    assert tab.deformations_file_path.text == ""
    assert tab.force_moment_file_path.text == ""
    assert reset.calls == clear_plot.calls == clear_display.calls == emit_initial.calls == 1


def test_initial_display_falls_back_to_deformation_coordinates():
    emitted = []
    deformation = SimpleNamespace(
        node_ids=np.array([20, 21]),
        node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
    )
    tab = SimpleNamespace(
        coord_loaded=True,
        modal_data=SimpleNamespace(time_values=np.array([0.0, 1.0])),
        stress_data=SimpleNamespace(node_ids=np.array([10]), node_coords=None),
        deformation_data=deformation,
        force_moment_data=None,
        deformation_loaded=True,
        initial_data_loaded=SimpleNamespace(emit=lambda value: emitted.append(value)),
    )

    SolverTab._check_and_emit_initial_data(tab)

    assert len(emitted) == 1
    np.testing.assert_array_equal(emitted[0][1], deformation.node_coords)
    np.testing.assert_array_equal(emitted[0][2], deformation.node_ids)
