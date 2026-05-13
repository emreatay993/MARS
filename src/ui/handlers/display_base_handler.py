"""
Base utilities for Display tab handler classes.
"""

import numpy as np

from ui.handlers.display_state import DisplayState


class DisplayBaseHandler:
    """Common base class providing access to the tab widget and shared state."""

    def __init__(self, tab, state: DisplayState):
        self.tab = tab
        self.state = state

    def set_state_attr(self, attr_name: str, value) -> None:
        """
        Convenience helper to keep DisplayTab attributes in sync with state.

        Args:
            attr_name: Name of the attribute to set.
            value: Value to assign.
        """
        if not hasattr(self.state, attr_name):
            raise AttributeError(f"DisplayState has no attribute '{attr_name}'")
        setattr(self.state, attr_name, value)
        setattr(self.tab, attr_name, value)

    def _capture_camera_position(self, plotter=None):
        """Return a detached camera tuple suitable for later restoration."""
        if plotter is None:
            plotter = getattr(self.tab, "plotter", None)
        if plotter is None:
            return None

        camera_position = getattr(plotter, "camera_position", None)
        if not isinstance(camera_position, (tuple, list)) or len(camera_position) != 3:
            return None

        cam_pos, cam_focal, cam_view_up = camera_position
        try:
            return (
                tuple(np.asarray(cam_pos, dtype=float)),
                tuple(np.asarray(cam_focal, dtype=float)),
                tuple(np.asarray(cam_view_up, dtype=float)),
            )
        except Exception:
            return None

    def _camera_value(self, camera, getter_name: str, attr_name: str):
        """Read a camera value through a VTK getter or Python attribute."""
        if camera is None:
            return None

        getter = getattr(camera, getter_name, None)
        if callable(getter):
            try:
                return getter()
            except Exception:
                return None

        try:
            return getattr(camera, attr_name)
        except Exception:
            return None

    def _set_camera_value(
        self,
        camera,
        setter_name: str,
        attr_name: str,
        value,
    ) -> bool:
        """Restore a camera value through a VTK setter or Python attribute."""
        if camera is None or value is None:
            return False

        setter = getattr(camera, setter_name, None)
        if callable(setter):
            try:
                if isinstance(value, (tuple, list)):
                    setter(*value)
                else:
                    setter(value)
                return True
            except TypeError:
                try:
                    setter(value)
                    return True
                except Exception:
                    return False
            except Exception:
                return False

        try:
            setattr(camera, attr_name, value)
            return True
        except Exception:
            return False

    def _capture_camera_state(self, plotter=None):
        """Return camera position plus zoom values that PyVista omits."""
        if plotter is None:
            plotter = getattr(self.tab, "plotter", None)
        if plotter is None:
            return None

        camera_state = {
            "position": self._capture_camera_position(plotter),
        }
        camera = getattr(plotter, "camera", None)
        if camera is not None:
            parallel_scale = self._camera_value(
                camera, "GetParallelScale", "parallel_scale"
            )
            if parallel_scale is not None:
                try:
                    camera_state["parallel_scale"] = float(parallel_scale)
                except (TypeError, ValueError):
                    pass

            view_angle = self._camera_value(camera, "GetViewAngle", "view_angle")
            if view_angle is not None:
                try:
                    camera_state["view_angle"] = float(view_angle)
                except (TypeError, ValueError):
                    pass

        if any(value is not None for value in camera_state.values()):
            return camera_state
        return None

    def _restore_camera_position(
        self,
        camera_position,
        plotter=None,
        render: bool = False,
    ) -> bool:
        """Restore a camera tuple to the plotter and optionally render."""
        if plotter is None:
            plotter = getattr(self.tab, "plotter", None)
        if plotter is None:
            return False

        if not isinstance(camera_position, (tuple, list)) or len(camera_position) != 3:
            return False

        try:
            plotter.camera_position = camera_position
            if render:
                plotter.render()
            return True
        except Exception:
            return False

    def _restore_camera_state(
        self,
        camera_state,
        plotter=None,
        render: bool = False,
    ) -> bool:
        """Restore camera position and zoom values captured before a redraw."""
        if isinstance(camera_state, (tuple, list)):
            return self._restore_camera_position(camera_state, plotter, render)

        if not isinstance(camera_state, dict):
            return False

        if plotter is None:
            plotter = getattr(self.tab, "plotter", None)
        if plotter is None:
            return False

        restored = self._restore_camera_position(
            camera_state.get("position"),
            plotter=plotter,
            render=False,
        )

        camera = getattr(plotter, "camera", None)
        restored = (
            self._set_camera_value(
                camera,
                "SetParallelScale",
                "parallel_scale",
                camera_state.get("parallel_scale"),
            )
            or restored
        )
        restored = (
            self._set_camera_value(
                camera,
                "SetViewAngle",
                "view_angle",
                camera_state.get("view_angle"),
            )
            or restored
        )

        if restored and render:
            try:
                plotter.render()
            except Exception:
                pass
        return restored
