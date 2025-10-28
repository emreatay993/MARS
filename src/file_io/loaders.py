"""
File loading helpers for MARS (Modal Analysis Response Solver).

Provides functions for loading input files and converting them into structured
data models.
"""

import json
import os
import pandas as pd
import numpy as np
from typing import Optional

from core.data_models import (
    ModalData,
    ModalStressData,
    DeformationData,
    SteadyStateData,
    TemperatureFieldData,
    MaterialProfileData,
)
from file_io.validators import (
    validate_mcf_file,
    validate_modal_stress_file,
    validate_deformation_file,
    validate_steady_state_file,
    validate_material_profile_payload,
)
from utils.file_utils import unwrap_mcf_file
from utils.constants import NP_DTYPE


def load_modal_coordinates(filename: str) -> ModalData:
    """
    Load modal coordinate data from an MCF file.
    
    Args:
        filename: Path to the MCF file.
    
    Returns:
        ModalData object containing modal coordinates and time values.
    
    Raises:
        ValueError: If the file is invalid or cannot be loaded.
    """
    # Validate first
    is_valid, error_msg = validate_mcf_file(filename)
    if not is_valid:
        raise ValueError(f"Invalid MCF file: {error_msg}")
    
    # Unwrap the file
    base, ext = os.path.splitext(filename)
    unwrapped_filename = base + "_unwrapped" + ext
    unwrap_mcf_file(filename, unwrapped_filename)
    
    try:
        # Find start of data
        with open(unwrapped_filename, 'r') as file:
            start_index = next(i for i, line in enumerate(file) if 'Time' in line)
        
        # Load data
        df_val = pd.read_csv(unwrapped_filename, sep='\\s+', 
                             skiprows=start_index + 1, header=None)
        
        # Extract time values and modal coordinates
        time_values = df_val.iloc[:, 0].to_numpy()
        modal_coord = df_val.drop(columns=df_val.columns[0]).transpose().to_numpy()
        
        return ModalData(modal_coord=modal_coord, time_values=time_values)
        
    finally:
        # Clean up temporary file
        if os.path.exists(unwrapped_filename):
            os.remove(unwrapped_filename)


def load_modal_stress(filename: str) -> ModalStressData:
    """
    Load modal stress data from a CSV file.
    
    Args:
        filename: Path to the modal stress CSV file.
    
    Returns:
        ModalStressData object containing stress components and node information.
    
    Raises:
        ValueError: If the file is invalid or cannot be loaded.
    """
    # Validate first
    is_valid, error_msg = validate_modal_stress_file(filename)
    if not is_valid:
        raise ValueError(f"Invalid modal stress file: {error_msg}")
    
    # Load data
    df = pd.read_csv(filename)

    # Drop duplicates, keeping the last entry
    df.drop_duplicates(subset=['NodeID'], keep='last', inplace=True)
    
    # Extract node IDs
    node_ids = df['NodeID'].to_numpy().flatten()
    
    # Extract coordinates if present
    node_coords = None
    if {'X', 'Y', 'Z'}.issubset(df.columns):
        node_coords = df[['X', 'Y', 'Z']].to_numpy()
    
    # Extract stress components
    modal_sx = df.filter(regex='(?i)sx_.*').to_numpy().astype(NP_DTYPE)
    modal_sy = df.filter(regex='(?i)sy_.*').to_numpy().astype(NP_DTYPE)
    modal_sz = df.filter(regex='(?i)sz_.*').to_numpy().astype(NP_DTYPE)
    modal_sxy = df.filter(regex='(?i)sxy_.*').to_numpy().astype(NP_DTYPE)
    modal_syz = df.filter(regex='(?i)syz_.*').to_numpy().astype(NP_DTYPE)
    modal_sxz = df.filter(regex='(?i)sxz_.*').to_numpy().astype(NP_DTYPE)
    
    return ModalStressData(
        node_ids=node_ids,
        modal_sx=modal_sx,
        modal_sy=modal_sy,
        modal_sz=modal_sz,
        modal_sxy=modal_sxy,
        modal_syz=modal_syz,
        modal_sxz=modal_sxz,
        node_coords=node_coords
    )


def load_modal_deformations(filename: str) -> DeformationData:
    """
    Load modal deformation data from a CSV file.
    
    Args:
        filename: Path to the modal deformations CSV file.
    
    Returns:
        DeformationData object containing deformation components.
    
    Raises:
        ValueError: If the file is invalid or cannot be loaded.
    """
    # Validate first
    is_valid, error_msg = validate_deformation_file(filename)
    if not is_valid:
        raise ValueError(f"Invalid deformation file: {error_msg}")
    
    # Load data
    df = pd.read_csv(filename)
    
    # Drop duplicates, keeping the last entry
    df.drop_duplicates(subset=['NodeID'], keep='last', inplace=True)

    # Extract node IDs
    node_ids = df['NodeID'].to_numpy().flatten()
    
    # Extract deformation components
    modal_ux = df.filter(regex='(?i)^ux_').to_numpy().astype(NP_DTYPE)
    modal_uy = df.filter(regex='(?i)^uy_').to_numpy().astype(NP_DTYPE)
    modal_uz = df.filter(regex='(?i)^uz_').to_numpy().astype(NP_DTYPE)
    
    return DeformationData(
        node_ids=node_ids,
        modal_ux=modal_ux,
        modal_uy=modal_uy,
        modal_uz=modal_uz
    )


def load_steady_state_stress(filename: str) -> SteadyStateData:
    """
    Load steady-state stress data from a TXT file.
    
    Args:
        filename: Path to the steady-state stress file.
    
    Returns:
        SteadyStateData object containing steady-state stress components.
    
    Raises:
        ValueError: If the file is invalid or cannot be loaded.
    """
    # Validate first
    is_valid, error_msg = validate_steady_state_file(filename)
    if not is_valid:
        raise ValueError(f"Invalid steady-state stress file: {error_msg}")
    
    # Load data
    df = pd.read_csv(filename, delimiter='\t', header=0)
    
    # Extract data
    node_ids = df['Node Number'].to_numpy().reshape(-1, 1)
    steady_sx = df['SX (MPa)'].to_numpy().reshape(-1, 1).astype(NP_DTYPE)
    steady_sy = df['SY (MPa)'].to_numpy().reshape(-1, 1).astype(NP_DTYPE)
    steady_sz = df['SZ (MPa)'].to_numpy().reshape(-1, 1).astype(NP_DTYPE)
    steady_sxy = df['SXY (MPa)'].to_numpy().reshape(-1, 1).astype(NP_DTYPE)
    steady_syz = df['SYZ (MPa)'].to_numpy().reshape(-1, 1).astype(NP_DTYPE)
    steady_sxz = df['SXZ (MPa)'].to_numpy().reshape(-1, 1).astype(NP_DTYPE)
    
    return SteadyStateData(
        node_ids=node_ids,
        steady_sx=steady_sx,
        steady_sy=steady_sy,
        steady_sz=steady_sz,
        steady_sxy=steady_sxy,
        steady_syz=steady_syz,
        steady_sxz=steady_sxz
    )


def load_temperature_field(filename: str) -> TemperatureFieldData:
    """Load nodal temperature field data from a TXT file."""
    try:
        df = pd.read_csv(filename, sep='\t', engine='python')
        if df.shape[1] <= 1:
            df = pd.read_csv(filename, sep=r'\s+', engine='python')
    except Exception as exc:
        raise ValueError(f"Failed to parse temperature field file: {exc}") from exc

    if df.empty:
        raise ValueError("Temperature field file is empty.")

    df.columns = [col.strip() for col in df.columns]

    if 'Node Number' not in df.columns:
        raise ValueError("Temperature field file must contain a 'Node Number' column.")

    return TemperatureFieldData(dataframe=df)


def _build_material_profile_dataframe(section: dict, expected_columns) -> pd.DataFrame:
    if section is None:
        return pd.DataFrame(columns=expected_columns)

    columns = section.get("columns", expected_columns)
    data = section.get("data", [])

    df = pd.DataFrame(data, columns=columns)
    rename_map = {columns[i]: expected_columns[i] for i in range(min(len(columns), len(expected_columns)))}
    df = df.rename(columns=rename_map)

    missing = [col for col in expected_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {', '.join(missing)}")

    df = df[expected_columns]
    for column in expected_columns:
        if df[column].empty:
            continue
        df[column] = pd.to_numeric(df[column], errors='raise')
    return df


def load_material_profile(filename: str) -> MaterialProfileData:
    """
    Load a material profile JSON file into a MaterialProfileData object.

    Args:
        filename: Path to the material profile JSON file.

    Returns:
        MaterialProfileData populated with Young's modulus, Poisson's ratio,
        and plastic curve datasets.
    """
    if not os.path.exists(filename):
        raise ValueError("File does not exist.")

    try:
        with open(filename, "r", encoding="utf-8-sig") as fh:
            payload = json.load(fh)
    except Exception as exc:
        raise ValueError(f"Failed to read material profile: {exc}") from exc

    is_valid, error = validate_material_profile_payload(payload)
    if not is_valid:
        raise ValueError(f"Invalid material profile: {error}")

    youngs_df = _build_material_profile_dataframe(
        payload.get("youngs_modulus"),
        ["Temperature (°C)", "Young's Modulus [MPa]"],
    )
    poisson_df = _build_material_profile_dataframe(
        payload.get("poisson_ratio"),
        ["Temperature (°C)", "Poisson's Ratio"],
    )

    plastic_curves = {}
    for entry in payload.get("plastic_curves", []):
        temperature = float(entry.get("temperature"))
        curve_df = _build_material_profile_dataframe(
            entry,
            ["Plastic Strain", "True Stress [MPa]"],
        )
        plastic_curves[temperature] = curve_df

    return MaterialProfileData(
        youngs_modulus=youngs_df,
        poisson_ratio=poisson_df,
        plastic_curves=plastic_curves,
    )
