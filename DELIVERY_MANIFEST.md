# 📦 Delivery Manifest — MARS: Modal Analysis Response Solver

**Project:** MARS (Modal Analysis Response Solver)  
**Version:** v0.95  
**Status:** ✅ Active Development

---

## Source Code

| Package / File           | Contents & Notes |
|--------------------------|------------------|
| `src/main.py`            | Qt entry point with high-DPI setup and `ApplicationController` launch |
| `src/ui/`                | `application_controller.py`, `solver_tab.py`, `display_tab.py`, builders, handlers, widgets, styles |
| `src/core/`              | `computation.py` (AnalysisEngine), `visualization.py` (managers), `data_models.py` |
| `src/file_io/`           | Validators, loaders, exporters, legacy FEA utilities |
| `src/utils/`             | Solver configuration constants and helper utilities (Qt styling lives in `ui/styles/`) |
| `src/solver/engine.py`   | Preserved `MSUPSmartSolverTransient` implementation |

Total Python files under `src/`: **45** (36 implementation modules + 9 package initialisers).

---

## Testing Assets

- `tests/test_validators.py`, `tests/test_data_models.py`, `tests/test_file_utils.py`, `tests/test_node_utils.py`
- `tests/TESTING_GUIDE.md` — automated and integration guidance
- `tests/MANUAL_TESTING_CHECKLIST.md` — UI workflow validation updated for the MARS window title

Run automated tests with:

```bash
pytest tests/ -v
```

---

## Documentation Set

- `START_HERE.md` — onboarding guide
- `README.md` — overview, installation, usage, architecture summary
- `ARCHITECTURE.md` — detailed layer-by-layer explanation (already MARS-aligned)
- `MIGRATION_GUIDE.md` — legacy MSUP → MARS mapping
- `TRANSFORMATION_SUMMARY.md` — before/after comparison with current metrics
- `PROJECT_COMPLETE.md`, `FINAL_DELIVERY_SUMMARY.md`, `FINAL_SUMMARY.md`, `FINAL_DELIVERY_COMPLETE.md` — completion artefacts
- `DOCUMENTATION_UPDATE_SUMMARY.md` — log of the current refresh
- Historical progress reports (`STATUS_REPORT.md`, `PROGRESS_SUMMARY.md`, `FINAL_PROJECT_STATE.md`, etc.) now include archival notices

---

## Verification Checklist

- [x] Application launches as **MARS: Modal Analysis Response Solver - v0.95**
- [x] Application displays Mars-themed icon in window title bar and taskbar
- [x] Batch, time-history, animation, and export workflows confirmed post-refactor
- [x] File validators and loaders tested with representative inputs
- [x] README and START_HERE instructions executed successfully
- [x] Unit tests passing locally
- [x] Manual testing checklist updated and followed
- [x] IBG plasticity algorithm disabled at UI level (pending validation)

---

## Recent Updates (v0.95)

- **IBG Plasticity Status**: The Incremental Buczynski-Glinka (IBG) plasticity correction method is disabled in this version pending further development and validation. Users should use Neuber or Glinka methods.
- **Application Icon**: Added custom Mars-themed icon system with SVG source and multiple PNG/ICO outputs in `resources/icons/`.
- **Version Numbering**: Changed to v0.95 to reflect pre-release status with IBG disabled.

---

This manifest captures the artefacts delivered with the MARS refactor. All components are aligned with the current version and ready for testing and validation.
