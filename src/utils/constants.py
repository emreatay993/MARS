"""
Global constants, configuration settings, and UI styles for the MSUP Smart Solver.

This module centralizes all configuration constants and UI stylesheets that are
used throughout the application.
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

# ===== UI Stylesheets =====

BUTTON_STYLE = """
    QPushButton {
        background-color: #e7f0fd;
        border: 1px solid #5b9bd5;
        padding: 10px;
        border-radius: 5px;
    }
    QPushButton:hover {
        background-color: #cce4ff;
    }
"""

GROUP_BOX_STYLE = """
    QGroupBox {
        border: 1px solid #5b9bd5;
        border-radius: 5px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 5px;
    }
"""

TAB_STYLE = """
    QTabBar::tab {
        background-color: #d6e4f5;  /* Pale blue background for inactive tabs */
        border: 1px solid #5b9bd5;   /* Default border for tabs */
        padding: 3px;
        border-top-left-radius: 5px;  /* Upper left corner rounded */
        border-top-right-radius: 5px; /* Upper right corner rounded */
        margin: 2px;
    }
    QTabBar::tab:hover {
        background-color: #cce4ff;  /* Background color when hovering over tabs */
    }
    QTabBar::tab:selected {
        background-color: #e7f0fd;  /* Active tab has your blue theme color */
        border: 2px solid #5b9bd5;  /* Thicker border for the active tab */
        color: #000000;  /* Active tab text color */
    }
    QTabBar::tab:!selected {
        background-color: #d6e4f5;  /* Paler blue for unselected tabs */
        color: #808080;  /* Gray text for inactive tabs */
        margin-top: 3px;  /* Make the unselected tabs slightly smaller */
    }
"""

READONLY_LINE_EDIT_STYLE = "background-color: #f0f0f0; color: grey; border: 1px solid #5b9bd5; padding: 5px;"
"""Style for read-only line edit widgets."""

CHECKBOX_STYLE = "margin: 10px 0;"
"""Style for checkbox widgets."""

CONSOLE_STYLE = "background-color: #ffffff; border: 1px solid #5b9bd5"
"""Style for console text edit widget."""

PROGRESS_BAR_STYLE = "border: 1px solid #5b9bd5; padding: 10px; background-color: #ffffff;"
"""Style for progress bar widget."""

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

