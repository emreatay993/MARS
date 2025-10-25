## Display Tab Refactor Plan

Goal: restructure `src/ui/display_tab.py` to match the modular handler- and manager-based pattern already used by `solver_tab.py`, without altering behaviour or user experience.

### 1. Responsibility Mapping
- Catalogue method groups in `display_tab.py` (file loading, mesh/scalar management, animation lifecycle, point picking, hotspot analysis, exporting, UI toggles).
- Record their dependencies on shared managers (`VisualizationManager`, `AnimationManager`, `HotspotDetector`), Qt widgets, timers, and solver-tab signals to ensure each responsibility can be relocated safely.

### 2. Target Module Layout
- Sketch lightweight helpers under `ui/handlers/`, e.g.:
  - `display_file_handler.py`
  - `display_visualization_handler.py`
  - `display_animation_handler.py`
  - `display_interaction_handler.py`
  - `display_export_handler.py`
- Consider a shared state object (`DisplayState`) in `ui/utils` or within `ui/handlers` to hold mesh references, cached values, and timer instances while avoiding circular imports.

### 3. Handler Interfaces
- Define what data each handler requires (PyVista objects, widgets, tab-level signals) and which methods remain as slots on `DisplayTab`.
- Document callbacks/emitters so handlers can communicate back to the tab or out to `SolverTab` without tight coupling.

### 4. Extraction Sequence
- Introduce the shared state container and instantiate new handlers while leaving logic in place.
- Migrate responsibilities incrementally in this order, validating after each move:
  1. File loading & initial mesh creation.
  2. Visualization updates (scalar ranges, hover annotations, camera setup).
  3. Animation control (precomputation integration, play/pause/stop, frame updates, saving).
  4. Interaction features (point picking, hotspot workflows, context menu actions).
  5. Export operations (time point CSV, APDL initial conditions).
- Keep intermediate states functional to reduce regression risk.

### 5. Wiring & Imports
- Update `DisplayTab.__init__` to inject the new handlers and state.
- Adjust `_connect_signals` to delegate to handler methods where appropriate.
- Ensure `ApplicationController` and `SolverTab` continue calling the same public methods (maintain shims if necessary).

### 6. Verification Strategy
- Run available automated tests after each major extraction step.
- Perform manual smoke checks:
  - Load CSV data and verify scalar rendering.
  - Update time point results and confirm scalar bar updates.
  - Play/pause/stop animation and check frame stepping.
  - Pick nodes, verify time-history integration, hotspot dialog, and selection box.
  - Export results (CSV and APDL) and ensure files are produced without errors.
- Monitor logs/console outputs for regressions or uncaught exceptions.

### Progress Notes
- Steps 1–5 now mapped to concrete handler modules under `src/ui/handlers/`, with display exports, interactions, and animation state synchronised through `DisplayState`.
