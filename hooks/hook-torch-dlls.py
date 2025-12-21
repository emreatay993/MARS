"""
Runtime hook to fix PyTorch DLL loading on Windows.
This MUST run before any torch imports - it sets up DLL search paths
for c10.dll and its dependencies (CUDA, cuDNN, VC++ Runtime).

This hook runs at the very start of the frozen application, BEFORE main.py.
"""

import os
import sys
import ctypes

def _setup_dll_paths():
    """Set up DLL search paths for PyTorch in frozen builds."""
    if sys.platform != "win32":
        return
    
    # In PyInstaller one-folder builds:
    # - sys._MEIPASS points to dist/MARS/_internal (where the files are extracted)
    # - sys.executable is dist/MARS/MARS.exe
    
    if hasattr(sys, "_MEIPASS"):
        # _MEIPASS is the _internal folder
        internal_dir = sys._MEIPASS
    else:
        # Fallback for non-frozen mode
        internal_dir = os.path.dirname(os.path.abspath(sys.executable))
    
    # All directories that might contain required DLLs
    # Note: torch/lib is relative to _internal (which is _MEIPASS)
    dll_directories = [
        internal_dir,  # _internal itself has CRT DLLs
        os.path.join(internal_dir, "torch", "lib"),  # Main torch DLLs
        os.path.join(internal_dir, "torch", "bin"),
    ]
    
    # Also add nvidia directories if they exist
    nvidia_base = os.path.join(internal_dir, "nvidia")
    if os.path.isdir(nvidia_base):
        for subdir in os.listdir(nvidia_base):
            for lib_subdir in ["bin", "lib"]:
                lib_path = os.path.join(nvidia_base, subdir, lib_subdir)
                if os.path.isdir(lib_path):
                    dll_directories.append(lib_path)
    
    # Configure Windows DLL loader BEFORE adding directories
    try:
        kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)
        
        # SetDefaultDllDirectories - LOAD_LIBRARY_SEARCH_DEFAULT_DIRS (0x1000)
        # This makes Windows use our add_dll_directory calls
        if hasattr(kernel32, "SetDefaultDllDirectories"):
            kernel32.SetDefaultDllDirectories(0x00001000)
        
        # Find torch lib and set it as the primary DLL directory
        for dll_dir in dll_directories:
            if "torch" in dll_dir and "lib" in dll_dir and os.path.isdir(dll_dir):
                if hasattr(kernel32, "SetDllDirectoryW"):
                    kernel32.SetDllDirectoryW(dll_dir)
                break
    except Exception:
        pass
    
    # Add all directories to both PATH and Python's DLL search
    for dll_dir in dll_directories:
        if os.path.isdir(dll_dir):
            # Prepend to PATH environment variable
            current_path = os.environ.get("PATH", "")
            if dll_dir not in current_path:
                os.environ["PATH"] = dll_dir + os.pathsep + current_path
            
            # Use Python 3.8+ API for DLL directory search
            if hasattr(os, "add_dll_directory"):
                try:
                    os.add_dll_directory(dll_dir)
                except (OSError, FileNotFoundError):
                    pass

# Execute immediately when hook is loaded (before ANY imports in main.py)
_setup_dll_paths()
