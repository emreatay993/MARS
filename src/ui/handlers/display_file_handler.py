"""
File loading logic for the Display tab.
"""

from typing import Optional, Sequence
import pandas as pd
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from ui.handlers.display_base_handler import DisplayBaseHandler
from core.visualization import VisualizationManager


class DisplayFileHandler(DisplayBaseHandler):
    """Handles loading external data sources for visualization."""

    def __init__(self, tab, state, viz_manager: VisualizationManager):
        super().__init__(tab, state)
        self.viz_manager = viz_manager
        self.plotting_handler = None

    def set_plotting_handler(self, plotting_handler: Optional[object]) -> None:
        """Assign plotting handler reference (mirrors DisplayTab API)."""
        self.plotting_handler = plotting_handler

    def open_file_dialog(self) -> None:
        """Open a file dialog for selecting a visualization CSV and load it."""
        file_name, _ = QFileDialog.getOpenFileName(
            self.tab, "Open Visualization File", "", "CSV Files (*.csv)"
        )
        if file_name:
            self.load_from_file(file_name)

    def load_from_file(self, filename: str) -> None:
        """
        Load visualization data from a CSV file and update the view.

        Args:
            filename: Absolute path to the CSV file selected by the user.
        """
        try:
            df = pd.read_csv(filename)
        except Exception as exc:
            QMessageBox.critical(
                self.tab, "Error Loading File",
                f"Failed to load file:\n{exc}"
            )
            return

        if not self._has_required_columns(df.columns):
            QMessageBox.warning(
                self.tab, "Invalid File",
                "File must contain X, Y, Z coordinate columns."
            )
            return

        coords = df[["X", "Y", "Z"]].to_numpy(dtype=float)
        node_ids = df["NodeID"].to_numpy(dtype=int) if "NodeID" in df.columns else None

        mesh = self.viz_manager.create_mesh_from_coords(coords, node_ids)

        scalar_name = self._apply_scalar_data(df, mesh)
        if scalar_name:
            self.state.data_column = scalar_name
            self.tab.data_column = scalar_name

        self.state.current_mesh = mesh
        self.tab.current_mesh = mesh
        self.tab.file_path.setText(filename)

        # Refresh the 3D view via the widget API
        self.tab.update_visualization()
        self.tab.plotter.reset_camera()

    @staticmethod
    def _has_required_columns(columns: Sequence[str]) -> bool:
        """Return True if the minimum coordinate columns are present."""
        required = {"X", "Y", "Z"}
        return required.issubset(set(columns))

    def _apply_scalar_data(self, df: pd.DataFrame, mesh) -> Optional[str]:
        """
        Attach scalar data to the mesh if present.

        Args:
            df: DataFrame loaded from CSV.
            mesh: PyVista mesh to update.

        Returns:
            Name of the scalar column applied, or None if none present.
        """
        scalar_cols = [
            col for col in df.columns
            if col not in {"X", "Y", "Z", "NodeID", "Index"}
        ]

        if not scalar_cols:
            return None

        scalar_name = scalar_cols[0]
        scalar_data = df[scalar_name].to_numpy()
        self.viz_manager.update_mesh_scalars(mesh, scalar_data, scalar_name)
        return scalar_name
