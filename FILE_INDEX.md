# File Index – MARS: Modal Analysis Response Solver

This reference lists every Python module and key testing asset that makes up the current codebase. It reflects the post-handler refactor captured in the `src/` directory.

## Snapshot (April 2026)

- 37 Python modules under `src/`
- 8,643 lines of Python code (`wc -l src/**/*.py`)
- UI layer spans 20 modules (6,063 lines) divided into controller, tabs, builders, handlers, styles, and widgets
- Automated test suite: 4 Python modules backed by 3 detailed testing guides

---

## Root Modules (2 files – 44 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/main.py` | 36 | Application entry point bootstrapping Qt and the main window |
| `src/__init__.py` | 8 | Package marker for the application namespace |

---

## Core Package (4 files – 750 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/core/computation.py` | 229 | High-level orchestration around `AnalysisEngine` |
| `src/core/data_models.py` | 186 | Structured data classes for solver configuration and results |
| `src/core/visualization.py` | 333 | Visualization, animation, and hotspot managers |
| `src/core/__init__.py` | 2 | Package initializer |

---

## File I/O Package (5 files – 571 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/file_io/exporters.py` | 158 | Result exporters (CSV, APDL, mesh snapshots) |
| `src/file_io/fea_utilities.py` | 40 | Legacy finite-element helpers retained for compatibility |
| `src/file_io/loaders.py` | 198 | Modal data loaders returning typed models |
| `src/file_io/validators.py` | 168 | Input validation for modal coordinate, stress, deformation, and steady-state files |
| `src/file_io/__init__.py` | 7 | Package initializer |

---

## UI Shell (4 files – 2,503 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/application_controller.py` | 212 | Top-level Qt `QMainWindow` orchestration and menu/navigation wiring |
| `src/ui/display_tab.py` | 1,822 | Display tab view logic, PyVista integration, animation control |
| `src/ui/solver_tab.py` | 467 | Solver tab view class delegating heavy logic to handlers |
| `src/ui/__init__.py` | 2 | Package initializer |

---

## UI Builders (3 files – 685 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/builders/display_ui.py` | 304 | Layout builder for the display/visualization tab |
| `src/ui/builders/solver_ui.py` | 379 | Layout builder for the solver tab |
| `src/ui/builders/__init__.py` | 2 | Package initializer |

---

## UI Handlers (7 files – 1,614 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/handlers/analysis_handler.py` | 916 | Executes analyses, builds solver configs, orchestrates logging, and channels results to the UI |
| `src/ui/handlers/file_handler.py` | 154 | Encapsulates file dialogs and modal data loading callbacks |
| `src/ui/handlers/log_handler.py` | 75 | Formats console output for solver operations |
| `src/ui/handlers/navigator_handler.py` | 54 | Handles project navigator tree interactions |
| `src/ui/handlers/plotting_handler.py` | 63 | Shares plotting widgets and routines across tabs |
| `src/ui/handlers/settings_handler.py` | 38 | Applies advanced solver settings to engine globals |
| `src/ui/handlers/ui_state_handler.py` | 314 | Manages checkbox state, visibility, and plot refresh logic |

---

## UI Styles (2 files – 424 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/styles/style_constants.py` | 418 | Centralized stylesheet strings matching the legacy PyQt look and feel |
| `src/ui/styles/__init__.py` | 6 | Package initializer |

---

## UI Widgets (4 files – 837 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/ui/widgets/console.py` | 66 | QTextEdit-based console widget |
| `src/ui/widgets/dialogs.py` | 221 | Advanced settings and hotspot dialogs |
| `src/ui/widgets/plotting.py` | 548 | Matplotlib and Plotly helper widgets |
| `src/ui/widgets/__init__.py` | 2 | Package initializer |

---

## Utils Package (4 files – 202 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/utils/constants.py` | 64 | Global configuration values and runtime toggles |
| `src/utils/file_utils.py` | 109 | File manipulation helpers (e.g., unwrap `.mcf`) |
| `src/utils/node_utils.py` | 27 | Node lookup helpers |
| `src/utils/__init__.py` | 2 | Package initializer |

---

## Solver Package (2 files – 1,013 lines)

| File | Lines | Description |
|------|-------|-------------|
| `src/solver/engine.py` | 1,011 | Modal analysis engine (thinly wrapped legacy solver) |
| `src/solver/__init__.py` | 2 | Package initializer |

---

## Test Assets

| File | Type | Description |
|------|------|-------------|
| `tests/test_data_models.py` | Unit test | Validates core data model behaviour |
| `tests/test_file_utils.py` | Unit test | Covers utility helpers for file transformations |
| `tests/test_node_utils.py` | Unit test | Exercises node lookup helpers |
| `tests/test_validators.py` | Unit test | Regression coverage for file validators |
| `tests/TESTING_GUIDE.md` | Documentation | End-to-end testing procedures |
| `tests/MANUAL_TESTING_CHECKLIST.md` | Documentation | ~250-point GUI regression checklist |
| `tests/BUGFIX_TESTING_CHECKLIST.md` | Documentation | Targeted validation for post-refactor fixes |
| `tests/__init__.py` | Package marker | Allows `pytest` discovery within the directory |

---

## Totals

- **Source totals**: 37 Python files, 8,643 lines
- **UI footprint**: 20 modules, 6,063 lines (tabs + builders + handlers + styles + widgets)
- **Testing footprint**: 4 automated test files + 3 living checklists

This index will remain the source of truth for module counts whenever new files are added to `src/`.
