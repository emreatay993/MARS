# QUICK USER MANUAL · MARS: Modal Analysis Response Solver

This guide condenses the end-to-end workflow for experienced analysts who need a refresher or rapid onboarding. Refer to `DETAILED_USER_MANUAL_20_Pages.md` for expanded explanations and theory.

---

## 1. Prerequisites

- Python 3.10+ with libraries from `requirements.txt`.
- Modal coordinate file (`.mcf`), modal stress CSV, optional deformation CSV, optional steady-state TXT.
- Optional CUDA-capable GPU if `utils/constants.py::IS_GPU_ACCELERATION_ENABLED` is set to `True`.

---

## 2. Launch Checklist

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.main
```

Confirm the main window shows **Main Window** and **Display** tabs, and the Navigator dock is visible.

---

## 3. Essential Workflow (11 Steps)

1. **Set Project Directory**: `File → Select Project Directory` or use Navigator.
2. **Load Modal Coordinates**: Solver tab → *Read Modal Coordinate File (.mcf)*.
3. **Load Modal Stress**: Solver tab → *Read Modal Stress File (.csv)*.
4. *(Optional)* **Load Steady-State**: Check *Include Steady-State* → pick `.txt`.
5. *(Optional)* **Load Deformations**: Check *Include Deformations* → pick `.csv`.
6. **Choose Outputs**: Select Von Mises / principal stress / deformation / velocity / acceleration / damage.
7. *(Optional)* **Skip Modes**: Set *Skip first n modes* to exclude rigid-body or erroneous modes (typically 0 or 6).
8. *(Optional)* **Enable Plasticity Correction**: Check box, select method (Neuber/Glinka), enter material profile and temperature field CSV.
9. *(Optional)* **Time History Mode**: Check box, enter `NodeID`.
10. *(Optional)* **Set Fatigue Parameters**: Provide `σ'f` and `b` when damage is enabled.
11. **Run Solver**: Click **SOLVE**; monitor console/progress bar.
12. **Inspect Results**:
    - Solver tab plots for time history outputs.
    - Switch to Display tab for 3D visualization, animation, and exports.

---

## 4. Advanced Settings (Performance Tuning)

Access via `Settings → Advanced`:

- **RAM Allocation (%)**: 10-95%, default 70%. Increase for large datasets; decrease if multitasking.
- **Solver Precision**: 
  - *Single* = faster, less memory (~7 digits accuracy)
  - *Double* = slower, 2× memory (~15 digits accuracy)
- **GPU Acceleration**: Enable if NVIDIA CUDA is installed for 2-10× speedup on large models.

Changes apply on next SOLVE. Use defaults unless experiencing performance issues.

---

## 5. Display Tab Fast Facts

- **Load Mesh/Results**: Use *Open File* button or double-click exports in Navigator.
- **Adjust Scalars**: Use min/max spin boxes.
- **Deformation Scale**: Enter factor and press <kbd>Enter</kbd>; keep values modest (≤5) to avoid distortion.
- **Deformation Display Mode**: Check "Show Absolute Deformations" for true displacement values; leave unchecked (default) for relative motion from animation start
- **Animation**: 
  - *Custom Time Step*: Uniform intervals
  - *Actual Data Time Steps*: Use "Every nth" to throttle frames (e.g., "Every 10th")
- **Pick Node**: Activate point picking via context menu; emits to solver tab for time history plotting.

---

## 6. Plasticity Correction Quick Reference

When enabled:
- **Methods**: Neuber (faster) or Glinka (conservative). IBG is experimental.
- **Temperature Field**: CSV with `NodeID, Temperature` columns matching material profile units.
- **Iteration Controls**: Max Iterations (default 60), Tolerance (default 1e-10).
- **Diagnostics**: Enable to plot Δεp and εp in Time History mode.
- **Output**: Produces `corrected_von_mises.csv` and `plastic_strain.csv`.

---

## 7. Exports at a Glance

- **Time Point CSV**: *Save Time Point Results* on Display tab.
- **APDL IC Commands**: *Extract Initial Conditions* (velocity) and save to file.
- **Mesh CSV**: Use *Export Mesh* once scalars are active.
- **Animation Video**: *Save Animation* (mp4/avi).

Outputs default to the solver's configured directory; update it before running if required.

---

## 8. Quick Troubleshooting

| Issue | Fix |
| --- | --- |
| `Invalid MCF file` | Re-export MCF ensuring `Time` header; delete stale `_unwrapped` file. |
| Solver stalls at 0% | Large dataset chunking – wait for progress or reduce outputs. |
| Blank Display | Load mesh or ensure exported CSV has `Result` column; reset camera. |
| Animation fails | Reduce frame count / adjust range; confirm deformation data exists. |
| GPU not used | Check `Settings → Advanced`; install CUDA toolkit or disable GPU. |
| Solver too slow | Increase RAM allocation, switch to Single precision, or enable GPU in Advanced Settings. |
| Temperature file error | Use CSV format with `NodeID, Temperature` columns (not tab-delimited .txt). |

Use the console log for diagnostics and re-run after correcting inputs.

---

## 9. Need More Detail?

- **Full walkthrough**: `DETAILED_USER_MANUAL_20_Pages.md`
- **Algorithm & architecture deep dive**: `DETAILED_THEORY_MANUAL.md`

Keep your project-specific notes alongside `PROJECT_COMPLETE.md` or `ARCHITECTURE.md` for team-wide visibility.

