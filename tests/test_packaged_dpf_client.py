"""Packaging contract for the bundled PyDPF client and batch launcher."""

import json
import os
import subprocess
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


def test_spec_builds_windowed_and_batch_launchers_from_one_analysis():
    spec = (PROJECT_ROOT / "MARS.spec").read_text(encoding="utf-8")
    gui_start = spec.index("gui_exe = EXE(")
    batch_start = spec.index("batch_exe = EXE(")
    collect_start = spec.index("coll = COLLECT(")
    gui_block = spec[gui_start:batch_start]
    batch_block = spec[batch_start:collect_start]
    collect_block = spec[collect_start:]

    assert spec.count("Analysis(") == 1
    assert 'name="MARS"' in gui_block
    assert "console=False" in gui_block
    assert 'name="MARSBatch"' in batch_block
    assert "console=True" in batch_block
    assert "gui_exe,\n    batch_exe," in collect_block


@pytest.mark.skipif(
    not os.environ.get("MARS_TEST_PACKAGED_DIR"),
    reason="Set MARS_TEST_PACKAGED_DIR to a built dist/MARS directory.",
)
def test_frozen_package_contains_gui_and_batch_launchers():
    package_dir = Path(os.environ["MARS_TEST_PACKAGED_DIR"]).resolve()

    assert (package_dir / "MARS.exe").is_file()
    assert (package_dir / "MARSBatch.exe").is_file()


@pytest.mark.skipif(
    not os.environ.get("MARS_TEST_PACKAGED_DIR"),
    reason="Set MARS_TEST_PACKAGED_DIR to a built dist/MARS directory.",
)
def test_frozen_batch_launcher_help():
    package_dir = Path(os.environ["MARS_TEST_PACKAGED_DIR"]).resolve()
    completed = subprocess.run(
        [str(package_dir / "MARSBatch.exe"), "--help"],
        cwd=package_dir,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0
    assert "usage:" in f"{completed.stdout}\n{completed.stderr}".lower()


@pytest.mark.parametrize("mode", ["batch", "time_history"])
@pytest.mark.skipif(
    not os.environ.get("MARS_TEST_PACKAGED_DIR"),
    reason="Set MARS_TEST_PACKAGED_DIR to a built dist/MARS directory.",
)
def test_frozen_batch_launcher_runs_deformation_job(tmp_path, mode):
    package_dir = Path(os.environ["MARS_TEST_PACKAGED_DIR"]).resolve()
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (inputs / "response.mcf").write_text(
        "Modal Coordinates File - Synthetic\n"
        "Number of Modes:   2\n"
        "  Mode: 1 2\n"
        "      Time          Coordinates...\n"
        "  0.0 0.0 1.0\n"
        "  0.1 1.0 0.0\n"
        "  0.2 2.0 -1.0\n"
        "  0.3 3.0 0.0\n",
        encoding="utf-8",
    )
    (inputs / "deformation.csv").write_text(
        "NodeID,X,Y,Z,ux_Mode1,uy_Mode1,uz_Mode1,ux_Mode2,uy_Mode2,uz_Mode2\n"
        "7,1,2,3,1,0,0,0.5,0,0\n",
        encoding="utf-8",
    )
    payload = {
        "schema_version": 1,
        "mode": mode,
        "inputs": {
            "modal_coordinates": "inputs/response.mcf",
            "modal_deformation": "inputs/deformation.csv",
        },
        "outputs": ["deformation"],
        "settings": {},
        "output_directory": "results",
    }
    if mode == "time_history":
        payload["node_id"] = 7
    job_path = tmp_path / "job.json"
    job_path.write_text(json.dumps(payload), encoding="utf-8")

    completed = subprocess.run(
        [
            str(package_dir / "MARSBatch.exe"),
            "run",
            str(job_path),
            "--format",
            "json",
        ],
        cwd=package_dir,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=60,
        check=False,
    )
    records = [json.loads(line) for line in completed.stdout.splitlines()]

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert records[-1]["record"] == "result"
    assert records[-1]["result"]["status"] == "completed"
    assert (tmp_path / "results/mars_result.json").is_file()
    expected = (
        "max_deformation.csv"
        if mode == "batch"
        else "time_history_node_7_deformation.csv"
    )
    assert (tmp_path / "results" / expected).is_file()


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
