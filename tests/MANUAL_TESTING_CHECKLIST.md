# Manual GUI Testing Checklist

**Version**: 2.0.0 (Modular)  
**Date**: ___________  
**Tester**: ___________

---

## Pre-Testing Setup

- [ ] Fresh Python environment activated
- [ ] All dependencies installed from requirements.txt
- [ ] Test data files prepared
- [ ] Legacy code available for comparison

**Note**: For testing recent bug fixes (Issues #6 and #7), see [BUGFIX_TESTING_CHECKLIST.md](BUGFIX_TESTING_CHECKLIST.md)

---

## 1. Application Launch ✅

- [ ] Application starts without errors
- [ ] Main window appears maximized
- [ ] Title shows "MSUP Smart Solver - v2.0.0 (Modular)"
- [ ] Two tabs visible: "Main Window" and "Display"
- [ ] Navigator dock visible on left
- [ ] Menu bar shows: File, View, Settings

---

## 2. File Loading - Modal Coordinate File

### Valid File
- [ ] Click "Read Modal Coordinate File (.mcf)"
- [ ] Select valid .mcf file
- [ ] File path appears in text field
- [ ] Console shows: "Successfully validated and loaded..."
- [ ] Console shows shape: "Modal coordinates tensor shape (m x n)"
- [ ] "Plot (Modal Coordinates)" tab appears
- [ ] Plot shows all modes
- [ ] Zoom/pan works on plot

### Invalid File
- [ ] Try to load invalid .mcf file
- [ ] Error dialog appears with descriptive message
- [ ] File path NOT updated
- [ ] Console does NOT show success message

---

## 3. File Loading - Modal Stress File

### Valid File
- [ ] Click "Read Modal Stress File (.csv)"
- [ ] Select valid stress CSV
- [ ] File path appears in text field
- [ ] Console shows: "Successfully validated and loaded..."
- [ ] Console shows: "Node IDs tensor shape"
- [ ] Console shows: "Normal stress components extracted"
- [ ] "Skip first n modes" combo appears
- [ ] Combo populated with 0 to N_modes
- [ ] Output checkboxes become enabled

### Invalid File
- [ ] Try file without NodeID column → Error
- [ ] Try file without stress components → Error
- [ ] Try non-CSV file → Error

---

## 4. Optional Files

### Steady-State Stress
- [ ] Check "Include Steady-State Stress Field"
- [ ] Button and path field appear
- [ ] Click button, select .txt file
- [ ] File loads successfully
- [ ] Uncheck → controls hide
- [ ] Uncheck → file path clears

### Deformations
- [ ] Check "Include Deformations"
- [ ] Button and path field appear
- [ ] Click button, select deformations CSV
- [ ] File loads successfully
- [ ] Console shows: "UX, UY, UZ shapes"
- [ ] Deformation outputs enabled
- [ ] Uncheck → controls hide

---

## 5. Mode Skipping

- [ ] Combo shows "0" to "N" (N = number of modes)
- [ ] Select different values
- [ ] Console shows: "[INFO] Skip Modes option is set to X"
- [ ] Console shows: "Modes to be used: Y (from mode X+1 to N)"
- [ ] Selecting "0" → all modes used
- [ ] Selecting "N" → error when solving

---

## 6. Output Selection

### Time History Mode OFF
- [ ] Can select multiple output checkboxes simultaneously
- [ ] Von Mises shows Damage Index checkbox when checked
- [ ] Damage checkbox disabled in time history mode

### Time History Mode ON
- [ ] Checkbox toggles "Scoping" group visibility
- [ ] Output checkboxes become mutually exclusive
- [ ] Checking one unchecks others
- [ ] "Plot (Time History)" tab appears
- [ ] Node ID field enabled

---

## 7. Time History Analysis

- [ ] Enter valid node ID
- [ ] Select one output (e.g., Von Mises)
- [ ] Click SOLVE
- [ ] Console shows: "BEGIN SOLVE"
- [ ] Progress bar appears (if applicable)
- [ ] Plot updates with stress vs time
- [ ] Plot shows correct title (stress type + node ID)
- [ ] Data table populated with time and values
- [ ] Max value annotation appears on plot
- [ ] Legend is interactive (click to hide/show)
- [ ] Hover shows tooltip with values
- [ ] Can copy data from table (Ctrl+C)

### Test Each Output Type
- [ ] Von Mises Stress
- [ ] Max Principal Stress (σ₁)
- [ ] Min Principal Stress (σ₃)
- [ ] Deformation (Magnitude + X,Y,Z)
- [ ] Velocity (Magnitude + X,Y,Z)
- [ ] Acceleration (Magnitude + X,Y,Z)

---

## 8. Batch Analysis

- [ ] Time History mode OFF
- [ ] Select output(s): Von Mises, Max S1, Min S3
- [ ] Click SOLVE
- [ ] Console shows: "BEGIN SOLVE"
- [ ] Console shows: "Starting Batch Processing"
- [ ] Console shows: "Processing X nodes in Y iterations"
- [ ] Progress bar updates 0% → 100%
- [ ] Console shows per-iteration progress
- [ ] Console shows: "Batch Processing Finished"
- [ ] Console shows: "SOLVE COMPLETE"
- [ ] Output CSV files created in project directory:
  - [ ] max_von_mises_stress.csv
  - [ ] time_of_max_von_mises_stress.csv
  - [ ] max_s1_stress.csv
  - [ ] time_of_max_s1_stress.csv
  - [ ] min_s3_stress.csv
  - [ ] time_of_min_s3_stress.csv
- [ ] CSV files have correct format (NodeID, X, Y, Z, Value)
- [ ] Values match legacy code output

---

## 9. Fatigue/Damage Analysis

- [ ] Check Von Mises checkbox
- [ ] Damage Index checkbox appears
- [ ] Check Damage Index
- [ ] Fatigue Parameters group appears
- [ ] Enter σ'f value (e.g., 1000)
- [ ] Enter b value (e.g., -3)
- [ ] Click SOLVE
- [ ] Analysis runs without error
- [ ] potential_damage_results.dat created
- [ ] potential_damage_results.csv created
- [ ] Values are reasonable (0 to 1 range typically)

---

## 10. Display Tab - File Loading

- [ ] Switch to "Display" tab
- [ ] Click "Load Visualization File"
- [ ] Select CSV with results
- [ ] 3D point cloud appears
- [ ] Nodes colored by scalar field
- [ ] Scalar bar shows value range
- [ ] Camera positioned appropriately

---

## 11. Display Tab - Visualization Controls

### Point Size
- [ ] Adjust point size slider
- [ ] Point size updates immediately
- [ ] Range 1-100 works

### Scalar Range
- [ ] Adjust Min spinbox
- [ ] Color map updates immediately
- [ ] Adjust Max spinbox
- [ ] Color map updates immediately
- [ ] Min cannot exceed Max
- [ ] Max cannot be less than Min

### Deformation Scale
- [ ] Field disabled if no deformation data
- [ ] Shows "0" when disabled
- [ ] Enabled when deformation loaded
- [ ] Can enter scale factor
- [ ] Invalid input reverts to last valid value

---

## 12. Display Tab - Time Point Analysis

- [ ] Time point controls visible after data load
- [ ] Spinbox shows time range
- [ ] Select different time values
- [ ] Click "Update"
- [ ] Visualization updates with new time point
- [ ] Scalar values change appropriately
- [ ] Click "Save Time Point as CSV"
- [ ] CSV saved with correct filename format
- [ ] CSV contains correct data

---

## 13. Display Tab - Animation

### Setup
- [ ] Animation controls visible
- [ ] Set time range (start/end)
- [ ] Set interval (ms)
- [ ] Select time step mode (Custom or Actual)

### Playback
- [ ] Click "Play"
- [ ] Animation starts
- [ ] Time display updates
- [ ] Mesh deforms (if deformation included)
- [ ] Scalar values update
- [ ] Click "Pause"
- [ ] Animation pauses
- [ ] Click "Play" again → resumes
- [ ] Click "Stop"
- [ ] Animation stops
- [ ] Returns to first frame

### Save Animation
- [ ] "Save as Video/GIF" button enabled after precomputation
- [ ] Click button
- [ ] Select format (MP4 or GIF)
- [ ] Select save location
- [ ] Animation renders and saves
- [ ] Output file playable
- [ ] Frame rate correct
- [ ] Visual quality acceptable

---

## 14. Display Tab - Context Menu Features

### Hotspot Detection
- [ ] Right-click in 3D view
- [ ] Select "Find Hotspots"
- [ ] Enter top N (e.g., 10)
- [ ] Select mode (Max/Min/Abs)
- [ ] Dialog shows hotspot table
- [ ] Click row → camera focuses on node
- [ ] Node highlighted in 3D

### Point Picking
- [ ] Right-click → "Enable Point Picking"
- [ ] Click on nodes in 3D
- [ ] Node info displayed
- [ ] Can send to time history
- [ ] Mode disables properly

### Box Selection
- [ ] Right-click → "Enable Selection Box"
- [ ] Box appears
- [ ] Can resize with handles
- [ ] Can move box
- [ ] "Find Hotspots in Box" shows filtered results

### Go To Node
- [ ] Right-click → "Go To Node"
- [ ] Enter node ID
- [ ] Camera focuses on node
- [ ] Marker appears
- [ ] Can track during animation
- [ ] Freeze option works

---

## 15. Navigator

- [ ] Shows project directory structure
- [ ] Only .csv, .mcf, .txt files visible
- [ ] Can sort by name/date
- [ ] Double-click opens file externally
- [ ] Drag file to input field loads it

---

## 16. Advanced Settings

- [ ] Settings → Advanced
- [ ] Dialog shows current settings
- [ ] Adjust RAM allocation (e.g., 80%)
- [ ] Change precision (Single ↔ Double)
- [ ] Toggle GPU acceleration
- [ ] Click OK
- [ ] Console confirms changes
- [ ] Next solve uses new settings

---

## 17. Error Handling

- [ ] Load invalid coordinate file → Clear error message
- [ ] Load invalid stress file → Clear error message
- [ ] Solve without files → Error message
- [ ] Time history without node ID → Error message
- [ ] Invalid node ID → Error message
- [ ] No outputs selected → Error message
- [ ] Damage without fatigue params → Error message

---

## 18. Performance

### Memory Management
- [ ] Monitor RAM usage during batch analysis
- [ ] Stays within configured limit
- [ ] No memory leaks after multiple solves
- [ ] Garbage collection works properly

### Speed
- [ ] File loading responsive (<5s for typical files)
- [ ] Time history calculation fast (<1s)
- [ ] Batch analysis uses chunking properly
- [ ] Progress updates smooth (not jerky)
- [ ] Animation playback smooth (no stuttering)

---

## 19. Comparison with Legacy

### Side-by-Side Test
- [ ] Run same analysis in both versions
- [ ] Compare output CSV files
- [ ] Stress values match (within 1e-6)
- [ ] Time values match exactly
- [ ] Node IDs match exactly
- [ ] Coordinates match exactly
- [ ] File formats identical
- [ ] GUI appearance identical
- [ ] Feature parity confirmed

---

## 20. Stability

- [ ] Run 10 consecutive analyses → No crashes
- [ ] Load 10 different files → No crashes
- [ ] Switch tabs repeatedly → No crashes
- [ ] Resize window repeatedly → No layout issues
- [ ] Open/close dialogs repeatedly → No memory leaks

---

## Issues Found

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| 1  |             |          |        |
| 2  |             |          |        |
| 3  |             |          |        |

---

## Test Summary

**Total Checks**: ~200  
**Passed**: _____  
**Failed**: _____  
**Blocked**: _____  

**Overall Status**: ⬜ Pass / ⬜ Fail / ⬜ Needs Work

**Notes**:
_____________________________________________
_____________________________________________
_____________________________________________

---

**Tester Signature**: ___________________  **Date**: __________

