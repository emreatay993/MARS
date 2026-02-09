"""
Regression tests for Display tab handler behavior.
"""

import os
import sys
from types import SimpleNamespace

import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ui.handlers.display_results_handler import DisplayResultsHandler
from ui.handlers.display_visualization_handler import DisplayVisualizationHandler


class FakeSpinBox:
    def __init__(self, value=0.0):
        self._value = float(value)
        self.minimum = None
        self.maximum = None

    def value(self):
        return self._value

    def setValue(self, value):
        self._value = float(value)

    def setRange(self, minimum, maximum):
        self.minimum = float(minimum)
        self.maximum = float(maximum)

    def blockSignals(self, _block):
        return None


class FakeComboBox:
    def __init__(self):
        self._items = []
        self._index = -1
        self.enabled = True

    def blockSignals(self, _block):
        return None

    def clear(self):
        self._items = []
        self._index = -1

    def addItems(self, items):
        for item in items:
            self.addItem(item)

    def addItem(self, text, user_data=None):
        self._items.append((str(text), user_data))
        if self._index == -1:
            self._index = 0

    def setCurrentText(self, text):
        target = str(text)
        for idx, (item_text, _data) in enumerate(self._items):
            if item_text == target:
                self._index = idx
                return

    def setCurrentIndex(self, index):
        if 0 <= index < len(self._items):
            self._index = index

    def findData(self, target_data):
        for idx, (_text, data) in enumerate(self._items):
            if data == target_data:
                return idx
        return -1

    def currentText(self):
        if 0 <= self._index < len(self._items):
            return self._items[self._index][0]
        return ""

    def currentData(self):
        if 0 <= self._index < len(self._items):
            return self._items[self._index][1]
        return None

    def count(self):
        return len(self._items)

    def setEnabled(self, enabled):
        self.enabled = bool(enabled)


class FakeMesh:
    def __init__(self, arrays, active_scalars_name=None):
        self._arrays = {name: np.asarray(values) for name, values in arrays.items()}
        self.array_names = list(self._arrays.keys())
        self.active_scalars_name = active_scalars_name
        self.n_points = len(next(iter(self._arrays.values()))) if self._arrays else 0

    def __getitem__(self, key):
        return self._arrays[key]


class FakeVisualHandler:
    def __init__(self):
        self.calls = []

    def apply_scalar_field(self, field_name, values):
        self.calls.append((field_name, np.asarray(values)))
        return True


class FakeActor:
    def __init__(self):
        self.mapper = SimpleNamespace(scalar_range=None)

    def GetProperty(self):
        return SimpleNamespace(SetPointSize=lambda _value: None)


class FakeCamera:
    def __init__(self):
        self.parallel_projection = False
        self.calls = 0

    def SetParallelProjection(self, value):
        self.parallel_projection = bool(value)
        self.calls += 1


class FakePlotter:
    def __init__(self, fail_on_parallel_enable=False):
        self.fail_on_parallel_enable = fail_on_parallel_enable
        self.camera = FakeCamera()
        self.enable_parallel_projection_calls = 0
        self.reset_camera_calls = 0
        self.render_calls = 0
        self.clear_calls = 0

    def clear(self):
        self.clear_calls += 1

    def add_mesh(self, *_args, **_kwargs):
        return FakeActor()

    def reset_camera(self):
        self.reset_camera_calls += 1

    def enable_parallel_projection(self):
        self.enable_parallel_projection_calls += 1
        if self.fail_on_parallel_enable:
            raise RuntimeError("parallel projection helper unavailable")

    def render(self):
        self.render_calls += 1


class FakeResultsTab:
    def __init__(self):
        self.result_group_combo = FakeComboBox()
        self.result_component_combo = FakeComboBox()
        self.result_mode_combo = FakeComboBox()
        self.scalar_min_spin = FakeSpinBox(0.0)
        self.scalar_max_spin = FakeSpinBox(1.0)
        self.current_mesh = None


class FakeVisualizationTab:
    def __init__(self, plotter):
        self.plotter = plotter
        self.point_size = FakeSpinBox(3.0)
        self.scalar_min_spin = FakeSpinBox(0.0)
        self.scalar_max_spin = FakeSpinBox(1.0)
        self.current_mesh = None
        self.current_actor = None
        self.data_column = ""
        self.camera_widget = None
        self.hover_annotation = None
        self.hover_observer = None
        self.last_hover_time = 0.0
        self._camera_widget_pending = False

    def isVisible(self):
        return False


def test_configure_time_point_catalog_keeps_existing_modes_and_solver_context():
    existing_catalog = {
        "Von Mises": {
            "Magnitude": {
                "max_over_time": {"field_name": "Max VM", "values": [10.0, 20.0, 30.0]},
                "time_of_max": {"field_name": "Time of Max VM", "values": [0.0, 0.1, 0.2]},
                "selected_time": {"field_name": "STALE FIELD", "values": [-1.0, -1.0, -1.0]},
            }
        }
    }
    state = SimpleNamespace(result_catalog=existing_catalog, result_selection={}, current_mesh=None)
    tab = FakeResultsTab()
    visual_handler = FakeVisualHandler()
    handler = DisplayResultsHandler(tab=tab, state=state, visual_handler=visual_handler)
    solver_marker = object()
    handler._active_solver = solver_marker

    mesh = FakeMesh({"SVM (MPa)": np.array([1.0, 2.0, 3.0])}, active_scalars_name="SVM (MPa)")
    state.current_mesh = mesh
    handler.configure_time_point_catalog(mesh, default_field="SVM (MPa)")

    updated_modes = state.result_catalog["Von Mises"]["Magnitude"]
    assert set(updated_modes.keys()) == {"max_over_time", "time_of_max", "selected_time"}
    assert updated_modes["selected_time"]["field_name"] == "SVM (MPa)"
    assert handler._active_solver is solver_marker
    assert state.result_selection["group"] == "Von Mises"
    assert state.result_selection["component"] == "Magnitude"
    assert state.result_selection["mode"] == "selected_time"


def test_update_visualization_enables_parallel_projection():
    mesh = FakeMesh({"Result": np.array([1.0, 2.0, 3.0])}, active_scalars_name="Result")
    plotter = FakePlotter(fail_on_parallel_enable=False)
    tab = FakeVisualizationTab(plotter=plotter)
    state = SimpleNamespace(
        current_mesh=mesh,
        current_actor=None,
        data_column="Result",
        camera_widget=None,
        hover_annotation=None,
        hover_observer=None,
        last_hover_time=0.0,
    )
    handler = DisplayVisualizationHandler(tab=tab, state=state, viz_manager=None)

    handler.update_visualization()

    assert plotter.enable_parallel_projection_calls == 1
    assert plotter.camera.calls == 0
    assert tab._camera_widget_pending is True


def test_update_visualization_falls_back_to_camera_parallel_projection():
    mesh = FakeMesh({"Result": np.array([1.0, 2.0, 3.0])}, active_scalars_name="Result")
    plotter = FakePlotter(fail_on_parallel_enable=True)
    tab = FakeVisualizationTab(plotter=plotter)
    state = SimpleNamespace(
        current_mesh=mesh,
        current_actor=None,
        data_column="Result",
        camera_widget=None,
        hover_annotation=None,
        hover_observer=None,
        last_hover_time=0.0,
    )
    handler = DisplayVisualizationHandler(tab=tab, state=state, viz_manager=None)

    handler.update_visualization()

    assert plotter.enable_parallel_projection_calls == 1
    assert plotter.camera.parallel_projection is True
    assert plotter.camera.calls == 1
