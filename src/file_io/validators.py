"""
File validation helpers for MARS (Modal Analysis Response Solver).

Validators check input file format and content before loading.
"""

import os
import pandas as pd
from typing import Tuple, Optional
from utils.file_utils import unwrap_mcf_file


class ValidationResult:
    """Result of a file validation operation."""
    
    def __init__(self, is_valid: bool, error_message: Optional[str] = None):
        self.is_valid = is_valid
        self.error_message = error_message
    
    def __bool__(self):
        return self.is_valid


def validate_mcf_file(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a Modal Coordinate File (MCF).
    
    Args:
        filename: Path to the MCF file.
    
    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    try:
        if not os.path.exists(filename):
            return False, "File does not exist."
        
        # Unwrap the file to a temporary location
        base, ext = os.path.splitext(filename)
        unwrapped_filename = base + "_unwrapped" + ext
        
        unwrap_mcf_file(filename, unwrapped_filename)
        
        # Find the start of data
        with open(unwrapped_filename, 'r') as file:
            try:
                start_index = next(i for i, line in enumerate(file) if 'Time' in line)
            except StopIteration:
                os.remove(unwrapped_filename)
                return False, "Could not find 'Time' header line in file."
        
        # Try to read the data
        df_val = pd.read_csv(unwrapped_filename, sep='\\s+', 
                             skiprows=start_index + 1, header=None)
        os.remove(unwrapped_filename)
        
        # Validate content
        if df_val.empty or df_val.shape[1] < 2:
            return False, "File appears to be empty or has no mode columns."
        
        if not all(pd.api.types.is_numeric_dtype(df_val[c]) for c in df_val.columns):
            return False, "File contains non-numeric data where modal coordinates are expected."
        
        return True, None
        
    except Exception as e:
        # Clean up temporary file if it exists
        if 'unwrapped_filename' in locals() and os.path.exists(unwrapped_filename):
            os.remove(unwrapped_filename)
        return False, str(e)


def validate_modal_stress_file(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a Modal Stress CSV file.
    
    Args:
        filename: Path to the modal stress CSV file.
    
    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    try:
        if not os.path.exists(filename):
            return False, "File does not exist."
        
        # Only read first 10 rows for validation - we only need to check headers
        df_val = pd.read_csv(filename, nrows=10)
        
        # Check for required NodeID column
        if 'NodeID' not in df_val.columns:
            return False, "Required 'NodeID' column not found."
        
        # Check for required stress component columns
        stress_components = ['sx_', 'sy_', 'sz_', 'sxy_', 'syz_', 'sxz_']
        for comp in stress_components:
            if df_val.filter(regex=f'(?i){comp}').empty:
                return False, f"Required stress component columns matching '{comp}*' not found."
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def validate_deformation_file(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a Modal Deformations CSV file.
    
    Args:
        filename: Path to the modal deformations CSV file.
    
    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    try:
        if not os.path.exists(filename):
            return False, "File does not exist."
        
        # Only read first 10 rows for validation - we only need to check headers
        df_val = pd.read_csv(filename, nrows=10)
        
        # Check for required NodeID column
        if 'NodeID' not in df_val.columns:
            return False, "Required 'NodeID' column not found."
        
        # Check for required deformation component columns
        deform_components = ['ux_', 'uy_', 'uz_']
        for comp in deform_components:
            if df_val.filter(regex=f'(?i){comp}').empty:
                return False, f"Required deformation columns matching '{comp}*' not found."
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def validate_steady_state_file(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a Steady-State Stress TXT file.
    
    Args:
        filename: Path to the steady-state stress file.
    
    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    try:
        if not os.path.exists(filename):
            return False, "File does not exist."
        
        df_val = pd.read_csv(filename, delimiter='\t', header=0)
        
        # Define and check for all required columns
        required_cols = [
            'Node Number', 'SX (MPa)', 'SY (MPa)', 'SZ (MPa)',
            'SXY (MPa)', 'SYZ (MPa)', 'SXZ (MPa)'
        ]
        
        for col in required_cols:
            if col not in df_val.columns:
                return False, f"Required column '{col}' not found."
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def validate_material_profile_payload(payload: dict) -> Tuple[bool, Optional[str]]:
    """
    Validate the structure of a material profile JSON payload.

    Args:
        payload: Parsed JSON object representing the material profile.

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """

    def _validate_table(section: dict, section_name: str, expected_columns) -> Tuple[bool, Optional[str]]:
        if section is None:
            # Treat missing section as empty table
            return True, None
        if not isinstance(section, dict):
            return False, f"{section_name} section must be an object."

        columns = section.get("columns")
        data = section.get("data")
        if columns is None or data is None:
            return False, f"{section_name} section must include 'columns' and 'data' entries."
        if not isinstance(columns, list) or not isinstance(data, list):
            return False, f"{section_name} section must provide list-based 'columns' and 'data'."

        try:
            df = pd.DataFrame(data, columns=columns)
        except Exception as exc:
            return False, f"Unable to parse {section_name} data: {exc}"

        rename_map = {columns[i]: expected_columns[i] for i in range(min(len(columns), len(expected_columns)))}
        df = df.rename(columns=rename_map)

        missing = [col for col in expected_columns if col not in df.columns]
        if missing:
            return False, f"{section_name} is missing expected columns: {', '.join(missing)}."

        df = df[expected_columns]
        try:
            for column in expected_columns:
                if df[column].empty:
                    continue
                pd.to_numeric(df[column], errors='raise')
        except Exception as exc:
            return False, f"{section_name} contains non-numeric values: {exc}"

        return True, None

    if not isinstance(payload, dict):
        return False, "Material profile JSON must be an object."

    youngs_valid, youngs_error = _validate_table(
        payload.get("youngs_modulus"),
        "Young's modulus",
        ["Temperature (°C)", "Young's Modulus [MPa]"]
    )
    if not youngs_valid:
        return False, youngs_error

    poisson_valid, poisson_error = _validate_table(
        payload.get("poisson_ratio"),
        "Poisson's ratio",
        ["Temperature (°C)", "Poisson's Ratio"]
    )
    if not poisson_valid:
        return False, poisson_error

    plastic_data = payload.get("plastic_curves", [])
    if plastic_data is None:
        plastic_data = []
    if not isinstance(plastic_data, list):
        return False, "Plastic curves section must be a list."

    for entry in plastic_data:
        if not isinstance(entry, dict):
            return False, "Each plastic curve entry must be an object."
        temperature = entry.get("temperature")
        if temperature is None:
            return False, "Plastic curve entries must include a temperature value."
        try:
            float(temperature)
        except (TypeError, ValueError):
            return False, f"Invalid temperature value '{temperature}' in plastic curve entry."

        curve_valid, curve_error = _validate_table(
            entry,
            f"Plastic curve (@ {temperature})",
            ["Plastic Strain", "True Stress [MPa]"]
        )
        if not curve_valid:
            return False, curve_error

    return True, None
