# File Index – MARS: Modal Analysis Response Solver

This index documents the current `src/` implementation layout and line counts.
All counts below were refreshed from the live tree.

## Snapshot (Refreshed 2026-02-22)

- 51 Python files under `src/` (excluding `__pycache__`)
- 16,067 Python lines in `src/`
- UI layer: 32 Python files and 10,219 lines
- Solver + core numerics: 8 Python files and 3,822 lines
- File I/O layer: 4 Python files and 1,451 lines
- Utility layer: 5 Python files and 501 lines
- Additional non-Python files in `src/`: 85 (spec/lint config, material CSV, and currently checked-in output artifacts)

---

## Root Modules (2 files - 74 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/main.py` | 67 | Application entry point (Qt setup, persisted settings bootstrap, and launching `ApplicationController`) |
| `src/__init__.py` | 7 | Package marker |

---

## Core Package (5 files - 1,189 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/core/computation.py` | 333 | `AnalysisEngine` facade that configures `MSUPSmartSolverTransient`, handles mode filtering (skip first/last), and runs batch/time-history workflows |
| `src/core/data_models.py` | 284 | Dataclasses for modal/stress/deformation/force-moment/steady-state data, material profile, temperature field, solver config, and analysis result |
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

## Solver Package (3 files - 2,633 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/solver/engine.py` | 1911 | Main CPU solver (`MSUPSmartSolverTransient`): chunked stress/kinematics/force-moment processing, memmap pipelines, damage, and plasticity integration |
| `src/solver/plasticity_engine.py` | 720 | Neuber/Glinka/IBG correction kernels and material database model |
| `src/solver/__init__.py` | 2 | Package initializer |

---

## UI Shell (5 files - 1,880 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/application_controller.py` | 259 | Main window controller: menu/navigation setup, tab wiring, advanced settings dialog flow, and cross-tab signal routing |
| `src/ui/display_tab.py` | 756 | Display tab widget delegating rendering, interaction, animation, export, and result selection (including mode-skip passthrough) to handler classes |
| `src/ui/solver_tab.py` | 634 | Solver tab widget delegating loading, validation, solving, UI-state logic, and logging, including skip-first/skip-last mode controls |
| `src/ui/tooltips.py` | 229 | Centralized HTML tooltip text for solver controls, including skip-first/skip-last guidance and detailed steady-state format/ANSYS export notes |
| `src/ui/__init__.py` | 2 | Package marker |

---

## UI Builders (3 files - 910 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/builders/display_ui.py` | 356 | Builder for display layouts (visualization controls, result selectors, time-point tools, animation controls) |
| `src/ui/builders/solver_ui.py` | 552 | Builder for solver layouts (file inputs, outputs, skip-first/skip-last controls, fatigue/plasticity options, plots, console, progress controls) |
| `src/ui/builders/__init__.py` | 2 | Package initializer |

---

## UI Dialogs (2 files - 475 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/dialogs/material_profile_dialog.py` | 470 | Dialog for editing/importing/exporting temperature-dependent material properties and plastic curves |
| `src/ui/dialogs/__init__.py` | 5 | Package initializer |

---

## UI Handlers (15 files - 5,211 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/handlers/analysis_handler.py` | 1572 | Main solve orchestration: config validation (including skip-first/skip-last checks), threaded solve execution, batch/time-history handling, time-point calculation, animation precomputation, and display result-catalog building |
| `src/ui/handlers/display_animation_handler.py` | 567 | Animation playback lifecycle, frame updates, save/export, memory-estimation logic, and animation requests with mode-skip parameters |
| `src/ui/handlers/display_base_handler.py` | 72 | Base helper for syncing `DisplayTab` attributes with shared `DisplayState` |
| `src/ui/handlers/display_export_handler.py` | 103 | Export current display results to CSV and APDL initial conditions |
| `src/ui/handlers/display_file_handler.py` | 104 | Direct CSV visualization-file ingestion and scalar binding |
| `src/ui/handlers/display_interaction_handler.py` | 595 | Context menu, box selection, hotspot analysis, point picking, and tracked-node workflows (including camera-stable Go To Node behavior) |
| `src/ui/handlers/display_results_handler.py` | 574 | Result catalog normalization, selector combo management, and applying selected solver datasets to mesh/scalar bar |
| `src/ui/handlers/display_state.py` | 54 | Shared display runtime dataclass for mesh, camera, animation, interaction, and selector state |
| `src/ui/handlers/display_visualization_handler.py` | 411 | Render pipeline, camera-widget lifecycle, hover annotations, scalar range updates, and scalar-field application |
| `src/ui/handlers/file_handler.py` | 318 | Solver-tab file dialog and background loader orchestration (including `.mcf`/`.pch`) |
| `src/ui/handlers/log_handler.py` | 131 | Structured console logging for file loads and material/temperature updates |
| `src/ui/handlers/navigator_handler.py` | 54 | Project directory navigation and opening selected files |
| `src/ui/handlers/plotting_handler.py` | 63 | Plotly WebView rendering and temp-file cleanup |
| `src/ui/handlers/settings_handler.py` | 43 | Runtime application/persistence of advanced settings (RAM %, precision, dtype updates, Software OpenGL preference) |
| `src/ui/handlers/ui_state_handler.py` | 550 | Solver-tab checkbox/state coordination, skip-first/skip-last UI state handling, mutual exclusions, and plot update triggers |

---

## UI Styles (2 files - 438 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/styles/style_constants.py` | 432 | Centralized Qt stylesheet constants (menus, tabs, controls, dialogs, context menu, tooltip style) |
| `src/ui/styles/__init__.py` | 6 | Package initializer |

---

## UI Widgets (5 files - 1,305 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/widgets/console.py` | 67 | Buffered stdout-to-`QTextEdit` logger |
| `src/ui/widgets/dialogs.py` | 231 | Advanced settings dialog (RAM/precision/Software OpenGL) and hotspot result dialog |
| `src/ui/widgets/editable_table.py` | 269 | Spreadsheet-style editable table with copy/paste and blank-row behavior |
| `src/ui/widgets/plotting.py` | 733 | Matplotlib and Plotly plotting widgets for time-history and max/min-over-time results |
| `src/ui/widgets/__init__.py` | 5 | Package initializer |

---

## Utils Package (5 files - 501 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/utils/app_settings.py` | 113 | Persistent app settings load/save helpers (`~/.mars_settings.json`) and environment override parsing for Software OpenGL |
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

- 16 Python files, 1,856 lines total
- Unit tests: `tests/test_data_models.py`, `tests/test_file_utils.py`, `tests/test_node_utils.py`, `tests/test_plasticity.py`, `tests/test_validators.py`
- Display/solver regression tests: `tests/test_solver_single_node_time_axis.py`, `tests/test_display_handlers_regressions.py`, `tests/test_analysis_handler_skip_modes.py`
- Performance/tooling scripts under `tests/performance/`

---

## Totals

- **`src/` Python total**: 51 files, 16,067 lines
- **UI total**: 32 files, 10,219 lines
- **Core + solver total**: 8 files, 3,822 lines
- **I/O + utils total**: 9 files, 1,952 lines

Update this file whenever modules are added/removed so architectural docs stay trustworthy.
