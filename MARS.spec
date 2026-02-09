# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


PROJECT_ROOT = Path(SPECPATH).resolve()
SRC_DIR = PROJECT_ROOT / "src"
HOOKS_DIR = PROJECT_ROOT / "hooks"
ICON_FILE = PROJECT_ROOT / "resources" / "icons" / "mars_icon.ico"


def _safe_collect_submodules(package_name):
    """Collect helper that tolerates missing optional packages."""
    try:
        return collect_submodules(package_name)
    except Exception:
        return []


datas = [(str(PROJECT_ROOT / "resources"), "resources")]
if (SRC_DIR / "youngs_modulus.csv").exists():
    datas.append((str(SRC_DIR / "youngs_modulus.csv"), "."))

binaries = []

hiddenimports = [
    "PyQt5.QtWebChannel",
    "PyQt5.QtWebEngineCore",
    "PyQt5.QtWebEngineWidgets",
    "matplotlib.backends.backend_qt5agg",
    "plotly.graph_objects",
    "plotly.io",
    "plotly.offline",
    "plotly.subplots",
    "plotly_resampler",
    "pyvistaqt",
    "vtkmodules.all",
]
hiddenimports += _safe_collect_submodules("vtkmodules")
hiddenimports = sorted(set(hiddenimports))

excludes = [
    "dash",
    "dash_core_components",
    "dash_html_components",
    "dash_table",
    "pytest",
    "scipy._lib.array_api_compat.cupy",
    "scipy._lib.array_api_compat.torch",
    "tensorboard",
    "torch",
    "torchaudio",
    "torchvision",
]


a = Analysis(
    [str(SRC_DIR / "main.py")],
    pathex=[str(SRC_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(HOOKS_DIR)],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MARS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=str(ICON_FILE) if ICON_FILE.exists() else None,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MARS",
)
