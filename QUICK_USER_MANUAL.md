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

## 3. Essential Workflow (10 Steps)

1. **Set Project Directory**: `File → Select Project Directory` or use Navigator.
2. **Load Modal Coordinates**: Solver tab → *Read Modal Coordinate File (.mcf)*.
3. **Load Modal Stress**: Solver tab → *Read Modal Stress File (.csv)*.
4. *(Optional)* **Load Steady-State**: Check *Include Steady-State* → pick `.txt`.
5. *(Optional)* **Load Deformations**: Check *Include Deformations* → pick `.csv`.
6. **Choose Outputs**: Select Von Mises / principal stress / deformation / velocity / acceleration / damage.
7. *(Optional)* **Time History Mode**: Check box, enter `NodeID`.
8. *(Optional)* **Set Fatigue Parameters**: Provide `A` and `m` when damage is enabled.
9. **Run Solver**: Click **SOLVE**; monitor console/progress bar.
10. **Inspect Results**:
    - Solver tab plots for time history outputs.
    - Switch to Display tab for 3D visualization, animation, and exports.

---

## 4. Display Tab Fast Facts

- **Load Mesh/Results**: Use *Open File* button or double-click exports in Navigator.
- **Adjust Scalars**: Use min/max spin boxes or percentile presets.
- **Deformation Scale**: Enter factor and press <kbd>Enter</kbd>; keep values modest (≤5) to avoid distortion.
- **Animation**: Set start/end indices, click **Play**, and optionally **Save Animation** (requires FFMPEG).
- **Pick Node**: Activate point picking via context menu; emits to solver tab for time history plotting.

---

## 5. Exports at a Glance

- **Time Point CSV**: *Save Time Point Results* on Display tab.
- **APDL IC Commands**: *Extract Initial Conditions* (velocity) and save to file.
- **Mesh CSV**: Use *Export Mesh* once scalars are active.
- **Animation Video**: *Save Animation* (mp4/avi).

Outputs default to the solver’s configured directory; update it before running if required.

---

## 6. Quick Troubleshooting

| Issue | Fix |
| --- | --- |
| `Invalid MCF file` | Re-export MCF ensuring `Time` header; delete stale `_unwrapped` file. |
| Solver stalls at 0% | Large dataset chunking – wait for progress or reduce outputs. |
| Blank Display | Load mesh or ensure exported CSV has `Result` column; reset camera. |
| Animation fails | Reduce frame count / adjust range; confirm deformation data exists. |

Use the console log for diagnostics and re-run after correcting inputs.

---

## 7. Need More Detail?

- **Full walkthrough**: `DETAILED_USER_MANUAL_20_Pages.md`
- **Algorithm & architecture deep dive**: `DETAILED_THEORY_MANUAL.md`

Keep your project-specific notes alongside `PROJECT_COMPLETE.md` or `ARCHITECTURE.md` for team-wide visibility.

