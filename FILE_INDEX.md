# File Index – MARS: Modal Analysis Response Solver

This index documents the current `src/` implementation layout and line counts.
All counts below were refreshed from the live tree.

## Snapshot (Current - v0.98)

- 50 Python files under `src/` (excluding `__pycache__`)
- 15,320 Python lines in `src/`
- UI layer: 32 Python files and 9,708 lines
- Solver + core numerics: 8 Python files and 3,724 lines
- File I/O layer: 4 Python files and 1,451 lines
- Utility layer: 4 Python files and 388 lines
- Additional non-Python files in `src/`: 85 (spec/lint config, material CSV, and currently checked-in output artifacts)

---

## Root Modules (2 files - 49 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/main.py` | 42 | Application entry point (Qt setup, DPI settings, and launching `ApplicationController`) |
| `src/__init__.py` | 7 | Package marker |

---

## Core Package (5 files - 1,186 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/core/computation.py` | 332 | `AnalysisEngine` facade that configures `MSUPSmartSolverTransient`, handles mode filtering, and runs batch/time-history workflows |
| `src/core/data_models.py` | 282 | Dataclasses for modal/stress/deformation/force-moment/steady-state data, material profile, temperature field, solver config, and analysis result |
| `src/core/plasticity.py` | 238 | Converts material profile + temperature field inputs into runtime plasticity data (`MaterialDB`) |
| `src/core/visualization.py` | 332 | `VisualizationManager`, `AnimationManager`, and `HotspotDetector` domain logic for display operations |
| `src/core/__init__.py` | 2 | Package initializer |

---

## File I/O Package (4 files - 1,451 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/file_io/exporters.py` | 192 | CSV/APDL export helpers plus material profile JSON export |
| `src/file_io/loaders.py` | 875 | Loaders for `.mcf`, `.pch`, stress/deformation/force-moment/steady-state files, temperature fields, and material profiles (with large-file progress/throughput tracking) |
| `src/file_io/validators.py` | 377 | Validation routines for all supported input formats including PCH and material-profile payloads |
| `src/file_io/__init__.py` | 7 | Package initializer |

---

## Solver Package (3 files - 2,538 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/solver/engine.py` | 1872 | Main CPU solver (`MSUPSmartSolverTransient`): chunked stress/kinematics/force-moment processing, memmap pipelines, damage, and plasticity integration |
| `src/solver/plasticity_engine.py` | 664 | Neuber/Glinka/IBG correction kernels and material database model |
| `src/solver/__init__.py` | 2 | Package initializer |

---

## UI Shell (5 files - 1,724 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/application_controller.py` | 237 | Main window controller: menu/navigation setup, tab wiring, and cross-tab signal routing |
| `src/ui/display_tab.py` | 682 | Display tab widget delegating rendering, interaction, animation, export, and result selection to handler classes |
| `src/ui/solver_tab.py` | 630 | Solver tab widget delegating loading, validation, solving, UI-state logic, and logging |
| `src/ui/tooltips.py` | 173 | Centralized HTML tooltip text for solver controls |
| `src/ui/__init__.py` | 2 | Package marker |

---

## UI Builders (3 files - 887 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/builders/display_ui.py` | 345 | Builder for display layouts (visualization controls, result selectors, time-point tools, animation controls) |
| `src/ui/builders/solver_ui.py` | 540 | Builder for solver layouts (file inputs, outputs, fatigue/plasticity options, plots, console, progress controls) |
| `src/ui/builders/__init__.py` | 2 | Package initializer |

---

## UI Dialogs (2 files - 475 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/dialogs/material_profile_dialog.py` | 470 | Dialog for editing/importing/exporting temperature-dependent material properties and plastic curves |
| `src/ui/dialogs/__init__.py` | 5 | Package initializer |

---

## UI Handlers (15 files - 4,906 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/handlers/analysis_handler.py` | 1521 | Main solve orchestration: config validation, threaded solve execution, batch/time-history handling, time-point calculation, animation precomputation, and display result-catalog building |
| `src/ui/handlers/display_animation_handler.py` | 565 | Animation playback lifecycle, frame updates, save/export, and memory-estimation logic |
| `src/ui/handlers/display_base_handler.py` | 26 | Base helper for syncing `DisplayTab` attributes with shared `DisplayState` |
| `src/ui/handlers/display_export_handler.py` | 103 | Export current display results to CSV and APDL initial conditions |
| `src/ui/handlers/display_file_handler.py` | 104 | Direct CSV visualization-file ingestion and scalar binding |
| `src/ui/handlers/display_interaction_handler.py` | 594 | Context menu, box selection, hotspot analysis, point picking, and tracked-node workflows |
| `src/ui/handlers/display_results_handler.py` | 574 | Result catalog normalization, selector combo management, and applying selected solver datasets to mesh/scalar bar |
| `src/ui/handlers/display_state.py` | 53 | Shared display runtime dataclass for mesh, camera, animation, interaction, and selector state |
| `src/ui/handlers/display_visualization_handler.py` | 270 | Render pipeline, camera-widget lifecycle, hover annotations, scalar range updates, and scalar-field application |
| `src/ui/handlers/file_handler.py` | 318 | Solver-tab file dialog and background loader orchestration (including `.mcf`/`.pch`) |
| `src/ui/handlers/log_handler.py` | 131 | Structured console logging for file loads and material/temperature updates |
| `src/ui/handlers/navigator_handler.py` | 54 | Project directory navigation and opening selected files |
| `src/ui/handlers/plotting_handler.py` | 63 | Plotly WebView rendering and temp-file cleanup |
| `src/ui/handlers/settings_handler.py` | 34 | Runtime application of advanced settings (RAM %, precision, dtype updates) |
| `src/ui/handlers/ui_state_handler.py` | 502 | Solver-tab checkbox/state coordination, mutual exclusions, and plot update triggers |

---

## UI Styles (2 files - 438 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/styles/style_constants.py` | 432 | Centralized Qt stylesheet constants (menus, tabs, controls, dialogs, context menu, tooltip style) |
| `src/ui/styles/__init__.py` | 6 | Package initializer |

---

## UI Widgets (5 files - 1,272 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/widgets/console.py` | 64 | Buffered stdout-to-`QTextEdit` logger |
| `src/ui/widgets/dialogs.py` | 202 | Advanced settings and hotspot result dialogs |
| `src/ui/widgets/editable_table.py` | 269 | Spreadsheet-style editable table with copy/paste and blank-row behavior |
| `src/ui/widgets/plotting.py` | 732 | Matplotlib and Plotly plotting widgets for time-history and max/min-over-time results |
| `src/ui/widgets/__init__.py` | 5 | Package initializer |

---

## Utils Package (4 files - 388 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/utils/constants.py` | 56 | Global solver/runtime defaults and display constants |
| `src/utils/file_utils.py` | 235 | `.mcf` unwrapping and NASTRAN `.pch` modal-coordinate parsing |
| `src/utils/node_utils.py` | 95 | Robust node-id normalization and index lookup across mixed input formats |
| `src/utils/__init__.py` | 2 | Package initializer |

---

## Non-Python Files Inside `src/` (85 files)

Current tree includes:
- `src/MARS.spec`, `src/.pylintrc`, `src/youngs_modulus.csv`
- 82 `.csv`/`.dat` solver output artifacts currently under `src/ui/handlers/`

Note: those artifact files are runtime outputs and are typically better kept in a dedicated output directory outside source modules.

---

## Test Code Snapshot (`tests/`)

- 15 Python files, 1,560 lines total
- Unit tests: `tests/test_data_models.py`, `tests/test_file_utils.py`, `tests/test_node_utils.py`, `tests/test_plasticity.py`, `tests/test_validators.py`
- Display/solver regression tests: `tests/test_solver_single_node_time_axis.py`, `tests/test_display_handlers_regressions.py`
- Performance/tooling scripts under `tests/performance/`

---

## Totals

- **`src/` Python total**: 50 files, 15,320 lines
- **UI total**: 32 files, 9,708 lines
- **Core + solver total**: 8 files, 3,724 lines
- **I/O + utils total**: 8 files, 1,839 lines

Update this file whenever modules are added/removed so architectural docs stay trustworthy.
