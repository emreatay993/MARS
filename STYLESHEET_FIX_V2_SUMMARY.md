# UI Stylesheet Fix V2 - Centralized Inline Styles

## Issue
The previous fix attempted to use external QSS files, but Qt's stylesheet cascading doesn't work the same way as CSS. The legacy code used **inline Python string styles** applied directly to individual widgets via `setStyleSheet()`.

## Solution Implemented
Created a **centralized style constants module** (`src/ui/styles/style_constants.py`) that contains all inline stylesheet strings as Python constants, matching the legacy approach but with clean, maintainable code.

## Changes Made

### 1. New File: `src/ui/styles/style_constants.py`
Created centralized module with all style constants:
- `BUTTON_STYLE` - Blue-themed button styling
- `GROUP_BOX_STYLE` - Group box borders and titles
- `TAB_STYLE` - Tab widget appearance
- `READONLY_INPUT_STYLE` - Read-only line edit styling
- `CHECKBOX_STYLE` - Checkbox margins
- `CONSOLE_STYLE` - Console/TextEdit styling
- `PROGRESS_BAR_STYLE` - Progress bar styling
- `NAVIGATOR_TITLE_STYLE` - Dock widget title styling
- `TREE_VIEW_STYLE` - Tree view and header styling
- `MENU_BAR_STYLE` - Menu bar and menu styling

### 2. Updated UI Builders
**`src/ui/builders/solver_ui.py`:**
- Removed local style string definitions
- Imported style constants from `style_constants`
- Applied styles using: `widget.setStyleSheet(BUTTON_STYLE)`

**`src/ui/builders/display_ui.py`:**
- Same approach as solver_ui.py
- Clean builder code with centralized styles

### 3. Updated Main Windows
**`src/ui/application_controller.py` and `src/ui/main_window.py`:**
- Removed `get_style_manager()` usage
- Imported style constants
- Applied styles directly: `self.menu_bar.setStyleSheet(MENU_BAR_STYLE)`

### 4. Updated Tab Classes
**`src/ui/solver_tab.py` and `src/ui/display_tab.py`:**
- Removed tab-level stylesheet application
- Child widgets get styles from builders (not inherited from parent tab)

## How It Works

1. **Style Constants Module** (`style_constants.py`): Contains all inline style strings
2. **Builders Import Styles**: Builders import needed constants
3. **Direct Application**: Styles applied to widgets using `setStyleSheet()`
4. **Clean Code**: Builders don't define styles locally
5. **Centralized Maintenance**: All styles in one place

## Advantages

✅ **Matches Legacy Behavior**: Uses inline Python strings like legacy
✅ **Centralized**: All styles in one module
✅ **Clean Builder Code**: No style definitions scattered in builders
✅ **Easy Maintenance**: Change styles in one place
✅ **Qt-Compatible**: Uses `setStyleSheet()` correctly

## Files Modified

- ✅ Created: `src/ui/styles/style_constants.py`
- ✅ Updated: `src/ui/builders/solver_ui.py`
- ✅ Updated: `src/ui/builders/display_ui.py`
- ✅ Updated: `src/ui/application_controller.py`
- ✅ Updated: `src/ui/main_window.py`
- ✅ Updated: `src/ui/solver_tab.py`
- ✅ Updated: `src/ui/display_tab.py`

## Expected Result

The UI should now look **exactly** like the legacy codebase with:
- Light gray window background (RGB: 230, 230, 230)
- Blue-themed buttons (#e7f0fd background, #5b9bd5 border)
- Styled group boxes with blue borders
- Properly styled tabs, checkboxes, inputs
- Read-only inputs with gray background
- Styled navigator and menu bar

## Testing
Run the application and verify:
1. Window background is light gray
2. All buttons have blue theme colors
3. Group boxes have blue borders and titles
4. Tabs show proper selected/unselected states
5. UI matches legacy screenshots

## Date
October 25, 2025

