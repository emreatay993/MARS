"""
Handles the application and management of advanced settings.
"""

import numpy as np
import torch
import solver.engine as solver_engine


class SettingsHandler:
    """Manages applying advanced settings to the solver engine."""

    def __init__(self):
        """Initialize the settings handler."""
        pass

    def apply_advanced_settings(self, settings):
        """Apply advanced settings to solver engine."""
        # Update global settings in solver engine
        solver_engine.RAM_PERCENT = settings["ram_percent"]
        solver_engine.DEFAULT_PRECISION = settings["precision"]
        solver_engine.IS_GPU_ACCELERATION_ENABLED = settings["gpu_acceleration"]

        # Update derived precision variables
        if solver_engine.DEFAULT_PRECISION == 'Single':
            solver_engine.NP_DTYPE = np.float32
            solver_engine.TORCH_DTYPE = torch.float32
            solver_engine.RESULT_DTYPE = 'float32'
        elif solver_engine.DEFAULT_PRECISION == 'Double':
            solver_engine.NP_DTYPE = np.float64
            solver_engine.TORCH_DTYPE = torch.float64
            solver_engine.RESULT_DTYPE = 'float64'

        print("\n--- Advanced settings updated ---")
        print(f"  RAM Allocation: {solver_engine.RAM_PERCENT * 100:.0f}%")
        print(f"  Solver Precision: {solver_engine.DEFAULT_PRECISION}")
        print(f"  GPU Acceleration: "
              f"{'Enabled' if solver_engine.IS_GPU_ACCELERATION_ENABLED else 'Disabled'}")
        print("---------------------------------")