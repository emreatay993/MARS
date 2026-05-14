# Signal & Slot Reference - MARS (Modal Analysis Response Solver)

This guide maps the main Qt signal/slot connections in the refactored MARS codebase. Use it to trace how user actions, solver progress, and visualization updates propagate through the application layers.

---

## 1. Application-Level Wiring

`src/ui/application_controller.py` bridges the solver and display tabs. `_connect_signals()` establishes the cross-tab flow summarized below.

| Emitter (Signal) | Payload | Connected Slot | Purpose |
| --- | --- | --- | --- |
| `SolverTab.initial_data_loaded` | `object` tuple: `(time_values, node_coords, node_ids, deformation_loaded)` | `DisplayTab._setup_initial_view` | Seed the display tab once modal coordinates plus stress or force/moment node data are available. |
| `SolverTab.time_point_result_ready` | `(mesh, display_name, data_min, data_max)` | `DisplayTab.update_view_with_results` | Push a freshly computed selected-time dataset to the 3D view. |
| `SolverTab.animation_data_ready` | `object` animation payload or `None` | `DisplayTab.on_animation_data_ready` | Deliver precomputed animation frames or reset playback after cancellation/failure. |
| `SolverTab.animation_precomputation_failed` | `str` | `ApplicationController._on_animation_precomputation_failed` | Surface animation precomputation failures and re-enable playback UI. |
| `DisplayTab.node_picked_signal` | `int` node ID | `SolverTab.plot_history_for_node` | Request a node-specific time-history solve from a 3D pick/tracked-node action. |
| `DisplayTab.time_point_update_requested` | `(float time_value, dict options)` | `SolverTab.request_time_point_calculation` | Trigger selected-time recomputation from Display tab controls. |
| `DisplayTab.animation_precomputation_requested` | `dict` parameters | `SolverTab.request_animation_precomputation` | Ask the Solver tab to compute animation frames. |

---

## 2. Solver-Side Signals

**Defined in:** `src/ui/solver_tab.py`  
**Emitted by:** Solver tab and analysis handler

| Signal | Emitted From | When / Why | Primary Consumers |
| --- | --- | --- | --- |
| `initial_data_loaded` | `SolverTab._check_and_emit_initial_data()` | Modal coordinates are loaded and either stress data or force/moment data provides node coordinates. | `DisplayTab._setup_initial_view` via controller. |
| `time_point_result_ready` | `SolverAnalysisHandler.perform_time_point_calculation()` | A selected-time field has been reconstructed into a PyVista mesh. | `DisplayTab.update_view_with_results`. |
| `animation_data_ready` | `SolverAnalysisHandler.perform_animation_precomputation()` | Animation precomputation succeeds or is cancelled. | `DisplayTab.on_animation_data_ready`. |
| `animation_precomputation_failed` | `SolverAnalysisHandler.perform_animation_precomputation()` | Animation request validation or computation fails. | `ApplicationController._on_animation_precomputation_failed`. |

### Worker Signals

| Worker / Source | Signals | Connected Slots | Purpose |
| --- | --- | --- | --- |
| `SolverThread` in `src/ui/handlers/analysis_handler.py` | `finished(result, config)`, `error(str)` | `SolverAnalysisHandler._on_solve_complete`, `SolverAnalysisHandler._on_solve_error` | Run batch or time-history analysis without blocking the UI. |
| `MSUPSmartSolverTransient.progress_signal` in `src/solver/engine.py` | `int` percent | `SolverTab.update_progress_bar` | Report batch/force-moment progress to the Solver tab. |
| `FileLoaderThread` in `src/ui/handlers/file_handler.py` | `finished(object)`, `error(str)` | Coordinate, stress, deformation, and force/moment loader callbacks | Load large modal inputs in background threads. |

Steady-state stress and temperature field files are currently loaded synchronously by `SolverFileHandler`.

---

## 3. Display-Side Signals

**Defined in:** `src/ui/display_tab.py` and supporting handlers

| Signal | Emitted From | When / Why | Primary Consumers |
| --- | --- | --- | --- |
| `node_picked_signal` | `DisplayInteractionHandler` emit paths around node tracking and point picking | User selects, tracks, or picks a node in the PyVista view. | `SolverTab.plot_history_for_node`. |
| `time_point_update_requested` | `DisplayTab.update_time_point_results()` | Display controls request a specific time snapshot and output type. | `SolverTab.request_time_point_calculation`. |
| `animation_precomputation_requested` | `DisplayAnimationHandler.start_animation()` | Play is requested and frames must be computed before playback. | `SolverTab.request_animation_precomputation`. |

Display result selectors usually call handler methods directly rather than adding new Qt signals. `DisplayResultsHandler` resolves group/component/mode changes and delegates scalar updates to `DisplayVisualizationHandler`.

---

## 4. Button, Menu, and Control Routing

| Area | Trigger | Connected Slot / Flow | Purpose |
| --- | --- | --- | --- |
| App menu | File -> Select Project Directory | `NavigatorHandler.select_project_directory` | Change the active project/output root. |
| App menu | Settings -> Advanced | `ApplicationController.open_advanced_settings` | Edit precision, RAM allocation, and rendering/runtime settings. |
| Navigator dock | `tree_view.doubleClicked` | `NavigatorHandler.open_navigator_file` | Open a file from the project tree. |
| Solver file buttons | `.clicked` | `SolverFileHandler.select_coord_file`, `select_stress_file`, `select_deformations_file`, `select_force_moment_file`, `select_steady_state_file`, `select_temperature_field_file` | Select and load solver inputs. |
| Material profile button | `.clicked` | `SolverTab.open_material_profile_dialog` | Open temperature-dependent material profile editing. |
| Solver option checkboxes | `.toggled` | `SolverUIHandler` methods | Maintain visibility, mutual exclusivity, solve-state, and plot-option updates. |
| Solve button | `.clicked` | `SolverAnalysisHandler.solve()` | Central entry point for batch or time-history analysis. |
| Display file button | `.clicked` | `DisplayTab.load_file` -> `DisplayFileHandler.open_file_dialog` | Load an external visualization mesh/result file. |
| Display time buttons | `.clicked` | `update_time_point_results`, `save_time_point_results`, `extract_initial_conditions` | Compute, save, or export selected-time data. |
| Display animation buttons | `.clicked` | `start_animation`, `pause_animation`, `stop_animation`, `save_animation` | Control playback and animation export. |
| Display context menu | `customContextMenuRequested` | `DisplayInteractionHandler.show_context_menu` | Expose picking, hotspot, region, camera, and reset tools. |

---

## 5. Dialog and Widget Signals

| Component | Signal / Trigger | Connected Slot / Flow | Purpose |
| --- | --- | --- | --- |
| `HotspotDialog` (`src/ui/widgets/dialogs.py`) | `table_view.clicked` -> `node_selected(int)` | `DisplayInteractionHandler.highlight_and_focus_on_node` | Focus the selected hotspot node in the 3D view. |
| `AdvancedSettingsDialog` | Button box accepted/rejected | `accept` / `reject`; controller applies settings after accepted `exec_()` | Apply or discard advanced settings. |
| `MaterialProfileDialog` | Import/export/save/cancel/plastic controls | Profile JSON/CSV import-export, table editing, and `accept` / `reject` | Build the material profile used by plasticity corrections. |
| `EditableTableWidget` | `cellChanged` | Blank-row and data normalization helpers | Keep material/table editors paste-friendly. |
| Plot widgets | Copy shortcut, Matplotlib hover, legend pick events | Copy/hover/legend handlers | Support time-history plot inspection and export. |

---

## 6. Timers and Deferred UI Updates

| Source | Signal / Mechanism | Connected Slot / Flow | Purpose |
| --- | --- | --- | --- |
| Display animation timer | `QTimer.timeout` | `DisplayAnimationHandler.animate_frame` or `_animate_frame` | Advance animation frames during playback. |
| Console logger | `QTimer.timeout` | `Logger.flush_buffer` | Flush buffered console text into the UI. |
| Camera/layout refresh | `QTimer.singleShot` | Camera widget or splitter resize callbacks | Defer camera/layout updates until widgets have settled. |

---

## 7. Runtime Flows

### Initial Display Setup

1. Loader callbacks update `SolverTab` state.
2. `SolverTab._check_and_emit_initial_data()` emits one tuple object.
3. `DisplayTab._setup_initial_view()` builds the point mesh and enables time/animation controls.

### Batch Solve

1. `solve_button.clicked` calls `SolverAnalysisHandler.solve()`.
2. `SolverThread` runs `AnalysisEngine` and `MSUPSmartSolverTransient`.
3. `_on_solve_complete()` routes batch results through `_handle_batch_results()`.
4. `DisplayResultsHandler.apply_solver_results()` populates result selectors and scalar fields.

### Selected-Time Display

1. Display controls emit `time_point_update_requested`.
2. `SolverTab.request_time_point_calculation()` delegates to `SolverAnalysisHandler.perform_time_point_calculation()`.
3. Solver emits `time_point_result_ready`.
4. `DisplayTab.update_view_with_results()` updates mesh scalars, scalar range, and visualization state.

### Animation

1. `DisplayAnimationHandler.start_animation()` validates playback state and emits `animation_precomputation_requested`.
2. `SolverAnalysisHandler.perform_animation_precomputation()` computes requested frames.
3. Solver emits `animation_data_ready`.
4. `DisplayTab.on_animation_data_ready()` starts timer-driven playback.

### Node History from 3D

1. Context-menu actions enable point picking or tracked-node behavior.
2. `DisplayInteractionHandler` emits `node_picked_signal`.
3. `SolverTab.plot_history_for_node()` forces a node time-history solve and opens the plot dialog.

---

## 8. Visual Reference

```text
SolverTab -- initial_data_loaded ------------> DisplayTab._setup_initial_view
SolverTab -- time_point_result_ready --------> DisplayTab.update_view_with_results
SolverTab -- animation_data_ready -----------> DisplayTab.on_animation_data_ready
SolverTab -- animation_precomputation_failed -> ApplicationController warning/reset

DisplayTab -- node_picked_signal ------------> SolverTab.plot_history_for_node
DisplayTab -- time_point_update_requested ---> SolverTab.request_time_point_calculation
DisplayTab -- animation_precomputation_requested -> SolverTab.request_animation_precomputation

SolverThread -- finished/error --------------> SolverAnalysisHandler completion/error handlers
FileLoaderThread -- finished/error ----------> SolverFileHandler load callbacks
Solver Engine -- progress_signal ------------> SolverTab.update_progress_bar
QTimer.timeout ------------------------------> DisplayAnimationHandler frame advancement
```

---

## 9. Maintenance Tips

1. Add new cross-tab signals on the owning tab class, emit them from the relevant handler, and wire them in `ApplicationController`.
2. Keep complex slots in handler classes; tab methods should mostly translate UI state into handler calls.
3. Update this guide when a signal crosses tab boundaries, starts background work, or changes the source of solver/display data.
4. When adding a new Display result selector path, document whether it uses a Qt signal or direct handler calls.

For broader context, see `ARCHITECTURE.md` and the source module docstrings.
