"""Regression coverage for modal-coordinate plus deformation-only solves."""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from solver.engine import MSUPSmartSolverTransient


def test_deformation_only_batch_writes_nodal_results(tmp_path):
    modal_coord = np.array([[0.0, 1.0, 2.0]])
    modal_ux = np.array([[2.0], [3.0]])
    zeros = np.zeros_like(modal_ux)
    node_ids = np.array([10, 20])
    coords = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])

    solver = MSUPSmartSolverTransient(
        modal_coord=modal_coord,
        time_values=np.array([0.0, 1.0, 2.0]),
        modal_node_ids=node_ids,
        modal_deformations=(modal_ux, zeros, zeros),
        output_directory=str(tmp_path),
    )

    solver.process_results_in_batch(
        np.array([0.0, 1.0, 2.0]),
        node_ids,
        coords,
        calculate_deformation=True,
    )

    result = pd.read_csv(tmp_path / "max_deformation.csv")
    np.testing.assert_array_equal(result["NodeID"].to_numpy(), node_ids)
    np.testing.assert_allclose(result["DEF_Max"].to_numpy(), [4.0, 6.0])
