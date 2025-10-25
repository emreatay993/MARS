# DETAILED USER MANUAL · MARS: Modal Analysis Response Solver

> **Revision**: 2024-## · **Audience**: Structural analysts, FEA engineers, visualization specialists  
> **Scope**: Desktop application under `src/` – solver, visualization, data I/O, utilities, UI scaffold

---

## Page 1 – Welcome & Product Overview

MARS (Modal Analysis Response Solver) is a PyQt5 desktop application that transforms modal analysis data into actionable stress, deformation, and fatigue insights. The refactored architecture in `src/` separates solver logic, data models, UI widgets, and visualization managers to deliver a modular, maintainable workflow.

**Highlights**
- **Batch & node-specific analyses** driven by `core.computation.AnalysisEngine`.
- **GPU-aware transient solver** implemented in `solver.engine.MSUPSmartSolverTransient`, supporting PyTorch acceleration.
- **Immersive 3D visualization** powered by PyVista, managed via `core.visualization`.
- **Robust file handling** (`file_io` package) validating and loading MCF, CSV, and TXT data sources.
- **Guided UI** with separate Solver and Display tabs, reusable builders, and handler classes under `src/ui/`.

Use this manual to understand end-to-end workflows—from preparing input files, configuring solver runs, and interpreting results, through to troubleshooting and extending the application.

---

## Page 2 – Table of Contents

1. Welcome & Product Overview  
2. Table of Contents  
3. System Requirements & Dependencies  
4. Installing & Launching MARS  
5. Orientation: UI Structure & Navigation  
6. Preparing Input Data  
7. Loading Modal Coordinate Files  
8. Importing Stress, Steady-State, and Deformation Data  
9. Configuring Analyses & Output Requests  
10. Running Batch vs Time History Analyses  
11. Reviewing Console Output & Logs  
12. Visual Explorer: Display Tab Fundamentals  
13. Scalar Controls, Colormaps & Layout  
14. Animations, Timing, and Playback Options  
15. Hotspot Detection & Node Tracking  
16. Exporting Results (CSV, APDL, Mesh)  
17. Advanced Topics: Steady-State, Deformation Scaling, and Damage  
18. Performance Tuning & Resource Management  
19. Troubleshooting & Common Recovery Paths  
20. Appendix: Shortcuts, Settings, and Reference Tables

---

## Page 3 – System Requirements & Dependencies

**Operating Systems**  
- Windows 10/11 (primary testing environment)  
- macOS & Linux supported where PyQt5 and PyVista dependencies resolve

**Hardware**  
- Intel/AMD CPU with SSE2 support  
- 16 GB RAM recommended (solver auto-chunks via `solver.engine._estimate_chunk_size`)  
- Optional CUDA-capable NVIDIA GPU for acceleration (`utils.constants.IS_GPU_ACCELERATION_ENABLED`)

**Software Prerequisites**  
- Python 3.10+ (see `venv` or `requirements.txt`)  
- Required packages: PyQt5, PyVista, NumPy, Pandas, Numba, PyTorch, psutil, matplotlib, plotly  
- Optional: CUDA Toolkit for GPU acceleration

**File Formats Supported**
- Modal Coordinates: `.mcf` (wrapped legacy format, unwrapped by `utils.file_utils.unwrap_mcf_file`)  
- Modal Stress & Deformations: `.csv` (columnar data with node identifiers)  
- Steady-State Stress: `.txt` (tab-delimited reports)

Before launch, ensure firewall policies allow PyVista’s off-screen rendering and PyTorch GPU initialization if applicable.

---

## Page 4 – Installing & Launching MARS

1. **Clone or extract** the repository containing the `src/` folder.  
2. **Create/activate** a Python virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Launch the application**:
   ```bash
   python -m src.main
   ```
   The `main()` function (`src/main.py`) configures high-DPI scaling via `QApplication.setAttribute`, instantiates `ApplicationController`, and displays the maximized window.

4. **First run checks**:
   - Confirm the menu bar, Navigator dock, and tabs render with legacy styles from `ui/styles/style_constants.py`.
   - Verify GPU availability in the console (solver logs device selection).

If PyQt5 fails to initialize due to missing platform plugins, ensure `QT_QPA_PLATFORM_PLUGIN_PATH` is set or reinstall PyQt5.

---

## Page 5 – Orientation: UI Structure & Navigation

**Main Window (`ui/application_controller.py`)**
- **Menu Bar**: File (project directory selection), View (toggle Navigator), Settings (Advanced dialog placeholder).
- **Navigator Dock**: File browser backed by `QFileSystemModel`, filtered for `.csv`, `.mcf`, `.txt`.
- **Tab Widget**: Two primary tabs—
  - **Main Window (Solver Tab)**: Handles data ingestion and analysis execution.
  - **Display Tab**: Hosts the 3D visualization and export tooling.

**Handlers & Builders**
- `ui.builders.solver_ui` and `display_ui` construct widgets with consistent styling.
- `ui.handlers.*` modules own logic for file selection, analysis, UI state, plot maintenance, animations, exports, and logging.

**Console Integration**
- Solver tab redirects `stdout` to `ui.widgets.console.Logger` for live progress messages and warnings.

**Navigation Tips**
- Use the Navigator to double-click input files; `ui.handlers.navigator_handler.NavigatorHandler` routes them to the correct handler in the active tab.
- Dock widgets can be re-positioned; layouts persist per Qt session.

---

## Page 6 – Preparing Input Data

### Modal Coordinate Files (`.mcf`)
- Contain time history of generalized coordinates per mode.
- Must include a header line with `Time` as detected in `file_io.loaders.load_modal_coordinates`.
- Wrapped lines are automatically flattened; ensure file permissions allow temporary `_unwrapped` creation.

### Modal Stress CSV
- Mandatory columns: `NodeID`, stress tensors matching regex `sx_`, `sy_`, `sz_`, `sxy_`, `syz_`, `sxz_`.
- Optional columns: `X`, `Y`, `Z` for nodal coordinates.
- Validate structure using `file_io.validators.validate_modal_stress_file`.

### Modal Deformation CSV (Optional)
- Required columns: `NodeID`, `ux_`, `uy_`, `uz_` series.
- Enables deformation, velocity, acceleration outputs.

### Steady-State Stress TXT (Optional)
- Tab-delimited with columns `Node Number`, `SX (MPa)`, `SY (MPa)`, `SZ (MPa)`, `SXY (MPa)`, `SYZ (MPa)`, `SXZ (MPa)`.
- Used when `Include Steady-State Stress Field` is checked.

Ensure consistent NodeID ordering across files; mismatches trigger validation warnings. Back up large datasets—solver logs chunk processing progress but cannot recover corrupted inputs.

---

## Page 7 – Loading Modal Coordinate Files

1. Navigate to the **Solver Tab**.
2. Click **Read Modal Coordinate File (.mcf)**.  
   - A file dialog opens within the currently selected project directory (`SolverFileHandler.select_coord_file`).
3. On selection, the path field populates, and validation runs:
   - `validate_mcf_file` ensures the `Time` header and numeric data.
   - `load_modal_coordinates` unwraps to a temporary file, parses with Pandas, then instantiates `core.data_models.ModalData`.
4. Successful load updates solver state:
   - Flags `coord_loaded` to `True`.
   - Prepares skip mode combo box with available indices.

**Best Practices**
- Keep coordinate files under 1 GB to avoid disk thrashing.
- If validation fails, inspect the console for the exact error message returned by the validator.
- Delete stale `_unwrapped` files if the process is interrupted mid-load.

---

## Page 8 – Importing Stress, Steady-State, and Deformation Data

### Modal Stress
1. Click **Read Modal Stress File (.csv)**.
2. File handler loads into a `ModalStressData` object, capturing:
   - `node_ids`, component arrays (`modal_sx`, `modal_sy`, etc.), optional coordinates.
3. On success, solver enables stress-dependent checkboxes (Von Mises, principal stresses).

### Steady-State Stress (Optional)
1. Tick **Include Steady-State Stress Field (Optional)**.
2. Hidden controls appear; select the `.txt` file.
3. Data is validated and stored in `SteadyStateData`; `AnalysisEngine.create_solver` maps steady-state data to modal nodes.

### Modal Deformations (Optional)
1. Tick **Include Deformations (Optional)**.
2. Load `.csv` to populate `DeformationData`.
3. Enables deformation, velocity, acceleration outputs and animation of geometric deformation.

**Validation Feedback**
- Failures surface via modal dialogs (`QMessageBox`) and console entries.
- Use consistent node counts; mismatches trigger alignment errors downstream.

---

## Page 9 – Configuring Analyses & Output Requests

**Core Options**
- `Skip first n modes`: Visible after stress load; choose modes to omit (high-frequency trimming).
- Output checkboxes grouped into:
  - **Time History Mode** (single-node evaluations)
  - **Field Outputs** (von Mises, principal stresses, deformation, velocity, acceleration, damage index)

**Time History Mode**
- Toggles UI to accept a **Node ID** target (`node_line_edit`).
- Locks out mutually exclusive outputs (e.g., field visualizations) to maintain solver constraints.
- `SolverAnalysisHandler._validate_time_history_mode` ensures node availability.

**Fatigue Parameters**
- When `Damage Index / Potential Damage` is enabled, provide:
  - `fatigue_A` (strength coefficient)
  - `fatigue_m` (exponent)
- Inputs are validated by `QDoubleValidator` and runtime checks.

**Output Directory**
- Set via Advanced settings (future) or defaults to modal stress directory.
- `SolverConfig.output_directory` directs file exports.

---

## Page 10 – Running Batch vs Time History Analyses

1. Confirm required datasets are loaded (`coord_loaded`, `stress_loaded`).
2. Click **SOLVE**.
3. `SolverAnalysisHandler.solve` orchestrates:
   - Validation & config assembly (`_validate_and_build_config`).
   - Engine setup (`AnalysisEngine.configure_data`).
   - Solver creation and run (`create_solver`, `run_batch_analysis` or `run_single_node_analysis`).

**Batch Mode**
- Computes requested field outputs for all nodes.
- Writes CSV exports as configured.
- Progress bar updates via `MSUPSmartSolverTransient.progress_signal`.

**Time History Mode**
- Produces `AnalysisResult` with `time_values` and `stress_values`.
- Plots appear within Matplotlib/Plotly tabs (`ui.widgets.plotting`).
- Optionally triggers Display tab updates if visualization is linked.

**During Execution**
- Console logs stage transitions, memory chunk sizes, GPU/CPU selection.
- Canceling is manual (close app); ensure data integrity before re-running.

---

## Page 11 – Reviewing Console Output & Logs

**Logger Widget (`ui.widgets.console.Logger`)**
- Captures `stdout` and color-codes warnings/errors.
- Use copy/paste for archiving run logs.

**Progress Indicators**
- `QProgressBar` becomes visible during solver execution.
- Percentages derive from chunk completion events in `solver.engine.MSUPSmartSolverTransient`.

**Common Messages**
- Validation errors (input mismatch).
- Memory warnings (`_estimate_ram_required_per_iteration`).
- Completion summaries with export locations.

**Log Maintenance**
- Logs are session-based; export or screenshot important diagnostics before closing the app.
- For automated logging, redirect output to files via Python when launching (`python -m src.main > mars.log`).

---

## Page 12 – Visual Explorer: Display Tab Fundamentals

After analysis or by loading exported data, switch to the **Display** tab.

**Key Components**
- **File Controls**: Import mesh-ready CSV/VTK to create a PyVista `PolyData`.
- **Plotter**: Embedded PyVista render window, managed by `DisplayVisualizationHandler`.
- **Scalar Controls**: Min/max spin boxes, color bar adjustments, percentile range tools.
- **Deformation Controls**: Scale factor entry; validated to avoid distorted geometry.
- **Time Point Group**: Request calculations from the solver tab via signals.
- **Animation Group**: Playback controls with Qt-standard media icons.

`DisplayTab` wires these pieces together, coordinating managers:
- `VisualizationManager` handles mesh creation/updating.
- `AnimationManager` precomputes frames.
- `HotspotDetector` (within `core.visualization`) assists with threshold-based selections.

---

## Page 13 – Scalar Controls, Colormaps & Layout

**Scalar Range**
- Use `Scalar Min/Max` spin boxes or percentile presets to focus on relevant ranges (`VisualizationManager.compute_scalar_range`).
- Dynamic updates propagate to the plotter via `DisplayVisualizationHandler`.

**Point Size & Representation**
- Adjust `Point Size` for scatter-like views; switch plot representation (surface, point cloud) via context menu.

**Color Mapping**
- Choose from PyVista palettes; ensure scalar field naming consistency (default `Result` or analysis-specific label).
- Out-of-range clipping indicates data issues—verify exports or re-run analysis with correct outputs.

**Layout Tips**
- Use PyVista’s toolbar (orbit, pan, zoom).
- Reset camera if geometry appears distorted after deformation scaling.

---

## Page 14 – Animations, Timing, and Playback Options

**Precomputation Workflow**
1. Configure animation parameters (start, end, interval).
2. Click **Play** or request precomputation (`DisplayTab.animation_precomputation_requested`).
3. `AnimationManager.precompute_frames` caches scalar data and optional deformed coordinates.

**Control Panel**
- `Time Step Mode`: Choose actual solver steps or custom sub-sampling.
- `Actual Interval (ms)`: Control playback rate.
- `Save Animation`: Export MP4/AVI using PyVista’s writer (ensure FFMPEG installed).

**Deformation Inclusion**
- When deformation data exists, the animation manager stores per-frame coordinates for realistic playback.
- Validate scale via `Deformation Scale` before playing to avoid fold-over artifacts.

**Troubleshooting**
- If precomputation fails, `animation_precomputation_failed` slot displays a warning and resets buttons.
- Large datasets may require increasing RAM or reducing frame counts.

---

## Page 15 – Hotspot Detection & Node Tracking

**Hotspot Tools**
- `HotspotDetector` identifies regions exceeding thresholds (e.g., top 5% stress).
- Initiate from the context menu; adjustable parameters appear in the dialog.

**Node Picking**
- Activate picking mode to select nodes and emit `node_picked_signal`.
- Selected nodes can be:
  - Sent to solver tab for time history (`SolverTab.plot_history_for_node`).
  - Highlighted with markers and labels.

**Navigator Integration**
- `NavigatorHandler` enables double-clicking exported CSVs to auto-load in display tab, streamlining hotspot review.

**Tracking Persistence**
- Freeze tracked node positions to monitor relative deformation.
- Use `freeze_tracked_node` toggles to compare different time steps.

---

## Page 16 – Exporting Results (CSV, APDL, Mesh)

**Time Point Exports**
- `DisplayExportHandler` leverages `file_io.exporters.export_time_point_results`.
- Include `NodeID`, coordinates, and scalar columns.

**Animation Snapshots**
- Export precomputed frames to disk; choose CSV sequences or video.
- Use consistent naming conventions for downstream scripts.

**APDL Initial Conditions**
- `export_apdl_ic` writes velocity-based initial condition commands:
  ```python
  export_apdl_ic(node_ids, vel_x, vel_y, vel_z, "velocity.ic")
  ```
- Output matches the format generated by legacy `file_io.fea_utilities.generate_apdl_ic`.

**Mesh Exports**
- `export_mesh_to_csv` captures PyVista meshes with active scalar fields for external plotting or reporting.

**Best Practices**
- Store exports in project-specific directories.
- Check units before importing into FE solvers (default velocities in mm/s).

---

## Page 17 – Advanced Topics: Steady-State, Deformation Scaling, and Damage

**Steady-State Integration**
- When included, solver maps steady-state stresses to modal node IDs.
- Combined stresses enhance accuracy for load cases with static bias.

**Deformation Scaling**
- Applied through `VisualizationManager.apply_deformation`.
- Maintain moderate scale factors to preserve element shape comprehension.
- Use `Reset` functionality if geometry diverges.

**Velocity & Acceleration**
- Derived via `_vel_acc_from_disp` (Numba-accelerated central differences).
- Ensure uniform time step spacing; solver warns if irregularities detected.

**Damage Index**
- Requires fatigue parameters `A` and `m`.
- Solver computes signed von Mises to evaluate damage accumulation.
- Validate with material-specific S-N curves for engineering relevance.

---

## Page 18 – Performance Tuning & Resource Management

**Memory Management**
- Solver estimates per-node memory and chunk size to prevent RAM exhaustion.
- Adjust `DEFAULT_PRECISION` in `utils/constants.py` to `Single` for lighter memory footprint (accuracy trade-off).

**GPU Acceleration**
- Enable `IS_GPU_ACCELERATION_ENABLED = True`; ensure CUDA is available.
- PyTorch tensors automatically migrate to GPU via `torch.device`.

**Parallelism**
- NumPy uses all CPU cores (see `OPENBLAS_NUM_THREADS`).
- Numba kernels (`@njit(parallel=True)`) accelerate velocity/acceleration computations.

**Large Dataset Tips**
- Reduce animation frames via custom step mode.
- Skip initial modes if dominated by noise.
- Disable unused outputs to minimize memory requirements.

---

## Page 19 – Troubleshooting & Common Recovery Paths

| Symptom | Possible Cause | Resolution |
| --- | --- | --- |
| “Invalid MCF file” | Missing `Time` header or wrapped data corruption | Re-export MCF, verify header, use validator script. |
| Solver stalls near 0% | Huge datasets chunking slowly | Wait for chunk estimation; monitor RAM usage via Task Manager. |
| Display shows blank scene | No active scalar or mesh not loaded | Load mesh, ensure `Result` column populated, reset camera. |
| Animation precompute fails | Insufficient memory / invalid time range | Reduce frame count, verify start/end indices, check console. |
| Damage index zero everywhere | Fatigue parameters unset or null data | Re-enter `A`/`m`, confirm solver outputs include von Mises. |

**Recovery Checklist**
- Review console logs to pinpoint failing stage.
- Confirm file paths (relative vs absolute) especially when using Navigator.
- For persistent UI issues, delete Qt cache directories or reset application state.

---

## Page 20 – Appendix: Shortcuts, Settings, and Reference Tables

**Qt Shortcuts**
- `Ctrl+O`: Open file dialog within focused tab (standard).
- `Ctrl+W`: Close dialogs.
- `F1`: Reserved for future in-app help.

**Configuration Summary**
- Precision: `utils/constants.py::DEFAULT_PRECISION`
- GPU Flag: `utils/constants.py::IS_GPU_ACCELERATION_ENABLED`
- Default animation interval: `utils/constants.py::DEFAULT_ANIMATION_INTERVAL_MS`

**Key Modules & Responsibilities**
- `core/data_models.py`: Typed containers for modal, stress, deformation data.
- `core/computation.py`: High-level solver façade and result aggregation.
- `solver/engine.py`: Numba/PyTorch-accelerated transient solver kernel.
- `file_io/validators.py`: Input verification pipelines.
- `ui/handlers/*`: Glue logic connecting UI events to backend operations.
- `core/visualization.py`: Mesh management, animation, hotspot detection.

**Support & Maintenance**
- Document unresolved issues in `BUGFIX_*.md` files.
- Coordinate architecture changes with the plans in `ARCHITECTURE.md`.
- For deployment scripts, maintain parity with `START_HERE.md` guidance.

---

### End of Detailed User Manual

Continue to the Quick User Manual for a concise reference, or the Detailed Theory Manual for algorithmic underpinnings.

