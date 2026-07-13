"""Qt-free JSON job runtime and command-line interface for MARS."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import sys
import tempfile
import time
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

import numpy as np

from . import __version__

from .core.computation import AnalysisEngine
from .core.data_models import (
    AnalysisResult,
    PlasticityConfig,
    SolverConfig,
    validate_modal_input_contracts,
)
from .file_io.loaders import (
    load_element_nodal_forces_moments,
    load_material_profile,
    load_modal_coordinates,
    load_modal_coordinates_pch,
    load_modal_deformations,
    load_modal_stress,
    load_steady_state_stress,
    load_temperature_field,
)
from .file_io.rst_service import ALL_SCOPE, RstLoadOptions, load_modal_rst


SCHEMA_VERSION = 1
MODES = {"batch", "time_history"}
OUTPUTS = {
    "von_mises",
    "max_principal",
    "min_principal",
    "deformation",
    "velocity",
    "acceleration",
    "force_moment",
    "damage",
}
STRESS_OUTPUTS = {"von_mises", "max_principal", "min_principal", "damage"}
KINEMATIC_OUTPUTS = {"deformation", "velocity", "acceleration"}
INPUT_KEYS = {
    "modal_coordinates",
    "modal_stress",
    "modal_deformation",
    "modal_force_moment",
    "steady_state_stress",
    "temperature_field",
    "material_profile",
    "modal_rst",
}
SETTING_KEYS = {
    "skip_first_modes",
    "skip_last_modes",
    "include_steady_state",
    "fatigue",
    "plasticity",
}
TOP_LEVEL_KEYS = {
    "schema_version",
    "mode",
    "inputs",
    "outputs",
    "settings",
    "output_directory",
    "node_id",
}
FATIGUE_KEYS = {"A", "m"}
PLASTICITY_KEYS = {
    "enabled",
    "method",
    "max_iterations",
    "tolerance",
    "default_temperature",
    "temperature_column",
    "poisson_ratio",
    "extrapolation_mode",
}
RST_KEYS = {"path", "scope_name", "shell_layer"}


class MarsJobValidationError(ValueError):
    """Raised when a job or one of its inputs is invalid."""


class MarsCliError(ValueError):
    """Raised for command-line parsing errors."""


@dataclass(frozen=True)
class MarsEvent:
    """One structured runtime event."""

    kind: str
    message: Optional[str] = None
    percent: Optional[int] = None
    level: Optional[str] = None
    data: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"kind": self.kind}
        if self.message is not None:
            payload["message"] = self.message
        if self.percent is not None:
            payload["percent"] = int(self.percent)
        if self.level is not None:
            payload["level"] = self.level
        if self.data:
            payload["data"] = dict(self.data)
        return payload


@dataclass(frozen=True)
class MarsRunResult:
    """Terminal result returned by :func:`run_job`."""

    status: str
    output_directory: str
    files: tuple[str, ...] = ()
    primary_files: Mapping[str, str] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    elapsed_seconds: float = 0.0
    error: Optional[str] = None
    error_kind: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status,
            "output_directory": self.output_directory,
            "files": list(self.files),
            "primary_files": dict(self.primary_files),
            "warnings": list(self.warnings),
            "elapsed_seconds": round(float(self.elapsed_seconds), 6),
        }
        if self.error is not None:
            payload["error"] = self.error
        if self.error_kind is not None:
            payload["error_kind"] = self.error_kind
        return payload


@dataclass(frozen=True)
class MarsJob:
    """Validated schema-v1 MARS job with absolute paths."""

    schema_version: int
    mode: str
    inputs: Mapping[str, Any]
    outputs: tuple[str, ...]
    settings: Mapping[str, Any]
    output_directory: str
    node_id: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "mode": self.mode,
            "inputs": dict(self.inputs),
            "outputs": list(self.outputs),
            "settings": dict(self.settings),
            "output_directory": self.output_directory,
        }
        if self.node_id is not None:
            payload["node_id"] = self.node_id
        return payload

    @classmethod
    def from_file(
        cls,
        filename: str | os.PathLike[str],
        *,
        output_directory: str | os.PathLike[str] | None = None,
    ) -> "MarsJob":
        path = Path(filename).expanduser().resolve()
        if not path.is_file():
            raise MarsJobValidationError(f"Job file does not exist: {path}")
        try:
            with path.open("r", encoding="utf-8-sig") as stream:
                payload = json.load(stream)
        except json.JSONDecodeError as exc:
            raise MarsJobValidationError(
                f"Invalid JSON in job file {path}: {exc.msg} (line {exc.lineno}, column {exc.colno})"
            ) from exc
        except OSError as exc:
            raise MarsJobValidationError(f"Unable to read job file {path}: {exc}") from exc
        if output_directory is not None:
            if not isinstance(payload, Mapping):
                raise MarsJobValidationError("Job JSON must be an object.")
            payload = dict(payload)
            payload["output_directory"] = str(Path(output_directory).expanduser().resolve())
        return cls.from_dict(payload, base_directory=path.parent)

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
        *,
        base_directory: str | os.PathLike[str] | None = None,
    ) -> "MarsJob":
        if not isinstance(payload, Mapping):
            raise MarsJobValidationError("Job JSON must be an object.")
        _reject_unknown(payload, TOP_LEVEL_KEYS, "job")

        version = payload.get("schema_version")
        if version != SCHEMA_VERSION or isinstance(version, bool):
            raise MarsJobValidationError(
                f"schema_version must be {SCHEMA_VERSION}."
            )

        mode = payload.get("mode")
        if mode not in MODES:
            raise MarsJobValidationError("mode must be 'batch' or 'time_history'.")

        raw_inputs = payload.get("inputs")
        if not isinstance(raw_inputs, Mapping):
            raise MarsJobValidationError("inputs must be an object.")
        _reject_unknown(raw_inputs, INPUT_KEYS, "inputs")
        if "modal_coordinates" not in raw_inputs:
            raise MarsJobValidationError("inputs.modal_coordinates is required.")

        raw_outputs = payload.get("outputs")
        if not isinstance(raw_outputs, list) or not raw_outputs:
            raise MarsJobValidationError("outputs must be a non-empty list.")
        if not all(isinstance(value, str) and value for value in raw_outputs):
            raise MarsJobValidationError("Every output must be a non-empty string.")
        unknown_outputs = sorted(set(raw_outputs) - OUTPUTS)
        if unknown_outputs:
            raise MarsJobValidationError(
                "Unsupported output(s): " + ", ".join(unknown_outputs)
            )
        if len(set(raw_outputs)) != len(raw_outputs):
            raise MarsJobValidationError("outputs must not contain duplicates.")

        raw_settings = payload.get("settings", {})
        if not isinstance(raw_settings, Mapping):
            raise MarsJobValidationError("settings must be an object.")
        _reject_unknown(raw_settings, SETTING_KEYS, "settings")

        output_directory = _non_empty_string(
            payload.get("output_directory"), "output_directory"
        )
        base = Path(base_directory or Path.cwd()).expanduser().resolve()
        inputs = _resolve_inputs(raw_inputs, base)
        output_path = _resolve_path(output_directory, base)

        settings = _validate_settings(raw_settings, inputs, tuple(raw_outputs), mode)
        node_id = payload.get("node_id")
        if mode == "time_history":
            if not _is_int(node_id):
                raise MarsJobValidationError(
                    "node_id must be an integer in time_history mode."
                )
            if len(raw_outputs) != 1 or raw_outputs[0] == "damage":
                raise MarsJobValidationError(
                    "time_history mode requires exactly one non-damage output."
                )
        elif node_id is not None:
            raise MarsJobValidationError("node_id is only valid in time_history mode.")

        _validate_output_contract(tuple(raw_outputs), settings, mode)
        _validate_input_sources(inputs, tuple(raw_outputs), settings)
        job = cls(
            schema_version=SCHEMA_VERSION,
            mode=mode,
            inputs=inputs,
            outputs=tuple(raw_outputs),
            settings=settings,
            output_directory=str(output_path),
            node_id=int(node_id) if node_id is not None else None,
        )
        _validate_target_paths(job)
        return job


def _reject_unknown(mapping: Mapping[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        raise MarsJobValidationError(
            f"Unknown {label} field(s): " + ", ".join(unknown)
        )


def _non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MarsJobValidationError(f"{label} must be a non-empty string.")
    return value.strip()


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _finite_float(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise MarsJobValidationError(f"{label} must be a finite number.")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise MarsJobValidationError(f"{label} must be a finite number.") from exc
    if not math.isfinite(result):
        raise MarsJobValidationError(f"{label} must be a finite number.")
    return result


def _resolve_path(value: str, base: Path) -> Path:
    path = Path(value).expanduser()
    return (base / path).resolve() if not path.is_absolute() else path.resolve()


def _resolve_inputs(raw_inputs: Mapping[str, Any], base: Path) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for key, value in raw_inputs.items():
        if key == "modal_rst":
            if not isinstance(value, Mapping):
                raise MarsJobValidationError("inputs.modal_rst must be an object.")
            _reject_unknown(value, RST_KEYS, "inputs.modal_rst")
            path = _non_empty_string(value.get("path"), "inputs.modal_rst.path")
            scope = value.get("scope_name", ALL_SCOPE)
            if not isinstance(scope, str) or not scope.strip():
                raise MarsJobValidationError(
                    "inputs.modal_rst.scope_name must be a non-empty string."
                )
            shell_layer = value.get("shell_layer", "top")
            if shell_layer not in {"top", "bottom", "mid", None}:
                raise MarsJobValidationError(
                    "inputs.modal_rst.shell_layer must be top, bottom, mid, or null."
                )
            resolved[key] = {
                "path": str(_resolve_path(path, base)),
                "scope_name": scope.strip(),
                "shell_layer": shell_layer,
            }
        else:
            path = _non_empty_string(value, f"inputs.{key}")
            resolved[key] = str(_resolve_path(path, base))
    return resolved


def _validate_settings(
    raw: Mapping[str, Any],
    inputs: Mapping[str, Any],
    outputs: tuple[str, ...],
    mode: str,
) -> dict[str, Any]:
    skip_first = raw.get("skip_first_modes", 0)
    skip_last = raw.get("skip_last_modes", 0)
    if not _is_int(skip_first) or skip_first < 0:
        raise MarsJobValidationError("settings.skip_first_modes must be a non-negative integer.")
    if not _is_int(skip_last) or skip_last < 0:
        raise MarsJobValidationError("settings.skip_last_modes must be a non-negative integer.")

    include_steady = raw.get(
        "include_steady_state", "steady_state_stress" in inputs
    )
    if not isinstance(include_steady, bool):
        raise MarsJobValidationError("settings.include_steady_state must be a boolean.")

    settings: dict[str, Any] = {
        "skip_first_modes": skip_first,
        "skip_last_modes": skip_last,
        "include_steady_state": include_steady,
    }

    fatigue = raw.get("fatigue")
    if fatigue is not None:
        if not isinstance(fatigue, Mapping):
            raise MarsJobValidationError("settings.fatigue must be an object.")
        _reject_unknown(fatigue, FATIGUE_KEYS, "settings.fatigue")
        if set(fatigue) != FATIGUE_KEYS:
            raise MarsJobValidationError("settings.fatigue requires both A and m.")
        settings["fatigue"] = {
            "A": _finite_float(fatigue["A"], "settings.fatigue.A"),
            "m": _finite_float(fatigue["m"], "settings.fatigue.m"),
        }
    if "damage" in outputs and "fatigue" not in settings:
        raise MarsJobValidationError("damage output requires settings.fatigue with A and m.")
    if "damage" not in outputs and fatigue is not None:
        raise MarsJobValidationError("settings.fatigue is only valid with damage output.")

    plasticity = raw.get("plasticity")
    if plasticity is not None:
        if not isinstance(plasticity, Mapping):
            raise MarsJobValidationError("settings.plasticity must be an object.")
        _reject_unknown(plasticity, PLASTICITY_KEYS, "settings.plasticity")
        enabled = plasticity.get("enabled", True)
        if not isinstance(enabled, bool):
            raise MarsJobValidationError("settings.plasticity.enabled must be a boolean.")
        method = plasticity.get("method", "neuber")
        if method not in {"neuber", "glinka", "ibg"}:
            raise MarsJobValidationError(
                "settings.plasticity.method must be neuber, glinka, or ibg."
            )
        max_iterations = plasticity.get("max_iterations", 60)
        if not _is_int(max_iterations) or max_iterations <= 0:
            raise MarsJobValidationError(
                "settings.plasticity.max_iterations must be a positive integer."
            )
        tolerance = _finite_float(
            plasticity.get("tolerance", 1e-10), "settings.plasticity.tolerance"
        )
        if tolerance <= 0:
            raise MarsJobValidationError("settings.plasticity.tolerance must be positive.")
        extrapolation = plasticity.get("extrapolation_mode", "linear")
        if extrapolation not in {"linear", "plateau"}:
            raise MarsJobValidationError(
                "settings.plasticity.extrapolation_mode must be linear or plateau."
            )
        default_temperature = plasticity.get("default_temperature")
        if default_temperature is not None:
            default_temperature = _finite_float(
                default_temperature, "settings.plasticity.default_temperature"
            )
        poisson = plasticity.get("poisson_ratio")
        if poisson is not None:
            poisson = _finite_float(poisson, "settings.plasticity.poisson_ratio")
            if not 0 <= poisson < 0.5:
                raise MarsJobValidationError(
                    "settings.plasticity.poisson_ratio must be in [0, 0.5)."
                )
        temperature_column = plasticity.get("temperature_column")
        if temperature_column is not None:
            temperature_column = _non_empty_string(
                temperature_column, "settings.plasticity.temperature_column"
            )
        settings["plasticity"] = {
            "enabled": enabled,
            "method": method,
            "max_iterations": max_iterations,
            "tolerance": tolerance,
            "default_temperature": default_temperature,
            "temperature_column": temperature_column,
            "poisson_ratio": poisson,
            "extrapolation_mode": extrapolation,
        }

    return settings


def _validate_output_contract(
    outputs: tuple[str, ...], settings: Mapping[str, Any], mode: str
) -> None:
    if "force_moment" in outputs and len(outputs) != 1:
        raise MarsJobValidationError(
            "force_moment cannot be combined with other output types."
        )
    include_steady = bool(settings["include_steady_state"])
    if include_steady and not (set(outputs) & STRESS_OUTPUTS):
        raise MarsJobValidationError(
            "Steady-state stress is only valid with a stress-derived output."
        )
    plasticity = settings.get("plasticity")
    if plasticity and plasticity["enabled"]:
        if "von_mises" not in outputs:
            raise MarsJobValidationError(
                "Plasticity correction requires von_mises output."
            )
        if plasticity["method"] == "ibg" and mode != "time_history":
            raise MarsJobValidationError("IBG plasticity requires time_history mode.")


def _validate_input_sources(
    inputs: Mapping[str, Any], outputs: tuple[str, ...], settings: Mapping[str, Any]
) -> None:
    rst_present = "modal_rst" in inputs
    family_sources = {
        "stress": "modal_stress",
        "deformation": "modal_deformation",
        "force_moment": "modal_force_moment",
    }
    for family, prepared_key in family_sources.items():
        if _family_required(family, outputs, settings):
            if prepared_key not in inputs and not rst_present:
                raise MarsJobValidationError(
                    f"The selected outputs require inputs.{prepared_key} or inputs.modal_rst."
                )

    if settings["include_steady_state"] and "steady_state_stress" not in inputs:
        raise MarsJobValidationError(
            "settings.include_steady_state requires inputs.steady_state_stress."
        )
    plasticity = settings.get("plasticity")
    if plasticity and plasticity["enabled"]:
        if "material_profile" not in inputs:
            raise MarsJobValidationError(
                "Plasticity correction requires inputs.material_profile."
            )
        if plasticity["method"] in {"neuber", "glinka"} and "temperature_field" not in inputs:
            raise MarsJobValidationError(
                "Neuber and Glinka plasticity require inputs.temperature_field."
            )


def _family_required(
    family: str, outputs: Sequence[str], settings: Mapping[str, Any]
) -> bool:
    selected = set(outputs)
    if family == "stress":
        return bool(selected & STRESS_OUTPUTS) or bool(
            settings.get("plasticity", {}).get("enabled", False)
        )
    if family == "deformation":
        return bool(selected & KINEMATIC_OUTPUTS)
    return "force_moment" in selected


class _EventLogStream(io.TextIOBase):
    def __init__(self, emit: Callable[[MarsEvent], None], fallback: io.TextIOBase):
        self._emit = emit
        self._fallback = fallback
        self._buffer = ""
        self._emitting = False

    def writable(self) -> bool:
        return True

    def write(self, value: str) -> int:
        if self._emitting:
            self._fallback.write(value)
            return len(value)
        self._buffer += value.replace("\r", "\n")
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self._emit_line(line)
        return len(value)

    def flush(self) -> None:
        if self._buffer:
            line, self._buffer = self._buffer, ""
            self._emit_line(line)

    def _emit_line(self, line: str) -> None:
        line = line.strip()
        if not line:
            return
        self._emitting = True
        try:
            self._emit(MarsEvent(kind="log", message=line, level="info"))
        finally:
            self._emitting = False


def _coerce_job(job: str | os.PathLike[str] | MarsJob) -> MarsJob:
    if isinstance(job, MarsJob):
        return MarsJob.from_dict(job.to_dict(), base_directory=Path.cwd())
    return MarsJob.from_file(job)


def run_job(
    job_path_or_mars_job: str | os.PathLike[str] | MarsJob,
    on_event: Optional[Callable[[MarsEvent], None]] = None,
) -> MarsRunResult:
    """Load, validate, and synchronously execute one MARS job."""

    started = time.perf_counter()
    job = _coerce_job(job_path_or_mars_job)
    output_dir = Path(job.output_directory)
    emit = on_event or (lambda _event: None)
    emit(MarsEvent(kind="started", message=f"Starting {job.mode} analysis."))

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        result = _failed_result(job, started, "runtime", f"Unable to create output directory: {exc}")
        emit(MarsEvent(kind="error", message=result.error, level="error"))
        return result

    original_stdout = sys.stdout
    log_stream = _EventLogStream(emit, original_stdout)
    warnings: list[str] = []
    try:
        try:
            with redirect_stdout(log_stream):
                loaded = _load_job_inputs(job, warnings)
                config = _build_solver_config(job, loaded)
                _validate_loaded_inputs(job, loaded)

                engine = AnalysisEngine()
                engine.configure_data(
                    loaded["modal"],
                    loaded.get("stress"),
                    loaded.get("deformation"),
                    loaded.get("steady"),
                    force_moment_data=loaded.get("force_moment"),
                )
                engine.create_solver(
                    config,
                    progress_callback=lambda percent: emit(
                        MarsEvent(
                            kind="progress",
                            percent=max(0, min(100, int(percent))),
                        )
                    ),
                )
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            result = _failed_result(job, started, "validation", str(exc), warnings)
            _try_persist_result(output_dir, result)
            emit(MarsEvent(kind="error", message=result.error, level="error"))
            return result
        finally:
            log_stream.flush()

        try:
            with redirect_stdout(log_stream):
                _remove_target_outputs(job, output_dir)
                if job.mode == "batch":
                    engine.run_batch_analysis(config)
                    files = _require_batch_outputs(job, output_dir)
                else:
                    analysis_result = engine.run_single_node_analysis(job.node_id, config)
                    files = (_write_time_history(job, analysis_result, output_dir),)
                warnings.extend(
                    str(value)
                    for value in getattr(engine.solver, "plasticity_warning_messages", [])
                    if str(value) not in warnings
                )
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            result = _failed_result(job, started, "runtime", str(exc), warnings)
            _try_persist_result(output_dir, result)
            emit(MarsEvent(kind="error", message=result.error, level="error"))
            return result
        finally:
            log_stream.flush()

        result = MarsRunResult(
            status="completed",
            output_directory=str(output_dir.resolve()),
            files=tuple(str(Path(value).resolve()) for value in files),
            primary_files=_primary_files(job, output_dir),
            warnings=tuple(warnings),
            elapsed_seconds=time.perf_counter() - started,
        )
        try:
            _persist_result(output_dir, result)
        except OSError as exc:
            failed = _failed_result(
                job, started, "runtime", f"Unable to write mars_result.json: {exc}", warnings
            )
            emit(MarsEvent(kind="error", message=failed.error, level="error"))
            return failed
        emit(
            MarsEvent(
                kind="completed",
                message="Analysis completed.",
                data={"files": len(result.files)},
            )
        )
        return result
    except KeyboardInterrupt:
        interrupted = MarsRunResult(
            status="interrupted",
            output_directory=str(output_dir.resolve()),
            warnings=tuple(warnings),
            elapsed_seconds=time.perf_counter() - started,
            error="Analysis interrupted.",
            error_kind="interrupted",
        )
        _try_persist_result(output_dir, interrupted)
        emit(MarsEvent(kind="error", message=interrupted.error, level="error"))
        return interrupted


def _load_job_inputs(job: MarsJob, warnings: list[str]) -> dict[str, Any]:
    inputs = job.inputs
    for key, value in inputs.items():
        path = value["path"] if key == "modal_rst" else value
        if not Path(path).is_file():
            raise MarsJobValidationError(f"Input file does not exist: {path}")

    coord_path = str(inputs["modal_coordinates"])
    modal = (
        load_modal_coordinates_pch(coord_path)
        if Path(coord_path).suffix.lower() == ".pch"
        else load_modal_coordinates(coord_path)
    )
    loaded: dict[str, Any] = {"modal": modal}

    if "modal_stress" in inputs:
        loaded["stress"] = load_modal_stress(str(inputs["modal_stress"]))
    if "modal_deformation" in inputs:
        loaded["deformation"] = load_modal_deformations(str(inputs["modal_deformation"]))
    if "modal_force_moment" in inputs:
        loaded["force_moment"] = load_element_nodal_forces_moments(
            str(inputs["modal_force_moment"])
        )
    if "steady_state_stress" in inputs:
        loaded["steady"] = load_steady_state_stress(str(inputs["steady_state_stress"]))
    if "temperature_field" in inputs:
        loaded["temperature"] = load_temperature_field(str(inputs["temperature_field"]))
    if "material_profile" in inputs:
        loaded["material_profile"] = load_material_profile(str(inputs["material_profile"]))

    if "modal_rst" in inputs:
        rst = inputs["modal_rst"]
        load_stress = _family_required("stress", job.outputs, job.settings) and "stress" not in loaded
        load_deformation = _family_required("deformation", job.outputs, job.settings) and "deformation" not in loaded
        load_force = _family_required("force_moment", job.outputs, job.settings) and "force_moment" not in loaded
        if not any((load_stress, load_deformation, load_force)):
            raise MarsJobValidationError(
                "inputs.modal_rst does not supply any selected output family."
            )
        bundle = load_modal_rst(
            rst["path"],
            RstLoadOptions(
                expected_modes=modal.num_modes,
                scope_name=rst["scope_name"],
                load_stress=load_stress,
                load_deformation=load_deformation,
                load_force_moment=load_force,
                shell_layer=rst["shell_layer"] if load_stress else None,
            ),
        )
        if bundle.stress_data is not None:
            loaded["stress"] = bundle.stress_data
        if bundle.deformation_data is not None:
            loaded["deformation"] = bundle.deformation_data
        if bundle.force_moment_data is not None:
            loaded["force_moment"] = bundle.force_moment_data
        warnings.extend(str(value) for value in bundle.warnings)
    return loaded


def _validate_loaded_inputs(job: MarsJob, loaded: Mapping[str, Any]) -> None:
    validate_modal_input_contracts(
        loaded["modal"],
        loaded.get("stress"),
        loaded.get("deformation"),
        loaded.get("force_moment"),
    )
    total_skipped = (
        job.settings["skip_first_modes"] + job.settings["skip_last_modes"]
    )
    if total_skipped >= loaded["modal"].num_modes:
        raise MarsJobValidationError(
            f"Mode skips exclude all {loaded['modal'].num_modes} available modes."
        )

    for family in ("stress", "deformation", "force_moment"):
        if _family_required(family, job.outputs, job.settings) and loaded.get(family) is None:
            raise MarsJobValidationError(
                f"The selected outputs require usable {family.replace('_', '/')} data."
            )

    if set(job.outputs) & {"velocity", "acceleration"}:
        times = np.asarray(loaded["modal"].time_values, dtype=float)
        if times.size < 4:
            raise MarsJobValidationError(
                "Velocity and acceleration require at least four time points."
            )
        steps = np.diff(times)
        if not np.all(np.isfinite(times)) or np.any(steps <= 0):
            raise MarsJobValidationError(
                "Velocity and acceleration require finite, strictly increasing time values."
            )
        if not np.allclose(steps, steps[0], rtol=1e-5, atol=1e-12):
            raise MarsJobValidationError(
                "Velocity and acceleration currently require a uniform time grid."
            )

    if job.mode == "time_history":
        output = job.outputs[0]
        if output == "force_moment":
            owner = loaded["force_moment"]
        elif output in STRESS_OUTPUTS:
            owner = loaded["stress"]
        else:
            owner = loaded["deformation"]
        if int(job.node_id) not in set(np.asarray(owner.node_ids, dtype=int).reshape(-1)):
            raise MarsJobValidationError(
                f"Node ID {job.node_id} was not found in the selected result data."
            )


def _build_solver_config(job: MarsJob, loaded: Mapping[str, Any]) -> SolverConfig:
    outputs = set(job.outputs)
    plasticity = None
    plasticity_settings = job.settings.get("plasticity")
    if plasticity_settings and plasticity_settings["enabled"]:
        plasticity = PlasticityConfig(
            enabled=True,
            method=plasticity_settings["method"],
            max_iterations=plasticity_settings["max_iterations"],
            tolerance=plasticity_settings["tolerance"],
            material_profile=loaded.get("material_profile"),
            temperature_field=loaded.get("temperature"),
            default_temperature=(
                plasticity_settings["default_temperature"]
                if plasticity_settings["default_temperature"] is not None
                else (22.0 if plasticity_settings["method"] == "ibg" else None)
            ),
            temperature_column=plasticity_settings["temperature_column"],
            poisson_ratio=plasticity_settings["poisson_ratio"],
            extrapolation_mode=plasticity_settings["extrapolation_mode"],
        )
    fatigue = job.settings.get("fatigue", {})
    return SolverConfig(
        calculate_von_mises="von_mises" in outputs,
        calculate_max_principal_stress="max_principal" in outputs,
        calculate_min_principal_stress="min_principal" in outputs,
        calculate_deformation="deformation" in outputs,
        calculate_velocity="velocity" in outputs,
        calculate_acceleration="acceleration" in outputs,
        calculate_force_moment="force_moment" in outputs,
        calculate_damage="damage" in outputs,
        fatigue_A=fatigue.get("A"),
        fatigue_m=fatigue.get("m"),
        skip_n_modes=job.settings["skip_first_modes"],
        skip_last_n_modes=job.settings["skip_last_modes"],
        time_history_mode=job.mode == "time_history",
        selected_node_id=job.node_id,
        include_steady_state=job.settings["include_steady_state"],
        output_directory=job.output_directory,
        plasticity=plasticity,
    )


def _batch_output_names(job: MarsJob) -> tuple[str, ...]:
    names: list[str] = []
    scalar_names = {
        "von_mises": (
            "max_von_mises_stress.csv",
            "time_of_max_von_mises_stress.csv",
        ),
        "max_principal": ("max_s1_stress.csv", "time_of_max_s1_stress.csv"),
        "min_principal": ("min_s3_stress.csv", "time_of_min_s3_stress.csv"),
        "damage": ("potential_damage_results.csv",),
    }
    for output in job.outputs:
        names.extend(scalar_names.get(output, ()))
        if output in KINEMATIC_OUTPUTS:
            for base in (output, f"{output}_x", f"{output}_y", f"{output}_z"):
                names.extend(
                    (
                        f"max_{base}.csv",
                        f"time_of_max_{base}.csv",
                        f"min_{base}.csv",
                        f"time_of_min_{base}.csv",
                    )
                )
        elif output == "force_moment":
            for base in (
                "element_nodal_force",
                "element_nodal_moment",
                "element_nodal_force_fx",
                "element_nodal_force_fy",
                "element_nodal_force_fz",
                "element_nodal_force_shear_xy",
                "element_nodal_force_shear_xz",
                "element_nodal_force_shear_yz",
                "element_nodal_moment_mx",
                "element_nodal_moment_my",
                "element_nodal_moment_mz",
            ):
                names.extend(
                    (
                        f"max_{base}.csv",
                        f"time_of_max_{base}.csv",
                        f"min_{base}.csv",
                        f"time_of_min_{base}.csv",
                    )
                )
    plasticity = job.settings.get("plasticity")
    if plasticity and plasticity["enabled"] and plasticity["method"] in {"neuber", "glinka"}:
        names.extend(
            (
                "corrected_von_mises.csv",
                "time_of_max_corrected_von_mises.csv",
                "plastic_strain.csv",
            )
        )
    return tuple(names)


def _primary_files(job: MarsJob, output_dir: Path) -> dict[str, str]:
    if job.mode == "time_history":
        name = f"time_history_node_{job.node_id}_{job.outputs[0]}.csv"
        return {"history_csv": str((output_dir / name).resolve())}

    names = {
        "von_mises": "max_von_mises_stress.csv",
        "max_principal": "max_s1_stress.csv",
        "min_principal": "min_s3_stress.csv",
        "deformation": "max_deformation.csv",
        "velocity": "max_velocity.csv",
        "acceleration": "max_acceleration.csv",
        "damage": "potential_damage_results.csv",
    }
    primary = {
        output: str((output_dir / names[output]).resolve())
        for output in job.outputs
        if output in names
    }
    if "force_moment" in job.outputs:
        primary.update(
            force=str((output_dir / "max_element_nodal_force.csv").resolve()),
            moment=str((output_dir / "max_element_nodal_moment.csv").resolve()),
        )
    return primary


def _validate_target_paths(job: MarsJob) -> None:
    """Prevent automatic result replacement from deleting an input file."""
    input_paths = {
        Path(value["path"] if key == "modal_rst" else value).resolve()
        for key, value in job.inputs.items()
    }
    names = (
        _batch_output_names(job)
        if job.mode == "batch"
        else (f"time_history_node_{job.node_id}_{job.outputs[0]}.csv",)
    )
    collisions = [
        name
        for name in (*names, "mars_result.json")
        if (Path(job.output_directory) / name).resolve() in input_paths
    ]
    if collisions:
        raise MarsJobValidationError(
            "Output file(s) would overwrite an input: " + ", ".join(collisions)
        )


def _require_batch_outputs(job: MarsJob, output_dir: Path) -> tuple[str, ...]:
    paths = tuple(output_dir / name for name in _batch_output_names(job))
    missing = [path.name for path in paths if not path.is_file()]
    if missing:
        raise RuntimeError("Expected result file(s) were not written: " + ", ".join(missing))
    return tuple(str(path) for path in paths)


def _remove_target_outputs(job: MarsJob, output_dir: Path) -> None:
    names = (
        _batch_output_names(job)
        if job.mode == "batch"
        else (f"time_history_node_{job.node_id}_{job.outputs[0]}.csv",)
    )
    for name in (*names, "mars_result.json"):
        path = output_dir / name
        if path.exists():
            path.unlink()


def _write_time_history(job: MarsJob, result: AnalysisResult, output_dir: Path) -> str:
    if result is None or result.time_values is None or result.stress_values is None:
        raise RuntimeError("The solver returned no time-history result.")
    times = np.asarray(result.time_values).reshape(-1)
    values = result.stress_values
    if isinstance(values, Mapping):
        columns = [(str(name), np.asarray(series).reshape(-1)) for name, series in values.items()]
    else:
        columns = [(job.outputs[0], np.asarray(values).reshape(-1))]
    for name, series in columns:
        if series.size != times.size:
            raise RuntimeError(
                f"Time-history column {name!r} has {series.size} rows; expected {times.size}."
            )
    path = output_dir / f"time_history_node_{job.node_id}_{job.outputs[0]}.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Time", *(name for name, _series in columns)])
        writer.writerows(
            [times[index], *(series[index] for _name, series in columns)]
            for index in range(times.size)
        )
    return str(path)


def _failed_result(
    job: MarsJob,
    started: float,
    kind: str,
    error: str,
    warnings: Sequence[str] = (),
) -> MarsRunResult:
    return MarsRunResult(
        status="failed",
        output_directory=str(Path(job.output_directory).resolve()),
        warnings=tuple(warnings),
        elapsed_seconds=time.perf_counter() - started,
        error=error or "Unknown MARS failure.",
        error_kind=kind,
    )


def _persist_result(output_dir: Path, result: MarsRunResult) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "mars_result.json"
    temporary: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=output_dir,
            prefix=".mars_result.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = stream.name
            json.dump(result.to_dict(), stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary:
            try:
                os.remove(temporary)
            except OSError:
                pass


def _try_persist_result(output_dir: Path, result: MarsRunResult) -> None:
    try:
        _persist_result(output_dir, result)
    except OSError:
        pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise MarsCliError(message)


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="MARSBatch", description="Run MARS JSON jobs headlessly.")
    parser.add_argument("--version", action="version", version=f"MARSBatch {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="Run one JSON job.")
    run_parser.add_argument("job", help="Path to a MARS schema-v1 JSON job.")
    run_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text).",
    )
    run_parser.add_argument(
        "--output-directory",
        help="Override the job output directory without changing job-relative input paths.",
    )
    return parser


def _write_json_record(stream: io.TextIOBase, record: str, payload: Mapping[str, Any]) -> None:
    stream.write(json.dumps({"record": record, record: payload}, ensure_ascii=False) + "\n")
    stream.flush()


def _write_text_event(stream: io.TextIOBase, event: MarsEvent) -> None:
    if event.kind == "progress" and event.percent is not None:
        stream.write(f"Progress: {event.percent}%\n")
    elif event.message:
        prefix = "ERROR: " if event.kind == "error" else ""
        stream.write(prefix + event.message + "\n")
    stream.flush()


def _write_text_result(stream: io.TextIOBase, result: MarsRunResult) -> None:
    if result.status == "completed":
        stream.write(f"Completed in {result.elapsed_seconds:.3f} seconds.\n")
        for filename in result.files:
            stream.write(f"  {filename}\n")
        for warning in result.warnings:
            stream.write(f"WARNING: {warning}\n")
    elif result.status == "interrupted":
        stream.write("Analysis interrupted.\n")
    else:
        stream.write(f"Failed: {result.error}\n")
    stream.flush()


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point used by source runs and ``MARSBatch.exe``."""

    try:
        args = _build_parser().parse_args(list(argv) if argv is not None else None)
    except MarsCliError as exc:
        sys.stderr.write(f"MARSBatch: error: {exc}\n")
        return 2

    output = sys.stdout
    json_mode = args.format == "json"

    def on_event(event: MarsEvent) -> None:
        if json_mode:
            _write_json_record(output, "event", event.to_dict())
        else:
            _write_text_event(output, event)

    try:
        job = (
            MarsJob.from_file(args.job, output_directory=args.output_directory)
            if args.output_directory
            else args.job
        )
        result = run_job(job, on_event=on_event)
    except MarsJobValidationError as exc:
        result = MarsRunResult(
            status="failed",
            output_directory="",
            error=str(exc),
            error_kind="validation",
        )
    except KeyboardInterrupt:
        result = MarsRunResult(
            status="interrupted",
            output_directory="",
            error="Analysis interrupted.",
            error_kind="interrupted",
        )

    if json_mode:
        _write_json_record(output, "result", result.to_dict())
    else:
        _write_text_result(output, result)
    if result.status == "completed":
        return 0
    if result.status == "interrupted":
        return 130
    return 2 if result.error_kind == "validation" else 1


def cli_main(argv: Optional[Sequence[str]] = None) -> int:
    """Stable console-script alias used by source and frozen entry points."""

    return main(argv)


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["MarsEvent", "MarsJob", "MarsRunResult", "cli_main", "main", "run_job"]
