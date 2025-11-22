# MARS Feature Checklist

> **Quick reference for all available features in MARS v0.95**  
> Check off features as you explore them or use this for onboarding new users.

---

## Core Workflow Features

### File Loading
- [ ] Load Modal Coordinate File (.mcf)
- [ ] Load Modal Stress File (.csv)
- [ ] Load Steady-State Stress Field (.txt) [Optional]
- [ ] Load Modal Deformations File (.csv) [Optional]
- [ ] Use Navigator to browse and double-click files
- [ ] Set Project Directory via File menu

### Output Selection
- [ ] Max Principal Stress (s1)
- [ ] Min Principal Stress (s3)
- [ ] Von-Mises Stress
- [ ] Deformation magnitude
- [ ] Velocity magnitude
- [ ] Acceleration magnitude
- [ ] Damage Index / Potential Damage (requires Von-Mises)
- [ ] Time History Mode (single node)

### Basic Solver Options
- [ ] Skip first n modes (for rigid-body mode exclusion)
- [ ] Set fatigue parameters (σ'f and b)
- [ ] Run SOLVE and monitor progress

---

## Advanced Analysis Features

### Plasticity Correction
- [ ] Enable Plasticity Correction checkbox
- [ ] Select method: Neuber or Glinka
- [ ] Enter Material Profile (multi-temperature stress-strain curves)
- [ ] Load Temperature Field File (.csv with NodeID, Temperature)
- [ ] Adjust iteration controls (Max Iterations, Tolerance) if needed
- [ ] Enable Plasticity Diagnostics for Time History plots
- [ ] Choose Extrapolation Mode (Linear or Plateau)

### Performance Tuning (Settings → Advanced)
- [ ] Adjust RAM Allocation percentage (10-95%)
- [ ] Select Solver Precision (Single or Double)
- [ ] Enable GPU Acceleration (if NVIDIA CUDA available)

---

## Visualization Features

### 3D Display Controls
- [ ] Load Visualization File (external CSV)
- [ ] Adjust Node Point Size
- [ ] Set Legend Range (Min/Max) manually
- [ ] Adjust Deformation Scale Factor
- [ ] Hover to inspect node values
- [ ] Reset Camera view

### Time Point Visualization
- [ ] Set time value and click Update
- [ ] Save Time Point as CSV
- [ ] Export Velocity as Initial Condition (APDL format)

### Animation
- [ ] Choose Time Step Mode:
  - [ ] Custom Time Step (uniform intervals)
  - [ ] Actual Data Time Steps (with "Every nth" throttling)
- [ ] Set Interval (ms) for playback speed
- [ ] Set Start and End time range
- [ ] Play / Pause / Stop controls
- [ ] Save as Video (MP4) or GIF

---

## Interactive Analysis Tools

### Right-Click Context Menu
#### Selection Tools
- [ ] Add Selection Box
- [ ] Remove Selection Box
- [ ] Pick Box Center (position box interactively)

#### Hotspot Analysis
- [ ] Find Hotspots (on current view)
- [ ] Find Hotspots in Selection (within box)
- [ ] Click hotspot table entry to zoom and label

#### Point-Based Analysis
- [ ] Plot Time History for Selected Node

#### View Control
- [ ] Go To Node (fly camera to specific node)
- [ ] Lock Camera for Animation (track node during playback)
- [ ] Reset Camera

---

## Export Features

### Data Export
- [ ] Export time point results as CSV
- [ ] Export velocity initial conditions (APDL)
- [ ] Export animation frames as video/GIF

### Automatic Solver Outputs
When solver completes, MARS generates:
- [ ] Max/min stress per node CSVs
- [ ] Time of peak occurrence CSVs
- [ ] Damage index CSVs (if enabled)
- [ ] Corrected stress and plastic strain CSVs (if plasticity enabled)

---

## Menu Bar Features

### File Menu
- [ ] Select Project Directory

### View Menu
- [ ] Toggle Navigator visibility

### Settings Menu
- [ ] Open Advanced Settings dialog

---

## Console and Plotting

### Main Window Tab
- [ ] Console log monitoring
- [ ] Time History plot viewing
- [ ] Modal Coordinates plot

---

## File Format Compatibility

### Input Files Supported
- [x] .mcf (Modal Coordinate File)
- [x] .csv (Stress, Deformation, Temperature)
- [x] .txt (Steady-state stress, tab-delimited)

### Output Formats
- [x] .csv (all numerical results)
- [x] .dat (ANSYS-compatible)
- [x] .mp4 / .gif (animations)
- [x] .txt (APDL initial conditions)

---

## Hidden/Automatic Behaviors

### Things MARS Does Automatically
- [ ] Filters Navigator to .mcf, .csv, .txt files only
- [ ] Enables/disables output checkboxes based on loaded files
- [ ] Validates file consistency (Node IDs, time ranges)
- [ ] Falls back to CPU if GPU fails
- [ ] Chunks large datasets if RAM limit exceeded
- [ ] Unwraps modal coordinates if needed

---

## Feature Maturity Levels

### ✅ Production Ready
- All stress/deformation outputs
- Damage index calculations
- Plasticity correction (Neuber, Glinka)
- GPU acceleration
- All visualization features
- Animation export

### ⚠️ Advanced Users Only
- Plasticity iteration tuning
- Plasticity diagnostics overlay
- Custom RAM allocation >90%
- Skip modes (requires modal analysis knowledge)

### 🚧 Experimental / Disabled
- Incremental Buczynski-Glinka (IBG) plasticity method (greyed out in UI)

---

## Quick Tips

1. **First-Time User**: Stick to defaults, only load .mcf and stress .csv, select Von-Mises output
2. **Performance Issues**: Go to Settings → Advanced, increase RAM to 90%, try Single precision
3. **Plasticity Correction**: Only use if elastic stress exceeds yield; requires cyclic material data
4. **Large Animations**: Use "Actual Data Time Steps" with "Every 10th" or "Every 20th"
5. **Hotspot Analysis**: Right-click → Find Hotspots after solver completes
6. **GPU Not Working**: Check that CUDA toolkit is installed; solver will work on CPU as fallback

---

## Checklist for a Complete Analysis

### Minimum Viable Workflow
1. Load .mcf file
2. Load stress .csv file
3. Select at least one output (e.g., Von-Mises)
4. Click SOLVE
5. Switch to Display tab
6. Review results visually

### Recommended Workflow
1. Set Project Directory
2. Load .mcf, stress .csv, (optional) deformations .csv
3. Select multiple outputs: Von-Mises, Max Principal, Deformation
4. Set Skip modes if needed (typically 0 or 6)
5. Click SOLVE and monitor console
6. Switch to Display tab
7. Find Hotspots to identify critical nodes
8. Go To Node for detailed inspection
9. Plot Time History for critical nodes
10. Adjust legend range for clearer visualization
11. Create animation for presentation
12. Export results as CSV and video

### Advanced Workflow with Plasticity
1. (All steps from Recommended Workflow)
2. Enable Plasticity Correction
3. Select method (Neuber or Glinka)
4. Enter Material Profile with temperature-dependent curves
5. Load Temperature Field CSV
6. Review iteration settings (adjust if warnings appear)
7. Enable Plasticity Diagnostics if validating model
8. Click SOLVE
9. Compare elastic vs. corrected results
10. Review plastic strain distribution
11. Use corrected stress for strain-based fatigue assessment

---

## Feature Coverage by Manual

| Feature | Quick Manual | Detailed Manual | Theory Manual |
|---------|--------------|-----------------|---------------|
| Advanced Settings | Section 4 | Page 15 | Section 10 |
| Plasticity Correction | Section 6 | Page 13 | Sections 8.1-8.10 |
| Skip Modes | Step 7 | Page 10 | Section 6.3 |
| Animation Throttling | Section 5 | Page 21 | — |
| GPU Acceleration | Section 4 | Page 15 | Section 10.3 |
| Context Menu | Section 5 | Pages 22-25 | — |
| File Formats | (implied) | Page 33 | Section 3 |

---

## Support and Documentation

- **Quick Start**: See `QUICK_USER_MANUAL.md`
- **Detailed Guidance**: See `DETAILED_USER_MANUAL_20_Pages.md`
- **Theory and Validation**: See `DETAILED_THEORY_MANUAL.md`
- **Recent Updates**: See `DOCUMENTATION_UPDATES_SUMMARY.md`
- **Architecture**: See `ARCHITECTURE.md`

---

**Last Updated**: November 22, 2025  
**MARS Version**: v0.95  
**Documentation Set**: Complete with all features documented

