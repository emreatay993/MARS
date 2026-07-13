"""
Regression tests for single-node time-history time axis behavior.
"""

import os
import sys

import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mars_solver.solver.engine import MSUPSmartSolverTransient
from mars_solver.utils import constants


def _make_solver(time_values):
    solver = MSUPSmartSolverTransient.__new__(MSUPSmartSolverTransient)
    solver.time_values = None if time_values is None else np.asarray(time_values, dtype=float)
    solver.plasticity_context = None
    solver.modal_deformations_ux = None
    solver.modal_forces_fx = None
    return solver


def _stub_stress_path(solver, num_steps):
    block = np.zeros((1, num_steps), dtype=float)
    solver.compute_normal_stresses_for_a_single_node = (
        lambda _idx: (block, block, block, block, block, block)
    )
    solver.compute_von_mises_stress = (
        lambda *_args: np.arange(num_steps, dtype=float).reshape(1, -1)
    )


def _stub_force_moment_path(solver, num_steps):
    solver.modal_forces_fx = np.ones((1, 1), dtype=float)
    series = np.linspace(1.0, 2.0, num_steps, dtype=float).reshape(1, -1)
    solver.compute_forces_moments = lambda *_args: (series, series, series, series, series, series)


def test_von_mises_time_history_uses_physical_time_values():
    solver = _make_solver([0.0, 0.1, 0.2, 0.3])
    _stub_stress_path(solver, num_steps=4)

    time_axis, values, metadata = solver.process_results_for_a_single_node(
        selected_node_idx=0,
        selected_node_id=101,
        _df_node_ids=None,
        calculate_von_mises=True,
    )

    np.testing.assert_allclose(time_axis, np.array([0.0, 0.1, 0.2, 0.3]))
    np.testing.assert_allclose(values, np.array([0.0, 1.0, 2.0, 3.0]))
    assert metadata == {}


def test_von_mises_time_history_falls_back_to_indices_when_time_length_mismatch():
    solver = _make_solver([0.0, 0.1])
    _stub_stress_path(solver, num_steps=4)

    time_axis, _, _ = solver.process_results_for_a_single_node(
        selected_node_idx=0,
        selected_node_id=101,
        _df_node_ids=None,
        calculate_von_mises=True,
    )

    np.testing.assert_array_equal(time_axis, np.array([0.0, 1.0, 2.0, 3.0]))


def test_force_moment_time_history_uses_physical_time_values():
    solver = _make_solver([1.0, 1.5, 2.0])
    _stub_force_moment_path(solver, num_steps=3)

    time_axis, values, metadata = solver.process_results_for_a_single_node(
        selected_node_idx=0,
        selected_node_id=202,
        _df_node_ids=None,
        calculate_force_moment=True,
    )

    np.testing.assert_allclose(time_axis, np.array([1.0, 1.5, 2.0]))
    assert "Force Mag" in values
    assert metadata == {}


def test_memory_estimate_accounts_for_scalar_plasticity_working_sets():
    solver = _make_solver(None)
    num_steps = 100

    base = solver._get_memory_per_node(
        num_steps,
        calculate_von_mises=True,
        calculate_max_principal_stress=False,
        calculate_damage=False,
        calculate_deformation=False,
        calculate_velocity=False,
        calculate_acceleration=False,
        calculate_scalar_plasticity=False,
    )
    with_plasticity = solver._get_memory_per_node(
        num_steps,
        calculate_von_mises=True,
        calculate_max_principal_stress=False,
        calculate_damage=False,
        calculate_deformation=False,
        calculate_velocity=False,
        calculate_acceleration=False,
        calculate_scalar_plasticity=True,
    )

    expected_extra = 4 * num_steps * np.dtype(constants.NP_DTYPE).itemsize
    assert with_plasticity - base == expected_extra
