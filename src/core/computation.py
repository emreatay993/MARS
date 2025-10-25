"""
Analysis engine wrapper for MARS (Modal Analysis Response Solver).

Provides a high-level façade around `MSUPSmartSolverTransient`, handling solver
instantiation, configuration, and result processing.
"""

import numpy as np
from typing import Optional, Tuple

from solver.engine import MSUPSmartSolverTransient
from core.data_models import (
    ModalData, ModalStressData, DeformationData, SteadyStateData,
    SolverConfig, AnalysisResult
)
from utils.node_utils import get_node_index_from_id


class AnalysisEngine:
    """
    High-level wrapper for running MARS analyses.

    Handles solver instantiation, configuration, and provides convenient
    methods for batch, single-node, and time-point analysis.
    """
    
    def __init__(self):
        """Initialize the analysis engine."""
        self.solver = None
        self.modal_data = None
        self.stress_data = None
        self.deformation_data = None
        self.steady_state_data = None
    
    def configure_data(self,
                      modal_data: ModalData,
                      stress_data: ModalStressData,
                      deformation_data: Optional[DeformationData] = None,
                      steady_state_data: Optional[SteadyStateData] = None):
        """
        Configure the engine with analysis data.
        
        Args:
            modal_data: Modal coordinate data.
            stress_data: Modal stress data.
            deformation_data: Optional deformation data.
            steady_state_data: Optional steady-state stress data.
        """
        self.modal_data = modal_data
        self.stress_data = stress_data
        self.deformation_data = deformation_data
        self.steady_state_data = steady_state_data
    
    def create_solver(self, config: SolverConfig) -> MSUPSmartSolverTransient:
        """
        Create and configure a solver instance.
        
        Args:
            config: Solver configuration.
        
        Returns:
            MSUPSmartSolverTransient: Configured solver instance.
        """
        # Apply mode skipping
        mode_slice = slice(config.skip_n_modes, None)
        
        # Prepare modal coordinates
        modal_coord_filtered = self.modal_data.modal_coord[mode_slice, :]
        
        # Prepare stress data
        modal_sx = self.stress_data.modal_sx[:, mode_slice]
        modal_sy = self.stress_data.modal_sy[:, mode_slice]
        modal_sz = self.stress_data.modal_sz[:, mode_slice]
        modal_sxy = self.stress_data.modal_sxy[:, mode_slice]
        modal_syz = self.stress_data.modal_syz[:, mode_slice]
        modal_sxz = self.stress_data.modal_sxz[:, mode_slice]
        
        # Prepare steady-state data
        steady_sx = None
        steady_sy = None
        steady_sz = None
        steady_sxy = None
        steady_syz = None
        steady_sxz = None
        steady_node_ids = None
        
        if config.include_steady_state and self.steady_state_data is not None:
            steady_sx = self.steady_state_data.steady_sx
            steady_sy = self.steady_state_data.steady_sy
            steady_sz = self.steady_state_data.steady_sz
            steady_sxy = self.steady_state_data.steady_sxy
            steady_syz = self.steady_state_data.steady_syz
            steady_sxz = self.steady_state_data.steady_sxz
            steady_node_ids = self.steady_state_data.node_ids
        
        # Prepare deformation data
        modal_deformations = None
        if self.deformation_data is not None:
            modal_deformations = (
                self.deformation_data.modal_ux[:, mode_slice],
                self.deformation_data.modal_uy[:, mode_slice],
                self.deformation_data.modal_uz[:, mode_slice]
            )
        
        # Create solver instance
        solver = MSUPSmartSolverTransient(
            modal_sx, modal_sy, modal_sz,
            modal_sxy, modal_syz, modal_sxz,
            modal_coord_filtered,
            self.modal_data.time_values,
            steady_sx=steady_sx,
            steady_sy=steady_sy,
            steady_sz=steady_sz,
            steady_sxy=steady_sxy,
            steady_syz=steady_syz,
            steady_sxz=steady_sxz,
            steady_node_ids=steady_node_ids,
            modal_node_ids=self.stress_data.node_ids,
            output_directory=config.output_directory,
            modal_deformations=modal_deformations
        )
        
        # Set fatigue parameters if damage calculation is enabled
        if config.calculate_damage:
            solver.fatigue_A = config.fatigue_A
            solver.fatigue_m = config.fatigue_m
        
        self.solver = solver
        return solver
    
    def run_batch_analysis(self, config: SolverConfig) -> None:
        """
        Run batch analysis for all nodes.
        
        Args:
            config: Solver configuration with output settings.
        """
        if self.solver is None:
            self.solver = self.create_solver(config)
        
        # Run batch processing
        self.solver.process_results_in_batch(
            self.modal_data.time_values,
            self.stress_data.node_ids,
            self.stress_data.node_coords,
            calculate_damage=config.calculate_damage,
            calculate_von_mises=config.calculate_von_mises,
            calculate_max_principal_stress=config.calculate_max_principal_stress,
            calculate_min_principal_stress=config.calculate_min_principal_stress,
            calculate_deformation=config.calculate_deformation,
            calculate_velocity=config.calculate_velocity,
            calculate_acceleration=config.calculate_acceleration
        )
    
    def run_single_node_analysis(self, node_id: int, 
                                 config: SolverConfig) -> AnalysisResult:
        """
        Run analysis for a single node.
        
        Args:
            node_id: Node ID to analyze.
            config: Solver configuration.
        
        Returns:
            AnalysisResult: Analysis results for the node.
        """
        if self.solver is None:
            self.solver = self.create_solver(config)
        
        # Get node index
        node_idx = get_node_index_from_id(node_id, self.stress_data.node_ids)
        if node_idx is None:
            raise ValueError(f"Node ID {node_id} not found.")
        
        # Run single-node processing
        time_indices, stress_values = self.solver.process_results_for_a_single_node(
            node_idx,
            node_id,
            self.stress_data.node_ids,
            calculate_von_mises=config.calculate_von_mises,
            calculate_max_principal_stress=config.calculate_max_principal_stress,
            calculate_min_principal_stress=config.calculate_min_principal_stress,
            calculate_deformation=config.calculate_deformation,
            calculate_velocity=config.calculate_velocity,
            calculate_acceleration=config.calculate_acceleration
        )
        
        # Determine result type
        result_type = "unknown"
        if config.calculate_von_mises:
            result_type = "von_mises"
        elif config.calculate_max_principal_stress:
            result_type = "max_principal"
        elif config.calculate_min_principal_stress:
            result_type = "min_principal"
        elif config.calculate_deformation:
            result_type = "deformation"
        elif config.calculate_velocity:
            result_type = "velocity"
        elif config.calculate_acceleration:
            result_type = "acceleration"
        
        return AnalysisResult(
            time_values=time_indices,
            stress_values=stress_values,
            result_type=result_type,
            node_id=node_id
        )
    
    def compute_time_point_stresses(self, time_index: int) -> Tuple[np.ndarray, ...]:
        """
        Compute stress components at a specific time point.
        
        Args:
            time_index: Index of the time point to compute.
        
        Returns:
            Tuple of stress component arrays.
        """
        if self.solver is None:
            raise ValueError("Solver not initialized. Call create_solver() first.")
        
        # Compute stresses for all nodes at the given time point
        return self.solver.compute_normal_stresses(0, self.stress_data.num_nodes)
    
    def reset(self):
        """Reset the engine state."""
        self.solver = None
