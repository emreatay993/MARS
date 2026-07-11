"""Direct modal RST import through PyDPF-Core.

The dependency is imported lazily so every CSV-only MARS workflow remains usable
without Ansys or PyDPF installed.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Mapping, Optional, Sequence

import numpy as np

from core.data_models import DeformationData, ElementNodalForceMomentData, ModalStressData
from utils.constants import NP_DTYPE


PYDPF_VERSION = "0.16.1"
MINIMUM_DPF_SERVER_VERSION = "10.0"  # Ansys 2025 R2; newer servers are accepted.
NMM_UNIT_SYSTEM_ID = 6
BATCH_SIZE = 4
ALL_SCOPE = "All result-support nodes"
SHELL_LAYERS = ("top", "bottom", "mid")
_SHELL_LAYER_IDS = {"top": 0, "bottom": 1, "mid": 3}


class RstImportError(RuntimeError):
    """Raised when an RST cannot provide an unambiguous MARS modal dataset."""


@dataclass(frozen=True)
class RstCapabilities:
    stress: bool
    deformation: bool
    force_moment: bool


@dataclass(frozen=True)
class RstScopeInfo:
    name: str
    source_location: str
    node_count: int
    stress_node_count: int
    deformation_node_count: int
    force_moment_node_count: int


@dataclass(frozen=True)
class ModalRstMetadata:
    path: str
    expected_modes: int
    available_modes: int
    set_ids: tuple[int, ...]
    frequencies_hz: tuple[float, ...]
    capabilities: RstCapabilities
    scopes: tuple[RstScopeInfo, ...]
    shell_layers: tuple[str, ...]
    default_shell_layer: Optional[str]
    warnings: tuple[str, ...]
    capability_errors: Mapping[str, str]
    dpf_version: str
    server_version: str


@dataclass(frozen=True)
class RstLoadOptions:
    expected_modes: int
    scope_name: str = ALL_SCOPE
    load_stress: bool = True
    load_deformation: bool = False
    load_force_moment: bool = False
    shell_layer: Optional[str] = "top"


@dataclass(frozen=True)
class ModalRstBundle:
    stress_data: Optional[ModalStressData]
    deformation_data: Optional[DeformationData]
    force_moment_data: Optional[ElementNodalForceMomentData]
    set_ids: tuple[int, ...]
    frequencies_hz: tuple[float, ...]
    scope_name: str
    shell_layer: Optional[str]
    units: Mapping[str, str]
    warnings: tuple[str, ...]


@dataclass
class _Session:
    dpf: Any
    server: Any
    data_sources: Any
    streams: Any
    model: Any


@dataclass(frozen=True)
class _ModalMatrix:
    node_ids: np.ndarray
    values: np.ndarray  # node, mode, component


class _Accumulator:
    """Preallocate from the first mode and retain only nodes present in every mode."""

    def __init__(self, mode_count: int, component_count: int):
        self.mode_count = mode_count
        self.component_count = component_count
        self.node_ids: Optional[np.ndarray] = None
        self.values: Optional[np.ndarray] = None
        self.valid: Optional[np.ndarray] = None

    def add(self, mode_index: int, node_ids: np.ndarray, data: np.ndarray) -> None:
        order = np.argsort(node_ids, kind="stable")
        ids = np.asarray(node_ids[order], dtype=np.int64)
        rows = np.asarray(data[order], dtype=NP_DTYPE)
        if len(ids) != len(np.unique(ids)):
            raise RstImportError("DPF returned duplicate NodeIDs in one modal field.")

        if self.node_ids is None:
            self.node_ids = ids
            self.values = np.full(
                (len(ids), self.mode_count, self.component_count), np.nan, dtype=NP_DTYPE
            )
            self.valid = np.ones(len(ids), dtype=bool)

        assert self.node_ids is not None and self.values is not None and self.valid is not None
        positions = np.searchsorted(ids, self.node_ids)
        present = positions < len(ids)
        present[present] &= ids[positions[present]] == self.node_ids[present]
        self.valid &= present
        target_rows = np.flatnonzero(present)
        self.values[target_rows, mode_index, :] = rows[positions[present], :]

    def finish(self) -> _ModalMatrix:
        if self.node_ids is None or self.values is None or self.valid is None:
            raise RstImportError("The requested RST result contains no modal fields.")
        if not np.any(self.valid):
            raise RstImportError("No result NodeID is present in every imported modal set.")
        values = self.values[self.valid]
        if not np.isfinite(values).all():
            raise RstImportError("The requested RST result contains missing or non-finite values.")
        return _ModalMatrix(self.node_ids[self.valid], values)


def _import_dpf() -> Any:
    try:
        import ansys.dpf.core as dpf
    except ImportError as exc:
        if getattr(sys, "frozen", False):
            message = (
                f"This MARS package is missing its bundled ansys-dpf-core=={PYDPF_VERSION} "
                "client. Reinstall or rebuild MARS."
            )
        else:
            message = (
                f"Source runs require ansys-dpf-core=={PYDPF_VERSION}; "
                "install the project requirements."
            )
        raise RstImportError(message) from exc
    version = str(getattr(dpf, "__version__", ""))
    if version != PYDPF_VERSION:
        raise RstImportError(
            f"MARS requires its ansys-dpf-core client at version {PYDPF_VERSION}; "
            f"found {version or 'unknown'}."
        )
    return dpf


def _server_is_supported(server: Any) -> bool:
    try:
        return bool(server.meet_version(MINIMUM_DPF_SERVER_VERSION))
    except Exception:
        try:
            major, minor = (int(part) for part in str(server.version).split(".")[:2])
            return (major, minor) >= (10, 0)
        except Exception:
            return False


@contextmanager
def _open_rst(path: str | Path):
    rst_path = Path(path).expanduser().resolve()
    if not rst_path.is_file():
        raise FileNotFoundError(f"RST file does not exist: {rst_path}")
    if rst_path.suffix.lower() != ".rst":
        raise RstImportError(f"Expected an Ansys .rst file, got: {rst_path.name}")

    dpf = _import_dpf()
    server = streams = None
    try:
        # Let PyDPF discover the compatible local Ansys runtime. as_global=False
        # prevents this worker-owned session from replacing another DPF session.
        server = dpf.start_local_server(
            as_global=False,
            use_docker_by_default=False,
            use_pypim_by_default=False,
            timeout=60.0,
        )
        if not _server_is_supported(server):
            raise RstImportError(
                "Direct RST loading requires an Ansys 2025 R2 or newer DPF server; "
                f"found {getattr(server, 'version', 'unknown')}."
            )
        data_sources = dpf.DataSources(str(rst_path), server=server)
        streams = dpf.operators.metadata.streams_provider(
            data_sources=data_sources, server=server
        ).outputs.streams_container()
        model = dpf.Model(data_sources, server=server)
        yield _Session(dpf, server, data_sources, streams, model)
    finally:
        if streams is not None:
            try:
                streams.release_handles()
            except Exception:
                pass
        if server is not None:
            try:
                server.shutdown()
            except Exception:
                pass


def _file_metadata(session: _Session, expected_modes: int) -> tuple[list[int], list[float], int]:
    if expected_modes <= 0:
        raise RstImportError("Modal coordinates must be loaded before the RST import.")
    info = session.model.metadata.result_info
    analysis_type = str(getattr(info, "analysis_type", "")).lower()
    if analysis_type != "modal":
        raise RstImportError(
            f"Expected a modal RST, but DPF reports analysis type {analysis_type or 'unknown'!r}."
        )
    support = session.model.metadata.time_freq_support
    available = int(support.n_sets)
    if available < expected_modes:
        raise RstImportError(
            f"Modal coordinates contain {expected_modes} modes, but the RST contains only {available}."
        )
    frequency_data = np.asarray(support.time_frequencies.data, dtype=float).reshape(-1)
    if len(frequency_data) < available:
        raise RstImportError("DPF returned incomplete modal frequency metadata.")
    # The DPF time-frequency field is scoped by load step, not cumulative set
    # ID. Result operators address the stored cumulative sets as 1..n_sets.
    return list(range(1, expected_modes + 1)), frequency_data[:expected_modes].tolist(), available


def _time_scoping(session: _Session, set_ids: Sequence[int]) -> Any:
    factory = getattr(session.dpf, "time_freq_scoping_factory", None)
    if factory is not None and hasattr(factory, "scoping_by_sets"):
        return factory.scoping_by_sets(list(set_ids), server=session.server)
    return session.dpf.Scoping(
        ids=list(set_ids), location=session.dpf.locations.time_freq, server=session.server
    )


def _operator_kwargs(session: _Session, set_ids: Sequence[int], mesh_scoping: Any) -> dict[str, Any]:
    kwargs = {
        "time_scoping": _time_scoping(session, set_ids),
        "streams_container": session.streams,
        "data_sources": session.data_sources,
        "bool_rotate_to_global": True,
        "server": session.server,
    }
    if mesh_scoping is not None:
        kwargs["mesh_scoping"] = mesh_scoping
    return kwargs


def _stress_fc(
    session: _Session,
    set_ids: Sequence[int],
    mesh_scoping: Any = None,
    shell_layer: Optional[str] = None,
    *,
    raw_shells: bool = False,
) -> Any:
    kwargs = _operator_kwargs(session, set_ids, mesh_scoping)
    kwargs.update(
        requested_location=(
            session.dpf.locations.elemental_nodal if raw_shells else session.dpf.locations.nodal
        ),
        split_shells=raw_shells,
        extend_to_mid_nodes=True,
    )
    if shell_layer is not None:
        kwargs["shell_layer"] = _SHELL_LAYER_IDS[shell_layer]
    return session.dpf.operators.result.stress(**kwargs).outputs.fields_container()


def _displacement_fc(session: _Session, set_ids: Sequence[int], mesh_scoping: Any = None) -> Any:
    return session.dpf.operators.result.displacement(
        **_operator_kwargs(session, set_ids, mesh_scoping)
    ).outputs.fields_container()


def _force_moment_fc(session: _Session, set_ids: Sequence[int], mesh_scoping: Any = None) -> Any:
    kwargs = _operator_kwargs(session, set_ids, mesh_scoping)
    kwargs.update(
        requested_location=session.dpf.locations.nodal,
        split_shells=False,
        extend_to_mid_nodes=True,
        split_force_components=True,
    )
    return session.dpf.operators.result.element_nodal_forces(
        **kwargs
    ).outputs.fields_container()


def _single_field(fields_container: Any, labels: Mapping[str, int]) -> Any:
    fields = list(fields_container.get_fields(dict(labels)))
    if len(fields) != 1:
        raise RstImportError(
            f"Expected one DPF field for label space {dict(labels)}, found {len(fields)}."
        )
    return fields[0]


def _force_field(fields_container: Any, set_id: int, dof: int) -> Any:
    """Select a split ENF field across the 0.16.x label spelling."""
    label_names = set(getattr(fields_container, "labels", []) or [])
    dof_label = "dofs" if "dofs" in label_names else "dof"
    return _single_field(
        fields_container,
        {"time": set_id, "derivative_order": 0, dof_label: dof},
    )


def _field_unit(field: Any) -> str:
    return str(getattr(field, "unit", "") or "").strip()


def _field_arrays(field: Any, component_count: int) -> tuple[np.ndarray, np.ndarray]:
    ids = np.asarray(field.scoping.ids, dtype=np.int64)
    data = np.asarray(field.data, dtype=NP_DTYPE)
    if data.ndim == 1 and component_count == 1:
        data = data.reshape(-1, 1)
    if data.ndim != 2 or data.shape != (len(ids), component_count):
        raise RstImportError(
            f"Expected DPF field shape ({len(ids)}, {component_count}), got {data.shape}."
        )
    if not _field_unit(field):
        raise RstImportError("DPF returned a result field with an unknown unit.")
    return ids, data


def _canonical_unit(unit: str) -> str:
    return (
        unit.lower()
        .replace(" ", "")
        .replace("\u00b7", "*")
        .replace("\u22c5", "*")
    )


def _convert_field(session: _Session, field: Any, expected: str) -> Any:
    if not _field_unit(field):
        raise RstImportError("DPF returned a result field with an unknown unit.")
    converted = session.dpf.operators.math.unit_convert(
        entity_to_convert=field,
        unit_name=NMM_UNIT_SYSTEM_ID,
        server=session.server,
    ).outputs.converted_entity_as_field()
    accepted = {
        "stress": {"mpa"},
        "length": {"mm"},
        "force": {"n"},
        "moment": {"mj", "n*mm", "n.mm", "nmm"},
    }[expected]
    if _canonical_unit(_field_unit(converted)) not in accepted:
        raise RstImportError(
            f"Could not normalize {_field_unit(field)!r} to the MARS {expected} unit."
        )
    return converted


def _field_ids(field: Any, component_count: int) -> set[int]:
    ids, _ = _field_arrays(field, component_count)
    return set(int(value) for value in ids)


def _batch_ids(set_ids: Sequence[int]):
    for start in range(0, len(set_ids), BATCH_SIZE):
        yield set_ids[start : start + BATCH_SIZE]


def _scan_support(
    session: _Session,
    result_kind: str,
    set_ids: Sequence[int],
    mesh_scoping: Any = None,
    shell_layer: Optional[str] = None,
) -> set[int]:
    stable: Optional[set[int]] = None
    for batch in _batch_ids(set_ids):
        if result_kind == "stress":
            fc = _stress_fc(session, batch, mesh_scoping, shell_layer)
        elif result_kind == "deformation":
            fc = _displacement_fc(session, batch, mesh_scoping)
        else:
            fc = _force_moment_fc(session, batch, mesh_scoping)
        for set_id in batch:
            if result_kind == "force_moment":
                force = _force_field(fc, set_id, 0)
                moment = _force_field(fc, set_id, 1)
                current = _field_ids(force, 3) & _field_ids(moment, 3)
            else:
                field = _single_field(fc, {"time": set_id})
                current = _field_ids(field, 6 if result_kind == "stress" else 3)
            stable = current if stable is None else stable & current
    return stable or set()


def _detect_shell_layers(session: _Session, first_set_id: int) -> tuple[str, ...]:
    fc = _stress_fc(session, [first_set_id], raw_shells=True)
    layers: set[str] = set()
    for field in fc.get_fields({"time": first_set_id}):
        layer = getattr(field, "shell_layers", None)
        name = str(getattr(layer, "name", layer) or "").lower().replace("_", "")
        if name.endswith("topbottommid"):
            layers.update(SHELL_LAYERS)
        elif name.endswith("topbottom"):
            layers.update(("top", "bottom"))
        elif name.endswith("top"):
            layers.add("top")
        elif name.endswith("bottom"):
            layers.add("bottom")
        elif name.endswith("mid"):
            layers.add("mid")
    return tuple(layer for layer in SHELL_LAYERS if layer in layers)


def _named_scope(session: _Session, name: str) -> Any:
    available = [
        str(value)
        for value in list(getattr(session.model.metadata, "available_named_selections", []) or [])
    ]
    match = next((value for value in available if value.casefold() == name.casefold()), None)
    if match is None:
        raise RstImportError(
            f"Named selection {name!r} was not found. Available: {', '.join(available)}"
        )
    return session.model.metadata.named_selection(match)


def _scope_node_ids(session: _Session, scope: Any) -> set[int]:
    location = str(getattr(scope, "location", "") or "")
    if "nodal" in location.lower():
        return set(int(value) for value in scope.ids)
    transposed = session.dpf.operators.scoping.transpose(
        mesh_scoping=scope,
        meshed_region=session.model.metadata.meshed_region,
        requested_location=session.dpf.locations.nodal,
        server=session.server,
    ).outputs.mesh_scoping_as_scoping()
    return set(int(value) for value in transposed.ids)


def inspect_modal_rst(path: str | Path, expected_modes: int) -> ModalRstMetadata:
    """Inspect modal sets and result support without returning live DPF objects."""

    warnings: list[str] = []
    errors: dict[str, str] = {}
    with _open_rst(path) as session:
        set_ids, frequencies, available = _file_metadata(session, expected_modes)
        if available > expected_modes:
            warnings.append(
                f"The RST contains {available} modes; only the first {expected_modes} are mapped."
            )

        try:
            shell_layers = _detect_shell_layers(session, set_ids[0])
        except Exception as exc:
            shell_layers = ()
            warnings.append(f"Shell-layer metadata could not be inspected: {exc}")
        default_layer = "top" if "top" in shell_layers else (shell_layers[0] if shell_layers else None)

        supports: dict[str, set[int]] = {}
        for kind in ("stress", "deformation", "force_moment"):
            try:
                supports[kind] = _scan_support(
                    session,
                    kind,
                    set_ids,
                    shell_layer=default_layer if kind == "stress" else None,
                )
                if not supports[kind]:
                    raise RstImportError("no NodeID is supported in every imported mode")
            except Exception as exc:
                supports[kind] = set()
                errors[kind] = str(exc)

        capabilities = RstCapabilities(
            stress=bool(supports["stress"]),
            deformation=bool(supports["deformation"]),
            force_moment=bool(supports["force_moment"]),
        )
        if not any((capabilities.stress, capabilities.deformation, capabilities.force_moment)):
            raise RstImportError("The RST contains no modal result supported by MARS.")

        union_support = set().union(*supports.values())
        scopes = [
            RstScopeInfo(
                name=ALL_SCOPE,
                source_location="Nodal",
                node_count=len(union_support),
                stress_node_count=len(supports["stress"]),
                deformation_node_count=len(supports["deformation"]),
                force_moment_node_count=len(supports["force_moment"]),
            )
        ]
        names = sorted(
            (
                str(value)
                for value in list(
                    getattr(session.model.metadata, "available_named_selections", []) or []
                )
            ),
            key=str.casefold,
        )
        for name in names:
            try:
                scope = _named_scope(session, name)
                nodes = _scope_node_ids(session, scope)
            except Exception as exc:
                warnings.append(f"Named selection {name!r} was ignored: {exc}")
                continue
            counts = {}
            for kind, global_support in supports.items():
                if not (nodes & global_support):
                    counts[kind] = 0
                    continue
                try:
                    scoped_support = _scan_support(
                        session,
                        kind,
                        set_ids,
                        mesh_scoping=scope,
                        shell_layer=default_layer if kind == "stress" else None,
                    )
                    counts[kind] = len(nodes & scoped_support)
                except Exception as exc:
                    counts[kind] = 0
                    warnings.append(
                        f"Named selection {name!r} has no usable {kind.replace('_', ' ')} "
                        f"result: {exc}"
                    )
            if not any(counts.values()):
                continue
            scopes.append(
                RstScopeInfo(
                    name=name,
                    source_location=str(getattr(scope, "location", "") or "unknown"),
                    node_count=len(nodes),
                    stress_node_count=counts["stress"],
                    deformation_node_count=counts["deformation"],
                    force_moment_node_count=counts["force_moment"],
                )
            )

        return ModalRstMetadata(
            path=str(Path(path).expanduser().resolve()),
            expected_modes=expected_modes,
            available_modes=available,
            set_ids=tuple(set_ids),
            frequencies_hz=tuple(frequencies),
            capabilities=capabilities,
            scopes=tuple(scopes),
            shell_layers=shell_layers,
            default_shell_layer=default_layer,
            warnings=tuple(warnings),
            capability_errors=errors,
            dpf_version=str(session.dpf.__version__),
            server_version=str(session.server.version),
        )


def _extract_modal_matrix(
    session: _Session,
    result_kind: str,
    set_ids: Sequence[int],
    mesh_scoping: Any,
    shell_layer: Optional[str],
) -> _ModalMatrix:
    component_count = 6 if result_kind in {"stress", "force_moment"} else 3
    accumulator = _Accumulator(len(set_ids), component_count)
    mode_index = {set_id: index for index, set_id in enumerate(set_ids)}
    for batch in _batch_ids(set_ids):
        if result_kind == "stress":
            fc = _stress_fc(session, batch, mesh_scoping, shell_layer)
        elif result_kind == "deformation":
            fc = _displacement_fc(session, batch, mesh_scoping)
        else:
            fc = _force_moment_fc(session, batch, mesh_scoping)
        for set_id in batch:
            if result_kind == "force_moment":
                force = _convert_field(
                    session,
                    _force_field(fc, set_id, 0),
                    "force",
                )
                moment = _convert_field(
                    session,
                    _force_field(fc, set_id, 1),
                    "moment",
                )
                force_ids, force_rows = _field_arrays(force, 3)
                moment_ids, moment_rows = _field_arrays(moment, 3)
                common = np.intersect1d(force_ids, moment_ids, assume_unique=False)
                if not len(common):
                    raise RstImportError(f"Force and moment have no common nodes in set {set_id}.")
                force_order = np.argsort(force_ids)
                moment_order = np.argsort(moment_ids)
                force_rows = force_rows[force_order][np.searchsorted(force_ids[force_order], common)]
                moment_rows = moment_rows[moment_order][np.searchsorted(moment_ids[moment_order], common)]
                accumulator.add(mode_index[set_id], common, np.column_stack((force_rows, moment_rows)))
            else:
                field = _convert_field(
                    session,
                    _single_field(fc, {"time": set_id}),
                    "stress" if result_kind == "stress" else "length",
                )
                ids, rows = _field_arrays(field, component_count)
                accumulator.add(mode_index[set_id], ids, rows)
    return accumulator.finish()


def _restrict(matrix: _ModalMatrix, node_ids: np.ndarray) -> _ModalMatrix:
    positions = np.searchsorted(matrix.node_ids, node_ids)
    if np.any(positions >= len(matrix.node_ids)) or not np.array_equal(
        matrix.node_ids[positions], node_ids
    ):
        raise RstImportError("Internal NodeID alignment failure.")
    return _ModalMatrix(node_ids, matrix.values[positions])


def _coordinates(session: _Session, node_ids: np.ndarray) -> np.ndarray:
    field = session.model.metadata.meshed_region.nodes.coordinates_field
    if hasattr(field, "deep_copy"):
        try:
            field = field.deep_copy(server=session.server)
        except TypeError:
            field = field.deep_copy()
    if not _field_unit(field):
        mesh_unit = str(getattr(session.model.metadata.meshed_region, "unit", "") or "")
        if not mesh_unit:
            raise RstImportError("The RST mesh coordinate unit is unknown.")
        field.unit = mesh_unit
    field = _convert_field(session, field, "length")
    coordinate_ids, rows = _field_arrays(field, 3)
    order = np.argsort(coordinate_ids)
    sorted_ids = coordinate_ids[order]
    positions = np.searchsorted(sorted_ids, node_ids)
    if np.any(positions >= len(sorted_ids)) or not np.array_equal(sorted_ids[positions], node_ids):
        raise RstImportError("Coordinates are missing for one or more imported result nodes.")
    return rows[order][positions]


def load_modal_rst(path: str | Path, options: RstLoadOptions) -> ModalRstBundle:
    """Load selected modal RST results and return existing MARS data models atomically."""

    requested = (options.load_stress, options.load_deformation, options.load_force_moment)
    if not any(requested):
        raise RstImportError("Select at least one RST result to load.")
    if options.load_stress and options.shell_layer not in (*SHELL_LAYERS, None):
        raise RstImportError(f"Unsupported shell layer: {options.shell_layer!r}")

    with _open_rst(path) as session:
        set_ids, frequencies, available = _file_metadata(session, options.expected_modes)
        warnings: list[str] = []
        if available > options.expected_modes:
            warnings.append(
                f"The RST contains {available} modes; only the first {options.expected_modes} are mapped."
            )
        mesh_scoping = None if options.scope_name == ALL_SCOPE else _named_scope(
            session, options.scope_name
        )

        if options.load_stress:
            stored_layers = _detect_shell_layers(session, set_ids[0])
            if stored_layers and options.shell_layer not in stored_layers:
                raise RstImportError(
                    "Select one of the shell stress layers stored in the RST: "
                    + ", ".join(layer.title() for layer in stored_layers)
                )
            if not stored_layers and options.shell_layer is not None:
                raise RstImportError(
                    "A shell stress layer was selected, but this RST has no stored shell layers."
                )

        stress = (
            _extract_modal_matrix(
                session, "stress", set_ids, mesh_scoping, options.shell_layer
            )
            if options.load_stress
            else None
        )
        deformation = (
            _extract_modal_matrix(session, "deformation", set_ids, mesh_scoping, None)
            if options.load_deformation
            else None
        )
        force_moment = (
            _extract_modal_matrix(session, "force_moment", set_ids, mesh_scoping, None)
            if options.load_force_moment
            else None
        )

        if stress is not None and deformation is not None:
            common = np.intersect1d(stress.node_ids, deformation.node_ids, assume_unique=True)
            if not len(common):
                raise RstImportError("Stress and deformation have no common stable NodeIDs.")
            stress = _restrict(stress, common)
            deformation = _restrict(deformation, common)

        matrices = [value for value in (stress, deformation, force_moment) if value is not None]
        all_node_ids = np.unique(np.concatenate([value.node_ids for value in matrices]))
        all_coordinates = _coordinates(session, all_node_ids)

        def coords_for(ids: np.ndarray) -> np.ndarray:
            return all_coordinates[np.searchsorted(all_node_ids, ids)]

        stress_data = None
        if stress is not None:
            stress_data = ModalStressData(
                node_ids=stress.node_ids,
                modal_sx=stress.values[:, :, 0],
                modal_sy=stress.values[:, :, 1],
                modal_sz=stress.values[:, :, 2],
                modal_sxy=stress.values[:, :, 3],
                modal_syz=stress.values[:, :, 4],
                modal_sxz=stress.values[:, :, 5],
                node_coords=coords_for(stress.node_ids),
            )

        deformation_data = None
        if deformation is not None:
            deformation_data = DeformationData(
                node_ids=deformation.node_ids,
                modal_ux=deformation.values[:, :, 0],
                modal_uy=deformation.values[:, :, 1],
                modal_uz=deformation.values[:, :, 2],
                node_coords=coords_for(deformation.node_ids),
            )

        force_moment_data = None
        if force_moment is not None:
            force_moment_data = ElementNodalForceMomentData(
                node_ids=force_moment.node_ids,
                modal_fx=force_moment.values[:, :, 0],
                modal_fy=force_moment.values[:, :, 1],
                modal_fz=force_moment.values[:, :, 2],
                modal_mx=force_moment.values[:, :, 3],
                modal_my=force_moment.values[:, :, 4],
                modal_mz=force_moment.values[:, :, 5],
                node_coords=coords_for(force_moment.node_ids),
            )

        units = {}
        if stress is not None:
            units["stress"] = "MPa"
        if deformation is not None:
            units["deformation"] = "mm"
        if force_moment is not None:
            units.update(force="N", moment="N*mm")
        return ModalRstBundle(
            stress_data=stress_data,
            deformation_data=deformation_data,
            force_moment_data=force_moment_data,
            set_ids=tuple(set_ids),
            frequencies_hz=tuple(frequencies),
            scope_name=options.scope_name,
            shell_layer=options.shell_layer if stress is not None else None,
            units=units,
            warnings=tuple(warnings),
        )
