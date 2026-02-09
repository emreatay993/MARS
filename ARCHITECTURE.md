# MARS: Modal Analysis Response Solver - Architecture

## Overview

MARS is a PyQt5 desktop application for modal superposition post-processing with:
- Batch solve outputs (max/min and time-of-extrema fields),
- Single-node time-history outputs,
- 3D visualization and animation workflows,
- Optional plasticity correction paths (Neuber, Glinka, IBG),
- Optional force/moment and steady-state integration.

The implementation is centered in `src/` and uses a layered, handler-driven GUI architecture.

---

## Codebase Snapshot (`src/`)

- 50 Python files
- 15,356 Python lines
- UI stack: 32 files / 9,744 lines
- Core + solver stack: 8 files / 3,724 lines
- I/O + utilities: 8 files / 1,839 lines

Primary entrypoints:
- `src/main.py`
- `src/ui/application_controller.py`
- `src/ui/solver_tab.py`
- `src/ui/display_tab.py`

---

## Recent Updates (February 9, 2026)

- Single-node time-history outputs now return physical time values (seconds) when `solver.time_values` length matches output length; they fall back to sample indices only when lengths differ.
- Display time-point updates now merge `selected_time` entries into the existing result catalog instead of replacing it, so users can switch back to max/min/time-of modes after pressing **Update**.
- Display contour rendering now forces orthographic projection (`enable_parallel_projection` with VTK camera fallback), eliminating perspective distortion in engineering views.
- `MARS.spec` was hardened for executable packaging with explicit hidden imports, hook path, resources, icon wiring, and GUI-friendly flags (`console=False`, `upx=False`).

---

## Architecture Layers

### 1. Entry Layer
**File**: `src/main.py`

Responsibilities:
- Initializes `QApplication`,
- Enables high-DPI settings,
- Creates and shows `ApplicationController`.

### 2. Application Orchestration Layer
**File**: `src/ui/application_controller.py`

Responsibilities:
- Builds main window, menu bar, navigator dock, and tab container,
- Instantiates `SolverTab` and `DisplayTab`,
- Wires cross-tab signals and global handlers (`PlottingHandler`, `SettingsHandler`),
- Applies app-wide tooltip style and window icon.

Cross-tab signal contract:
- Solver -> Display:
  - `initial_data_loaded`
  - `time_point_result_ready`
  - `animation_data_ready`
  - `animation_precomputation_failed`
- Display -> Solver:
  - `node_picked_signal`
  - `time_point_update_requested`
  - `animation_precomputation_requested`

### 3. Solver Workbench Layer
**Files**: `src/ui/solver_tab.py`, `src/ui/builders/solver_ui.py`, `src/ui/handlers/*.py`

Responsibilities:
- Owns user inputs for analysis setup and output selection,
- Delegates file loading, UI state management, logging, and solve orchestration to dedicated handlers,
- Emits data/results for the display workflow.

Key collaborators:
- `SolverTabUIBuilder` (builds widgets/layout),
- `SolverFileHandler` (async file loading incl. `.mcf` and `.pch`),
- `SolverUIHandler` (checkbox/state rules and output gating),
- `SolverAnalysisHandler` (threaded solve, config validation, batch/time-history/time-point/animation precompute),
- `SolverLogHandler` (structured console logging).

### 4. Display Workbench Layer
**Files**: `src/ui/display_tab.py`, `src/ui/builders/display_ui.py`, `src/ui/handlers/display_*.py`

Responsibilities:
- Owns PyVista rendering surface and visualization controls,
- Handles CSV visualization loading, scalar selection, hotspot interaction, and animation playback/export,
- Consumes solver-emitted meshes and precomputed animation data.

Key design point:
- `DisplayState` (`src/ui/handlers/display_state.py`) is shared mutable state used by all display handlers.

Major display handlers:
- `display_visualization_handler.py`: render pipeline, scalar range, hover, camera widget lifecycle.
- `display_results_handler.py`: result catalog normalization + selector combo orchestration.
- `display_interaction_handler.py`: context menu, hotspots, pick/track node workflows.
- `display_animation_handler.py`: play/pause/stop/save animation and frame application.
- `display_export_handler.py`: CSV/APDL exports.
- `display_file_handler.py`: direct visualization CSV ingestion.

### 5. Domain Facade Layer
**Files**: `src/core/computation.py`, `src/core/data_models.py`, `src/core/plasticity.py`, `src/core/visualization.py`

Responsibilities:
- Provides typed data contracts (`ModalData`, `ModalStressData`, `DeformationData`, `ElementNodalForceMomentData`, `SolverConfig`, etc.),
- Wraps solver creation/execution via `AnalysisEngine`,
- Bridges UI material/temperature data to solver plasticity runtime context,
- Encapsulates visualization-domain operations (`VisualizationManager`, `AnimationManager`, `HotspotDetector`).

### 6. I/O Layer
**Files**: `src/file_io/loaders.py`, `src/file_io/validators.py`, `src/file_io/exporters.py`

Responsibilities:
- Validate and parse input files into typed models,
- Support multiple formats (`.mcf`, `.pch`, stress/deformation/force-moment CSV, steady-state TXT, temperature field TXT, material profile JSON),
- Export solver/display results to CSV and APDL, and export material profiles.

Notable loader behavior:
- Large-file progress support with adaptive throughput history cache.

### 7. Numerical Solver Layer
**Files**: `src/solver/engine.py`, `src/solver/plasticity_engine.py`

Responsibilities:
- High-throughput CPU transient processing (`MSUPSmartSolverTransient`),
- Chunked memory-aware batch processing using memmap intermediates,
- Stress, principal stress, deformation, velocity, acceleration, damage index, and force/moment result generation,
- Plasticity correction integration (Neuber/Glinka scalar and IBG tensor-history paths).

### 8. Utility/Presentation Support Layer
**Files**:
- `src/utils/constants.py`
- `src/utils/file_utils.py`
- `src/utils/node_utils.py`
- `src/ui/styles/style_constants.py`
- `src/ui/tooltips.py`
- `src/ui/widgets/*.py`
- `src/ui/dialogs/material_profile_dialog.py`

Responsibilities:
- Runtime constants and precision/RAM toggles,
- Node ID normalization/mapping,
- PCH parsing + MCF unwrapping,
- Central style and tooltip definitions,
- Reusable plotting/dialog/table widgets.

---

## Threading and Runtime State Model

### Background Threads

- `FileLoaderThread` (`src/ui/handlers/file_handler.py`)
  - Prevents UI freezing during heavy file reads.

- `SolverThread` (`src/ui/handlers/analysis_handler.py`)
  - Runs solve computations in background,
  - Emits `finished(result, config)` or `error`.

### Shared Display State

`DisplayState` centralizes mutable state used across display handlers:
- mesh/actor/camera references,
- animation timer and frame state,
- interaction artifacts (box widget, hotspot dialog, picked node markers),
- result catalog + current selector selection.

This avoids fragile cross-handler attribute drift and keeps update points explicit.

---

## Data Flow

### A) Batch Solve Flow

1. User configures outputs in `SolverTab`.
2. `SolverAnalysisHandler` validates inputs and builds `SolverConfig`.
3. `AnalysisEngine.create_solver()` instantiates `MSUPSmartSolverTransient`.
4. `MSUPSmartSolverTransient.process_results_in_batch()` computes results chunk-by-chunk.
5. Memmap intermediates are finalized to CSV outputs.
6. `SolverAnalysisHandler` builds a dataset catalog for display selectors.
7. `DisplayResultsHandler` loads/applies selected fields to current mesh.

### B) Single Node Time-History Flow

1. Node ID selected (manual entry or picked in display).
2. `SolverAnalysisHandler` runs `AnalysisEngine.run_single_node_analysis()`.
3. Solver returns `AnalysisResult` (+ optional plasticity metadata overlays).
4. `MatplotlibWidget` is updated in solver tab, optionally shown in popup.

### C) Display Time-Point Request Flow

1. Display tab emits `time_point_update_requested(selected_time, options)`.
2. Solver creates a temporary solver for the selected time (or local window for vel/acc).
3. Scalar field + optional deformation coordinates are computed.
4. Mesh is emitted via `time_point_result_ready`.
5. Display updates scalar controls and result selectors.

### D) Animation Precomputation Flow

1. Display tab emits animation request params.
2. Solver validates request + RAM estimate.
3. Temporary solver computes frame scalar arrays and optional deformed coordinates.
4. Precomputed payload is emitted to display.
5. Display animation handler drives playback with `QTimer` and updates mesh per frame.

---

## Output Artifact Model

Primary output mode for batch solves:
- memmap `.dat` intermediates per metric/component/mode,
- finalized `.csv` files for:
  - max/min over time,
  - time of max/min,
  - plasticity/corrected fields where enabled.

Display result selection is catalog-driven:
- `catalog[group][component][mode] -> {field_name, csv_filename, units, ...}`
- The catalog is used to populate group/component/mode comboboxes and resolve arrays on demand.

---

## Dependency Map (High-Level)

```
src/main.py
  -> ui/application_controller.py
      -> ui/solver_tab.py
          -> ui/builders/solver_ui.py
          -> ui/handlers/{file_handler,ui_state_handler,analysis_handler,log_handler}.py
          -> core/computation.py
          -> file_io/loaders.py
      -> ui/display_tab.py
          -> ui/builders/display_ui.py
          -> ui/handlers/display_*.py
          -> core/visualization.py
      -> ui/handlers/{plotting_handler,settings_handler,navigator_handler}.py

core/computation.py
  -> solver/engine.py
      -> solver/plasticity_engine.py
  -> core/plasticity.py

file_io/loaders.py
  -> file_io/validators.py
  -> core/data_models.py
  -> utils/file_utils.py
```

---

## Design Patterns in Use

- Builder Pattern:
  - `SolverTabUIBuilder`, `DisplayTabUIBuilder`
- Facade Pattern:
  - `AnalysisEngine` wraps solver complexity
- Handler/Coordinator Pattern:
  - UI behavior split across specialized handler modules
- Shared State Object Pattern:
  - `DisplayState` synchronizes display handler state
- DTO/Data Model Pattern:
  - Dataclasses in `core/data_models.py`

---

## Current Extension Points

### Add a New Output Metric

1. Add computation path in `src/solver/engine.py`.
2. Expose toggle/config in `src/core/data_models.py` (`SolverConfig`) and solver UI builder.
3. Wire validation/state rules in `src/ui/handlers/ui_state_handler.py` and `src/ui/handlers/analysis_handler.py`.
4. Add catalog entries in `SolverAnalysisHandler._build_display_dataset_catalog`.
5. Ensure display selector mapping includes the new field (`display_results_handler.py`).

### Add a New Input File Type

1. Add validator in `src/file_io/validators.py`.
2. Add loader in `src/file_io/loaders.py`.
3. Add datamodel in `src/core/data_models.py` (if needed).
4. Add UI wiring in solver builder/tab and `file_handler.py`.

### Add a New Display Interaction Tool

1. Implement behavior in `src/ui/handlers/display_interaction_handler.py`.
2. Register action in the context menu builder flow.
3. Persist any extra shared state in `DisplayState`.

---

## Notes

- `src/ui/handlers/` currently contains checked-in `.dat`/`.csv` output artifacts in addition to Python modules. These are runtime outputs and can be redirected to external output folders for cleaner source trees.
- Advanced settings (RAM %, precision) are runtime-applied via `SettingsHandler` and `utils.constants`.

---

**Document Version**: 1.5  
**Last Updated**: February 8, 2026  
**Status**: Current with live `src/` structure
