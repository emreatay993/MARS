"""
Visualization updates and rendering helpers for the Display tab.
"""

import time
import numpy as np
import vtk

from ui.handlers.display_base_handler import DisplayBaseHandler
from core.visualization import VisualizationManager


class DisplayVisualizationHandler(DisplayBaseHandler):
    """Coordinates rendering operations on the PyVista plotter."""

    def __init__(self, tab, state, viz_manager: VisualizationManager):
        super().__init__(tab, state)
        self.viz_manager = viz_manager

    def update_visualization(self) -> None:
        """Refresh the 3D view with the current mesh."""
        mesh = self.state.current_mesh or self.tab.current_mesh
        if mesh is None:
            return

        plotter = self.tab.plotter
        plotter.clear()

        active_scalars = mesh.active_scalars_name
        if active_scalars:
            self.state.data_column = active_scalars
            self.tab.data_column = active_scalars

        actor = plotter.add_mesh(
            mesh,
            scalars=active_scalars,
            point_size=self.tab.point_size.value(),
            render_points_as_spheres=True,
            show_scalar_bar=True,
            cmap="jet",
            below_color="gray",
            above_color="magenta",
            scalar_bar_args={
                "title": self.tab.data_column,
                "fmt": "%.4f",
                "position_x": 0.04,
                "position_y": 0.35,
                "width": 0.05,
                "height": 0.5,
                "vertical": True,
                "title_font_size": 14,
                "label_font_size": 12,
                "shadow": True,
                "n_labels": 10,
            },
        )

        self.state.current_actor = actor
        self.tab.current_actor = actor

        if self.tab.scalar_min_spin.value() != self.tab.scalar_max_spin.value():
            actor.mapper.scalar_range = (
                self.tab.scalar_min_spin.value(),
                self.tab.scalar_max_spin.value(),
            )

        self.setup_hover_annotation()

        if not self.state.camera_widget:
            camera_widget = plotter.add_camera_orientation_widget()
            camera_widget.EnabledOn()
            self.state.camera_widget = camera_widget
            self.tab.camera_widget = camera_widget

        plotter.reset_camera()

    def setup_hover_annotation(self) -> None:
        """Set up hover callbacks to display node information."""
        mesh = self.state.current_mesh or self.tab.current_mesh
        if not mesh or "NodeID" not in mesh.array_names:
            return

        self.clear_hover_elements()

        annotation = self.tab.plotter.add_text(
            "",
            position="upper_right",
            font_size=8,
            color="black",
            name="hover_annotation",
        )
        self.state.hover_annotation = annotation
        self.tab.hover_annotation = annotation

        picker = vtk.vtkPointPicker()
        picker.SetTolerance(0.01)

        def hover_callback(obj, _event):
            now = time.time()
            if (now - self.state.last_hover_time) < 0.033:
                return

            current_mesh = self.state.current_mesh or self.tab.current_mesh
            if current_mesh is None:
                return

            iren = obj
            pos = iren.GetEventPosition()
            picker.Pick(pos[0], pos[1], 0, self.tab.plotter.renderer)
            point_id = picker.GetPointId()

            if point_id != -1 and point_id < current_mesh.n_points:
                node_id = current_mesh["NodeID"][point_id]
                value = current_mesh[self.tab.data_column][point_id]
                annotation.SetText(
                    2,
                    f"Node ID: {node_id}\n{self.tab.data_column}: {value:.5f}",
                )
            else:
                annotation.SetText(2, "")

            iren.GetRenderWindow().Render()
            self.state.last_hover_time = now
            self.tab.last_hover_time = now

        observer_id = self.tab.plotter.iren.add_observer(
            "MouseMoveEvent", hover_callback
        )
        self.state.hover_observer = observer_id
        self.tab.hover_observer = observer_id

    def clear_hover_elements(self) -> None:
        """Remove hover annotation text and observer callbacks."""
        if self.state.hover_annotation:
            try:
                self.tab.plotter.remove_actor(self.state.hover_annotation)
            except Exception:
                pass
            self.state.hover_annotation = None
            self.tab.hover_annotation = None

        if self.state.hover_observer:
            try:
                self.tab.plotter.iren.remove_observer(self.state.hover_observer)
            except Exception:
                pass
            self.state.hover_observer = None
            self.tab.hover_observer = None

    def update_point_size(self) -> None:
        """Adjust point size and refresh hover annotations."""
        actor = self.state.current_actor or self.tab.current_actor
        if actor is None:
            return

        self.clear_hover_elements()
        actor.GetProperty().SetPointSize(self.tab.point_size.value())
        self.setup_hover_annotation()
        self.tab.plotter.render()

    def update_scalar_range(self) -> None:
        """Update scalar range on the current actor."""
        actor = self.state.current_actor or self.tab.current_actor
        if actor is None:
            return

        actor.mapper.scalar_range = (
            self.tab.scalar_min_spin.value(),
            self.tab.scalar_max_spin.value(),
        )
        self.tab.plotter.render()

    def validate_deformation_scale(self) -> None:
        """Validate deformation scale factor input."""
        text = self.tab.deformation_scale_edit.text()
        try:
            value = float(text)
        except ValueError:
            fallback = str(self.state.last_valid_deformation_scale)
            self.tab.deformation_scale_edit.setText(fallback)
            self.tab.last_valid_deformation_scale = self.state.last_valid_deformation_scale
            return

        self.state.last_valid_deformation_scale = value
        self.tab.last_valid_deformation_scale = value

    def apply_scalar_field(self, field_name: str, values) -> bool:
        """
        Apply a scalar field to the current mesh and refresh the visualization.

        Args:
            field_name: Name of the scalar field to apply.
            values: Iterable of scalar values per node.

        Returns:
            bool: True if the field was applied successfully, False otherwise.
        """
        mesh = self.state.current_mesh or self.tab.current_mesh
        if mesh is None:
            return False

        array = np.asarray(values)
        if array.ndim > 1:
            array = array.reshape(-1)

        if mesh.n_points != array.shape[0]:
            raise ValueError(
                f"Scalar field '{field_name}' length {array.shape[0]} does not match mesh nodes {mesh.n_points}"
            )

        mesh[field_name] = array
        mesh.set_active_scalars(field_name)

        self.state.data_column = field_name
        self.tab.data_column = field_name

        self.update_visualization()
        return True
