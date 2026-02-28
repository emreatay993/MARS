# FILE_INDEX

Generated: `2026-02-28 21:33:05`

## Scope

- Source root: `src/`
- Python modules indexed: `51`
- Total Python lines (physical): `16159`
- Line counts include blank lines and comments.
- Descriptions come from each module's top docstring (first sentence when possible).

## Package Totals

| Package | Modules | Lines |
| --- | ---: | ---: |
| `(root)` | 2 | 74 |
| `core` | 5 | 1189 |
| `file_io` | 4 | 1458 |
| `solver` | 3 | 2667 |
| `ui` | 32 | 10270 |
| `utils` | 5 | 501 |

## Module Index

| Path | Module | Lines | Classes | Functions | Description |
| --- | --- | ---: | ---: | ---: | --- |
| `src/__init__.py` | `src.__init__` | 7 | 0 | 0 | MARS: Modal Analysis Response Solver Modernised successor to the legacy MSUP Smart Solver for transient structural analysis. |
| `src/core/__init__.py` | `src.core.__init__` | 2 | 0 | 0 | Core business logic and computation modules. |
| `src/core/computation.py` | `src.core.computation` | 333 | 1 | 0 | Analysis engine wrapper for MARS (Modal Analysis Response Solver). |
| `src/core/data_models.py` | `src.core.data_models` | 284 | 10 | 0 | Data models for MARS (Modal Analysis Response Solver). |
| `src/core/plasticity.py` | `src.core.plasticity` | 238 | 1 | 7 | Utilities for preparing plasticity solver inputs. |
| `src/core/visualization.py` | `src.core.visualization` | 332 | 3 | 0 | Visualization management classes for MARS (Modal Analysis Response Solver). |
| `src/file_io/__init__.py` | `src.file_io.__init__` | 7 | 0 | 0 | File I/O operations for loading and exporting data. |
| `src/file_io/exporters.py` | `src.file_io.exporters` | 192 | 0 | 7 | Export helpers for MARS (Modal Analysis Response Solver). |
| `src/file_io/loaders.py` | `src.file_io.loaders` | 882 | 0 | 18 | File loading helpers for MARS (Modal Analysis Response Solver). |
| `src/file_io/validators.py` | `src.file_io.validators` | 377 | 1 | 7 | File validation helpers for MARS (Modal Analysis Response Solver). |
| `src/main.py` | `src.main` | 67 | 0 | 1 | Entry point for the MARS: Modal Analysis Response Solver application. |
| `src/solver/__init__.py` | `src.solver.__init__` | 2 | 0 | 0 | Solver engine for transient analysis computations. |
| `src/solver/engine.py` | `src.solver.engine` | 1945 | 2 | 0 | No module docstring. |
| `src/solver/plasticity_engine.py` | `src.solver.plasticity_engine` | 720 | 1 | 23 | Plasticity correction solvers for Neuber, Glinka, and IBG methods. |
| `src/ui/__init__.py` | `src.ui.__init__` | 2 | 0 | 0 | GUI components and user interface modules. |
| `src/ui/application_controller.py` | `src.ui.application_controller` | 259 | 1 | 0 | Main window for the MARS: Modal Analysis Response Solver application. |
| `src/ui/builders/__init__.py` | `src.ui.builders.__init__` | 2 | 0 | 0 | UI builders for constructing complex widget layouts. |
| `src/ui/builders/display_ui.py` | `src.ui.builders.display_ui` | 356 | 1 | 0 | UI Builder for the Display Tab. |
| `src/ui/builders/solver_ui.py` | `src.ui.builders.solver_ui` | 552 | 1 | 0 | UI Builder for the Solver Tab. |
| `src/ui/dialogs/__init__.py` | `src.ui.dialogs.__init__` | 5 | 0 | 0 | Dialog components for the UI package. |
| `src/ui/dialogs/material_profile_dialog.py` | `src.ui.dialogs.material_profile_dialog` | 470 | 1 | 0 | Material profile dialog providing editors for temperature-dependent properties. |
| `src/ui/display_tab.py` | `src.ui.display_tab` | 756 | 1 | 0 | Refactored Display Tab for 3D visualization. |
| `src/ui/handlers/analysis_handler.py` | `src.ui.handlers.analysis_handler` | 1584 | 2 | 0 | Analysis Handler for the SolverTab. |
| `src/ui/handlers/display_animation_handler.py` | `src.ui.handlers.display_animation_handler` | 567 | 1 | 0 | Animation lifecycle management for the Display tab. |
| `src/ui/handlers/display_base_handler.py` | `src.ui.handlers.display_base_handler` | 72 | 1 | 0 | Base utilities for Display tab handler classes. |
| `src/ui/handlers/display_export_handler.py` | `src.ui.handlers.display_export_handler` | 103 | 1 | 0 | Export-related functionality for the Display tab. |
| `src/ui/handlers/display_file_handler.py` | `src.ui.handlers.display_file_handler` | 104 | 1 | 0 | File loading logic for the Display tab. |
| `src/ui/handlers/display_interaction_handler.py` | `src.ui.handlers.display_interaction_handler` | 595 | 1 | 0 | Node interaction, picking, and hotspot analysis for the Display tab. |
| `src/ui/handlers/display_results_handler.py` | `src.ui.handlers.display_results_handler` | 581 | 1 | 0 | Helpers for applying solver output datasets to the Display tab. |
| `src/ui/handlers/display_state.py` | `src.ui.handlers.display_state` | 54 | 1 | 0 | Shared state container for the Display tab. |
| `src/ui/handlers/display_visualization_handler.py` | `src.ui.handlers.display_visualization_handler` | 411 | 1 | 0 | Visualization updates and rendering helpers for the Display tab. |
| `src/ui/handlers/file_handler.py` | `src.ui.handlers.file_handler` | 318 | 2 | 0 | File loading handler for the SolverTab. |
| `src/ui/handlers/log_handler.py` | `src.ui.handlers.log_handler` | 131 | 1 | 0 | Log Handler for the SolverTab. |
| `src/ui/handlers/navigator_handler.py` | `src.ui.handlers.navigator_handler` | 55 | 1 | 0 | Handles user interactions with the File Navigator dock, such as selecting project directories and opening files. |
| `src/ui/handlers/plotting_handler.py` | `src.ui.handlers.plotting_handler` | 64 | 1 | 0 | Handles plotting operations, such as loading Plotly figures into WebViews and managing temporary files. |
| `src/ui/handlers/settings_handler.py` | `src.ui.handlers.settings_handler` | 43 | 1 | 0 | Handles the application and management of advanced settings. |
| `src/ui/handlers/ui_state_handler.py` | `src.ui.handlers.ui_state_handler` | 550 | 1 | 0 | UI State Handler for the SolverTab. |
| `src/ui/solver_tab.py` | `src.ui.solver_tab` | 634 | 1 | 0 | Solver tab implementation for MARS (Modal Analysis Response Solver). |
| `src/ui/styles/__init__.py` | `src.ui.styles.__init__` | 6 | 0 | 0 | UI Styles module for MARS GUI. |
| `src/ui/styles/style_constants.py` | `src.ui.styles.style_constants` | 432 | 0 | 0 | Centralized style constants for MARS GUI. |
| `src/ui/tooltips.py` | `src.ui.tooltips` | 229 | 0 | 0 | Centralized tooltip text definitions for the MARS GUI. |
| `src/ui/widgets/__init__.py` | `src.ui.widgets.__init__` | 5 | 0 | 0 | Reusable UI widgets. |
| `src/ui/widgets/console.py` | `src.ui.widgets.console` | 97 | 1 | 0 | Console logger widget for MARS (Modal Analysis Response Solver). |
| `src/ui/widgets/dialogs.py` | `src.ui.widgets.dialogs` | 231 | 2 | 0 | Dialog widgets for MARS (Modal Analysis Response Solver). |
| `src/ui/widgets/editable_table.py` | `src.ui.widgets.editable_table` | 269 | 1 | 0 | Generic editable table widget with copy/paste helpers and trailing blank row. |
| `src/ui/widgets/plotting.py` | `src.ui.widgets.plotting` | 733 | 3 | 0 | Plotting widgets for MARS (Modal Analysis Response Solver). |
| `src/utils/__init__.py` | `src.utils.__init__` | 2 | 0 | 0 | Utility functions and helpers. |
| `src/utils/app_settings.py` | `src.utils.app_settings` | 113 | 0 | 6 | Persistent application settings helpers for MARS. |
| `src/utils/constants.py` | `src.utils.constants` | 56 | 0 | 0 | Global constants, configuration settings, and UI styles for MARS (Modal Analysis Response Solver). |
| `src/utils/file_utils.py` | `src.utils.file_utils` | 235 | 0 | 2 | File utility helpers for MARS (Modal Analysis Response Solver). |
| `src/utils/node_utils.py` | `src.utils.node_utils` | 95 | 0 | 2 | Node-related utility helpers for MARS (Modal Analysis Response Solver). |
