#!/usr/bin/env python3
"""
MARS Build Verification Script

Run this script to verify that all dependencies are properly installed
and the application can start successfully.

Usage:
    python verify_build.py           # Quick check
    python verify_build.py --full    # Full verification
"""

from __future__ import annotations

import argparse
import importlib.metadata
import os
import re
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
    ok = version[:2] == (3, 12)
    print_status(
        f"Python {version.major}.{version.minor}.{version.micro}",
        ok,
        "Release builds require Python 3.12" if not ok else ""
    )
    return ok


def _discover_ansys_dpf_runtimes() -> list[tuple[int, Path]]:
    """Return installed Ansys 2025 R2+ roots in newest-first order."""
    candidates: dict[int, Path] = {}
    for name, value in os.environ.items():
        match = re.fullmatch(r"AWP_ROOT(\d{3})", name.upper())
        if match and int(match.group(1)) >= 252 and Path(value).is_dir():
            candidates[int(match.group(1))] = Path(value)

    program_files = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
    ansys_root = program_files / "ANSYS Inc"
    if ansys_root.is_dir():
        for path in ansys_root.glob("v[0-9][0-9][0-9]"):
            try:
                release = int(path.name[1:])
            except ValueError:
                continue
            if release >= 252:
                candidates.setdefault(release, path)

    return sorted(candidates.items(), reverse=True)


def check_dpf_environment(validate_server: bool = False) -> bool:
    """Report whether direct RST loading dependencies are available."""
    try:
        client_version = importlib.metadata.version("ansys-dpf-core")
    except importlib.metadata.PackageNotFoundError:
        print_status(
            "Ansys DPF RST support",
            False,
            "ansys-dpf-core is not installed; CSV workflows remain available",
        )
        return False

    client_ok = client_version == "0.16.1"
    print_status(
        "ansys-dpf-core",
        client_ok,
        f"v{client_version}; expected v0.16.1" if not client_ok else f"v{client_version}",
    )

    runtimes = _discover_ansys_dpf_runtimes()
    if runtimes:
        release, path = runtimes[0]
        print_status(
            "Compatible installed DPF runtime",
            True,
            f"Ansys v{release}: {path}",
        )
    else:
        print_status(
            "Compatible installed DPF runtime",
            False,
            "Install Ansys 2025 R2 or newer for direct .rst loading; CSV workflows remain available",
        )
    runtime_ok = bool(runtimes)
    server_ok = True
    if validate_server and client_ok and runtime_ok:
        server = None
        try:
            import ansys.dpf.core as dpf

            server = dpf.start_local_server(
                as_global=False,
                use_docker_by_default=False,
                use_pypim_by_default=False,
                timeout=60.0,
            )
            server_ok = bool(server.meet_version("10.0"))
            print_status(
                "DPF server startup",
                server_ok,
                f"server v{server.version}; requires v10.0 or newer",
            )
        except Exception as exc:
            server_ok = False
            print_status("DPF server startup", False, str(exc))
        finally:
            if server is not None:
                try:
                    server.shutdown()
                except Exception:
                    pass

    return client_ok and runtime_ok and server_ok


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


def main():
    parser = argparse.ArgumentParser(description="MARS Build Verification")
    parser.add_argument("--full", action="store_true", help="Run full verification")
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

    # Direct RST support is optional for CSV-only use, but required by --full.
    print_header("Ansys DPF RST Support")
    dpf_ready = check_dpf_environment(validate_server=args.full)
    if args.full:
        all_ok &= dpf_ready
    
    # Application modules
    print_header("Application Modules")
    all_ok &= check_application_modules()
    
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

