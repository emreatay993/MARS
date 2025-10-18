"""
Data models for the MSUP Smart Solver.

This module defines dataclasses and structures to hold various types of
analysis data in a structured and type-safe manner.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple
import numpy as np


@dataclass
class ModalData:
    """
    Container for modal coordinate data.
    
    Attributes:
        modal_coord: Modal coordinates array, shape (num_modes, num_time_points).
        time_values: Array of time values.
        num_modes: Number of modes in the modal coordinate data.
        num_time_points: Number of time points in the analysis.
    """
    modal_coord: np.ndarray
    time_values: np.ndarray
    
    @property
    def num_modes(self) -> int:
        """Number of modes."""
        return self.modal_coord.shape[0]
    
    @property
    def num_time_points(self) -> int:
        """Number of time points."""
        return self.modal_coord.shape[1]


@dataclass
class ModalStressData:
    """
    Container for modal stress components.
    
    Attributes:
        node_ids: Array of node IDs.
        modal_sx: Modal stress in X direction, shape (num_nodes, num_modes).
        modal_sy: Modal stress in Y direction, shape (num_nodes, num_modes).
        modal_sz: Modal stress in Z direction, shape (num_nodes, num_modes).
        modal_sxy: Modal shear stress XY, shape (num_nodes, num_modes).
        modal_syz: Modal shear stress YZ, shape (num_nodes, num_modes).
        modal_sxz: Modal shear stress XZ, shape (num_nodes, num_modes).
        node_coords: Optional node coordinates, shape (num_nodes, 3).
    """
    node_ids: np.ndarray
    modal_sx: np.ndarray
    modal_sy: np.ndarray
    modal_sz: np.ndarray
    modal_sxy: np.ndarray
    modal_syz: np.ndarray
    modal_sxz: np.ndarray
    node_coords: Optional[np.ndarray] = None
    
    @property
    def num_nodes(self) -> int:
        """Number of nodes."""
        return len(self.node_ids)
    
    @property
    def num_modes(self) -> int:
        """Number of modes."""
        return self.modal_sx.shape[1]


@dataclass
class DeformationData:
    """
    Container for modal deformation components.
    
    Attributes:
        node_ids: Array of node IDs.
        modal_ux: Modal displacement in X direction, shape (num_nodes, num_modes).
        modal_uy: Modal displacement in Y direction, shape (num_nodes, num_modes).
        modal_uz: Modal displacement in Z direction, shape (num_nodes, num_modes).
    """
    node_ids: np.ndarray
    modal_ux: np.ndarray
    modal_uy: np.ndarray
    modal_uz: np.ndarray
    
    @property
    def num_nodes(self) -> int:
        """Number of nodes."""
        return len(self.node_ids)
    
    @property
    def num_modes(self) -> int:
        """Number of modes."""
        return self.modal_ux.shape[1]
    
    def as_tuple(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return deformations as a tuple (ux, uy, uz)."""
        return (self.modal_ux, self.modal_uy, self.modal_uz)


@dataclass
class SteadyStateData:
    """
    Container for steady-state stress data.
    
    Attributes:
        node_ids: Array of node IDs.
        steady_sx: Steady-state stress in X direction.
        steady_sy: Steady-state stress in Y direction.
        steady_sz: Steady-state stress in Z direction.
        steady_sxy: Steady-state shear stress XY.
        steady_syz: Steady-state shear stress YZ.
        steady_sxz: Steady-state shear stress XZ.
    """
    node_ids: np.ndarray
    steady_sx: np.ndarray
    steady_sy: np.ndarray
    steady_sz: np.ndarray
    steady_sxy: np.ndarray
    steady_syz: np.ndarray
    steady_sxz: np.ndarray
    
    @property
    def num_nodes(self) -> int:
        """Number of nodes."""
        return len(self.node_ids)


@dataclass
class SolverConfig:
    """
    Configuration settings for the solver.
    
    Attributes:
        calculate_von_mises: Whether to calculate von Mises stress.
        calculate_max_principal_stress: Whether to calculate max principal stress.
        calculate_min_principal_stress: Whether to calculate min principal stress.
        calculate_deformation: Whether to calculate deformation.
        calculate_velocity: Whether to calculate velocity.
        calculate_acceleration: Whether to calculate acceleration.
        calculate_damage: Whether to calculate damage index.
        fatigue_A: Fatigue strength coefficient (for damage calculation).
        fatigue_m: Fatigue strength exponent (for damage calculation).
        skip_n_modes: Number of modes to skip from the beginning.
        time_history_mode: Whether in time history mode (single node).
        selected_node_id: Node ID for time history mode.
        include_steady_state: Whether to include steady-state stress.
        output_directory: Directory for output files.
    """
    calculate_von_mises: bool = False
    calculate_max_principal_stress: bool = False
    calculate_min_principal_stress: bool = False
    calculate_deformation: bool = False
    calculate_velocity: bool = False
    calculate_acceleration: bool = False
    calculate_damage: bool = False
    fatigue_A: Optional[float] = None
    fatigue_m: Optional[float] = None
    skip_n_modes: int = 0
    time_history_mode: bool = False
    selected_node_id: Optional[int] = None
    include_steady_state: bool = False
    output_directory: Optional[str] = None


@dataclass
class AnalysisResult:
    """
    Container for analysis results.
    
    Attributes:
        time_values: Array of time values (for time history).
        stress_values: Computed stress or other values.
        result_type: Type of result (e.g., 'von_mises', 'max_principal').
        node_id: Node ID (for single node results).
        metadata: Additional metadata dictionary.
    """
    time_values: Optional[np.ndarray] = None
    stress_values: Optional[np.ndarray] = None
    result_type: str = "unknown"
    node_id: Optional[int] = None
    metadata: dict = field(default_factory=dict)

