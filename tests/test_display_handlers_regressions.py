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
from ui.handlers.display_interaction_handler import DisplayInteractionHandler
from ui.handlers.display_visualization_handler import DisplayVisualizationHandler
from ui.handlers.display_animation_handler import DisplayAnimationHandler
from core.visualization import HotspotDetector


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


class FakeCameraWidget:
    def __init__(self):
        self.enabled = False
        self.enabled_on_calls = 0
        self.enabled_off_calls = 0

    def EnabledOn(self):
        self.enabled = True
        self.enabled_on_calls += 1

    def EnabledOff(self):
        self.enabled = False
        self.enabled_off_calls += 1


class FakePlotter:
    def __init__(self, fail_on_parallel_enable=False):
        self.fail_on_parallel_enable = fail_on_parallel_enable
        self.camera = FakeCamera()
        self.camera_position = (
            (5.0, 6.0, 7.0),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
        )
        self.enable_parallel_projection_calls = 0
        self.reset_camera_calls = 0
        self.render_calls = 0
        self.clear_calls = 0
        self.add_camera_widget_calls = 0

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

    def add_camera_orientation_widget(self):
        self.add_camera_widget_calls += 1
        return FakeCameraWidget()


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


class FakeAnimationMesh:
    def __init__(self, points, arrays, active_scalars_name="Result"):
        self.points = np.asarray(points, dtype=float)
        self._arrays = {name: np.asarray(values).copy() for name, values in arrays.items()}
        self.array_names = list(self._arrays.keys())
        self.active_scalars_name = active_scalars_name
        self.n_points = self.points.shape[0]
        self.points_modified_calls = 0

    def __getitem__(self, key):
        return self._arrays[key]

    def __setitem__(self, key, value):
        if key not in self.array_names:
            self.array_names.append(key)
        self._arrays[key] = np.asarray(value).copy()

    def set_active_scalars(self, key):
        self.active_scalars_name = key

    def points_modified(self):
        self.points_modified_calls += 1


class FakeAnimationManager:
    def __init__(self, frame_scalars, frame_coords, frame_times, data_column_name="Result"):
        self.precomputed_scalars = np.asarray(frame_scalars)
        self.precomputed_coords = np.asarray(frame_coords)
        self.precomputed_anim_times = np.asarray(frame_times)
        self.data_column_name = data_column_name

    def get_num_frames(self):
        return len(self.precomputed_anim_times)

    def get_frame_data(self, frame_index):
        return (
            self.precomputed_scalars[frame_index],
            self.precomputed_coords[frame_index],
            self.precomputed_anim_times[frame_index],
        )


class FakeAnimationPlotter:
    def __init__(self):
        self.camera_position = (
            (10.0, 20.0, 30.0),
            (1.0, 2.0, 3.0),
            (0.0, 0.0, 1.0),
        )
        self.render_calls = 0
        self.screenshot_calls = []

    def render(self):
        self.render_calls += 1

    def screenshot(self, **kwargs):
        self.screenshot_calls.append(kwargs)
        return np.full((13, 17, 3), len(self.screenshot_calls), dtype=np.uint8)


class FakeAnimationTimer:
    def __init__(self, active=True):
        self.active = active
        self.stop_calls = 0
        self.start_calls = 0
        self.started_intervals = []

    def isActive(self):
        return self.active

    def stop(self):
        self.active = False
        self.stop_calls += 1

    def start(self, interval):
        self.active = True
        self.start_calls += 1
        self.started_intervals.append(interval)


class FakeAnimationTextActor:
    def __init__(self, text):
        self.text = text

    def GetInput(self):
        return self.text

    def SetInput(self, text):
        self.text = text


class FakeIntegerSpinBox:
    def __init__(self, value):
        self._value = int(value)

    def value(self):
        return self._value


class FakeAnimationTab:
    def __init__(self, mesh, plotter, actor):
        self.current_mesh = mesh
        self.plotter = plotter
        self.current_actor = actor
        self.anim_interval_spin = FakeIntegerSpinBox(10)
        self.freeze_tracked_node = False
        self.freeze_baseline = None
        self.target_node_index = None
        self.target_node_label_actor = None
        self.target_node_marker_actor = None
        self.label_point_data = None
        self.marker_poly = None


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


def test_configure_time_point_catalog_exposes_force_shear_components():
    state = SimpleNamespace(result_catalog={}, result_selection={}, current_mesh=None)
    tab = FakeResultsTab()
    visual_handler = FakeVisualHandler()
    handler = DisplayResultsHandler(tab=tab, state=state, visual_handler=visual_handler)

    mesh = FakeMesh(
        {
            "Force (N)": np.array([10.0, 20.0, 30.0]),
            "FX (N)": np.array([1.0, 2.0, 3.0]),
            "FY (N)": np.array([4.0, 5.0, 6.0]),
            "FZ (N)": np.array([7.0, 8.0, 9.0]),
            "Shear XY (N)": np.array([4.123, 5.385, 6.708]),
            "Shear XZ (N)": np.array([7.071, 8.246, 9.487]),
            "Shear YZ (N)": np.array([8.062, 9.434, 10.817]),
        },
        active_scalars_name="Shear XY (N)",
    )
    state.current_mesh = mesh

    handler.configure_time_point_catalog(mesh, default_field="Shear XY (N)")

    force_components = state.result_catalog["Force/Moment"]
    assert "Shear XY" in force_components
    assert "Shear XZ" in force_components
    assert "Shear YZ" in force_components
    assert force_components["Shear XY"]["selected_time"]["field_name"] == "Shear XY (N)"
    assert force_components["Shear XZ"]["selected_time"]["field_name"] == "Shear XZ (N)"
    assert force_components["Shear YZ"]["selected_time"]["field_name"] == "Shear YZ (N)"
    assert state.result_selection["group"] == "Force/Moment"
    assert state.result_selection["component"] == "Shear XY"
    assert state.result_selection["mode"] == "selected_time"


def test_solver_csv_values_are_aligned_to_current_mesh_node_ids(tmp_path):
    csv_path = tmp_path / "max_element_nodal_force.csv"
    csv_path.write_text(
        "NodeID,Force_Mag_Max,X,Y,Z\n"
        "10,100.0,0,0,0\n"
        "20,200.0,0,0,0\n"
        "30,300.0,0,0,0\n",
        encoding="utf-8",
    )

    state = SimpleNamespace(
        result_catalog={},
        result_selection={},
        current_mesh=FakeMesh({"NodeID": np.array([30, 10, 20])}),
    )
    tab = FakeResultsTab()
    visual_handler = FakeVisualHandler()
    handler = DisplayResultsHandler(tab=tab, state=state, visual_handler=visual_handler)

    values = handler._load_solver_array(
        SimpleNamespace(output_directory=str(tmp_path)),
        "max_element_nodal_force.csv",
        "Force_Mag_Max",
    )

    np.testing.assert_allclose(values, np.array([300.0, 100.0, 200.0]))


def test_solver_csv_values_are_not_positionally_applied_to_wrong_node_ids(tmp_path):
    csv_path = tmp_path / "max_element_nodal_force.csv"
    csv_path.write_text(
        "NodeID,Force_Mag_Max,X,Y,Z\n"
        "10,100.0,0,0,0\n"
        "20,200.0,0,0,0\n"
        "30,300.0,0,0,0\n",
        encoding="utf-8",
    )

    state = SimpleNamespace(
        result_catalog={},
        result_selection={},
        current_mesh=FakeMesh({"NodeID": np.array([30, 10, 99])}),
    )
    tab = FakeResultsTab()
    visual_handler = FakeVisualHandler()
    handler = DisplayResultsHandler(tab=tab, state=state, visual_handler=visual_handler)

    values = handler._load_solver_array(
        SimpleNamespace(output_directory=str(tmp_path)),
        "max_element_nodal_force.csv",
        "Force_Mag_Max",
    )

    assert values is None


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


def test_update_visualization_preserves_camera_when_requested():
    mesh = FakeMesh({"Result": np.array([1.0, 2.0, 3.0])}, active_scalars_name="Result")
    plotter = FakePlotter(fail_on_parallel_enable=False)
    initial_camera = (
        (10.0, 20.0, 30.0),
        (1.0, 2.0, 3.0),
        (0.0, 0.0, 1.0),
    )
    plotter.camera_position = initial_camera
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

    handler.update_visualization(preserve_camera=True)

    assert plotter.reset_camera_calls == 0
    assert np.allclose(plotter.camera_position[0], initial_camera[0])
    assert np.allclose(plotter.camera_position[1], initial_camera[1])
    assert np.allclose(plotter.camera_position[2], initial_camera[2])


def test_update_visualization_preserves_camera_by_default():
    mesh = FakeMesh({"Result": np.array([1.0, 2.0, 3.0])}, active_scalars_name="Result")
    plotter = FakePlotter(fail_on_parallel_enable=False)
    initial_camera = (
        (12.0, 22.0, 32.0),
        (2.0, 3.0, 4.0),
        (0.0, 1.0, 0.0),
    )
    plotter.camera_position = initial_camera
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

    assert plotter.reset_camera_calls == 0
    assert np.allclose(plotter.camera_position[0], initial_camera[0])
    assert np.allclose(plotter.camera_position[1], initial_camera[1])
    assert np.allclose(plotter.camera_position[2], initial_camera[2])


def test_update_visualization_can_reset_camera_for_new_geometry():
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

    handler.update_visualization(preserve_camera=False)

    assert plotter.reset_camera_calls == 1


def test_compatibility_rendering_toggle_preserves_camera():
    mesh = FakeMesh({"Result": np.array([1.0, 2.0, 3.0])}, active_scalars_name="Result")
    plotter = FakePlotter(fail_on_parallel_enable=False)
    initial_camera = (
        (15.0, 25.0, 35.0),
        (5.0, 6.0, 7.0),
        (0.0, 0.0, 1.0),
    )
    plotter.camera_position = initial_camera
    tab = FakeVisualizationTab(plotter=plotter)
    state = SimpleNamespace(
        current_mesh=mesh,
        current_actor=None,
        data_column="Result",
        camera_widget=None,
        hover_annotation=None,
        hover_observer=None,
        last_hover_time=0.0,
        compatibility_rendering=False,
    )
    handler = DisplayVisualizationHandler(tab=tab, state=state, viz_manager=None)

    handler.toggle_compatibility_rendering(True)

    assert state.compatibility_rendering is True
    assert plotter.reset_camera_calls == 0
    assert np.allclose(plotter.camera_position[0], initial_camera[0])
    assert np.allclose(plotter.camera_position[1], initial_camera[1])
    assert np.allclose(plotter.camera_position[2], initial_camera[2])


def test_add_camera_widget_is_idempotent():
    plotter = FakePlotter()
    tab = FakeVisualizationTab(plotter=plotter)
    state = SimpleNamespace(
        current_mesh=None,
        current_actor=None,
        data_column="",
        camera_widget=None,
        hover_annotation=None,
        hover_observer=None,
        last_hover_time=0.0,
    )
    handler = DisplayVisualizationHandler(tab=tab, state=state, viz_manager=None)

    handler._add_camera_widget()
    first_widget = state.camera_widget
    handler._add_camera_widget()

    assert first_widget is not None
    assert state.camera_widget is first_widget
    assert tab.camera_widget is first_widget
    assert plotter.add_camera_widget_calls == 1


def test_animation_export_captures_live_plotter_and_restores_visible_state(monkeypatch, tmp_path):
    import imageio.v2 as imageio

    saved = {}

    def fake_mimsave(path, frames, **kwargs):
        saved["path"] = path
        saved["frames"] = list(frames)
        saved["kwargs"] = kwargs

    monkeypatch.setattr(imageio, "mimsave", fake_mimsave)

    original_points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    original_scalars = np.array([9.0, 10.0])
    mesh = FakeAnimationMesh(
        original_points,
        {"Result": original_scalars},
        active_scalars_name="Result",
    )
    plotter = FakeAnimationPlotter()
    original_camera = plotter.camera_position
    actor = SimpleNamespace(mapper=SimpleNamespace(scalar_range=(2.0, 8.0)))
    tab = FakeAnimationTab(mesh=mesh, plotter=plotter, actor=actor)
    timer = FakeAnimationTimer(active=True)
    time_actor = FakeAnimationTextActor("Time: original")
    state = SimpleNamespace(
        anim_timer=timer,
        current_anim_frame_index=5,
        time_text_actor=time_actor,
    )
    manager = FakeAnimationManager(
        frame_scalars=np.array([[1.0, 2.0], [3.0, 4.0]]),
        frame_coords=np.array([
            [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
            [[0.0, 1.0, 0.0], [3.0, 0.0, 0.0]],
        ]),
        frame_times=np.array([0.0, 0.1]),
    )
    handler = DisplayAnimationHandler(tab=tab, state=state, anim_manager=manager)

    output_path = tmp_path / "animation.mp4"
    assert handler.write_animation_to_file(str(output_path), "mp4") is True

    assert saved["path"] == str(output_path)
    assert len(saved["frames"]) == 2
    assert saved["frames"][0].shape == (14, 18, 3)
    assert saved["kwargs"]["macro_block_size"] == 2
    assert all(call == {"return_img": True} for call in plotter.screenshot_calls)
    assert np.allclose(mesh.points, original_points)
    assert np.allclose(mesh["Result"], original_scalars)
    assert mesh.active_scalars_name == "Result"
    assert state.current_anim_frame_index == 5
    assert time_actor.GetInput() == "Time: original"
    assert actor.mapper.scalar_range == (2.0, 8.0)
    assert plotter.camera_position == original_camera
    assert timer.stop_calls == 1
    assert timer.start_calls == 1
    assert timer.started_intervals == [10]


class FakeInteractionMesh:
    def __init__(self, points, node_ids):
        self.points = np.asarray(points, dtype=float)
        self._node_ids = np.asarray(node_ids, dtype=int)
        self.array_names = ["NodeID"]

    def __getitem__(self, key):
        if key == "NodeID":
            return self._node_ids
        raise KeyError(key)


class FakeInteractionPlotter:
    def __init__(self, camera_position, reset_on_first_label=False):
        self.camera_position = camera_position
        self._reset_on_first_label = reset_on_first_label
        self._label_calls = 0
        self.render_calls = 0
        self.fly_to_calls = 0

    def add_points(self, *_args, **_kwargs):
        return object()

    def add_point_labels(self, *_args, **_kwargs):
        self._label_calls += 1
        if self._reset_on_first_label and self._label_calls == 1:
            # Mimic a first-call camera change.
            self.camera_position = (
                (100.0, 100.0, 100.0),
                (0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
            )
        return object()

    def remove_actor(self, *_args, **_kwargs):
        return None

    def fly_to(self, *_args, **_kwargs):
        self.fly_to_calls += 1

    def render(self):
        self.render_calls += 1


class FakeHotspotMesh:
    def __init__(self, points, arrays, active_scalars_name):
        self.points = np.asarray(points, dtype=float)
        self._arrays = {name: np.asarray(values) for name, values in arrays.items()}
        self.array_names = list(self._arrays.keys())
        self.active_scalars_name = active_scalars_name
        self.n_points = self.points.shape[0]

    @property
    def active_scalars(self):
        return self._arrays.get(self.active_scalars_name)

    def __getitem__(self, key):
        return self._arrays[key]


class FakeHotspotResultsHandler:
    def _resolve_values(self, entry, _field_name):
        values = entry.get("values")
        if values is None:
            return None
        return np.asarray(values, dtype=float)


class FakeSignal:
    def __init__(self):
        self.connections = []

    def connect(self, callback):
        self.connections.append(callback)


class CapturingHotspotDialog:
    instances = []

    def __init__(self, hotspot_df, parent=None):
        self.hotspot_df = hotspot_df.copy()
        self.parent = parent
        self.node_selected = FakeSignal()
        self.finished = FakeSignal()
        self.show_calls = 0
        self.close_calls = 0
        CapturingHotspotDialog.instances.append(self)

    def show(self):
        self.show_calls += 1

    def close(self):
        self.close_calls += 1


def test_hotspot_table_adds_time_of_max_for_max_over_time_contour(monkeypatch):
    CapturingHotspotDialog.instances = []
    monkeypatch.setattr(
        "ui.handlers.display_interaction_handler.QInputDialog.getInt",
        lambda *_args, **_kwargs: (2, True),
    )
    monkeypatch.setattr(
        "ui.handlers.display_interaction_handler.HotspotDialog",
        CapturingHotspotDialog,
    )

    value_field = "SVM (MPa) - Max over Time"
    time_field = "Time of Max: SVM (s)"
    full_mesh = FakeHotspotMesh(
        points=np.zeros((4, 3)),
        arrays={
            "NodeID": np.array([101, 102, 103, 104]),
            value_field: np.array([10.0, 5.0, 20.0, 30.0]),
        },
        active_scalars_name=value_field,
    )
    visible_mesh = FakeHotspotMesh(
        points=np.array([
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [3.0, 0.0, 0.0],
        ]),
        arrays={
            "NodeID": np.array([103, 101, 104]),
            value_field: np.array([20.0, 10.0, 30.0]),
        },
        active_scalars_name=value_field,
    )
    state = SimpleNamespace(
        result_catalog={
            "Von Mises": {
                "Magnitude": {
                    "max_over_time": {
                        "field_name": value_field,
                        "values": np.array([10.0, 5.0, 20.0, 30.0]),
                    },
                    "time_of_max": {
                        "field_name": time_field,
                        "values": np.array([0.1, 0.2, 0.3, 0.4]),
                    },
                }
            }
        },
        result_selection={
            "group": "Von Mises",
            "component": "Magnitude",
            "mode": "max_over_time",
        },
        current_mesh=full_mesh,
        hotspot_dialog=None,
        box_widget=None,
    )
    tab = SimpleNamespace(
        current_mesh=full_mesh,
        results_handler=FakeHotspotResultsHandler(),
    )
    handler = DisplayInteractionHandler(
        tab=tab,
        state=state,
        hotspot_detector=HotspotDetector(),
    )

    handler._find_and_show_hotspots(visible_mesh)

    dialog = CapturingHotspotDialog.instances[-1]
    df = dialog.hotspot_df
    assert list(df.columns) == ["Rank", "NodeID", value_field, time_field, "X", "Y", "Z"]
    np.testing.assert_array_equal(df["NodeID"].to_numpy(), np.array([104, 103]))
    np.testing.assert_allclose(df[value_field].to_numpy(), np.array([30.0, 20.0]))
    np.testing.assert_allclose(df[time_field].to_numpy(), np.array([0.4, 0.3]))
    assert dialog.show_calls == 1
    assert state.hotspot_dialog is dialog


def test_hotspot_table_adds_min_over_time_for_time_of_min_contour(monkeypatch):
    CapturingHotspotDialog.instances = []
    monkeypatch.setattr(
        "ui.handlers.display_interaction_handler.QInputDialog.getInt",
        lambda *_args, **_kwargs: (2, True),
    )
    monkeypatch.setattr(
        "ui.handlers.display_interaction_handler.HotspotDialog",
        CapturingHotspotDialog,
    )

    value_field = "S3 (MPa) - Min over Time"
    time_field = "Time of Min: S3 (s)"
    full_mesh = FakeHotspotMesh(
        points=np.zeros((3, 3)),
        arrays={
            "NodeID": np.array([11, 22, 33]),
            time_field: np.array([0.1, 0.4, 0.2]),
        },
        active_scalars_name=time_field,
    )
    visible_mesh = FakeHotspotMesh(
        points=np.array([
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [3.0, 0.0, 0.0],
        ]),
        arrays={
            "NodeID": np.array([11, 22, 33]),
            time_field: np.array([0.1, 0.4, 0.2]),
        },
        active_scalars_name=time_field,
    )
    state = SimpleNamespace(
        result_catalog={
            "Min Principal": {
                "S3": {
                    "min_over_time": {
                        "field_name": value_field,
                        "values": np.array([-10.0, -5.0, -20.0]),
                    },
                    "time_of_min": {
                        "field_name": time_field,
                        "values": np.array([0.1, 0.4, 0.2]),
                    },
                }
            }
        },
        result_selection={
            "group": "Min Principal",
            "component": "S3",
            "mode": "time_of_min",
        },
        current_mesh=full_mesh,
        hotspot_dialog=None,
        box_widget=None,
    )
    tab = SimpleNamespace(
        current_mesh=full_mesh,
        results_handler=FakeHotspotResultsHandler(),
    )
    handler = DisplayInteractionHandler(
        tab=tab,
        state=state,
        hotspot_detector=HotspotDetector(),
    )

    handler._find_and_show_hotspots(visible_mesh)

    dialog = CapturingHotspotDialog.instances[-1]
    df = dialog.hotspot_df
    assert list(df.columns) == ["Rank", "NodeID", value_field, time_field, "X", "Y", "Z"]
    np.testing.assert_array_equal(df["NodeID"].to_numpy(), np.array([22, 33]))
    np.testing.assert_allclose(df[value_field].to_numpy(), np.array([-5.0, -20.0]))
    np.testing.assert_allclose(df[time_field].to_numpy(), np.array([0.4, 0.2]))
    assert dialog.show_calls == 1
    assert state.hotspot_dialog is dialog


def test_go_to_node_preserves_full_camera_tuple(monkeypatch):
    points = np.array([[0.0, 0.0, 0.0], [4.0, 5.0, 6.0]])
    node_ids = np.array([1001, 1002])
    mesh = FakeInteractionMesh(points=points, node_ids=node_ids)
    initial_camera_position = ((10.0, 20.0, 30.0), (1.0, 2.0, 3.0), (0.0, 0.0, 1.0))
    plotter = FakeInteractionPlotter(
        camera_position=initial_camera_position,
        reset_on_first_label=True,
    )

    tab = SimpleNamespace(
        current_mesh=mesh,
        plotter=plotter,
        point_size=FakeSpinBox(5.0),
    )
    state = SimpleNamespace(
        target_node_marker_actor=None,
        target_node_label_actor=None,
        marker_poly=None,
        label_point_data=None,
        target_node_index=None,
        target_node_id=None,
        last_goto_node_id=None,
        freeze_tracked_node=False,
        freeze_baseline=None,
    )
    handler = DisplayInteractionHandler(tab=tab, state=state, hotspot_detector=None)

    monkeypatch.setattr(
        "ui.handlers.display_interaction_handler.QInputDialog.getInt",
        lambda *_args, **_kwargs: (1002, True),
    )

    handler.go_to_node()

    # Camera tuple is fully preserved.
    assert np.allclose(plotter.camera_position[0], initial_camera_position[0])
    assert np.allclose(plotter.camera_position[1], initial_camera_position[1])
    assert np.allclose(plotter.camera_position[2], initial_camera_position[2])
    assert plotter.fly_to_calls == 0
    assert state.target_node_id == 1002
