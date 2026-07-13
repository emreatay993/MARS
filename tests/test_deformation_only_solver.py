"""Regression coverage for modal-coordinate plus deformation-only solves."""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mars_solver.solver.engine import MSUPSmartSolverTransient


def _make_solver(tmp_path, progress_callback=None):
    modal_coord = np.array([[0.0, 1.0, 2.0]])
    modal_ux = np.array([[2.0], [3.0]])
    zeros = np.zeros_like(modal_ux)
    node_ids = np.array([10, 20])

    solver = MSUPSmartSolverTransient(
        modal_coord=modal_coord,
        time_values=np.array([0.0, 1.0, 2.0]),
        modal_node_ids=node_ids,
        modal_deformations=(modal_ux, zeros, zeros),
        output_directory=str(tmp_path),
        progress_callback=progress_callback,
    )
    return solver, node_ids


def test_deformation_only_batch_writes_nodal_results(tmp_path):
    progress_values = []
    solver, node_ids = _make_solver(tmp_path, progress_values.append)
    coords = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])

    solver.process_results_in_batch(
        np.array([0.0, 1.0, 2.0]),
        node_ids,
        coords,
        calculate_deformation=True,
    )

    result = pd.read_csv(tmp_path / "max_deformation.csv")
    np.testing.assert_array_equal(result["NodeID"].to_numpy(), node_ids)
    np.testing.assert_allclose(result["DEF_Max"].to_numpy(), [4.0, 6.0])
    assert progress_values == [100]
    assert not list(tmp_path.glob("*.dat"))


def test_batch_propagates_csv_failures_and_removes_memmaps(tmp_path, monkeypatch):
    solver, node_ids = _make_solver(tmp_path)
    coords = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])

    def fail_to_csv(*_args, **_kwargs):
        raise OSError("simulated persistence failure")

    monkeypatch.setattr(pd.DataFrame, "to_csv", fail_to_csv)

    with pytest.raises(OSError, match="simulated persistence failure"):
        solver.process_results_in_batch(
            np.array([0.0, 1.0, 2.0]),
            node_ids,
            coords,
            calculate_deformation=True,
        )

    assert not list(tmp_path.glob("*.dat"))
