# UI Stylesheet Fix Summary

## Problem Identified

The refactored codebase had **over-applied stylesheets** compared to the legacy codebase, causing the UI to look different. The issue was:

### Legacy Approach (Correct)
- **NO global application-wide stylesheet**
- Styles defined as local string variables in Python code
- Applied **selectively** only to specific widgets that needed them
- Used `QPalette` to set window background color to light gray (RGB: 230, 230, 230)

### Refactored Approach (Problem)
1. **Global stylesheet** applied to entire `QApplication` at startup
2. **Additional widget-specific stylesheets** applied in various places
3. Builders trying to apply **non-existent style files** ("buttons", "inputs", etc.)
4. This created **double/triple styling conflicts** and broke inheritance

## Solution Implemented (Option 1)

Removed global stylesheet application and applied styles selectively to match legacy behavior.

## Changes Made

### 1. Main Application Entry Point (`src/main.py`)
- ✅ Removed global stylesheet initialization
- ✅ Removed `init_styles(app)` call that was applying all styles globally
- ✅ Added comment explaining selective styling approach

### 2. Style Manager (`src/ui/styles/style_manager.py` and `__init__.py`)
- ✅ Updated `apply_style()` method to apply specific stylesheets to individual widgets
- ✅ Deprecated `apply_global_styles()` method (now returns False)
- ✅ Removed `init_styles()` function from `__init__.py`
- ✅ Added documentation explaining selective widget styling

### 3. Main Windows (`src/ui/application_controller.py` and `src/ui/main_window.py`)
- ✅ Added `QPalette` with light gray background color (230, 230, 230) matching legacy
- ✅ Changed from `apply_widget_specific_style()` to `apply_style()` for menu bar
- ✅ Changed from `apply_widget_specific_style()` to `apply_style()` for navigator dock
- ✅ Changed from `apply_widget_specific_style()` to `apply_style()` for tab widget
- ✅ Simplified style applications to match legacy approach

### 4. Tab Widgets (`src/ui/solver_tab.py` and `src/ui/display_tab.py`)
- ✅ Added `apply_style(self, "main")` to apply main.qss stylesheet to tab itself
- ✅ This allows all child widgets to **inherit** styles from parent
- ✅ Added import for `get_style_manager`

### 5. UI Builders (`src/ui/builders/solver_ui.py` and `display_ui.py`)
- ✅ Removed ALL individual widget style applications (35+ instances in solver_ui.py)
- ✅ Removed ALL individual widget style applications (8 instances in display_ui.py)
- ✅ Removed attempts to apply non-existent style files like "buttons", "inputs", "checkboxes", etc.
- ✅ Child widgets now inherit styles from parent tabs

### 6. Display Tab Context Menu (`src/ui/display_tab.py`)
- ✅ Changed from `apply_widget_specific_style()` to `apply_style()` for context menu

## How It Works Now

1. **No global stylesheet** applied to QApplication
2. **Main window** gets light gray background via QPalette
3. **Menu bar**, **navigator dock**, and **tab widget** get selective styles applied
4. **Each tab** (Solver and Display) gets `main.qss` applied to it
5. **All child widgets** (buttons, checkboxes, line edits, group boxes, etc.) **inherit** styles from their parent tabs
6. This matches the legacy approach where styles cascaded naturally through the widget hierarchy

## Files Modified

- `src/main.py`
- `src/ui/styles/style_manager.py`
- `src/ui/styles/__init__.py`
- `src/ui/application_controller.py`
- `src/ui/main_window.py`
- `src/ui/solver_tab.py`
- `src/ui/display_tab.py`
- `src/ui/builders/solver_ui.py`
- `src/ui/builders/display_ui.py`

## Expected Result

The UI should now look identical to the legacy codebase with:
- Light gray window background
- Properly styled buttons, inputs, group boxes, tabs, etc.
- All widgets inheriting styles naturally from their parents
- No style conflicts or over-application issues

## Testing Recommendations

1. Launch the application and verify the window background is light gray
2. Check that all buttons have the blue theme color (#e7f0fd background, #5b9bd5 border)
3. Verify group boxes have proper borders and titles
4. Check tabs have the correct selected/unselected appearance
5. Ensure checkboxes, line edits, and other controls match legacy styling
6. Test all UI elements for consistent appearance across both tabs

## Date
October 25, 2025

