# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_dynamic_libs,
    collect_submodules,
    copy_metadata,
)


PROJECT_ROOT = Path(SPECPATH).resolve()
SRC_DIR = PROJECT_ROOT / "src"
HOOKS_DIR = PROJECT_ROOT / "hooks"
ICON_FILE = PROJECT_ROOT / "resources" / "icons" / "mars_icon.ico"


datas = [(str(PROJECT_ROOT / "resources"), "resources")]
if (SRC_DIR / "youngs_modulus.csv").exists():
    datas.append((str(SRC_DIR / "youngs_modulus.csv"), "."))
datas += copy_metadata("ansys-dpf-core")
datas += copy_metadata("ansys-tools-common")

binaries = collect_dynamic_libs("ansys.dpf.gatebin")

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
]
hiddenimports += collect_submodules("ansys.dpf")
hiddenimports += collect_submodules("ansys.grpc.dpf")
hiddenimports = sorted(set(hiddenimports))

excludes = [
    "PyQt5.Qt",
    "PyQt5.QtOpenGL",
    "_tkinter",
    "pytest",
    "scipy._lib.array_api_compat.cupy",
    "scipy._lib.array_api_compat.torch",
    "tensorboard",
    "tkinter",
    "torch",
    "torchaudio",
    "torchvision",
    "vtk",
    "vtkmodules.vtkIOExodus",
    "vtkmodules.vtkIOExport",
    "vtkmodules.vtkIOExportGL2PS",
    "vtkmodules.vtkIOImport",
    "vtkmodules.vtkIOParallel",
]


a = Analysis(
    [str(SRC_DIR / "main.py")],
    pathex=[str(SRC_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(HOOKS_DIR)],
    hooksconfig={"matplotlib": {"backends": ["QtAgg", "Agg"]}},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

gui_exe = EXE(
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
batch_exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MARSBatch",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=str(ICON_FILE) if ICON_FILE.exists() else None,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    gui_exe,
    batch_exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MARS",
)
