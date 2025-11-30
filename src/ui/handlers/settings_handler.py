"""
Handles the application and management of advanced settings.
"""

import numpy as np
import torch
import utils.constants as constants


class SettingsHandler:
    """Manages applying advanced settings to the solver engine."""

    def __init__(self):
        """Initialize the settings handler."""
        pass

    def apply_advanced_settings(self, settings):
        """Apply advanced settings to global constants."""
        # Update global settings in constants module
        constants.RAM_PERCENT = settings["ram_percent"]
        constants.DEFAULT_PRECISION = settings["precision"]
        constants.IS_GPU_ACCELERATION_ENABLED = settings["gpu_acceleration"]

        # Update derived precision variables
        if constants.DEFAULT_PRECISION == 'Single':
            constants.NP_DTYPE = np.float32
            constants.TORCH_DTYPE = torch.float32
            constants.RESULT_DTYPE = 'float32'
        elif constants.DEFAULT_PRECISION == 'Double':
            constants.NP_DTYPE = np.float64
            constants.TORCH_DTYPE = torch.float64
            constants.RESULT_DTYPE = 'float64'

        print("\n--- Advanced settings updated ---")
        print(f"  RAM Allocation: {constants.RAM_PERCENT * 100:.0f}%")
        print(f"  Solver Precision: {constants.DEFAULT_PRECISION}")
        print(f"  GPU Acceleration: "
              f"{'Enabled' if constants.IS_GPU_ACCELERATION_ENABLED else 'Disabled'}")
        print("---------------------------------")