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

    def _capture_camera_state(self, plotter=None):
        """Return camera position plus orthographic zoom."""
        if plotter is None:
            plotter = getattr(self.tab, "plotter", None)
        if plotter is None:
            return None

        camera_state = {
            "position": self._capture_camera_position(plotter),
        }
        camera = getattr(plotter, "camera", None)
        if camera is not None:
            try:
                camera_state["parallel_scale"] = float(camera.GetParallelScale())
            except (AttributeError, TypeError, ValueError):
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
        """Restore camera position and orthographic zoom captured before a redraw."""
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
        parallel_scale = camera_state.get("parallel_scale")
        if camera is not None and parallel_scale is not None:
            try:
                camera.SetParallelScale(parallel_scale)
                restored = True
            except (AttributeError, TypeError, ValueError):
                pass

        if restored and render:
            try:
                plotter.render()
            except Exception:
                pass
        return restored
