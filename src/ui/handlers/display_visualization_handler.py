"""
Visualization updates and rendering helpers for the Display tab.
"""

import time
import numpy as np
import vtk
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from ui.handlers.display_base_handler import DisplayBaseHandler
from core.visualization import VisualizationManager


class DisplayVisualizationHandler(DisplayBaseHandler):
    """Coordinates rendering operations on the PyVista plotter."""

    def __init__(self, tab, state, viz_manager: VisualizationManager):
        super().__init__(tab, state)
        self.viz_manager = viz_manager

    def _compatibility_rendering_enabled(self) -> bool:
        """Return whether compatibility rendering mode is active."""
        checkbox = getattr(self.tab, "compatibility_rendering_checkbox", None)
        if checkbox is not None:
            return bool(checkbox.isChecked())
        return bool(getattr(self.state, "compatibility_rendering", False))

    def _set_compatibility_rendering(self, enabled: bool) -> None:
        """Synchronize compatibility rendering state between tab and state."""
        enabled = bool(enabled)
        if hasattr(self.state, "compatibility_rendering"):
            self.state.compatibility_rendering = enabled
        if hasattr(self.tab, "compatibility_rendering"):
            self.tab.compatibility_rendering = enabled

        checkbox = getattr(self.tab, "compatibility_rendering_checkbox", None)
        if checkbox is not None and checkbox.isChecked() != enabled:
            checkbox.blockSignals(True)
            checkbox.setChecked(enabled)
            checkbox.blockSignals(False)

    def toggle_compatibility_rendering(self, enabled: bool) -> None:
        """Toggle compatibility mode and refresh the mesh if loaded."""
        self._set_compatibility_rendering(enabled)
        if (self.state.current_mesh or getattr(self.tab, "current_mesh", None)) is not None:
            self.update_visualization()

    def _compute_effective_point_size(
        self, base_point_size: float, compatibility_mode: bool
    ) -> float:
        """Scale point size based on display DPI so clouds remain visible."""
        effective_size = max(1.0, float(base_point_size))
        dpi_scale = 1.0

        plotter_widget = getattr(self.tab, "plotter", None)
        if plotter_widget is not None:
            try:
                device_ratio = float(plotter_widget.devicePixelRatioF())
                if device_ratio > 1.0:
                    dpi_scale = max(dpi_scale, device_ratio)
            except Exception:
                pass

        screen = None
        try:
            window_handle = self.tab.window().windowHandle()
            if window_handle is not None:
                screen = window_handle.screen()
        except Exception:
            screen = None

        if screen is None:
            app = QApplication.instance()
            if app is not None:
                try:
                    screen = app.primaryScreen()
                except Exception:
                    screen = None

        if screen is not None:
            try:
                logical_dpi = float(screen.logicalDotsPerInch())
                if logical_dpi > 96.0:
                    dpi_scale = max(dpi_scale, logical_dpi / 96.0)
            except Exception:
                pass

        effective_size *= dpi_scale
        if compatibility_mode:
            effective_size = max(effective_size, 8.0)

        return min(effective_size, 300.0)

    def _add_mesh_actor(
        self,
        mesh,
        active_scalars,
        point_size: float,
        compatibility_mode: bool,
    ):
        """Add the mesh actor using the selected rendering mode."""
        return self.tab.plotter.add_mesh(
            mesh,
            scalars=active_scalars,
            point_size=point_size,
            render_points_as_spheres=not compatibility_mode,
            lighting=not compatibility_mode,
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

    def update_visualization(self, preserve_camera: bool = False) -> None:
        """Refresh the 3D view with the current mesh."""
        mesh = self.state.current_mesh or self.tab.current_mesh
        if mesh is None:
            return

        plotter = self.tab.plotter
        preserved_camera = (
            self._capture_camera_position(plotter) if preserve_camera else None
        )
        plotter.clear()

        # Use active scalars if set, otherwise fall back to first array (e.g., NodeID)
        active_scalars = mesh.active_scalars_name
        if not active_scalars and mesh.array_names:
            active_scalars = mesh.array_names[0]
        if active_scalars:
            self.state.data_column = active_scalars
            self.tab.data_column = active_scalars

        compatibility_mode = self._compatibility_rendering_enabled()
        point_size = self._compute_effective_point_size(
            self.tab.point_size.value(),
            compatibility_mode,
        )

        try:
            actor = self._add_mesh_actor(
                mesh,
                active_scalars,
                point_size,
                compatibility_mode,
            )
        except Exception as exc:
            if compatibility_mode:
                raise
            print(
                "Warning: sphere point rendering failed; "
                f"falling back to compatibility mode ({exc})."
            )
            self._set_compatibility_rendering(True)
            point_size = self._compute_effective_point_size(
                self.tab.point_size.value(),
                True,
            )
            actor = self._add_mesh_actor(
                mesh,
                active_scalars,
                point_size,
                True,
            )

        self.state.current_actor = actor
        self.tab.current_actor = actor

        if self.tab.scalar_min_spin.value() != self.tab.scalar_max_spin.value():
            actor.mapper.scalar_range = (
                self.tab.scalar_min_spin.value(),
                self.tab.scalar_max_spin.value(),
            )

        self.setup_hover_annotation()

        if not self._restore_camera_position(preserved_camera, plotter=plotter):
            plotter.reset_camera()
        try:
            # Use orthographic projection for engineering contour views.
            plotter.enable_parallel_projection()
        except Exception:
            try:
                plotter.camera.SetParallelProjection(True)
            except Exception:
                pass
        
        # Clear old camera widget if it exists
        self._clear_camera_widget()
        
        # Force render to establish window size
        plotter.render()
        if hasattr(self.tab, "log_renderer_capabilities_once"):
            self.tab.log_renderer_capabilities_once()
        
        # Check if tab is visible - if so, add widget immediately
        # If not visible, set flag for showEvent to handle it
        if self.tab.isVisible():
            # Tab is visible, add widget with minimal delay
            self.tab._camera_widget_pending = False
            QTimer.singleShot(10, self._add_camera_widget)
        else:
            # Tab not visible yet, mark as pending for showEvent
            self.tab._camera_widget_pending = True

    def _clear_camera_widget(self) -> None:
        """Remove existing camera orientation widget."""
        if self.state.camera_widget:
            try:
                self.state.camera_widget.EnabledOff()
                if hasattr(self.tab.plotter, 'remove_actor'):
                    try:
                        self.tab.plotter.remove_actor(self.state.camera_widget)
                    except Exception:
                        pass
            except Exception:
                pass
            self.state.camera_widget = None
            self.tab.camera_widget = None

    def _add_camera_widget(self) -> None:
        """Add camera orientation widget after Qt layout has settled."""
        try:
            existing_widget = self.state.camera_widget or getattr(self.tab, "camera_widget", None)
            if existing_widget is not None:
                self.state.camera_widget = existing_widget
                self.tab.camera_widget = existing_widget
                self.tab._camera_widget_pending = False
                return

            # Render again to ensure proper sizing
            self.tab.plotter.render()
            
            # Add camera widget with correct size
            camera_widget = self.tab.plotter.add_camera_orientation_widget()
            camera_widget.EnabledOn()
            
            # Store reference
            self.state.camera_widget = camera_widget
            self.tab.camera_widget = camera_widget
            self.tab._camera_widget_pending = False
        except Exception:
            pass  # Plotter may have been closed

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
        picker.SetTolerance(0.025)  # 2.5% of window diagonal for better zoom-in tolerance

        def hover_callback(obj, _event):
            now = time.time()
            if (now - self.state.last_hover_time) < 0.033:  # 30 FPS throttle
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

        compatibility_mode = self._compatibility_rendering_enabled()
        point_size = self._compute_effective_point_size(
            self.tab.point_size.value(),
            compatibility_mode,
        )
        self.clear_hover_elements()
        actor_prop = actor.GetProperty()
        actor_prop.SetPointSize(point_size)
        try:
            actor_prop.SetRenderPointsAsSpheres(not compatibility_mode)
        except Exception:
            pass
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

    def apply_scalar_field(self, field_name: str, values, preserve_camera: bool = True) -> bool:
        """
        Apply a scalar field to the current mesh and refresh the visualization.

        Args:
            field_name: Name of the scalar field to apply.
            values: Iterable of scalar values per node.
            preserve_camera: Keep current camera state after the refresh.

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

        self.update_visualization(preserve_camera=preserve_camera)
        return True
