"""Packaging contract for the bundled PyDPF client."""

import os
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_spec_collects_pydpf_client():
    spec = (PROJECT_ROOT / "MARS.spec").read_text(encoding="utf-8")
    for required in (
        'copy_metadata("ansys-dpf-core")',
        'collect_dynamic_libs("ansys.dpf.gatebin")',
        'collect_submodules("ansys.dpf")',
        'collect_submodules("ansys.grpc.dpf")',
    ):
        assert required in spec


def test_spec_avoids_optional_qt_and_vtk_umbrellas():
    spec = (PROJECT_ROOT / "MARS.spec").read_text(encoding="utf-8")

    assert '"PyQt5.Qt"' in spec
    assert '"PyQt5.QtOpenGL"' in spec
    assert '"_tkinter"' in spec
    assert '"tkinter"' in spec
    assert '"vtk"' in spec
    assert '"vtkmodules.all"' not in spec
    assert 'collect_submodules("vtkmodules")' not in spec
    assert '"matplotlib": {"backends": ["QtAgg", "Agg"]}' in spec


@pytest.mark.skipif(
    not os.environ.get("MARS_TEST_PACKAGED_DIR"),
    reason="Set MARS_TEST_PACKAGED_DIR to a built dist/MARS directory.",
)
def test_frozen_package_contains_pydpf_client():
    package_dir = Path(os.environ["MARS_TEST_PACKAGED_DIR"]).resolve()
    internal = package_dir / "_internal"
    metadata = internal / "ansys_dpf_core-0.16.1.dist-info" / "METADATA"

    assert metadata.is_file()
    assert "Version: 0.16.1" in metadata.read_text(encoding="utf-8")
    gatebin = internal / "ansys" / "dpf" / "gatebin"
    assert (gatebin / "Ans.Dpf.GrpcClient.dll").is_file()
    assert (gatebin / "DPFClientAPI.dll").is_file()
    assert not any("dpf" in path.name.lower() for path in package_dir.rglob("*.exe"))


@pytest.mark.skipif(
    not os.environ.get("MARS_TEST_PACKAGED_DIR"),
    reason="Set MARS_TEST_PACKAGED_DIR to a built dist/MARS directory.",
)
def test_frozen_package_omits_optional_qt_and_vtk_modules():
    package_dir = Path(os.environ["MARS_TEST_PACKAGED_DIR"]).resolve()
    internal = package_dir / "_internal"

    qt_modules = {path.stem for path in internal.rglob("Qt*.pyd")}
    assert qt_modules == {
        "QtCore", "QtGui", "QtNetwork", "QtPositioning", "QtPrintSupport",
        "QtQml", "QtQuick", "QtQuickWidgets", "QtWebChannel",
        "QtWebEngineCore", "QtWebEngineWidgets", "QtWidgets",
    }
    assert not (internal / "_tkinter.pyd").exists()

    vtk_modules = {
        path.name.split(".", 1)[0]
        for path in (internal / "vtkmodules").glob("vtk*.pyd")
    }
    assert {
        "vtkCommonDataModel", "vtkFiltersGeneral", "vtkInteractionWidgets",
        "vtkRenderingCore", "vtkRenderingFreeType", "vtkRenderingLabel",
        "vtkRenderingOpenGL2", "vtkRenderingUI",
    } <= vtk_modules
    assert not {
        "vtkIOExodus", "vtkIOExport", "vtkIOExportGL2PS", "vtkIOImport",
        "vtkIOParallel",
    } & vtk_modules
    assert not any(
        name.startswith((
            "vtkParallelMPI", "vtkRenderingOpenXR", "vtkRenderingVR",
            "vtkTesting", "vtkWeb",
        ))
        for name in vtk_modules
    )
