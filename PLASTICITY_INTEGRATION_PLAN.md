# Plasticity Correction Integration Plan

This document captures the detailed plan for integrating the new plasticity correction engine into the MARS codebase while respecting the existing modular architecture.

---

## 1. Goals
- Support Neuber, Glinka, and Incremental Buczynski–Glinka (IBG) corrections using the new solver logic located in `code_to_implement/plasticity_correction_engine.py`.
- Allow plasticity correction to participate in both batch computations and single-node (time history) solves without breaking current functionality.
- Maintain chunk-based processing for large datasets: when plasticity is active, each processed chunk is corrected immediately and the corrected values feed the usual min/max aggregation and UI export pipeline.
- Retain or improve UI/UX for configuration, validation, and result visualization of plasticity outputs.

---

## 2. Existing Architecture Touchpoints

| Area | Location | Interaction Notes |
| ---- | -------- | ----------------- |
| Solver core | `src/solver/engine.py` | Handles chunked stress processing, kinematics, and min/max aggregation. |
| Analysis facade | `src/core/computation.py` | Instantiates `MSUPSmartSolverTransient`, runs batch/time history solves. |
| UI orchestration | `src/ui/solver_tab.py`, `src/ui/handlers/analysis_handler.py` | Builds `SolverConfig`, triggers solves, routes results to plots/UI. |
| Data models | `src/core/data_models.py` | Defines modal/steady-state data containers and `SolverConfig`. |
| Material profile & temperature field inputs | `src/ui/dialogs/material_profile_dialog.py`, `src/file_io/loaders.py` | Already provide curated `MaterialProfileData` and `TemperatureFieldData`. |
| Display tab | `src/ui/display_tab.py`, handler suite | Consumes solver outputs via memmaps (`display_results_handler`). |

---

## 3. New Plasticity Pipeline Overview

1. **Module relocation & API surface**
   - Move `code_to_implement/plasticity_correction_engine.py` into `src/solver/plasticity_engine.py` (or `src/solver/plasticity/__init__.py` + helpers).
   - Strip CLI-only code; expose functions/classes that:
     - Build `MaterialDB` from numpy arrays.
     - Run Neuber/Glinka on vectors (`solve_neuber_batch`, `solve_glinka_batch`).
     - Run IBG on tensor histories (`solve_ibg_history`).
   - Ensure optional `numba` usage follows repo patterns (fallback if unavailable).

2. **Configuration & data conversion**
   - Extend `core/data_models.py` with a `PlasticityConfig` dataclass storing:
     - `enabled`, `method`, `max_iterations`, `tolerance`.
     - `material_profile: MaterialProfileData`.
     - Temperature handling (`temperature_field: Optional[TemperatureFieldData]`, `default_temperature`).
   - Introduce `core/plasticity.py` with utilities to:
     - Convert `MaterialProfileData` into the blended array representation required by `MaterialDB`.
     - Map temperature data to solver node ordering, with interpolation/default fallbacks.
     - Prepare per-node stress inputs (e.g., von Mises) and capture outputs into numpy arrays or memmaps.

3. **UI validation & configuration assembly**
   - Update `SolverAnalysisHandler._validate_and_build_config` (`src/ui/handlers/analysis_handler.py`) to:
     - Create and attach a `PlasticityConfig` when the plasticity checkbox is enabled.
     - Enforce that Von Mises output is selected whenever plasticity is active (already partially enforced via UI handler).
     - Validate required artifacts per method:
       - Neuber/Glinka: needs material profile + temperature data (or explicit default temperature).
       - IBG: allowed only in time history mode; must ensure deformation data (tensor inputs) available or derived.
     - Surface actionable warnings/errors through the console and dialogs.
   - Keep iteration/tolerance warnings in `SolverUIHandler` (`src/ui/handlers/ui_state_handler.py`) but make them configurable via the new config.

4. **Solver integration (chunk workflow)**
   - Inside `MSUPSmartSolverTransient.process_results_in_batch` (`src/solver/engine.py`):
     - After `_process_stress_chunk` computes von Mises/principal stresses for a node batch, detect whether plasticity is enabled.
     - Prepare the elastic input vector(s) for the selected method (e.g., maximum von Mises per node, or time history arrays if the design needs step-wise data).
     - Call the plasticity engine immediately for that chunk.
     - Replace or augment memmap writes (`max_memmap`, etc.) with **corrected** values so downstream logic remains unchanged.
     - Maintain additional memmaps/arrays for plastic strain if needed (`plastic_strain.dat`).
   - Ensure chunk-level processing respects memory constraints by:
     - Reusing existing batch iteration boundaries.
     - Avoiding full-history allocations when unnecessary (e.g., Neuber/Glinka operate on single scalar per node).
   - Record corrected max/min values and corresponding timestamps just like the elastic case.

5. **Single-node / time history integration**
   - In `AnalysisEngine.run_single_node_analysis`:
     - When plasticity is active and IBG selected, grab the node’s stress tensor history (`compute_normal_stresses_for_a_single_node`).
     - Feed the history to the IBG routine to produce corrected tensors, von Mises history, and cumulative plastic strain.
     - Return the corrected history within `AnalysisResult`, possibly via `metadata` (`{"elastic_history": ..., "plastic_strain": ...}`) so the plotting widget can overlay both if desired.

6. **Result propagation to UI**
   - Extend `_handle_batch_results` (`src/ui/handlers/analysis_handler.py`) to add dataset options for corrected stress/strain outputs (e.g., `("Corrected SVM (MPa)", "corrected_von_mises.dat")`, `("Plastic Strain", "plastic_strain.dat")`).
   - Update `_handle_time_history_result` to:
     - Plot corrected stress traces and optionally overlay elastic vs corrected if metadata present.
     - Display plastic strain history when available (could use additional y-axis or console summary).
   - Adjust `MatplotlibWidget.update_plot` (`src/ui/widgets/plotting.py`) to accept optional plasticity series/legend.
   - Ensure `DisplayResultsHandler.apply_solver_results` (`src/ui/handlers/display_results_handler.py`) recognises new dataset names and loads corresponding memmaps correctly.

7. **Exports & logging**
   - If the legacy solver exports CSV summaries, add corrected values (max corrected stress, time of occurrence, plastic strain) to match existing UX.
   - Update console logs to note when plasticity correction is applied per chunk, including iteration stats if helpful.

8. **Testing & QA**
   - Add unit tests in `tests/` for:
     - Material profile conversion (`core/plasticity.py`).
     - Temperature-field mapping and edge cases (missing nodes, default temperature usage).
     - Plasticity config validation logic (invalid combinations, missing inputs).
   - Create smoke tests (possibly in `tests/integration/`) that run the plasticity engine on small synthetic datasets to ensure chunk integration works.
   - If feasible, add regression comparisons for elastic vs corrected extrema to confirm memmap outputs are updated.

---

## 4. Detailed Chunk Workflow (High-Level Pseudocode)

```python
# inside MSUPSmartSolverTransient.process_results_in_batch(...)
for nodes in chunked_range:
    actual_stresses = self.compute_normal_stresses(chunk)
    self._process_stress_chunk(... elastic calculations ...)

    if plasticity_active:
        # Choose inputs based on method
        if method in ("neuber", "glinka"):
            vm_elastic = np.max(sigma_vm, axis=1)  # or other scalar per node
            corrected_vm, plastic_strain = plasticity_engine.correct_batch(vm_elastic, nodal_temperatures)
            write corrected_vm/plastic_strain to memmaps
            update max_over_time_svm with corrected_vm
        elif method == "ibg":
            # For batch mode, IBG may not run unless we precompute histories; optional extension.
            pass

    self._process_kinematics_chunk(...)
    clean up, update progress, continue
```

Key property: corrected results are recorded *before* min/max aggregation finalization, so existing UI/export pathways remain valid.

---

## 5. Implementation Phases

1. **Module preparation**
   - Relocate plasticity engine file and expose clean API.
   - Add new core utilities (`core/plasticity.py`).
2. **Data model & config updates**
   - Extend `SolverConfig` and introduce `PlasticityConfig`.
   - Implement UI validation + config assembly.
3. **Solver integration**
   - Wire chunk-level plasticity calls inside `MSUPSmartSolverTransient`.
   - Support single-node IBG corrections.
4. **UI & display updates**
   - Update handlers, plotting widgets, and display dataset ingestion.
5. **Testing & documentation**
   - Write or update relevant unit/integration tests.
   - Refresh architecture docs (e.g., reference this plan / new pipeline summary).

Deliverables can be merged incrementally, but maintaining the above order minimises churn and makes partial reviews practical.

---

## 6. Open Questions / Assumptions
- **IBG in batch mode**: the initial implementation will prioritise time-history (single-node) scenarios; extending IBG to batch mode may require additional storage and is out of scope unless deemed critical.
- **Temperature defaults**: plan assumes we can fall back to a constant temperature (from material profile or UI field) if a temperature file is not provided.
- **GPU/Numba compatibility**: plasticity routines rely on NumPy/Numba. Need to confirm compatibility with existing GPU acceleration flags (probably run on CPU only).

---

## Appendix A – Plasticity Output Inventory

| Scenario | Artifact | Purpose | Display/Export Availability |
| -------- | -------- | ------- | --------------------------- |
| **Batch analysis** | `corrected_von_mises.dat` (memmap) + `time_of_max_corrected_von_mises.dat` | Stores node-wise peak corrected von Mises stress and the time of occurrence. | Display tab “Corrected SVM (MPa)” scalar; summary CSV alongside existing elastic extrema. |
| | `plastic_strain.dat` | Cumulative plastic strain per node (scalar from Neuber/Glinka). | Display tab “Plastic Strain” scalar; optional CSV column in batch exports; console summary of global max. |
| | `corrected_von_mises.csv` (if CSV export enabled) | Human-readable export mirroring memmap values. | Saved in output directory when batch CSV flag is active. |
| **Time history (single node, IBG)** | Corrected von Mises history (stored in `AnalysisResult.stress_values` when plasticity active). | Populates time-history plot; labelled as “Corrected von Mises (MPa)”. | Plot overlay vs elastic; can be exported via plot widget save. |
| | Elastic von Mises history (metadata) | Allows overlay comparison when requested. | Optional toggle in time-history plot; remains in metadata for future exports. |
| | Plastic strain history (metadata → table/secondary axis) | Shows cumulative plastic strain evolution. | Displayed in plot table and/or secondary y-axis; exported with time-history save. |
| | Corrected tensor components (metadata arrays) | Future-proofing for tensor exports (IBG). | Not visualised by default; available for dedicated export dialog if added later. |

*Notes:*
- Elastic datasets remain untouched and continue to drive existing UI elements; corrected datasets are added in parallel so users can compare both.
- Non-stress outputs (deformation, velocity, damage index) are not plasticity-corrected in this iteration.
- Naming conventions mirror current memmap files to keep the display/export handlers simple.

---

This plan will be the reference while implementing plasticity correction into MARS. Any deviations or discoveries during development will be appended here for traceability.
