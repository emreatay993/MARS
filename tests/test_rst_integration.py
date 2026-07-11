"""Environment-gated comparison of direct RST import with trusted CSV exports."""

import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from file_io.loaders import (
    load_element_nodal_forces_moments,
    load_modal_deformations,
    load_modal_stress,
)
from file_io.rst_service import ALL_SCOPE, RstLoadOptions, inspect_modal_rst, load_modal_rst


RST_PATH = os.environ.get("MARS_TEST_MODAL_RST")
pytestmark = pytest.mark.skipif(
    not RST_PATH,
    reason="Set MARS_TEST_MODAL_RST to run trusted real-RST comparisons.",
)


def test_real_modal_rst_matches_trusted_csv_exports():
    rst_path = Path(RST_PATH).resolve()
    golden_dir = Path(os.environ.get("MARS_TEST_MODAL_GOLDEN_DIR", rst_path.parent))
    paths = {
        "stress": golden_dir / "modal_stress.csv",
        "deformation": golden_dir / "modal_deformations.csv",
        "force_moment": golden_dir / "modal_element_nodal_forces_moments.csv",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    assert not missing, "Missing trusted RST comparison exports: " + ", ".join(missing)

    golden_stress = load_modal_stress(str(paths["stress"]))
    golden_deformation = load_modal_deformations(str(paths["deformation"]))
    golden_force_moment = load_element_nodal_forces_moments(str(paths["force_moment"]))
    expected_modes = golden_stress.num_modes
    assert golden_deformation.num_modes == expected_modes
    assert golden_force_moment.num_modes == expected_modes

    metadata = inspect_modal_rst(rst_path, expected_modes)
    scope_name = os.environ.get("MARS_TEST_MODAL_SCOPE", ALL_SCOPE)
    assert scope_name in {scope.name for scope in metadata.scopes}
    bundle = load_modal_rst(
        rst_path,
        RstLoadOptions(
            expected_modes=expected_modes,
            scope_name=scope_name,
            load_stress=True,
            load_deformation=True,
            load_force_moment=True,
            shell_layer=metadata.default_shell_layer,
        ),
    )

    def assert_dataset(actual, expected, components):
        np.testing.assert_array_equal(actual.node_ids, expected.node_ids)
        for component in components:
            np.testing.assert_allclose(
                getattr(actual, component),
                getattr(expected, component),
                rtol=1e-5,
                atol=1e-8,
            )

    assert_dataset(
        bundle.stress_data,
        golden_stress,
        ("modal_sx", "modal_sy", "modal_sz", "modal_sxy", "modal_syz", "modal_sxz"),
    )
    assert_dataset(
        bundle.deformation_data,
        golden_deformation,
        ("modal_ux", "modal_uy", "modal_uz"),
    )
    assert_dataset(
        bundle.force_moment_data,
        golden_force_moment,
        ("modal_fx", "modal_fy", "modal_fz", "modal_mx", "modal_my", "modal_mz"),
    )
