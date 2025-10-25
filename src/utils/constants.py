"""
Global constants, configuration settings, and UI styles for MARS (Modal Analysis Response Solver).

Centralises configuration values and Qt styles used across the application.
"""

import os
import numpy as np
import torch

# ===== Solver Configuration =====
# These constants control the core behavior and precision of the solver.

RAM_PERCENT = 0.9
"""Default RAM allocation percentage based on available memory."""

DEFAULT_PRECISION = 'Double'
"""Precision for numerical computations: 'Single' or 'Double'."""

IS_GPU_ACCELERATION_ENABLED = False
"""Set to True to use GPU (requires compatible NVIDIA GPU and CUDA)."""

# ===== Data Type Configuration =====
# Dynamically set NumPy and Torch data types based on the selected precision.

if DEFAULT_PRECISION == 'Single':
    NP_DTYPE = np.float32
    TORCH_DTYPE = torch.float32
    RESULT_DTYPE = 'float32'
elif DEFAULT_PRECISION == 'Double':
    NP_DTYPE = np.float64
    TORCH_DTYPE = torch.float64
    RESULT_DTYPE = 'float64'
else:
    raise ValueError(f"Invalid precision: {DEFAULT_PRECISION}. Must be 'Single' or 'Double'.")

# ===== Environment Configuration =====
# Set OpenBLAS to use all available CPU cores for NumPy operations.
os.environ["OPENBLAS_NUM_THREADS"] = str(os.cpu_count())

# ===== UI Configuration =====
# Note: All styling is now centralized in src/ui/styles/style_constants.py
# and applied directly to widgets using setStyleSheet().

# ===== UI Colors =====

WINDOW_BACKGROUND_COLOR = (230, 230, 230)
"""Light gray background color for main window (R, G, B)."""

THEME_BLUE = "#5b9bd5"
"""Primary theme color used throughout the UI."""

# ===== Display Tab Constants =====

DEFAULT_POINT_SIZE = 5
"""Default point size for 3D visualization."""

DEFAULT_BACKGROUND_COLOR = "#FFFFFF"
"""Default background color for PyVista plotter."""

DEFAULT_ANIMATION_INTERVAL_MS = 100
"""Default animation frame interval in milliseconds."""
