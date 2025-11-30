# Orientation Widget Size Bug Fix

## Date
November 22, 2025

## Bug Description

**Issue:** The orientation widget (XYZ axes indicator) appears **huge** on the Display tab when:
1. User loads files
2. User runs solve
3. User switches to Display tab **after** solve

**Expected:** Small widget in top-right corner (15% of viewport)

**Actual:** Huge widget covering significant portion of screen

## Root Cause

**PyVista Initialization Timing Issue:**

The orientation widget was added without explicit size parameters:
```python
camera_widget = plotter.add_camera_orientation_widget()  # No size specified!
```

PyVista's behavior:
- **If plotter already rendered** (user visited Display tab first): Uses sensible default size
- **If plotter not yet rendered** (user visits Display tab after solve): Uses huge default size

This is because PyVista calculates widget size based on the current render window state, which differs depending on initialization order.

## Solution

**Add explicit viewport parameter** to `add_camera_orientation_widget()`:

### Code Location
**File:** `src/ui/handlers/display_visualization_handler.py`  
**Method:** `update_visualization()`  
**Lines:** 69-73

### Before (Broken)
```python
if not self.state.camera_widget:
    camera_widget = plotter.add_camera_orientation_widget()
    camera_widget.EnabledOn()
    self.state.camera_widget = camera_widget
    self.tab.camera_widget = camera_widget
```

### After (Fixed)
```python
if not self.state.camera_widget:
    # Add orientation widget with explicit size (prevents huge widget bug)
    # viewport=(x_min, y_min, x_max, y_max) as fractions of window
    # (0.85, 0.85, 1.0, 1.0) = Top-right corner, 15% of viewport size
    camera_widget = plotter.add_camera_orientation_widget(
        viewport=(0.85, 0.85, 1.0, 1.0)
    )
    camera_widget.EnabledOn()
    self.state.camera_widget = camera_widget
    self.tab.camera_widget = camera_widget
```

## Viewport Parameter Explanation

The `viewport` parameter defines widget position and size as **fractions** of the render window:

```
viewport = (x_min, y_min, x_max, y_max)

(0.85, 0.85, 1.0, 1.0) means:
  - Bottom-left corner: (85%, 85%) of window
  - Top-right corner: (100%, 100%) of window
  - Result: 15% × 15% widget in top-right corner
```

**Coordinate System:**
- (0, 0) = Bottom-left of window
- (1, 1) = Top-right of window

**Examples:**
- `(0.85, 0.85, 1.0, 1.0)` = Top-right, 15% size (our choice)
- `(0.0, 0.85, 0.15, 1.0)` = Top-left, 15% size
- `(0.0, 0.0, 0.15, 0.15)` = Bottom-left, 15% size
- `(0.8, 0.8, 1.0, 1.0)` = Top-right, 20% size (larger)

## Why This Fix Works

✅ **Explicit sizing** - No dependency on render state  
✅ **Consistent behavior** - Same size regardless of initialization order  
✅ **Small and unobtrusive** - 15% of viewport in top-right corner  
✅ **Matches expected behavior** - Same as when Display tab visited first  

## Testing

To verify the fix:
1. ✅ Load files → Solve → Switch to Display tab (widget should be small)
2. ✅ Load files → Switch to Display tab first (widget should be small)
3. ✅ Multiple solves (widget should stay small)
4. ✅ Window resize (widget should scale proportionally)

## Files Modified

**`src/ui/handlers/display_visualization_handler.py`:**
- Modified `update_visualization()` method
- Added explicit `viewport` parameter to `add_camera_orientation_widget()`
- Added explanatory comments

## Related Issues

This is a common PyVista/VTK issue when:
- Widgets added before first render
- No explicit sizing provided
- Render window state affects default calculations

## Conclusion

The orientation widget will now **always** appear in the correct position and size (top-right corner, 15% of viewport), regardless of:
- When the Display tab is first accessed
- Whether solve runs before or after visiting Display tab
- Window size or resolution

**Status:** ✅ Fixed - Widget will be consistently sized and positioned

