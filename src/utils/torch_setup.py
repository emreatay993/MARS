"""
PyTorch initialization module for Windows CUDA compatibility.

This module MUST be imported before any other module that uses torch.
It fixes DLL loading issues on Windows when old CUDA DLLs exist in PATH
(e.g., from NVIDIA PhysX).

Usage:
    In your entry point (main.py), add as the FIRST import:
        import utils.torch_setup  # noqa: F401
"""

import os
import sys

if sys.platform == 'win32':
    import importlib.util
    
    torch_spec = importlib.util.find_spec('torch')
    if torch_spec and torch_spec.submodule_search_locations:
        torch_lib_path = os.path.join(torch_spec.submodule_search_locations[0], 'lib')
        if os.path.isdir(torch_lib_path):
            # Add to PATH for legacy DLL resolution
            os.environ['PATH'] = torch_lib_path + os.pathsep + os.environ.get('PATH', '')
            # Use add_dll_directory for Python 3.8+ DLL resolution
            if hasattr(os, 'add_dll_directory'):
                os.add_dll_directory(torch_lib_path)

# Import torch to lock in the correct DLLs and export for other modules
import torch

__all__ = ['torch']

