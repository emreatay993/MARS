"""
Unit tests for data model classes.

Tests creation and properties of data model classes.
"""

import os
import sys
import numpy as np
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.data_models import (
    ModalData, ModalStressData, DeformationData,
    SteadyStateData, SolverConfig, AnalysisResult
)


class TestModalData:
    """Test suite for ModalData class."""
    
    def test_modal_data_creation(self):
        """Test creating ModalData instance."""
        modal_coord = np.random.rand(10, 100)
        time_values = np.linspace(0, 1, 100)
        
        data = ModalData(modal_coord=modal_coord, time_values=time_values)
        
        assert data.num_modes == 10
        assert data.num_time_points == 100
        assert np.array_equal(data.modal_coord, modal_coord)
        assert np.array_equal(data.time_values, time_values)


class TestModalStressData:
    """Test suite for ModalStressData class."""
    
    def test_stress_data_creation(self):
        """Test creating ModalStressData instance."""
        node_ids = np.array([1, 2, 3, 4, 5])
        modal_sx = np.random.rand(5, 10)
        modal_sy = np.random.rand(5, 10)
        modal_sz = np.random.rand(5, 10)
        modal_sxy = np.random.rand(5, 10)
        modal_syz = np.random.rand(5, 10)
        modal_sxz = np.random.rand(5, 10)
        
        data = ModalStressData(
            node_ids=node_ids,
            modal_sx=modal_sx,
            modal_sy=modal_sy,
            modal_sz=modal_sz,
            modal_sxy=modal_sxy,
            modal_syz=modal_syz,
            modal_sxz=modal_sxz
        )
        
        assert data.num_nodes == 5
        assert data.num_modes == 10
        assert np.array_equal(data.node_ids, node_ids)
    
    def test_stress_data_with_coords(self):
        """Test ModalStressData with optional coordinates."""
        node_ids = np.array([1, 2, 3])
        node_coords = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]])
        modal_sx = np.random.rand(3, 5)
        
        data = ModalStressData(
            node_ids=node_ids,
            modal_sx=modal_sx,
            modal_sy=modal_sx,
            modal_sz=modal_sx,
            modal_sxy=modal_sx,
            modal_syz=modal_sx,
            modal_sxz=modal_sx,
            node_coords=node_coords
        )
        
        assert data.node_coords is not None
        assert data.node_coords.shape == (3, 3)


class TestDeformationData:
    """Test suite for DeformationData class."""
    
    def test_deformation_data_creation(self):
        """Test creating DeformationData instance."""
        node_ids = np.array([1, 2, 3])
        modal_ux = np.random.rand(3, 10)
        modal_uy = np.random.rand(3, 10)
        modal_uz = np.random.rand(3, 10)
        
        data = DeformationData(
            node_ids=node_ids,
            modal_ux=modal_ux,
            modal_uy=modal_uy,
            modal_uz=modal_uz
        )
        
        assert data.num_nodes == 3
        assert data.num_modes == 10
    
    def test_deformation_as_tuple(self):
        """Test as_tuple method."""
        node_ids = np.array([1, 2, 3])
        modal_ux = np.random.rand(3, 10)
        modal_uy = np.random.rand(3, 10)
        modal_uz = np.random.rand(3, 10)
        
        data = DeformationData(
            node_ids=node_ids,
            modal_ux=modal_ux,
            modal_uy=modal_uy,
            modal_uz=modal_uz
        )
        
        ux, uy, uz = data.as_tuple()
        assert np.array_equal(ux, modal_ux)
        assert np.array_equal(uy, modal_uy)
        assert np.array_equal(uz, modal_uz)


class TestSolverConfig:
    """Test suite for SolverConfig class."""
    
    def test_solver_config_defaults(self):
        """Test default values of SolverConfig."""
        config = SolverConfig()
        
        assert config.calculate_von_mises is False
        assert config.calculate_max_principal_stress is False
        assert config.calculate_damage is False
        assert config.skip_n_modes == 0
        assert config.time_history_mode is False
        assert config.include_steady_state is False
    
    def test_solver_config_custom(self):
        """Test creating SolverConfig with custom values."""
        config = SolverConfig(
            calculate_von_mises=True,
            skip_n_modes=2,
            fatigue_A=1000.0,
            fatigue_m=-3.0
        )
        
        assert config.calculate_von_mises is True
        assert config.skip_n_modes == 2
        assert config.fatigue_A == 1000.0
        assert config.fatigue_m == -3.0


class TestAnalysisResult:
    """Test suite for AnalysisResult class."""
    
    def test_analysis_result_creation(self):
        """Test creating AnalysisResult instance."""
        time_vals = np.linspace(0, 1, 100)
        stress_vals = np.random.rand(100)
        
        result = AnalysisResult(
            time_values=time_vals,
            stress_values=stress_vals,
            result_type="von_mises",
            node_id=123
        )
        
        assert result.result_type == "von_mises"
        assert result.node_id == 123
        assert len(result.time_values) == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

