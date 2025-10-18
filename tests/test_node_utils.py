"""
Unit tests for node utility functions.

Tests node ID mapping and manipulation functions.
"""

import os
import sys
import numpy as np
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.node_utils import get_node_index_from_id


class TestNodeUtils:
    """Test suite for node utility functions."""
    
    def test_get_node_index_valid_id(self):
        """Test getting index for valid node ID."""
        node_ids = np.array([10, 20, 30, 40, 50])
        
        index = get_node_index_from_id(30, node_ids)
        
        assert index == 2
    
    def test_get_node_index_first_node(self):
        """Test getting index for first node."""
        node_ids = np.array([100, 200, 300])
        
        index = get_node_index_from_id(100, node_ids)
        
        assert index == 0
    
    def test_get_node_index_last_node(self):
        """Test getting index for last node."""
        node_ids = np.array([100, 200, 300])
        
        index = get_node_index_from_id(300, node_ids)
        
        assert index == 2
    
    def test_get_node_index_invalid_id(self):
        """Test getting index for invalid node ID."""
        node_ids = np.array([10, 20, 30])
        
        index = get_node_index_from_id(999, node_ids)
        
        assert index is None
    
    def test_get_node_index_empty_array(self):
        """Test with empty node ID array."""
        node_ids = np.array([])
        
        index = get_node_index_from_id(10, node_ids)
        
        assert index is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

