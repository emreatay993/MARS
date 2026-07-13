"""Installed-package boundaries for the Qt-free MARS runtime."""

import subprocess
import sys
from pathlib import Path


def test_public_package_and_module_cli_are_qt_free():
    src = Path(__file__).resolve().parents[1] / "src"
    code = (
        "import sys, mars_solver; "
        "assert mars_solver.__version__ == '1.0.0'; "
        "assert not any(n == 'PyQt5' or n.startswith('PyQt5.') for n in sys.modules)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
        cwd=src,
    )
    assert completed.returncode == 0, completed.stderr

    version = subprocess.run(
        [sys.executable, "-m", "mars_solver", "--version"],
        capture_output=True,
        text=True,
        check=False,
        cwd=src,
    )
    assert version.returncode == 0, version.stderr
    assert version.stdout.strip() == "MARSBatch 1.0.0"
