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


def test_build_material_db_requires_plastic_curves():
    empty_profile = MaterialProfileData.empty()
    with pytest.raises(PlasticityDataError):
        build_material_db_from_profile(empty_profile)


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
    assert pytest.approx(extract_poisson_ratio(profile), 0.299)  # mean value

    empty_profile = MaterialProfileData.empty()
    assert extract_poisson_ratio(empty_profile) == pytest.approx(0.3)
