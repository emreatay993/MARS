import warnings

import numpy as np
import pandas as pd
import pytest

from core.data_models import MaterialProfileData, TemperatureFieldData
from core.plasticity import (
    PlasticityDataError,
    build_material_db_from_profile,
    extract_poisson_ratio,
    map_temperature_field_to_nodes,
)
from solver.plasticity_engine import (
    MaterialDB,
    E_of_T_njit,
    Up_of_T_sigma_njit,
    apply_glinka_correction,
    apply_neuber_correction,
    epsp_of_T_sigma_njit,
    sigma_of_T_epsp_njit,
    yield_of_T_njit,
)


def _sample_material_profile() -> MaterialProfileData:
    youngs = pd.DataFrame(
        {
            "Temperature (°C)": [20.0, 60.0],
            "Young's Modulus [MPa]": [70_000.0, 68_500.0],
        }
    )
    poisson = pd.DataFrame(
        {
            "Temperature (°C)": [20.0, 60.0],
            "Poisson's Ratio": [0.3, 0.295],
        }
    )
    plastic_curves = {
        20.0: pd.DataFrame(
            {
                "Plastic Strain": [0.0, 0.01, 0.05],
                "True Stress [MPa]": [350.0, 420.0, 480.0],
            }
        ),
        60.0: pd.DataFrame(
            {
                "Plastic Strain": [0.0, 0.01, 0.05],
                "True Stress [MPa]": [320.0, 390.0, 450.0],
            }
        ),
    }
    return MaterialProfileData(
        youngs_modulus=youngs,
        poisson_ratio=poisson,
        plastic_curves=plastic_curves,
    )


def test_build_material_db_from_profile():
    profile = _sample_material_profile()
    db = build_material_db_from_profile(profile)

    assert np.allclose(db.TEMP, np.array([20.0, 60.0]))
    assert db.SIG.shape == (2, 3)
    assert db.EPSP.shape == (2, 3)
    # Young's modulus interpolated directly for provided temps
    assert np.allclose(db.E_tab, np.array([70_000.0, 68_500.0]))


def test_build_material_db_handles_resampling():
    profile = _sample_material_profile()
    # Replace one curve with fewer points (will trigger resampling)
    profile.plastic_curves[60.0] = pd.DataFrame(
        {
            "Plastic Strain": [0.0, 0.05],
            "True Stress [MPa]": [320.0, 450.0],
        }
    )

    db = build_material_db_from_profile(profile)

    assert db.SIG.shape == (2, 3)
    # Resampled curve should match expected interpolation at 0.01 strain
    expected_resampled = np.array([320.0, 346.0, 450.0])
    np.testing.assert_allclose(db.SIG[1], expected_resampled, rtol=1e-6)


def test_build_material_db_preserves_long_tail_from_short_curve():
    profile = _sample_material_profile()
    # Fewer points, but extends much farther in plastic strain.
    profile.plastic_curves[60.0] = pd.DataFrame(
        {
            "Plastic Strain": [0.0, 0.20],
            "True Stress [MPa]": [320.0, 500.0],
        }
    )

    db = build_material_db_from_profile(profile)

    # Shared grid should include the far tail (0.20), not stop at 0.05.
    assert db.EPSP.shape == (2, 4)
    assert db.EPSP[0, -1] == pytest.approx(0.20)
    assert db.SIG[1, -1] == pytest.approx(500.0)


def test_build_material_db_requires_plastic_curves():
    empty_profile = MaterialProfileData.empty()
    with pytest.raises(PlasticityDataError):
        build_material_db_from_profile(empty_profile)


def test_build_material_db_requires_plastic_strain_to_start_at_zero():
    profile = _sample_material_profile()
    profile.plastic_curves[20.0] = pd.DataFrame(
        {
            "Plastic Strain": [0.001, 0.01, 0.05],
            "True Stress [MPa]": [350.0, 420.0, 480.0],
        }
    )

    with pytest.raises(PlasticityDataError, match="start at zero"):
        build_material_db_from_profile(profile)


def test_build_material_db_requires_youngs_modulus_temperature_coverage():
    profile = _sample_material_profile()
    profile.youngs_modulus = pd.DataFrame(
        {
            "Temperature": [20.0],
            "Young's Modulus [MPa]": [70_000.0],
        }
    )

    with pytest.raises(PlasticityDataError, match="Young's modulus temperature range"):
        build_material_db_from_profile(profile)


def test_map_temperature_field_to_nodes_exact_match():
    df = pd.DataFrame(
        {
            "Node Number": [1, 2, 3],
            "Temperature": [25.0, 30.0, 35.0],
        }
    )
    temp_data = TemperatureFieldData(dataframe=df)
    node_ids = np.array([1, 2, 3])

    mapped = map_temperature_field_to_nodes(temp_data, node_ids)
    assert np.allclose(mapped, np.array([25.0, 30.0, 35.0]))


def test_map_temperature_field_to_nodes_with_default():
    df = pd.DataFrame(
        {
            "Node Number": [1, 3],
            "Temperature": [25.0, 35.0],
        }
    )
    temp_data = TemperatureFieldData(dataframe=df)
    node_ids = np.array([1, 2, 3])

    mapped = map_temperature_field_to_nodes(temp_data, node_ids, default_temperature=22.0)
    assert np.allclose(mapped, np.array([25.0, 22.0, 35.0]))


def test_map_temperature_field_to_nodes_missing_without_default():
    df = pd.DataFrame(
        {
            "Node Number": [1],
            "Temperature": [25.0],
        }
    )
    temp_data = TemperatureFieldData(dataframe=df)
    node_ids = np.array([1, 2])

    with pytest.raises(PlasticityDataError):
        map_temperature_field_to_nodes(temp_data, node_ids)


def test_extract_poisson_ratio_fallback():
    profile = _sample_material_profile()
    assert extract_poisson_ratio(profile) == pytest.approx(0.2975)  # mean value

    empty_profile = MaterialProfileData.empty()
    assert extract_poisson_ratio(empty_profile) == pytest.approx(0.3)


def _simple_plateau_material() -> MaterialDB:
    return MaterialDB.from_arrays(
        temp=np.array([20.0]),
        e_tab=np.array([200_000.0]),
        sig=np.array([[300.0, 400.0]], dtype=float),
        epsp=np.array([[0.0, 0.10]], dtype=float),
    )


def test_neuber_plateau_caps_stress_and_allows_tail_strain_growth():
    material = _simple_plateau_material()
    sigma_e = np.array([10_000.0], dtype=float)
    temp = np.array([20.0], dtype=float)

    with pytest.warns(RuntimeWarning, match="plateau mode extended beyond supplied plastic curve tail"):
        corrected, epsp = apply_neuber_correction(sigma_e, temp, material, use_plateau=True)

    assert corrected[0] <= 400.0 + 1e-8
    assert epsp[0] > 0.10


def test_glinka_plateau_caps_stress_and_allows_tail_strain_growth():
    material = _simple_plateau_material()
    sigma_e = np.array([10_000.0], dtype=float)
    temp = np.array([20.0], dtype=float)

    with pytest.warns(RuntimeWarning, match="plateau mode extended beyond supplied plastic curve tail"):
        corrected, epsp = apply_glinka_correction(sigma_e, temp, material, use_plateau=True)

    assert corrected[0] <= 400.0 + 1e-8
    assert epsp[0] > 0.10


def test_plateau_mode_does_not_warn_when_tail_is_not_extended():
    material = _simple_plateau_material()
    sigma_e = np.array([350.0], dtype=float)
    temp = np.array([20.0], dtype=float)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        apply_neuber_correction(sigma_e, temp, material, use_plateau=True)
        apply_glinka_correction(sigma_e, temp, material, use_plateau=True)

    assert not any("plateau mode extended" in str(item.message) for item in caught)


def _nonlinear_hardening_material() -> MaterialDB:
    return MaterialDB.from_arrays(
        temp=np.array([20.0]),
        e_tab=np.array([200_000.0]),
        sig=np.array([[300.0, 400.0, 500.0, 650.0]], dtype=float),
        epsp=np.array([[0.0, 0.01, 0.04, 0.12]], dtype=float),
    )


def test_neuber_correction_matches_closed_form_and_residual():
    material = _nonlinear_hardening_material()
    sigma_e = np.array([600.0], dtype=float)
    temp = np.array([20.0], dtype=float)

    corrected, epsp = apply_neuber_correction(sigma_e, temp, material)

    assert corrected[0] == pytest.approx(336.637999517865, rel=1e-10)
    assert epsp[0] == pytest.approx(0.00366379995178648, rel=1e-10)
    E = material.E_tab[0]
    assert corrected[0] / E + epsp[0] == pytest.approx(
        sigma_e[0] ** 2 / (corrected[0] * E),
        rel=1e-12,
    )


def test_glinka_correction_matches_closed_form_and_energy_residual():
    material = _nonlinear_hardening_material()
    sigma_e = np.array([600.0], dtype=float)
    temp = np.array([20.0], dtype=float)

    corrected, epsp = apply_glinka_correction(sigma_e, temp, material)

    assert corrected[0] == pytest.approx(320.713490294909, rel=1e-10)
    assert epsp[0] == pytest.approx(0.00207134902949093, rel=1e-10)
    E = material.E_tab[0]
    plastic_energy = Up_of_T_sigma_njit(20.0, corrected[0], material.TEMP, material.SIG, material.EPSP, 0)
    assert corrected[0] ** 2 / (2.0 * E) + plastic_energy == pytest.approx(
        sigma_e[0] ** 2 / (2.0 * E),
        rel=1e-10,
    )


def test_neuber_and_glinka_remain_elastic_below_and_at_yield():
    material = _nonlinear_hardening_material()
    sigma_e = np.array([250.0, 300.0], dtype=float)
    temp = np.array([20.0, 20.0], dtype=float)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        for correction in (apply_neuber_correction, apply_glinka_correction):
            corrected, epsp = correction(sigma_e, temp, material)
            np.testing.assert_allclose(corrected, sigma_e)
            np.testing.assert_allclose(epsp, np.zeros_like(sigma_e))

    assert not any(issubclass(item.category, RuntimeWarning) for item in caught)


def test_neuber_default_uses_linear_tail_extrapolation():
    material = _simple_plateau_material()
    sigma_e = np.array([10_000.0], dtype=float)
    temp = np.array([20.0], dtype=float)

    corrected, epsp = apply_neuber_correction(sigma_e, temp, material, use_plateau=False)

    assert corrected[0] == pytest.approx(870.217748566639, rel=1e-9)
    assert epsp[0] == pytest.approx(0.570217748566639, rel=1e-9)
    assert corrected[0] > 400.0
    assert epsp[0] > 0.10


def test_glinka_default_uses_linear_tail_extrapolation():
    material = _simple_plateau_material()
    sigma_e = np.array([10_000.0], dtype=float)
    temp = np.array([20.0], dtype=float)

    corrected, epsp = apply_glinka_correction(sigma_e, temp, material, use_plateau=False)

    assert corrected[0] == pytest.approx(766.201459550238, rel=1e-9)
    assert epsp[0] == pytest.approx(0.466201459550238, rel=1e-9)
    assert corrected[0] > 400.0
    assert epsp[0] > 0.10


def test_material_db_interpolates_temperature_dependent_flow_curve_and_modulus():
    material = MaterialDB.from_arrays(
        temp=np.array([20.0, 60.0]),
        e_tab=np.array([200_000.0, 160_000.0]),
        sig=np.array([[300.0, 500.0], [260.0, 460.0]], dtype=float),
        epsp=np.array([[0.0, 0.1], [0.0, 0.1]], dtype=float),
    )

    assert E_of_T_njit(40.0, material.TEMP, material.E_tab) == pytest.approx(180_000.0)
    assert yield_of_T_njit(40.0, material.TEMP, material.SIG) == pytest.approx(280.0)
    assert epsp_of_T_sigma_njit(40.0, 380.0, material.TEMP, material.SIG, material.EPSP, 0) == pytest.approx(0.05)
    assert sigma_of_T_epsp_njit(40.0, 0.05, material.TEMP, material.SIG, material.EPSP, 0) == pytest.approx(380.0)
    assert Up_of_T_sigma_njit(40.0, 380.0, material.TEMP, material.SIG, material.EPSP, 0) == pytest.approx(16.4)


def test_neuber_and_glinka_do_not_warn_when_converged():
    material = _nonlinear_hardening_material()
    sigma_e = np.array([600.0], dtype=float)
    temp = np.array([20.0], dtype=float)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        apply_neuber_correction(sigma_e, temp, material)
        apply_glinka_correction(sigma_e, temp, material)

    assert not any(issubclass(item.category, RuntimeWarning) for item in caught)


def test_neuber_warns_when_iteration_limit_prevents_convergence():
    material = _nonlinear_hardening_material()
    sigma_e = np.array([1_200.0], dtype=float)
    temp = np.array([20.0], dtype=float)

    with pytest.warns(RuntimeWarning, match="Neuber correction did not converge"):
        apply_neuber_correction(sigma_e, temp, material, max_iterations=1, tol=1e-14)


def test_glinka_warns_when_iteration_limit_prevents_convergence():
    material = _nonlinear_hardening_material()
    sigma_e = np.array([1_200.0], dtype=float)
    temp = np.array([20.0], dtype=float)

    with pytest.warns(RuntimeWarning, match="Glinka correction did not converge"):
        apply_glinka_correction(sigma_e, temp, material, max_iterations=1, tol=1e-14)
