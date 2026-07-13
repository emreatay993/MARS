"""Focused tests for direct modal RST import."""

import os
import sys
from contextlib import contextmanager
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mars_solver.file_io import rst_service as rst


class Field:
    def __init__(self, ids, data, unit, shell_layer=None):
        self.scoping = SimpleNamespace(ids=list(ids))
        self.data = np.asarray(data, dtype=float)
        self.unit = unit
        self.shell_layers = SimpleNamespace(name=shell_layer) if shell_layer else None


class FieldsContainer:
    def __init__(self, fields):
        self.fields = fields
        self.requests = []
        self.labels = sorted({key for label_space, _field in fields for key in label_space})

    def get_fields(self, labels):
        self.requests.append(dict(labels))
        matches = []
        for label_space, field in self.fields:
            if all(label_space.get(key) == value for key, value in labels.items()):
                matches.append(field)
        return matches


def session(metadata=None, dpf=None):
    return rst._Session(
        dpf=dpf or SimpleNamespace(__version__=rst.PYDPF_VERSION),
        server=SimpleNamespace(version="11.0"),
        data_sources=object(),
        streams=object(),
        model=SimpleNamespace(metadata=metadata or SimpleNamespace()),
    )


def test_accumulator_intersects_modes_and_orders_node_ids():
    accumulator = rst._Accumulator(mode_count=2, component_count=3)
    accumulator.add(0, np.array([3, 1, 2]), np.array([[30, 31, 32], [10, 11, 12], [20, 21, 22]]))
    accumulator.add(1, np.array([4, 3, 2]), np.array([[40, 41, 42], [33, 34, 35], [23, 24, 25]]))

    result = accumulator.finish()

    assert result.node_ids.tolist() == [2, 3]
    assert result.values[:, 0, 0].tolist() == [20, 30]
    assert result.values[:, 1, 0].tolist() == [23, 33]


def test_force_operator_uses_split_output_labels_contract():
    captured = {}
    output_fc = object()

    def element_nodal_forces(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(outputs=SimpleNamespace(fields_container=lambda: output_fc))

    fake_dpf = SimpleNamespace(
        locations=SimpleNamespace(nodal="Nodal", time_freq="TimeFreq"),
        time_freq_scoping_factory=SimpleNamespace(
            scoping_by_sets=lambda ids, server=None: (tuple(ids), server)
        ),
        operators=SimpleNamespace(
            result=SimpleNamespace(element_nodal_forces=element_nodal_forces)
        ),
    )
    current = session(dpf=fake_dpf)

    assert rst._force_moment_fc(current, [1, 2]) is output_fc
    assert captured["requested_location"] == "Nodal"
    assert captured["split_force_components"] is True
    assert captured["split_shells"] is False
    assert "derivative_order" not in captured
    assert "dof" not in captured


def test_force_support_requires_both_output_labels_on_every_mode(monkeypatch):
    fields = []
    supports = {
        (1, 0): [1, 2, 3],
        (1, 1): [2, 3],
        (2, 0): [2, 3],
        (2, 1): [3, 4],
    }
    for (set_id, dof), ids in supports.items():
        fields.append(
            (
                {"time": set_id, "derivative_order": 0, "dofs": dof},
                Field(ids, np.ones((len(ids), 3)), "N" if dof == 0 else "mJ"),
            )
        )
    fc = FieldsContainer(fields)
    monkeypatch.setattr(rst, "_force_moment_fc", lambda *args, **kwargs: fc)

    assert rst._scan_support(session(), "force_moment", [1, 2]) == {3}
    assert {tuple(sorted(request.items())) for request in fc.requests} == {
        (("derivative_order", 0), ("dofs", 0), ("time", 1)),
        (("derivative_order", 0), ("dofs", 1), ("time", 1)),
        (("derivative_order", 0), ("dofs", 0), ("time", 2)),
        (("derivative_order", 0), ("dofs", 1), ("time", 2)),
    }


def test_four_set_batching_is_deterministic():
    assert list(rst._batch_ids([7, 3, 9, 2, 8, 4])) == [[7, 3, 9, 2], [8, 4]]


def test_file_metadata_uses_cumulative_set_order():
    frequencies = SimpleNamespace(
        data=np.array([10.0, 20.0, 30.0]),
        scoping=SimpleNamespace(ids=[1]),
    )
    metadata = SimpleNamespace(
        result_info=SimpleNamespace(analysis_type="modal"),
        time_freq_support=SimpleNamespace(n_sets=3, time_frequencies=frequencies),
    )

    set_ids, values, available = rst._file_metadata(session(metadata=metadata), 2)

    assert set_ids == [1, 2]
    assert values == [10.0, 20.0]
    assert available == 3


def test_shell_layer_discovery_exposes_only_stored_layers(monkeypatch):
    fc = FieldsContainer(
        [
            ({"time": 1, "elshape": 9}, Field([1], [[1] * 6], "MPa", "topbottom")),
            ({"time": 1, "elshape": 10}, Field([2], [[1] * 6], "MPa", "topbottommid")),
            ({"time": 1, "elshape": 2}, Field([3], [[1] * 6], "MPa", "nonelayer")),
        ]
    )
    monkeypatch.setattr(rst, "_stress_fc", lambda *args, **kwargs: fc)

    assert rst._detect_shell_layers(session(), 1) == ("top", "bottom", "mid")


def test_unit_normalization_rejects_unknown_and_checks_target():
    def convert(entity_to_convert, unit_name, server):
        assert unit_name == rst.NMM_UNIT_SYSTEM_ID
        entity_to_convert.unit = "N"
        return SimpleNamespace(
            outputs=SimpleNamespace(converted_entity_as_field=lambda: entity_to_convert)
        )

    fake_dpf = SimpleNamespace(
        operators=SimpleNamespace(math=SimpleNamespace(unit_convert=convert))
    )
    current = session(dpf=fake_dpf)

    assert rst._convert_field(current, Field([1], [[1, 2, 3]], "lbf"), "force").unit == "N"
    with pytest.raises(rst.RstImportError, match="unknown unit"):
        rst._convert_field(current, Field([1], [[1, 2, 3]], ""), "force")


def test_unit_normalization_accepts_real_middle_dot():
    assert rst._canonical_unit("N\u00b7mm") == "n*mm"


def test_inspection_filters_named_selections_by_stable_capability(monkeypatch):
    scopes = {
        "KEEP": SimpleNamespace(location="Nodal", ids=[2, 3, 9]),
        "EMPTY": SimpleNamespace(location="Nodal", ids=[99]),
    }
    metadata = SimpleNamespace(
        available_named_selections=list(scopes),
        named_selection=lambda name: scopes[name],
    )
    current = session(metadata=metadata)

    @contextmanager
    def fake_open(_path):
        yield current

    monkeypatch.setattr(rst, "_open_rst", fake_open)
    monkeypatch.setattr(rst, "_file_metadata", lambda *_: ([1, 2], [10.0, 20.0], 3))
    monkeypatch.setattr(rst, "_detect_shell_layers", lambda *_: ("top", "bottom"))
    support = {
        "stress": {1, 2, 3},
        "deformation": {2, 3, 4},
        "force_moment": set(),
    }
    monkeypatch.setattr(
        rst,
        "_scan_support",
        lambda _session, kind, *_args, mesh_scoping=None, **_kwargs: (
            support[kind]
            if mesh_scoping is None
            else support[kind] & set(mesh_scoping.ids)
        ),
    )

    result = rst.inspect_modal_rst("model.rst", 2)

    assert result.set_ids == (1, 2)
    assert result.frequencies_hz == (10.0, 20.0)
    assert result.capabilities == rst.RstCapabilities(True, True, False)
    assert [scope.name for scope in result.scopes] == [rst.ALL_SCOPE, "KEEP"]
    keep = result.scopes[1]
    assert (keep.stress_node_count, keep.deformation_node_count) == (2, 2)
    assert result.default_shell_layer == "top"
    assert result.warnings == ("The RST contains 3 modes; only the first 2 are mapped.",)


def test_load_returns_aligned_existing_mars_models(monkeypatch):
    current = session()

    @contextmanager
    def fake_open(_path):
        yield current

    stress_values = np.arange(3 * 2 * 6, dtype=float).reshape(3, 2, 6)
    deformation_values = np.arange(3 * 2 * 3, dtype=float).reshape(3, 2, 3)
    force_values = np.arange(1 * 2 * 6, dtype=float).reshape(1, 2, 6)
    matrices = {
        "stress": rst._ModalMatrix(np.array([1, 2, 3]), stress_values),
        "deformation": rst._ModalMatrix(np.array([2, 3, 4]), deformation_values),
        "force_moment": rst._ModalMatrix(np.array([9]), force_values),
    }
    monkeypatch.setattr(rst, "_open_rst", fake_open)
    monkeypatch.setattr(rst, "_file_metadata", lambda *_: ([1, 2], [11.0, 22.0], 2))
    monkeypatch.setattr(rst, "_detect_shell_layers", lambda *_: ("top",))
    monkeypatch.setattr(
        rst,
        "_extract_modal_matrix",
        lambda _session, kind, *_args: matrices[kind],
    )
    monkeypatch.setattr(
        rst,
        "_coordinates",
        lambda _session, ids: np.column_stack((ids, ids + 0.1, ids + 0.2)),
    )

    bundle = rst.load_modal_rst(
        "model.rst",
        rst.RstLoadOptions(
            expected_modes=2,
            load_stress=True,
            load_deformation=True,
            load_force_moment=True,
        ),
    )

    assert bundle.stress_data.node_ids.tolist() == [2, 3]
    assert bundle.deformation_data.node_ids.tolist() == [2, 3]
    assert bundle.force_moment_data.node_ids.tolist() == [9]
    assert bundle.deformation_data.node_coords.shape == (2, 3)
    assert bundle.units == {
        "stress": "MPa",
        "deformation": "mm",
        "force": "N",
        "moment": "N*mm",
    }


def test_load_rejects_shell_layer_not_stored(monkeypatch):
    current = session()

    @contextmanager
    def fake_open(_path):
        yield current

    monkeypatch.setattr(rst, "_open_rst", fake_open)
    monkeypatch.setattr(rst, "_file_metadata", lambda *_: ([1], [10.0], 1))
    monkeypatch.setattr(rst, "_detect_shell_layers", lambda *_: ("top", "bottom"))

    with pytest.raises(rst.RstImportError, match="stored in the RST"):
        rst.load_modal_rst(
            "model.rst",
            rst.RstLoadOptions(expected_modes=1, shell_layer="mid"),
        )


def test_isolated_session_releases_streams_and_server_on_failure(tmp_path, monkeypatch):
    rst_path = tmp_path / "model.rst"
    rst_path.write_bytes(b"rst")
    released = SimpleNamespace(streams=False, server=False)

    class Server:
        version = "11.0"

        def meet_version(self, _minimum):
            return True

        def shutdown(self):
            released.server = True

    class Streams:
        def release_handles(self):
            released.streams = True

    streams = Streams()
    fake_dpf = SimpleNamespace(
        __version__=rst.PYDPF_VERSION,
        start_local_server=lambda **kwargs: Server(),
        DataSources=lambda *args, **kwargs: object(),
        Model=lambda *args, **kwargs: object(),
        operators=SimpleNamespace(
            metadata=SimpleNamespace(
                streams_provider=lambda **kwargs: SimpleNamespace(
                    outputs=SimpleNamespace(streams_container=lambda: streams)
                )
            )
        ),
    )
    monkeypatch.setattr(rst, "_import_dpf", lambda: fake_dpf)

    with pytest.raises(RuntimeError, match="stop"):
        with rst._open_rst(rst_path):
            raise RuntimeError("stop")

    assert released.streams is True
    assert released.server is True
