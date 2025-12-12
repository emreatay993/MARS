# src/sitecustomize.py
# Runs automatically on Python startup (after site.py) if it's on sys.path.
# This is the earliest reliable place to fix DLL search paths on Windows.

import os
import sys
from pathlib import Path

def _add_torch_lib_to_dll_search_path() -> None:
    if not sys.platform.startswith("win"):
        return

    # Typical venv location
    torch_lib = Path(sys.prefix) / "Lib" / "site-packages" / "torch" / "lib"

    # Fallback: look through sys.path
    if not torch_lib.is_dir():
        for p in sys.path:
            try:
                pp = Path(p)
            except Exception:
                continue
            if pp.name.lower() == "site-packages":
                cand = pp / "torch" / "lib"
                if cand.is_dir():
                    torch_lib = cand
                    break

    if torch_lib.is_dir():
        # Python 3.8+ preferred method (affects DLL resolution)
        os.add_dll_directory(str(torch_lib))

        # Also prepend PATH for any nested loads / subprocesses
        os.environ["PATH"] = str(torch_lib) + os.pathsep + os.environ.get("PATH", "")

_add_torch_lib_to_dll_search_path()
