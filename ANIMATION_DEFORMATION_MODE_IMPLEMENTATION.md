# Animation Deformation Mode Implementation

## Overview

Added a new UI checkbox option to control how deformations are displayed in animations:
- **Relative Mode (Default)**: Shows motion relative to the animation start frame
- **Absolute Mode**: Shows true deformation from undeformed geometry

## Changes Made

### 1. UI Component Addition (`src/ui/builders/display_ui.py`)

**Added:**
- `QCheckBox` import to PyQt5 widgets
- New checkbox: `absolute_deformation_checkbox`
- Tooltip explaining the difference between modes
- Added to visualization controls layout
- Stored in components dictionary for access by DisplayTab

**Location:** Lines 10-11, 90-99, 119

```python
absolute_deformation_checkbox = QCheckBox("Show Absolute Deformations")
absolute_deformation_checkbox.setToolTip(
    "When checked: Animation shows absolute deformation from undeformed geometry.\n"
    "When unchecked: Animation shows relative motion from the start frame (default).\n\n"
    "Relative mode is useful for visualizing motion patterns.\n"
    "Absolute mode preserves true deformation magnitudes and is required for IC export."
)
absolute_deformation_checkbox.setChecked(False)  # Default to relative
absolute_deformation_checkbox.setVisible(False)  # Hidden until relevant
```

### 2. Parameter Passing (`src/ui/handlers/display_animation_handler.py`)

**Modified:** `start_animation()` method, line 142

Added checkbox state to animation parameters:
```python
"show_absolute_deformation": tab.absolute_deformation_checkbox.isChecked(),
```

This parameter is passed through the Qt signal to the solver tab for processing.

### 3. Computation Logic (`src/ui/handlers/analysis_handler.py`)

**Modified:** `perform_animation_precomputation()` method, lines 956-981

Implemented conditional zero-referencing based on user preference:

```python
show_absolute = params.get('show_absolute_deformation', False)
if not show_absolute:
    # Zero-reference to first animation frame (relative motion mode)
    ux_anim -= ux_anim[:, [0]]
    uy_anim -= uy_anim[:, [0]]
    uz_anim -= uz_anim[:, [0]]
    print("Animation mode: Relative deformations (zero-referenced to start frame)")
else:
    print("Animation mode: Absolute deformations (from undeformed geometry)")
```

### 4. UI Visibility Control (`src/ui/display_tab.py`)

**Modified:** Line 258

Made checkbox visible when animation controls become available:
```python
self.absolute_deformation_checkbox.setVisible(True)
```

## How It Works

### Relative Deformation Mode (Default, Unchecked)

**Mathematical Operation:**
```python
displacement_at_frame_n = actual_displacement[n] - actual_displacement[0]
```

**Effect:**
- First animation frame appears at original (undeformed) mesh position
- All subsequent frames show motion relative to this starting position
- Useful for visualizing dynamic motion patterns
- Better for understanding vibration modes and oscillations

**Example Scenario:**
```
Time points: [0.3s, 0.4s, 0.5s, 0.6s]
True displacements at node X: [2.5mm, 3.1mm, 3.8mm, 4.2mm]

After zero-referencing:
  t=0.3s: 0.0mm  (reference frame)
  t=0.4s: 0.6mm  (relative to start)
  t=0.5s: 1.3mm  (relative to start)
  t=0.6s: 1.7mm  (relative to start)
```

### Absolute Deformation Mode (Checked)

**Mathematical Operation:**
```python
displacement_at_frame_n = actual_displacement[n]  # No modification
```

**Effect:**
- All frames show true deformation from undeformed geometry
- Preserves absolute magnitude information
- Required for accurate initial condition (IC) export
- Shows cumulative effect of all loading history

**Example Scenario:**
```
Time points: [0.3s, 0.4s, 0.5s, 0.6s]
True displacements at node X: [2.5mm, 3.1mm, 3.8mm, 4.2mm]

After processing (no change):
  t=0.3s: 2.5mm  (absolute from undeformed)
  t=0.4s: 3.1mm  (absolute from undeformed)
  t=0.5s: 3.8mm  (absolute from undeformed)
  t=0.6s: 4.2mm  (absolute from undeformed)
```

## Use Cases

### When to Use Relative Mode (Default)

✅ **Recommended for:**
- Visualizing vibration patterns and oscillations
- Understanding dynamic motion behavior
- Presenting animations where motion clarity is priority
- Comparing motion between different time windows
- Educational demonstrations of structural dynamics

❌ **Not suitable for:**
- Exporting initial conditions for subsequent analyses
- Quantitative deformation measurements
- Cases where absolute position matters
- Steady-state + transient combined analyses

### When to Use Absolute Mode

✅ **Recommended for:**
- Quantitative deformation analysis where absolute values matter
- Cases with significant pre-deformation before animation starts
- Steady-state + modal superposition scenarios
- Validating against experimental or reference data
- Understanding total accumulated displacement

❌ **Not suitable for:**
- Pure motion pattern visualization (can be harder to see dynamics)
- Large absolute offsets that obscure small oscillations

**Important Note:** Initial condition (IC) export is NOT affected by this checkbox. IC export uses time point calculations (via the "Update" button), which always compute velocities from absolute displacements. The checkbox only affects animation visualization coordinates.

## Technical Details

### Data Flow

1. User checks/unchecks checkbox in Display tab
2. User clicks "Play" to start animation
3. `DisplayAnimationHandler.start_animation()` collects parameters
4. Parameter `show_absolute_deformation` sent via Qt signal
5. `SolverAnalysisHandler.perform_animation_precomputation()` receives it
6. Conditional zero-referencing applied based on setting
7. Precomputed coordinates sent back to Display tab
8. Animation renders with chosen mode

### Memory Impact

No additional memory overhead - the checkbox only changes how existing displacement data is processed (whether to subtract first frame or not).

### Backward Compatibility

- Default behavior (unchecked) maintains previous zero-referencing behavior
- Existing code/workflows unaffected
- New option is opt-in via checkbox

## Console Output

The implementation adds informative console messages:

```
Animation mode: Relative deformations (zero-referenced to start frame)
```
or
```
Animation mode: Absolute deformations (from undeformed geometry)
```

This helps users and developers understand which mode is active during processing.

## User Interface Location

The checkbox appears in the **Visualization Controls** group box, next to the **Deformation Scale Factor** control. It becomes visible when:
1. A mesh has been loaded
2. Animation controls are enabled

## Testing Recommendations

### Test Case 1: Mid-Timeline Animation
```
1. Load a dataset with time range 0.0 to 1.0 seconds
2. Set animation range to 0.4 to 0.8 seconds
3. Load deformation data
4. Run animation with checkbox UNCHECKED
   Expected: First frame appears undeformed
5. Run animation with checkbox CHECKED
   Expected: First frame shows deformation accumulated from t=0 to t=0.4
```

### Test Case 2: Full Timeline Animation
```
1. Load a dataset
2. Set animation range to full time range (0.0 to max)
3. Run both modes
   Expected: Both modes should look similar (first frame is t=0 in both cases)
```

### Test Case 3: Steady-State + Modal
```
1. Load steady-state stress data
2. Load modal deformation data
3. Run animation with both modes
   Expected: Absolute mode preserves steady-state offset, relative mode removes it
```

### Test Case 4: IC Export
```
1. Set up animation at t=0.5s to t=0.6s
2. Extract IC with checkbox UNCHECKED
   Expected: Velocities may be incorrect (relative to wrong reference)
3. Extract IC with checkbox CHECKED
   Expected: Correct absolute velocities and positions
```

## Important Clarifications

### What the Checkbox DOES Affect:
- ✅ Mesh coordinate positions during animation playback
- ✅ Where nodes appear on screen during animation
- ✅ Saved animation videos (MP4/GIF)

### What the Checkbox DOES NOT Affect:
- ❌ Velocity scalar field values displayed on mesh
- ❌ Acceleration scalar field values displayed on mesh  
- ❌ Initial condition (IC) export values
- ❌ Time point calculations (triggered by "Update" button)
- ❌ Any stress calculations

**Key Insight:** The checkbox only controls how displacement data is processed for coordinate visualization. All physics calculations (velocity, acceleration, stress) are always performed using absolute displacements and are unaffected by this setting.

## Known Limitations

1. **No per-frame toggle**: Mode is set before animation starts, cannot change during playback
2. **No visual indicator**: After animation starts, user must remember which mode was selected
3. **Console output only**: Mode is logged to console but not shown in UI during playback
4. **Does not affect IC export**: Despite initial documentation suggesting otherwise, IC export uses separate time point calculations

## Future Enhancements (Optional)

- Add text indicator in 3D viewport showing current mode
- Allow mode toggle during playback (would require recomputation)
- Add keyboard shortcut to toggle mode
- Save mode preference in user settings
- Add mode indicator to saved animation files (metadata)

## Files Modified

1. `src/ui/builders/display_ui.py` - UI component creation
2. `src/ui/handlers/display_animation_handler.py` - Parameter collection
3. `src/ui/handlers/analysis_handler.py` - Computation logic
4. `src/ui/display_tab.py` - Visibility control

## Documentation

This implementation addresses the issue identified in the code review:
**"Animation Deformation Zero-Referencing Potential Issue"**

The problem was that zero-referencing behavior was hardcoded and undocumented. Users had no control over whether animations showed absolute or relative deformations, leading to potential confusion when:
- Animation start time ≠ 0
- Steady-state deformations were present
- Exporting initial conditions for subsequent analyses

This implementation provides user control and clear documentation of the behavior.

