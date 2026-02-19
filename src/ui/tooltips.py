"""
Centralized tooltip text definitions for the MARS GUI.

All user-facing tooltip strings are defined here so they can be maintained
in one place and reused across the UI.

Tooltips use HTML for precise formatting. Header examples use <pre> blocks
with monospace font to prevent line wrapping.
"""

# =============================================================================
# Input Files Section
# =============================================================================

COORD_FILE_BUTTON = (
    "<b>Modal Coordinate File</b><br>"
    "<hr>"
    "Contains modal participation factors (generalized coordinates) "
    "for each mode at every time step. Always required as the time "
    "basis for all MSUP transient calculations.<br><br>"
    "<b>Formats:</b>&nbsp;&nbsp;.mcf&nbsp;&nbsp;|&nbsp;&nbsp;.pch (NASTRAN punch file)<br><br>"
    "<b>Example header (.mcf):</b><br>"
    "<pre style='font-family: Consolas; font-size: 8pt; margin: 4px 0 0 0;'>"
    "Time   Mode1   Mode2   Mode3   ...   ModeN</pre>"
    "<br>The .pch format is parsed from NASTRAN SOL 112 SDISPLACEMENT output."
)

COORD_FILE_PATH = "Path to the currently loaded modal coordinate file."

STRESS_FILE_BUTTON = (
    "<b>Modal Stress File</b><br>"
    "<hr>"
    "Contains all 6 stress tensor components per mode per node. "
    "Used for Von Mises, principal stress, and damage calculations.<br><br>"
    "<b>Format:</b>&nbsp;&nbsp;.csv&nbsp;&nbsp;(comma-separated)<br><br>"
    "<b>Example header:</b><br>"
    "<pre style='font-family: Consolas; font-size: 8pt; margin: 4px 0 0 0;'>"
    "NodeID, X, Y, Z, sx_Mode1, sy_Mode1, sz_Mode1, sxy_Mode1, syz_Mode1, sxz_Mode1, ..., sxz_ModeN</pre>"
    "<br><b>Notes:</b><br>"
    "<ul style='margin-top: 2px; margin-bottom: 0;'>"
    "<li>X, Y, Z columns are optional (enable 3D visualization)</li>"
    "<li>Not required for force/moment-only runs</li>"
    "</ul>"
)

STRESS_FILE_PATH = "Path to the currently loaded modal stress file."

STEADY_STATE_CHECKBOX = (
    "<b>Include Steady-State Stress Field</b><br>"
    "<hr>"
    "Superimposes a static stress field onto the transient results. "
    "The steady-state tensor is added at every time step before "
    "computing Von Mises or principal stresses.<br><br>"
    "<b>Typical use cases:</b><br>"
    "<ul style='margin-top: 2px; margin-bottom: 0;'>"
    "<li>Bolt preload</li>"
    "<li>Thermal stresses</li>"
    "<li>Pressure loads</li>"
    "</ul>"
)

STEADY_STATE_FILE_BUTTON = (
    "<b>Steady-State Stress Tensor File</b><br>"
    "<hr>"
    "<b>Format:</b>&nbsp;&nbsp;.txt&nbsp;&nbsp;(tab-delimited)<br><br>"
    "<b>Example header:</b><br>"
    "<pre style='font-family: Consolas; font-size: 8pt; margin: 4px 0 0 0;'>"
    "Node Number&#9;SX (MPa)&#9;SY (MPa)&#9;SZ (MPa)&#9;SXY (MPa)&#9;SYZ (MPa)&#9;SXZ (MPa)</pre>"
    "<br><b>Notes:</b><br>"
    "<ul style='margin-top: 2px; margin-bottom: 0;'>"
    "<li>Nodes are mapped to the modal stress node set</li>"
    "<li>Missing nodes default to zero stress</li>"
    "</ul>"
)

STEADY_STATE_FILE_PATH = "Path to the currently loaded steady-state stress file."

DEFORMATIONS_CHECKBOX = (
    "<b>Include Deformations</b><br>"
    "<hr>"
    "Enables the following outputs:<br>"
    "<ul style='margin-top: 2px; margin-bottom: 0;'>"
    "<li>Nodal deformation (magnitude + X/Y/Z components)</li>"
    "<li>Velocity (time derivative of displacement)</li>"
    "<li>Acceleration (second time derivative)</li>"
    "<li>Deformed shape visualization and animation</li>"
    "</ul>"
    "<br>Requires a CSV with the same node set as the stress file."
)

DEFORMATIONS_FILE_BUTTON = (
    "<b>Modal Deformations File</b><br>"
    "<hr>"
    "Contains 3 displacement components (UX, UY, UZ) per mode per node.<br><br>"
    "<b>Format:</b>&nbsp;&nbsp;.csv&nbsp;&nbsp;(comma-separated)<br><br>"
    "<b>Example header:</b><br>"
    "<pre style='font-family: Consolas; font-size: 8pt; margin: 4px 0 0 0;'>"
    "NodeID, X, Y, Z, ux_Mode1, uy_Mode1, uz_Mode1, ..., uz_ModeN</pre>"
    "<br>Node IDs should match the modal stress file."
)

DEFORMATIONS_FILE_PATH = "Path to the currently loaded modal deformations file."

FORCE_MOMENT_CHECKBOX = (
    "<b>Include Element Nodal Forces &amp; Moments</b><br>"
    "<hr>"
    "Enables loading and processing of element nodal forces and moments.<br><br>"
    "<b>Key features:</b><br>"
    "<ul style='margin-top: 2px; margin-bottom: 0;'>"
    "<li>Fully independent of stress data</li>"
    "<li>No stress file needed for force/moment-only runs</li>"
    "<li>Node set can differ from the stress file</li>"
    "</ul>"
    "<b>Typical use case:</b><br>"
    "Checking bolt/fastener loads on a small set of interface "
    "nodes without solving the full stress matrix."
)

FORCE_MOMENT_FILE_BUTTON = (
    "<b>Element Nodal Forces &amp; Moments File</b><br>"
    "<hr>"
    "Contains 6 components per mode per node:<br>"
    "&nbsp;&nbsp;3 forces&nbsp;&nbsp;&nbsp;(enfox, enfoy, enfoz)<br>"
    "&nbsp;&nbsp;3 moments&nbsp;(enmox, enmoy, enmoz)<br><br>"
    "<b>Format:</b>&nbsp;&nbsp;.csv&nbsp;&nbsp;(comma-separated)<br><br>"
    "<b>Example header:</b><br>"
    "<pre style='font-family: Consolas; font-size: 8pt; margin: 4px 0 0 0;'>"
    "NodeID, X, Y, Z, enfox_Mode1, enfoy_Mode1, enfoz_Mode1, enmox_Mode1, enmoy_Mode1, enmoz_Mode1, ..., enmoz_ModeN</pre>"
    "<br><b>Notes:</b><br>"
    "<ul style='margin-top: 2px; margin-bottom: 0;'>"
    "<li>X, Y, Z columns are optional (enable 3D visualization)</li>"
    "<li>Forces and moments are interleaved per mode</li>"
    "</ul>"
)

FORCE_MOMENT_FILE_PATH = (
    "Path to the currently loaded element nodal forces &amp; moments file."
)

FORCE_MOMENT_OUTPUT_CHECKBOX = (
    "<b>Element Nodal Forces &amp; Moments (Output)</b><br>"
    "<hr>"
    "Computes element nodal force and moment outputs for the selected solve.<br><br>"
    "<b>Important:</b> This output is exclusive.<br>"
    "When selected, other output types are automatically disabled to prevent mixed visualization states.<br><br>"
    "Time History Mode can still be enabled; only output type mixing is restricted."
)

SKIP_MODES_LABEL = (
    "<b>Skip First N Modes</b><br>"
    "<hr>"
    "Excludes the first N modes from the transient superposition.<br><br>"
    "<b>Typical use case:</b><br>"
    "Skipping rigid-body modes (modes 1&ndash;6 in free-free analyses) "
    "or low-frequency modes not relevant to the response."
)

SKIP_MODES_COMBO = (
    "Number of leading modes to skip.<br><br>"
    "Set to 0 to use all available modes.<br>"
    "Range is populated from the loaded data file."
)

SKIP_LAST_MODES_LABEL = (
    "<b>Skip Last N Modes</b><br>"
    "<hr>"
    "Excludes the final N modes from the transient superposition.<br><br>"
    "<b>Typical use case:</b><br>"
    "Ignoring highest-frequency modes that are outside the analysis band "
    "or contain noisy content."
)

SKIP_LAST_MODES_COMBO = (
    "Number of trailing modes to skip.<br><br>"
    "Set to 0 to keep all trailing modes.<br>"
    "Range is populated from the loaded data file."
)

# =============================================================================
# Plasticity Options Section
# =============================================================================

PLASTICITY_DIAG_CHECKBOX = (
    "<b>Plasticity Diagnostics Overlay</b><br>"
    "<hr>"
    "Plots per-step &Delta;&epsilon;<sub>p</sub> and cumulative "
    "&epsilon;<sub>p</sub> on a secondary axis in Time History mode."
)

# =============================================================================
# Display Tab Section
# =============================================================================

DISPLAY_FILE_BUTTON = (
    "<b>Load Visualization File</b><br>"
    "<hr>"
    "Loads a CSV directly into the Display tab for standalone visualization "
    "without running a new solve.<br><br>"
    "<b>Format:</b>&nbsp;&nbsp;.csv&nbsp;&nbsp;(comma-separated)<br><br>"
    "<b>Expected columns:</b><br>"
    "<pre style='font-family: Consolas; font-size: 8pt; margin: 4px 0 0 0;'>"
    "X, Y, Z, NodeID, Result</pre>"
    "<br><b>Notes:</b><br>"
    "<ul style='margin-top: 2px; margin-bottom: 0;'>"
    "<li>X, Y, Z are required for 3D plotting</li>"
    "<li>NodeID is optional (enables node hover/picking labels)</li>"
    "<li>If multiple scalar columns exist, the first valid scalar is shown initially</li>"
    "</ul>"
)
