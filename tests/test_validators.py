"""
Unit tests for file validators.

Tests validation functions for MCF, stress, deformation, and steady-state files.
"""

import os
import tempfile
import pytest
import pandas as pd

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from file_io.validators import (
    validate_mcf_file,
    validate_modal_stress_file,
    validate_deformation_file,
    validate_steady_state_file
)


class TestValidators:
    """Test suite for validation functions."""
    
    def test_validate_mcf_file_nonexistent(self):
        """Test MCF validator with nonexistent file."""
        is_valid, error = validate_mcf_file("nonexistent.mcf")
        assert not is_valid
        assert error is not None
    
    def test_validate_modal_stress_file_nonexistent(self):
        """Test stress validator with nonexistent file."""
        is_valid, error = validate_modal_stress_file("nonexistent.csv")
        assert not is_valid
        assert error is not None
    
    def test_validate_deformation_file_nonexistent(self):
        """Test deformation validator with nonexistent file."""
        is_valid, error = validate_deformation_file("nonexistent.csv")
        assert not is_valid
        assert error is not None
    
    def test_validate_steady_state_file_nonexistent(self):
        """Test steady state validator with nonexistent file."""
        is_valid, error = validate_steady_state_file("nonexistent.txt")
        assert not is_valid
        assert error is not None
    
    def test_validate_modal_stress_file_missing_nodeid(self):
        """Test stress validator with missing NodeID column."""
        # Create temp file without NodeID
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("X,Y,Z,sx_1,sy_1\n")
            f.write("1,2,3,4,5\n")
            temp_path = f.name
        
        try:
            is_valid, error = validate_modal_stress_file(temp_path)
            assert not is_valid
            assert "NodeID" in error
        finally:
            os.remove(temp_path)
    
    def test_validate_deformation_file_missing_components(self):
        """Test deformation validator with missing component columns."""
        # Create temp file without ux_ columns
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("NodeID,X,Y,Z\n")
            f.write("1,2,3,4\n")
            temp_path = f.name
        
        try:
            is_valid, error = validate_deformation_file(temp_path)
            assert not is_valid
            assert "ux_" in error
        finally:
            os.remove(temp_path)
    
    def test_validate_steady_state_file_missing_columns(self):
        """Test steady state validator with missing required columns."""
        # Create temp file without all required columns
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Node Number\tSX (MPa)\n")
            f.write("1\t100\n")
            temp_path = f.name
        
        try:
            is_valid, error = validate_steady_state_file(temp_path)
            assert not is_valid
            assert "SY (MPa)" in error or "SZ (MPa)" in error
        finally:
            os.remove(temp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

