# File Index – MARS: Modal Analysis Response Solver

This reference captures every Python module that ships with the refactored MARS codebase. Line counts were refreshed from the current `src/` tree to help you find the right file quickly.

## Snapshot (Current - v0.98)

- 51 Python files (including package initialisers) live under `src/`
- ~11,500 lines of implementation code
- UI layer spans 31 Python files (~7,300 lines) split across controller/tab views, builders, dialogs, 15 handler modules, widgets, and centralised style constants
- Automated tests: 5 unit-test modules plus 3 living guides in `tests/`
- Application resources: Icon system in `resources/icons/` with SVG source, PNG/ICO outputs, and generation script

---

## Root Modules (2 files – 29 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/main.py` | 24 | Application entry point bootstrapping Qt, DPI tweaks, PyTorch CUDA init, and the `ApplicationController` |
| `src/__init__.py` | 5 | Package marker |

---

## Core Package (5 files – 1,008 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/core/computation.py` | 278 | `AnalysisEngine` facade that configures the solver, applies mode skipping, and runs batch/time-history flows |
| `src/core/data_models.py` | 217 | Dataclasses for modal data, stresses, deformations, steady-state inputs, solver configuration, and results |
| `src/core/plasticity.py` | 188 | Plasticity correction algorithms (Neuber, Glinka) with temperature-dependent material interpolation |
| `src/core/visualization.py` | 324 | `VisualizationManager`, `AnimationManager`, and `HotspotDetector` helpers for PyVista operations |
| `src/core/__init__.py` | 1 | Package initialiser |

---

## File I/O Package (5 files – 1,086 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/file_io/exporters.py` | 172 | CSV exports, APDL initial-condition writer, and mesh/point-data exporters |
| `src/file_io/fea_utilities.py` | 33 | Legacy finite-element helper preserved for compatibility |
| `src/file_io/loaders.py` | 643 | Loaders that return typed data models after validation |
| `src/file_io/validators.py` | 233 | Validators for modal coordinate, stress, deformation, and steady-state inputs |
| `src/file_io/__init__.py` | 5 | Package initialiser |

---

## Solver Package (3 files – 1,858 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/solver/engine.py` | 1,274 | `MSUPSmartSolverTransient` implementation with stress reconstruction, principal stresses, GPU memory management, and damage calculation |
| `src/solver/plasticity_engine.py` | 583 | Plasticity correction engine integrating Neuber/Glinka methods with time-history stress data |
| `src/solver/__init__.py` | 1 | Package initialiser |

---

## UI Shell (4 files – 1,349 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/application_controller.py` | 218 | Main window controller managing menus, navigator dock, cross-tab signal wiring, and application icon loading |
| `src/ui/display_tab.py` | 620 | Display tab view constructing widgets and delegating to specialised handlers |
| `src/ui/solver_tab.py` | 510 | Solver tab view handling UI wiring, signal emission, and console integration |
| `src/ui/__init__.py` | 1 | Package docstring / marker |

---

## UI Builders (3 files – 786 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/builders/display_ui.py` | 316 | Builder for display tab layouts (file controls, PyVista panel, time-point, animation groups) |
| `src/ui/builders/solver_ui.py` | 469 | Builder for solver tab layouts (file inputs, output toggles, fatigue params, plots, progress, plasticity options) |
| `src/ui/builders/__init__.py` | 1 | Package initialiser |

---

## UI Dialogs (2 files – 411 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/dialogs/material_profile_dialog.py` | 408 | Temperature-dependent material curve entry dialog for plasticity correction |
| `src/ui/dialogs/__init__.py` | 3 | Package initialiser |

---

## UI Handlers (15 files – 3,274 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/handlers/analysis_handler.py` | 963 | Validates inputs, builds `SolverConfig`, orchestrates solves, logging, progress, and plotting |
| `src/ui/handlers/display_animation_handler.py` | 456 | Precomputes animation frames, manages timers, playback, and export hooks |
| `src/ui/handlers/display_base_handler.py` | 20 | Shared base utilities for display handlers (state sync helpers) |
| `src/ui/handlers/display_export_handler.py` | 86 | Save-as flows for CSV snapshots, APDL exports, and animation writers |
| `src/ui/handlers/display_file_handler.py` | 81 | CSV ingestion for the display tab with mesh creation and scalar binding |
| `src/ui/handlers/display_interaction_handler.py` | 496 | Hover annotations, hotspot detection, node picking with visual indicator, tracking, and camera controls |
| `src/ui/handlers/display_results_handler.py` | 91 | Loads solver-generated arrays (memmap) and applies them to the active mesh |
| `src/ui/handlers/display_state.py` | 45 | Dataclass capturing shared display state (mesh, camera, animation, selection, pick indicator) |
| `src/ui/handlers/display_visualization_handler.py` | 218 | PyVista rendering pipeline, scalar updates, deformation scaling, hover observers, deferred camera widget |
| `src/ui/handlers/file_handler.py` | 238 | Solver tab file dialogs, validation hand-off, and modal data lifecycle management |
| `src/ui/handlers/log_handler.py` | 102 | Routes solver text output to the embedded console widget |
| `src/ui/handlers/navigator_handler.py` | 44 | Project tree double-click handling and drag-and-drop integration |
| `src/ui/handlers/plotting_handler.py` | 53 | Shares matplotlib/plotly widgets across tabs and cleans up temp files |
| `src/ui/handlers/settings_handler.py` | 33 | Applies advanced solver settings (RAM usage, precision, GPU toggle) |
| `src/ui/handlers/ui_state_handler.py` | 348 | Manages solver tab checkbox logic, fatigue controls, and plot updates |

---

## UI Styles (2 files – 373 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/styles/style_constants.py` | 368 | Centralised Qt stylesheet strings and colour palette matching the legacy UI |
| `src/ui/styles/__init__.py` | 5 | Package initialiser |

---

## UI Widgets (5 files – 1,090 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/widgets/console.py` | 60 | QTextEdit-based logger with auto-scroll and clipboard support |
| `src/ui/widgets/dialogs.py` | 208 | Advanced settings dialog, hotspot dialog, and supporting UI helpers |
| `src/ui/widgets/editable_table.py` | 234 | Editable table widget for material profile data entry |
| `src/ui/widgets/plotting.py` | 585 | Matplotlib and Plotly widgets with interactive legends, tables, and resampling |
| `src/ui/widgets/__init__.py` | 3 | Package initialiser |

---

## Utils Package (5 files – 202 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/utils/constants.py` | 48 | Solver configuration, dtype selection, environment flags, and display defaults |
| `src/utils/file_utils.py` | 105 | File manipulation helpers (e.g., unwrap `.mcf` archives) |
| `src/utils/node_utils.py` | 22 | Node ID lookup helper |
| `src/utils/torch_setup.py` | 26 | PyTorch Windows CUDA DLL compatibility module |
| `src/utils/__init__.py` | 1 | Package initialiser |

---

## Test Assets

| File | Type | Description |
|------|------|-------------|
| `tests/test_data_models.py` | Unit test | Validates data model properties and helper methods |
| `tests/test_file_utils.py` | Unit test | Covers unwrap utilities and helper functions |
| `tests/test_node_utils.py` | Unit test | Exercises node lookup helpers |
| `tests/test_plasticity.py` | Unit test | Validates plasticity correction calculations |
| `tests/test_validators.py` | Unit test | Regression coverage for modal/stress/deformation validators |
| `tests/TESTING_GUIDE.md` | Documentation | End-to-end testing procedures |
| `tests/MANUAL_TESTING_CHECKLIST.md` | Documentation | ~250-point GUI regression checklist |
| `tests/BUGFIX_TESTING_CHECKLIST.md` | Documentation | Targeted validation for refactor bug fixes |
| `tests/__init__.py` | Package marker | Enables `pytest` discovery |

---

## Totals

- **Source totals**: 51 Python files, ~11,500 lines overall
- **UI footprint**: 31 files, ~7,300 lines (controllers/tabs, builders, dialogs, 15 handlers, widgets, styles)
- **Testing footprint**: 5 automated test modules plus 3 living guides/checklists

Keep this index handy whenever new files are added—updating the counts here keeps the documentation trustworthy.
