#!/usr/bin/env python3
"""
MARS Build Verification Script

Run this script to verify that all dependencies are properly installed
and the application can start successfully.

Usage:
    python verify_build.py           # Quick check
    python verify_build.py --full    # Full verification with GPU test
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def print_status(name: str, status: bool, details: str = "") -> None:
    """Print a status line with checkmark or X."""
    icon = "✓" if status else "✗"
    color_start = "\033[92m" if status else "\033[91m"  # Green or Red
    color_end = "\033[0m"
    
    # Windows console might not support colors
    try:
        print(f"  {color_start}{icon}{color_end} {name}")
    except Exception:
        print(f"  [{'+' if status else 'X'}] {name}")
    
    if details:
        print(f"      {details}")


def check_python() -> bool:
    """Check Python version."""
    version = sys.version_info
    ok = version >= (3, 9)
    print_status(
        f"Python {version.major}.{version.minor}.{version.micro}",
        ok,
        "Requires Python 3.9+" if not ok else ""
    )
    return ok


def check_import(module_name: str, display_name: str = None) -> bool:
    """Try to import a module and report status."""
    display = display_name or module_name
    try:
        module = __import__(module_name)
        version = getattr(module, "__version__", "")
        print_status(display, True, f"v{version}" if version else "")
        return True
    except ImportError as e:
        print_status(display, False, str(e))
        return False


def check_torch_cuda() -> tuple[bool, bool]:
    """Check PyTorch and CUDA availability."""
    try:
        import torch
        print_status("PyTorch", True, f"v{torch.__version__}")
        
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            device_name = torch.cuda.get_device_name(0)
            print_status("CUDA", True, f"{device_name}")
        else:
            print_status("CUDA", False, "Not available (CPU mode will be used)")
        
        return True, cuda_available
        
    except ImportError as e:
        print_status("PyTorch", False, str(e))
        return False, False
    except Exception as e:
        print_status("PyTorch", False, f"Error: {e}")
        return False, False


def check_pyqt() -> bool:
    """Check PyQt5 installation."""
    try:
        from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
        from PyQt5.QtWidgets import QApplication
        print_status("PyQt5", True, f"Qt {QT_VERSION_STR}, PyQt {PYQT_VERSION_STR}")
        return True
    except ImportError as e:
        print_status("PyQt5", False, str(e))
        return False


def check_vtk_pyvista() -> bool:
    """Check VTK and PyVista installation."""
    try:
        import vtk
        import pyvista as pv
        print_status("VTK", True, f"v{vtk.vtkVersion.GetVTKVersion()}")
        print_status("PyVista", True, f"v{pv.__version__}")
        return True
    except ImportError as e:
        print_status("VTK/PyVista", False, str(e))
        return False


def check_application_modules() -> bool:
    """Check that application modules can be imported."""
    modules = [
        ("utils.torch_setup", "torch_setup"),
        ("utils.constants", "constants"),
        ("core.data_models", "data_models"),
        ("core.computation", "computation"),
        ("file_io.loaders", "loaders"),
        ("solver.engine", "engine"),
        ("ui.application_controller", "ApplicationController"),
    ]
    
    all_ok = True
    for module_path, display_name in modules:
        try:
            __import__(module_path)
            print_status(f"src/{module_path.replace('.', '/')}.py", True)
        except ImportError as e:
            print_status(f"src/{module_path.replace('.', '/')}.py", False, str(e))
            all_ok = False
    
    return all_ok


def run_gpu_test() -> bool:
    """Run a simple GPU computation test."""
    try:
        import torch
        
        if not torch.cuda.is_available():
            print("  (Skipping GPU test - CUDA not available)")
            return True
        
        # Simple tensor operation on GPU
        x = torch.randn(1000, 1000, device="cuda")
        y = torch.randn(1000, 1000, device="cuda")
        z = torch.matmul(x, y)
        _ = z.cpu()  # Sync with CPU
        
        print_status("GPU computation test", True, "Matrix multiply OK")
        return True
        
    except Exception as e:
        print_status("GPU computation test", False, str(e))
        return False


def main():
    parser = argparse.ArgumentParser(description="MARS Build Verification")
    parser.add_argument("--full", action="store_true", help="Run full verification including GPU test")
    args = parser.parse_args()
    
    print_header("MARS Build Verification")
    
    print("System Information:")
    print(f"  Platform: {sys.platform}")
    print(f"  Python executable: {sys.executable}")
    print(f"  Working directory: {os.getcwd()}")
    
    all_ok = True
    
    # Core Python
    print_header("Python Environment")
    all_ok &= check_python()
    
    # Core dependencies
    print_header("Core Dependencies")
    all_ok &= check_import("numpy", "NumPy")
    all_ok &= check_import("scipy", "SciPy")
    all_ok &= check_import("pandas", "Pandas")
    all_ok &= check_import("matplotlib", "Matplotlib")
    
    # PyTorch
    print_header("PyTorch & CUDA")
    torch_ok, cuda_ok = check_torch_cuda()
    all_ok &= torch_ok
    
    # GUI
    print_header("GUI Libraries")
    all_ok &= check_pyqt()
    all_ok &= check_vtk_pyvista()
    
    # Optional packages
    print_header("Optional Packages")
    check_import("numba", "Numba")
    check_import("h5py", "h5py")
    check_import("meshio", "meshio")
    check_import("plotly", "Plotly")
    
    # Application modules
    print_header("Application Modules")
    all_ok &= check_application_modules()
    
    # GPU test (if full mode)
    if args.full and torch_ok:
        print_header("GPU Test")
        run_gpu_test()
    
    # Summary
    print_header("Verification Result")
    if all_ok:
        print("  All critical checks passed!")
        print("  MARS should be able to run on this system.\n")
        return 0
    else:
        print("  Some checks failed!")
        print("  Please review the errors above and install missing dependencies.\n")
        print("  Suggested fix:")
        print("    pip install -r requirements-portable.txt\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

