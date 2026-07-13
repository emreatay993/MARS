"""Focused contract tests for the Qt-free MARS job runtime."""

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import mars_solver.headless_runtime as runtime
from mars_solver.core.data_models import AnalysisResult, DeformationData, ModalData, ModalStressData


def _modal():
    return ModalData(
        modal_coord=np.array([[0.0, 1.0, 2.0, 3.0], [1.0, 0.0, -1.0, 0.0]]),
        time_values=np.array([0.0, 0.1, 0.2, 0.3]),
    )


def _stress():
    values = np.ones((1, 2), dtype=float)
    return ModalStressData(
        node_ids=np.array([7]),
        modal_sx=values,
        modal_sy=values,
        modal_sz=values,
        modal_sxy=values,
        modal_syz=values,
        modal_sxz=values,
        node_coords=np.array([[1.0, 2.0, 3.0]]),
    )


def _deformation():
    values = np.ones((1, 2), dtype=float)
    return DeformationData(
        node_ids=np.array([7]),
        modal_ux=values,
        modal_uy=values,
        modal_uz=values,
        node_coords=np.array([[1.0, 2.0, 3.0]]),
    )


def _files(tmp_path, *names):
    paths = {}
    for name in names:
        path = tmp_path / name
        path.write_text("fixture", encoding="utf-8")
        paths[name] = path
    return paths


def _payload(tmp_path, *, output="von_mises", mode="batch"):
    return {
        "schema_version": 1,
        "mode": mode,
        "inputs": {
            "modal_coordinates": "inputs/response.mcf",
            "modal_stress": "inputs/stress.csv",
        },
        "outputs": [output],
        "settings": {},
        "output_directory": "results",
        **({"node_id": 7} if mode == "time_history" else {}),
    }


class _FakeEngine:
    instances = []
    fail_batch = False

    def __init__(self):
        self.config = None
        self.solver = SimpleNamespace(plasticity_warning_messages=[])
        self.__class__.instances.append(self)

    def configure_data(self, modal, stress, deformation, steady, force_moment_data=None):
        self.modal = modal
        self.stress = stress
        self.deformation = deformation
        self.force_moment = force_moment_data

    def create_solver(self, config, progress_callback=None):
        self.config = config
        if progress_callback:
            progress_callback(35)
        return self.solver

    def run_batch_analysis(self, config):
        print("solver batch log")
        if self.fail_batch:
            raise RuntimeError("solver exploded")
        output = Path(config.output_directory)
        if config.calculate_von_mises:
            (output / "max_von_mises_stress.csv").write_text(
                "NodeID,SVM_Max\n7,1.0\n", encoding="utf-8"
            )
            (output / "time_of_max_von_mises_stress.csv").write_text(
                "NodeID,Time_of_SVM_Max\n7,0.2\n", encoding="utf-8"
            )

    def run_single_node_analysis(self, node_id, config):
        print("solver time-history log")
        if config.calculate_deformation:
            values = {
                "Magnitude": np.array([1.0, 2.0, 3.0, 4.0]),
                "X": np.array([0.0, 1.0, 2.0, 3.0]),
                "Y": np.zeros(4),
                "Z": np.zeros(4),
            }
            result_type = "deformation"
        else:
            values = np.array([0.0, 1.0, 2.0, 3.0])
            result_type = "von_mises"
        return AnalysisResult(
            time_values=self.modal.time_values,
            stress_values=values,
            result_type=result_type,
            node_id=node_id,
        )


@pytest.fixture
def fake_runtime(monkeypatch):
    _FakeEngine.instances = []
    _FakeEngine.fail_batch = False
    monkeypatch.setattr(runtime, "AnalysisEngine", _FakeEngine)
    monkeypatch.setattr(runtime, "load_modal_coordinates", lambda _path: (print("loader log"), _modal())[1])
    monkeypatch.setattr(runtime, "load_modal_stress", lambda _path: _stress())
    monkeypatch.setattr(runtime, "load_modal_deformations", lambda _path: _deformation())
    return _FakeEngine


def test_schema_resolves_paths_and_rejects_unknown_fields(tmp_path):
    payload = _payload(tmp_path)
    job = runtime.MarsJob.from_dict(payload, base_directory=tmp_path)

    assert job.inputs["modal_coordinates"] == str((tmp_path / "inputs/response.mcf").resolve())
    assert job.output_directory == str((tmp_path / "results").resolve())

    payload["surprise"] = True
    with pytest.raises(runtime.MarsJobValidationError, match="Unknown job field"):
        runtime.MarsJob.from_dict(payload, base_directory=tmp_path)


def test_schema_rejects_output_that_would_overwrite_an_input(tmp_path):
    payload = _payload(tmp_path)
    payload["inputs"]["modal_stress"] = "results/max_von_mises_stress.csv"

    with pytest.raises(runtime.MarsJobValidationError, match="overwrite an input"):
        runtime.MarsJob.from_dict(payload, base_directory=tmp_path)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda p: p["outputs"].append("force_moment"), "cannot be combined"),
        (lambda p: p["settings"].update(skip_first_modes=-1), "non-negative"),
        (
            lambda p: (p.update(mode="time_history", node_id=7), p["outputs"].__setitem__(0, "damage"), p["settings"].update(fatigue={"A": 1, "m": -3})),
            "non-damage",
        ),
    ],
)
def test_schema_rejects_invalid_output_contracts(tmp_path, change, message):
    payload = _payload(tmp_path)
    change(payload)
    with pytest.raises(runtime.MarsJobValidationError, match=message):
        runtime.MarsJob.from_dict(payload, base_directory=tmp_path)


def test_batch_run_streams_logs_progress_and_persists_atomic_result(tmp_path, monkeypatch, fake_runtime):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    _files(inputs, "response.mcf", "stress.csv")
    job = runtime.MarsJob.from_dict(_payload(tmp_path), base_directory=tmp_path)
    events = []

    result = runtime.run_job(job, events.append)

    assert result.status == "completed"
    assert [Path(value).name for value in result.files] == [
        "max_von_mises_stress.csv",
        "time_of_max_von_mises_stress.csv",
    ]
    assert Path(result.primary_files["von_mises"]).name == "max_von_mises_stress.csv"
    assert any(event.kind == "progress" and event.percent == 35 for event in events)
    assert any(event.kind == "log" and event.message == "loader log" for event in events)
    assert any(event.kind == "log" and event.message == "solver batch log" for event in events)
    persisted = json.loads((tmp_path / "results/mars_result.json").read_text(encoding="utf-8"))
    assert persisted["status"] == "completed"
    assert Path(persisted["primary_files"]["von_mises"]).name == "max_von_mises_stress.csv"
    assert len(_FakeEngine.instances) == 1
    assert not list((tmp_path / "results").glob(".mars_result.*.tmp"))


def test_each_run_uses_a_fresh_engine(tmp_path, fake_runtime):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    _files(inputs, "response.mcf", "stress.csv")
    job = runtime.MarsJob.from_dict(_payload(tmp_path), base_directory=tmp_path)

    results = tmp_path / "results"
    results.mkdir()
    (results / "max_von_mises_stress.csv").write_text("stale", encoding="utf-8")
    (results / "unrelated.txt").write_text("keep me", encoding="utf-8")
    (results / "mars_result.json").write_text(
        '{"status":"stale"}', encoding="utf-8"
    )

    assert runtime.run_job(job).status == "completed"
    assert runtime.run_job(job).status == "completed"
    assert len(_FakeEngine.instances) == 2
    assert (results / "max_von_mises_stress.csv").read_text(encoding="utf-8").startswith(
        "NodeID,SVM_Max"
    )
    assert (results / "unrelated.txt").read_text(encoding="utf-8") == "keep me"
    persisted = json.loads((results / "mars_result.json").read_text(encoding="utf-8"))
    assert persisted["status"] == "completed"


def test_real_deformation_job_runs_through_loaders_and_solver(tmp_path):
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
    payload = _payload(tmp_path, output="deformation")
    payload["inputs"] = {
        "modal_coordinates": "inputs/response.mcf",
        "modal_deformation": "inputs/deformation.csv",
    }

    result = runtime.run_job(runtime.MarsJob.from_dict(payload, base_directory=tmp_path))

    assert result.status == "completed", result.error
    assert len(result.files) == 16
    assert Path(result.primary_files["deformation"]).name == "max_deformation.csv"
    assert (tmp_path / "results/max_deformation.csv").is_file()


def test_time_history_writes_physical_time_and_vector_columns(tmp_path, fake_runtime):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    _files(inputs, "response.mcf", "deformation.csv")
    payload = _payload(tmp_path, output="deformation", mode="time_history")
    payload["inputs"] = {
        "modal_coordinates": "inputs/response.mcf",
        "modal_deformation": "inputs/deformation.csv",
    }
    job = runtime.MarsJob.from_dict(payload, base_directory=tmp_path)

    result = runtime.run_job(job)

    assert result.status == "completed"
    path = tmp_path / "results/time_history_node_7_deformation.csv"
    assert Path(result.primary_files["history_csv"]).name == path.name
    rows = path.read_text(encoding="utf-8").splitlines()
    assert rows[0] == "Time,Magnitude,X,Y,Z"
    assert rows[1].startswith("0.0,1.0,0.0")


def test_rst_load_options_are_inferred_from_selected_outputs(tmp_path, monkeypatch, fake_runtime):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    _files(inputs, "response.mcf", "modal.rst")
    payload = _payload(tmp_path)
    payload["inputs"] = {
        "modal_coordinates": "inputs/response.mcf",
        "modal_rst": {"path": "inputs/modal.rst", "scope_name": "HOT", "shell_layer": "bottom"},
    }
    captured = {}

    def fake_rst(path, options):
        captured.update(path=path, options=options)
        return SimpleNamespace(
            stress_data=_stress(),
            deformation_data=None,
            force_moment_data=None,
            warnings=("extra mode ignored",),
        )

    monkeypatch.setattr(runtime, "load_modal_rst", fake_rst)
    job = runtime.MarsJob.from_dict(payload, base_directory=tmp_path)

    result = runtime.run_job(job)

    assert result.status == "completed"
    assert captured["options"].expected_modes == 2
    assert captured["options"].scope_name == "HOT"
    assert captured["options"].load_stress is True
    assert captured["options"].load_deformation is False
    assert captured["options"].shell_layer == "bottom"
    assert result.warnings == ("extra mode ignored",)


def test_prepared_family_and_rst_missing_family_can_be_combined(
    tmp_path, monkeypatch, fake_runtime
):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    _files(inputs, "response.mcf", "stress.csv", "modal.rst")
    payload = _payload(tmp_path)
    payload["inputs"]["modal_rst"] = {"path": "inputs/modal.rst"}
    payload["outputs"].append("deformation")
    captured = {}

    def fake_rst(_path, options):
        captured["options"] = options
        return SimpleNamespace(
            stress_data=None,
            deformation_data=_deformation(),
            force_moment_data=None,
            warnings=(),
        )

    monkeypatch.setattr(runtime, "load_modal_rst", fake_rst)
    monkeypatch.setattr(runtime, "_require_batch_outputs", lambda *_args: ())
    job = runtime.MarsJob.from_dict(payload, base_directory=tmp_path)

    result = runtime.run_job(job)

    assert result.status == "completed"
    assert captured["options"].load_stress is False
    assert captured["options"].load_deformation is True


def test_json_cli_stdout_contains_only_jsonl_records(tmp_path, monkeypatch, fake_runtime, capsys):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    _files(inputs, "response.mcf", "stress.csv")
    job_path = tmp_path / "job.json"
    job_path.write_text(json.dumps(_payload(tmp_path)), encoding="utf-8")

    exit_code = runtime.cli_main(["run", str(job_path), "--format", "json"])
    captured = capsys.readouterr()
    records = [json.loads(line) for line in captured.out.splitlines()]

    assert exit_code == 0
    assert captured.err == ""
    assert records[-1]["record"] == "result"
    assert records[-1]["result"]["status"] == "completed"
    log_messages = [
        item["event"].get("message")
        for item in records
        if item["record"] == "event" and item["event"]["kind"] == "log"
    ]
    assert "loader log" in log_messages
    assert "solver batch log" in log_messages


def test_cli_output_override_preserves_job_relative_inputs(tmp_path, fake_runtime, capsys):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    _files(inputs, "response.mcf", "stress.csv")
    job_path = tmp_path / "job.json"
    job_path.write_text(json.dumps(_payload(tmp_path)), encoding="utf-8")
    override = tmp_path / "sandbox" / "results"

    exit_code = runtime.cli_main(
        [
            "run",
            str(job_path),
            "--format",
            "json",
            "--output-directory",
            str(override),
        ]
    )
    record = json.loads(capsys.readouterr().out.splitlines()[-1])

    assert exit_code == 0
    assert Path(record["result"]["output_directory"]) == override.resolve()
    assert (override / "max_von_mises_stress.csv").is_file()
    assert not (tmp_path / "results").exists()


def test_cli_exit_codes_distinguish_validation_and_solver_failure(tmp_path, fake_runtime, capsys):
    missing = tmp_path / "missing.json"
    assert runtime.cli_main(["run", str(missing), "--format", "json"]) == 2
    validation_record = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert validation_record["result"]["error_kind"] == "validation"

    inputs = tmp_path / "inputs"
    inputs.mkdir()
    _files(inputs, "response.mcf", "stress.csv")
    job_path = tmp_path / "job.json"
    job_path.write_text(json.dumps(_payload(tmp_path)), encoding="utf-8")
    _FakeEngine.fail_batch = True

    assert runtime.cli_main(["run", str(job_path), "--format", "json"]) == 1
    failure_record = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert failure_record["result"]["error_kind"] == "runtime"
    assert "solver exploded" in failure_record["result"]["error"]
