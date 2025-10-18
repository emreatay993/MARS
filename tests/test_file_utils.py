"""
Unit tests for file utility functions.

Tests file manipulation and processing utilities.
"""

import os
import sys
import tempfile
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.file_utils import unwrap_mcf_file


class TestFileUtils:
    """Test suite for file utility functions."""
    
    def test_unwrap_mcf_file_basic(self):
        """Test basic MCF file unwrapping."""
        # Create a simple test MCF file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mcf', delete=False) as f:
            f.write("Header Line 1\n")
            f.write("Number of Modes: 5\n")
            f.write("      Time          Coordinates\n")
            f.write("  0.0  1.0  2.0  3.0  4.0\n")
            f.write("      5.0\n")  # Wrapped line
            f.write("  1.0  1.1  2.1  3.1  4.1\n")
            input_path = f.name
        
        output_path = input_path.replace('.mcf', '_unwrapped.mcf')
        
        try:
            result = unwrap_mcf_file(input_path, output_path)
            
            # Check that output file was created
            assert os.path.exists(output_path)
            
            # Check that result is a list
            assert isinstance(result, list)
            
            # Check that lines were unwrapped
            assert len(result) > 0
            
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_unwrap_mcf_file_preserves_header(self):
        """Test that unwrapping preserves header lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mcf', delete=False) as f:
            f.write("Test Header\n")
            f.write("Number of Modes: 2\n")
            f.write("      Time          Coordinates\n")
            f.write("  0.0  1.0\n")
            input_path = f.name
        
        output_path = input_path.replace('.mcf', '_unwrapped.mcf')
        
        try:
            result = unwrap_mcf_file(input_path, output_path)
            
            # Check header is preserved
            assert "Test Header" in result[0]
            assert "Number of Modes: 2" in result[1]
            
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

