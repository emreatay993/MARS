# MARS: Modal Analysis Response Solver - Testing Guide

## Overview

This guide provides comprehensive testing procedures for MARS (the refactored MSUP Smart Solver). Testing is divided into three levels: unit tests, integration tests, and manual GUI testing.

## Unit Tests

### Running Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_validators.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

**Created Tests**:
- `test_validators.py` - File validation functions (8 tests)
- `test_data_models.py` - Data model classes (8 tests)
- `test_file_utils.py` - File utility functions (3 tests)
- `test_node_utils.py` - Node mapping functions (5 tests)

**Total**: 24 unit tests covering core utilities and data structures.

**Target Coverage**: >80% for utils, io, and core packages.

### Adding New Tests

To add tests for additional modules:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from module_to_test import function_to_test

def test_function():
    result = function_to_test(input_data)
    assert result == expected_output
```

## Integration Tests

### Test Workflows

These tests verify complete workflows from file loading to result export:

#### Workflow 1: Load → Batch Solve → Export
1. Load modal coordinate file (.mcf)
2. Load modal stress file (.csv)
3. Run batch analysis (von Mises stress)
4. Verify output CSV files are created
5. Compare results with legacy code output

#### Workflow 2: Load → Time History → Plot
1. Load modal coordinate file
2. Load modal stress file
3. Run time history analysis for a specific node
4. Verify plot data matches legacy code

#### Workflow 3: Load → Time Point → Export
1. Load all required files
2. Request time point calculation
3. Display results in 3D
4. Export time point results
5. Verify CSV format and data

#### Workflow 4: Load → Animation → Save
1. Load files with deformations
2. Precompute animation frames
3. Playback animation
4. Save as video/GIF
5. Verify output file

### Creating Integration Tests

```python
def test_complete_workflow():
    # Setup
    app = QApplication([])
    main_window = MainWindow()
    
    # Load files
    main_window.solver_tab._load_coordinate_file('test_data/test.mcf')
    main_window.solver_tab._load_stress_file('test_data/test.csv')
    
    # Run analysis
    config = SolverConfig(calculate_von_mises=True)
    main_window.solver_tab.analysis_engine.run_batch_analysis(config)
    
    # Verify outputs exist
    assert os.path.exists('output/max_von_mises_stress.csv')
    
    # Cleanup
    app.quit()
```

## Manual GUI Testing Checklist

### File Loading Tests
- [ ] Load modal coordinate file (.mcf)
  - [ ] Valid file loads successfully
  - [ ] Invalid file shows error message
  - [ ] File path displays in UI
  - [ ] Modal coordinates plot appears
  - [ ] Console shows success message
- [ ] Load modal stress file (.csv)
  - [ ] Valid file loads successfully
  - [ ] Invalid file shows error message
  - [ ] Node IDs extracted correctly
  - [ ] Coordinates extracted if present
  - [ ] Skip modes combo populated
- [ ] Load deformations file (.csv) [Optional]
  - [ ] Checkbox enables/disables controls
  - [ ] Valid file loads successfully
  - [ ] Invalid file shows error
  - [ ] Deformation outputs become available
- [ ] Load steady-state stress file (.txt) [Optional]
  - [ ] Checkbox enables/disables controls
  - [ ] Valid file loads successfully
  - [ ] Invalid file shows error
  - [ ] Data stored correctly

### Mode Skipping Tests
- [ ] Skip modes combo appears after stress file load
- [ ] Selecting different skip values shows console message
- [ ] Skipping modes affects calculation correctly
- [ ] Cannot skip more modes than available (shows error)

### Time History Mode Tests
- [ ] Checkbox toggles single node group visibility
- [ ] Output checkboxes become mutually exclusive
- [ ] Node ID input field accepts valid IDs
- [ ] Invalid node IDs show error message
- [ ] Plot tab becomes visible
- [ ] Each output type plots correctly:
  - [ ] Von Mises stress
  - [ ] Max principal stress
  - [ ] Min principal stress
  - [ ] Deformation (magnitude + components)
  - [ ] Velocity (magnitude + components)
  - [ ] Acceleration (magnitude + components)
- [ ] Plot legend is interactive (click to hide/show)
- [ ] Hover shows data point values
- [ ] Data table shows correct values
- [ ] Ctrl+C copies selected cells

### Batch Analysis Tests
- [ ] Multiple outputs can be selected
- [ ] Progress bar shows during calculation
- [ ] Console displays progress messages
- [ ] Output CSV files created:
  - [ ] Max von Mises stress + time
  - [ ] Max S1 stress + time
  - [ ] Min S3 stress + time
  - [ ] Max deformation + time
  - [ ] Max velocity + time
  - [ ] Max acceleration + time
  - [ ] Potential damage (if selected)
- [ ] Results match legacy code output
- [ ] Max over time plots appear (if applicable)

### Fatigue/Damage Tests
- [ ] Damage checkbox only visible when von Mises selected
- [ ] Damage checkbox disabled in time history mode
- [ ] Fatigue parameters group appears when damage selected
- [ ] Must enter valid A and m values
- [ ] Invalid values show error message
- [ ] Damage calculation produces results

### 3D Visualization Tests (Display Tab)
- [ ] Load visualization file (.csv)
- [ ] Point cloud displays correctly
- [ ] Node IDs visible if present
- [ ] Scalar bar shows correct range
- [ ] Point size control works
- [ ] Scalar range controls work:
  - [ ] Min/max spinboxes update range
  - [ ] Changes reflected immediately
  - [ ] Min cannot exceed max (and vice versa)
- [ ] Camera controls work (rotate, pan, zoom)
- [ ] Reset camera works

### Time Point Analysis Tests (Display Tab)
- [ ] Time point spinbox shows correct range
- [ ] Update button triggers calculation
- [ ] 3D view updates with new data
- [ ] Scalar bar title shows correct field name
- [ ] Save time point button exports CSV correctly
- [ ] CSV contains NodeID, X, Y, Z, and scalar field

### Animation Tests (Display Tab)
- [ ] Animation controls visible after file load
- [ ] Time range spinboxes work correctly
- [ ] Play button starts animation
- [ ] Pause button pauses (can resume)
- [ ] Stop button stops and resets
- [ ] Animation interval control works
- [ ] Custom time step mode works
- [ ] Actual data time steps mode works
- [ ] Deformation scale factor applies correctly
- [ ] Time display updates during playback
- [ ] Save animation button enabled after precomputation
- [ ] Can save as MP4 (requires ffmpeg)
- [ ] Can save as GIF

### Hotspot Detection Tests (Display Tab Context Menu)
- [ ] Right-click shows context menu
- [ ] Find Hotspots option works:
  - [ ] Top N selection works
  - [ ] Maximum value mode works
  - [ ] Minimum value mode works
  - [ ] Absolute value mode works
- [ ] Hotspot dialog displays results
- [ ] Clicking row in hotspot dialog focuses on node
- [ ] Hotspot node highlighted in 3D view

### Node Picking Tests (Display Tab Context Menu)
- [ ] Enable Point Picking mode works
- [ ] Clicking on nodes picks them
- [ ] Node ID displayed
- [ ] Can send to time history analysis
- [ ] Mode disables properly

### Box Selection Tests (Display Tab Context Menu)
- [ ] Enable Selection Box works
- [ ] Box appears in 3D view
- [ ] Can resize and move box
- [ ] Find Hotspots in Box works
- [ ] Results filtered to box region

### Go To Node Tests (Display Tab Context Menu)
- [ ] Go To Node dialog appears
- [ ] Enter valid node ID focuses camera
- [ ] Node marker appears
- [ ] Invalid node ID shows error
- [ ] Can track node during animation
- [ ] Freeze option works

### Initial Conditions Export Tests (Display Tab)
- [ ] Export velocity option appears after velocity calculation
- [ ] APDL file generated correctly
- [ ] File contains IC commands for all nodes
- [ ] Velocity units correct (mm/s)
- [ ] File format valid for ANSYS

### Navigator Tests
- [ ] Navigator dock visible by default
- [ ] Can hide/show via View menu
- [ ] Select Project Directory updates navigator
- [ ] Only shows .csv, .mcf, .txt files
- [ ] Double-click opens file in default app
- [ ] Drag from navigator to file fields works

### Advanced Settings Tests
- [ ] Settings dialog opens from menu
- [ ] Current settings displayed
- [ ] RAM allocation adjustable (10-95%)
- [ ] Precision selection works (Single/Double)
- [ ] GPU acceleration toggle works
- [ ] OK applies settings
- [ ] Cancel discards changes
- [ ] Console confirms settings applied

### Drag and Drop Tests
- [ ] Can drag files onto file path fields
- [ ] Correct file type loads in correct field
- [ ] Invalid files show error message

### Console Output Tests
- [ ] All operations log to console
- [ ] Console auto-scrolls to bottom
- [ ] Progress messages appear during solve
- [ ] Error messages appear when appropriate
- [ ] Success messages appear after operations

### Performance Tests
- [ ] Large files (10,000+ nodes) load successfully
- [ ] Batch analysis completes without memory errors
- [ ] Animation precomputation doesn't freeze GUI
- [ ] Memory usage stays within configured limits
- [ ] No memory leaks during repeated operations

## Comparison with Legacy Code

### Output Comparison

For each analysis type, compare outputs with legacy code:

1. **Run analysis in legacy code** → Save outputs
2. **Run same analysis in refactored code** → Save outputs  
3. **Compare CSV files**:
   - Same number of rows/columns
   - Same node IDs
   - Same coordinates
   - Stress values match (within numerical precision)
   - Time values match

### Numerical Accuracy

Expected differences:
- None - algorithms are identical
- Floating point differences <1e-10 acceptable (rounding)

If differences >1e-6:
- **STOP** - investigate discrepancy
- Check input files match
- Check mode skipping settings match
- Check solver settings match

## Regression Testing

After any code changes, run:

1. **Quick Test** (5 minutes):
   - Load test files
   - Run time history for one node
   - Verify plot appears

2. **Standard Test** (15 minutes):
   - Run unit tests
   - Load test files
   - Run batch analysis
   - Check outputs match expected

3. **Full Test** (45 minutes):
   - All unit tests
   - Manual checklist (key features)
   - Compare with legacy output
   - Performance check

## Bug Reporting

When reporting issues, include:

1. **Steps to reproduce**
2. **Expected behavior**
3. **Actual behavior**
4. **Input files used** (if possible)
5. **Console output**
6. **Screenshots** (for GUI issues)
7. **Error messages/tracebacks**

## Test Data

### Creating Test Data

Minimal test files for unit testing:

**test.mcf** (Modal Coordinates):
```
Test Header
Number of Modes: 2
      Time          Mode_1          Mode_2
  0.000000     0.100000     0.200000
  0.001000     0.110000     0.210000
  0.002000     0.120000     0.220000
```

**test_stress.csv** (Modal Stress):
```
NodeID,X,Y,Z,sx_1,sx_2,sy_1,sy_2,sz_1,sz_2,sxy_1,sxy_2,syz_1,syz_2,sxz_1,sxz_2
1,0,0,0,10,20,30,40,50,60,5,10,15,20,25,30
2,1,1,1,11,21,31,41,51,61,6,11,16,21,26,31
```

Use these for rapid testing during development.

## Test Status

| Test Category | Status | Coverage |
|---------------|--------|----------|
| Unit Tests | ✅ Created | 24 tests |
| Validators | ✅ Done | 100% |
| Data Models | ✅ Done | 100% |
| File Utils | ✅ Done | 100% |
| Node Utils | ✅ Done | 100% |
| Integration Tests | 📋 TODO | - |
| Manual GUI Tests | 📋 TODO | - |
| Performance Tests | 📋 TODO | - |
| Regression Tests | 📋 TODO | - |

## Continuous Testing

As development continues:

1. Run unit tests after each module change
2. Run integration tests after major refactoring
3. Manual GUI test before each milestone
4. Full regression test before release

---

**Note**: This is a living document. Update as new tests are added or testing procedures are refined.

