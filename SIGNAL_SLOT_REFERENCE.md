# Signal & Slot Reference — MARS (Modal Analysis Response Solver)

This guide maps the key Qt signal/slot connections in the refactored MARS codebase. Use it to trace how user actions, solver progress, and visualization updates propagate through the application layers.

---

## 1. Application-Level Wiring

`src/ui/application_controller.py` bridges the solver and display tabs. When the main window is created, `_connect_signals()` establishes the cross-tab flow summarised below.

| Emitter (Signal) | Payload | Connected Slot | Purpose |
|------------------|---------|----------------|---------|
| `SolverTab.initial_data_loaded` | `(time_values, node_coords, node_ids, deformation_loaded)` | `DisplayTab._setup_initial_view` | Seed the display tab once modal/stress data are loaded. |
| `SolverTab.time_point_result_ready` | `(mesh, display_name, data_min, data_max)` | `DisplayTab.update_view_with_results` | Push a freshly computed time-point dataset to the 3D view. |
| `SolverTab.animation_data_ready` | `object` (precomputed animation or `None`) | `DisplayTab.on_animation_data_ready` | Deliver precomputed animation frames or a reset instruction. |
| `SolverTab.animation_precomputation_failed` | `str` (error message) | `ApplicationController._on_animation_precomputation_failed` | Surface animation precomputation failures and reset playback UI. |
| `DisplayTab.node_picked_signal` | `int` (node ID) | `SolverTab.plot_history_for_node` | Request a node-specific time history when a node is picked in 3D. |
| `DisplayTab.time_point_update_requested` | `(float time_value, dict options)` | `SolverTab.request_time_point_calculation` | Trigger recomputation of time-point data from display controls. |
| `DisplayTab.animation_precomputation_requested` | `dict` (parameters) | `SolverTab.request_animation_precomputation` | Ask the solver tab to launch animation precomputation. |

---

## 2. Solver-Side Signals

**Defined in:** `src/ui/solver_tab.py`  
**Emitted by:** Solver tab + analysis handler

| Signal | Emitted From | When / Why | Primary Consumers |
|--------|--------------|------------|-------------------|
| `initial_data_loaded` | `_check_and_emit_initial_data()` | Both modal and stress files are loaded. | `DisplayTab._setup_initial_view` (via controller). |
| `time_point_result_ready` | `SolverAnalysisHandler._handle_time_point_result()` | A time-point solve completes. | `DisplayTab.update_view_with_results`. |
| `animation_data_ready` | `SolverAnalysisHandler._handle_animation_results()` | Animation precomputation succeeds or is cancelled. | `DisplayTab.on_animation_data_ready`. |
| `animation_precomputation_failed` | `SolverAnalysisHandler._handle_animation_results()` | Animation precomputation raises an exception. | `ApplicationController._on_animation_precomputation_failed`. |

### Progress Reporting

* `MSUPSmartSolverTransient.progress_signal` (defined in `src/solver/engine.py`) emits `int` percentages during long-running batch operations.
* Connected in `SolverAnalysisHandler._execute_analysis()` to `SolverTab.update_progress_bar`, keeping the UI progress bar in sync with solver execution.

---

## 3. Display-Side Signals

**Defined in:** `src/ui/display_tab.py` and supporting handlers

| Signal | Emitted From | When / Why | Primary Consumers |
|--------|--------------|------------|-------------------|
| `node_picked_signal` | `DisplayInteractionHandler` (`emit` calls at lines 391 and 430) | User picks or selects a node within the PyVista view. | `SolverTab.plot_history_for_node`. |
| `time_point_update_requested` | `DisplayTab.update_time_point_results()` | Display controls request a specific time snapshot. | `SolverTab.request_time_point_calculation`. |
| `animation_precomputation_requested` | `DisplayAnimationHandler.request_precomputation()` | Play button demands precomputed frames. | `SolverTab.request_animation_precomputation`. |

Other display handlers feed results back to the tab without new signals (e.g. `DisplayResultsHandler.apply_solver_results` updates the mesh directly).

---

## 4. Dialog & Interaction Signals

| Component | Signal | Connected Slot | Purpose |
|-----------|--------|----------------|---------|
| `HotspotDialog` (`src/ui/widgets/dialogs.py`) | `node_selected(int)` | `DisplayInteractionHandler.highlight_and_focus_on_node` | When a user double-clicks a hotspot table entry, focus that node in the 3D view. |

---

## 5. Button & Control Routing (Selected Highlights)

While most button/checkbox connections live inside `_connect_signals()` on `SolverTab` and `DisplayTab`, the heavy logic is delegated to handlers. Key examples:

| UI Control | Connected Slot | Description |
|------------|----------------|-------------|
| `SolverTab.solve_button.clicked` | `SolverAnalysisHandler.solve` | Central entry point for batch/time-history analysis. |
| Time-history checkboxes (solver tab) | `SolverUIHandler` methods | Maintain mutually exclusive selection logic and update preview plots. |
| Display playback buttons | `DisplayTab.start_animation / pause_animation / stop_animation` | Control playback based on animation state and handler-managed timers. |

Refer directly to `_connect_signals()` in each tab module for the complete list of widget-level wiring.

---

## 6. Visual Reference

```
SolverTab ──(initial_data_loaded)────▶ DisplayTab._setup_initial_view
    │                                      ▲
    │                                      │
    ├─(time_point_result_ready)────────────┘
    │
    ├─(animation_data_ready)──────────────▶ DisplayTab.on_animation_data_ready
    └─(animation_precomputation_failed)──▶ ApplicationController warning dialog

DisplayTab ──(node_picked_signal)────────▶ SolverTab.plot_history_for_node
          ├─(time_point_update_requested)▶ SolverTab.request_time_point_calculation
          └─(animation_precomputation_requested)▶ SolverTab.request_animation_precomputation

Solver Engine ──(progress_signal)───────▶ SolverTab.update_progress_bar
```

---

## 7. Maintenance Tips

1. **Add new signals close to the owning widget or handler.** Follow the existing pattern: define the signal on the owning class, emit it in handler logic, wire it in `ApplicationController` if it crosses tab boundaries.
2. **Document new cross-component flows here.** If you add a new signal or change the consumer, update this guide so other developers can trace the flow quickly.
3. **Prefer handler methods for complex slots.** Keep slots thin on the tab classes and delegate work to the appropriate handler to preserve separation of concerns.

For deeper architectural background, continue to reference `ARCHITECTURE.md` and the module docstrings.

