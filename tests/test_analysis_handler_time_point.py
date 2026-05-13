"""
Regression tests for selected-time-point result calculation.
"""

import os
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd


# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.data_models import SteadyStateData
from file_io.exporters import export_mesh_to_csv
from ui.handlers.analysis_handler import SolverAnalysisHandler


class _CaptureSignal:
    def __init__(self):
        self.args = None

    def emit(self, *args):
        self.args = args


def test_time_point_von_mises_includes_steady_state_in_mesh_and_csv(tmp_path):
    """
    Selected-time display should use the same steady-state stress bias as a solve.
    """
    node_ids = np.array([101, 102])
    zero_modal_stress = np.zeros((2, 1), dtype=float)
    expected_svm = np.array([10.0, 20.0])

    tab = SimpleNamespace(
        coord_loaded=True,
        stress_loaded=True,
        force_moment_loaded=False,
        modal_data=SimpleNamespace(
            time_values=np.array([0.0, 1.0]),
            modal_coord=np.array([[0.0, 0.0]]),
            num_modes=1,
            num_time_points=2,
        ),
        stress_data=SimpleNamespace(
            modal_sx=zero_modal_stress,
            modal_sy=zero_modal_stress,
            modal_sz=zero_modal_stress,
            modal_sxy=zero_modal_stress,
            modal_syz=zero_modal_stress,
            modal_sxz=zero_modal_stress,
            node_ids=node_ids,
            node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
            num_nodes=2,
        ),
        deformation_data=None,
        force_moment_data=None,
        steady_state_data=SteadyStateData(
            node_ids=node_ids,
            steady_sx=expected_svm,
            steady_sy=np.zeros(2),
            steady_sz=np.zeros(2),
            steady_sxy=np.zeros(2),
            steady_syz=np.zeros(2),
            steady_sxz=np.zeros(2),
        ),
        time_point_result_ready=_CaptureSignal(),
    )

    SolverAnalysisHandler(tab).perform_time_point_calculation(
        selected_time=1.0,
        options={
            "compute_von_mises": True,
            "include_steady": True,
            "skip_n_modes": 0,
            "skip_last_n_modes": 0,
            "scale_factor": 1.0,
        },
    )

    assert tab.time_point_result_ready.args is not None
    mesh, display_name, data_min, data_max = tab.time_point_result_ready.args

    assert display_name == "SVM (MPa)"
    assert mesh.active_scalars_name == display_name
    np.testing.assert_allclose(mesh[display_name], expected_svm)
    assert data_min == 10.0
    assert data_max == 20.0

    output_path = tmp_path / "selected_time.csv"
    export_mesh_to_csv(mesh, display_name, str(output_path))

    exported = pd.read_csv(output_path)
    assert list(exported.columns) == ["NodeID", "X", "Y", "Z", "SVM (MPa)"]
    np.testing.assert_array_equal(exported["NodeID"].to_numpy(), node_ids)
    np.testing.assert_allclose(exported["SVM (MPa)"].to_numpy(), expected_svm)
