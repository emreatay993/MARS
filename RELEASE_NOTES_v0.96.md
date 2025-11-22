# MARS v0.96 Release Notes

**Release Date:** November 2025  
**Status:** Pre-Release / Active Development

---

## Overview

Version 0.95 represents a stabilization and refinement release of MARS (Modal Analysis Response Solver). This version focuses on improving code quality, adding visual polish, and ensuring that experimental features are properly gated until they are production-ready.

---

## What's New

### 🎨 Application Icon

MARS now features a professional, custom-designed icon with a Mars-themed aesthetic:

- **Icon Location:** `resources/icons/`
- **Formats Available:**
  - SVG source file (`mars_logo.svg`) for future modifications
  - PNG files in multiple resolutions (16, 32, 64, 128, 256, 512 pixels)
  - Windows ICO file with embedded sizes (`mars_icon.ico`)
- **Visual Design:**
  - Mars-inspired gradient background (deep reds and oranges)
  - Bold "M" letterform with lava-like radial gradient
  - Horizontal beams representing structural analysis
  - Wave pattern symbolizing modal vibrations
- **Automatic Application:** Icon is applied to window title bar and taskbar on application launch

**Files Added:**
- `resources/icons/mars_logo.svg`
- `resources/icons/mars_*.png` (multiple sizes)
- `resources/icons/mars_icon.ico`
- `resources/icons/generate_icons.py` (regeneration script)
- `resources/icons/README.md` (documentation)

---

### ✨ Animation Deformation Display Mode

**New Feature: User-Selectable Absolute vs. Relative Deformation Visualization**

Added a new checkbox control that gives users explicit control over how deformations are displayed during animation playback.

**Feature Overview:**
- **Location:** Display Tab → Visualization Controls → "Show Absolute Deformations" checkbox
- **Default:** Unchecked (Relative Mode) - maintains backward compatibility
- **Purpose:** Choose between two visualization modes for animation playback

**Two Visualization Modes:**

1. **Relative Mode (Unchecked - Default)**
   - Animation shows motion relative to the first animation frame
   - First frame appears at "zero" position (undeformed appearance)
   - Ideal for visualizing motion patterns, dynamics, and vibration modes
   - Better clarity when absolute offsets would obscure small motions

2. **Absolute Mode (Checked)**
   - Animation shows true deformation from undeformed geometry
   - Preserves absolute displacement magnitudes
   - Shows accumulated deformation history
   - Better for quantitative analysis and understanding total displacement

**Important Clarifications:**
- ✅ **Only affects mesh coordinate visualization** during animation playback
- ✅ **Does NOT affect** velocity or acceleration scalar field values
- ✅ **Does NOT affect** initial condition (IC) export (uses separate time point calculations)
- ✅ **Does NOT affect** any stress or physics calculations
- ✅ Default behavior matches previous version for backward compatibility

**User Interface:**
- Descriptive tooltip explains both modes and their use cases
- Checkbox becomes visible when animation controls are enabled
- Console output confirms which mode is active during animation precomputation

**Use Cases:**
- **Relative Mode:** Motion visualization, presentations, dynamics studies
- **Absolute Mode:** Quantitative analysis, steady-state + transient cases, validation

**Files Modified:**
- `src/ui/builders/display_ui.py` - Added checkbox UI component
- `src/ui/handlers/display_animation_handler.py` - Parameter collection
- `src/ui/handlers/analysis_handler.py` - Conditional zero-referencing logic
- `src/ui/display_tab.py` - Component reference setup

**Documentation Added:**
- `ANIMATION_DEFORMATION_MODE_IMPLEMENTATION.md` - Technical details
- `USER_GUIDE_ANIMATION_MODES.md` - User guide with examples
- `IMPLEMENTATION_SUMMARY.md` - Change summary

---

## Changes

### 🔧 User Interface

- **Window Title:** Updated from `MARS: Modal Analysis Response Solver - v1.0.0 (Modular)` to `MARS: Modal Analysis Response Solver - v0.95`
  - Removed "(Modular)" suffix for cleaner branding
  - Updated version number to reflect pre-release status

### 🔴 Plasticity Correction: IBG Algorithm Disabled

The **Incremental Buczynski-Glinka (IBG)** plasticity correction method has been **temporarily disabled** in this release.

**Status:**
- The IBG option appears in the plasticity method dropdown but is **greyed out and unselectable**
- The implementation exists in `src/solver/plasticity_engine.py` but is deactivated at the UI level
- Users should rely on **Neuber** or **Glinka** methods for plasticity corrections

**Reason for Disabling:**
- IBG requires additional algorithmic development and refinement
- Comprehensive verification against known test cases needed
- Validation with experimental data required
- Improvements to numerical robustness and accuracy planned

**Future Work:**
- IBG will be re-enabled in a future release once validation is complete
- Development tracked in `PLASTICITY_INTEGRATION_PLAN.md`

**Code Changes:**
- `src/ui/builders/solver_ui.py`: IBG combobox item disabled with `setEnabled(False)`
- Added TODO comment explaining the rationale and future work
- Updated `PLASTICITY_INTEGRATION_PLAN.md` with prominent status notice

---

### 🐛 Bug Fixes

**Fixed: Deformation Controls Visibility**

**Issue:** Deformation scale factor and "Show Absolute Deformations" checkbox were visible even when modal deformations were not loaded, causing UI clutter and user confusion.

**Fix:** 
- Deformation controls now properly hide when modal deformations are not loaded
- Controls only appear when deformation data is actually available
- Provides clear visual feedback about feature availability

**Impact:**
- Cleaner UI when deformations not loaded
- Reduced confusion about non-functional controls
- Better alignment with user expectations

**Files Modified:**
- `src/ui/display_tab.py` - Enhanced `_update_deformation_controls()` method to manage visibility
- `src/ui/display_tab.py` - Removed unconditional visibility in `on_time_values_ready()`

**Documentation:**
- `BUGFIX_DEFORMATION_CONTROLS_VISIBILITY.md` - Complete fix documentation with testing checklist

---

## Dependencies

### New Dependencies Added

The following libraries were added to support icon generation:

- `cairosvg==2.8.2` - SVG to PNG conversion
- `cairocffi==1.7.1` - Cairo graphics library bindings
- `cffi==2.0.0` - Foreign function interface
- `cssselect2==0.8.0` - CSS selector implementation
- `defusedxml==0.7.1` - Safe XML parsing
- `pycparser==2.23` - C parser for CFFI
- `tinycss2==1.4.0` - CSS parser
- `webencodings==0.5.1` - Character encoding support

**Note:** These dependencies are optional for running the application. They are only required if you need to regenerate the icon files from the SVG source.

**Existing Dependency:** `pillow` (already in requirements.txt) is used for ICO file generation.

---

## Documentation Updates

### Updated Files

1. **README.md**
   - Added version number (v0.95) at the top
   - Added "Important Notes (v0.95)" section documenting:
     - IBG plasticity algorithm status
     - Application icon information
   - Updated project structure to include `resources/icons/`

2. **PLASTICITY_INTEGRATION_PLAN.md**
   - Added prominent "IMPORTANT: IBG Algorithm Status" section
   - Documented reasons for disabling IBG
   - Added references to implementation details

3. **DELIVERY_MANIFEST.md**
   - Updated version to v0.95
   - Updated verification checklist with new title
   - Added "Recent Updates (v0.95)" section

4. **tests/MANUAL_TESTING_CHECKLIST.md**
   - Updated version to 0.95
   - Updated expected window title
   - Added icon verification step

5. **resources/icons/README.md** (New)
   - Documentation for icon system
   - Instructions for regenerating icons
   - Icon design description

---

## Version Numbering

The version has been changed from v1.0.0 to v0.95 to reflect:

1. **Pre-Release Status:** IBG plasticity feature is not yet production-ready
2. **Active Development:** Ongoing refinement and validation work
3. **Feature-Complete Core:** All other features (Neuber, Glinka plasticity, batch mode, time history, animations, etc.) are fully functional

**Path to v1.0.0:**
- Complete IBG algorithm verification and validation
- Enable IBG in UI
- Comprehensive testing of all plasticity methods
- Final documentation review

---

## Known Limitations

### Disabled Features

- **IBG Plasticity Correction:** Currently disabled (see Plasticity Correction section above)

### Platform-Specific Notes

- Icon system has been tested on Windows 10/11
- Linux and macOS users may experience slight variations in icon rendering

---

## Installation & Upgrade

### Fresh Installation

```bash
# Clone/download the project
cd MARS_

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run application
python src/main.py
```

### Upgrading from Previous Version

```bash
# Activate your existing virtual environment
venv\Scripts\activate  # Windows

# Update dependencies (new icon libraries added)
pip install -r requirements.txt --upgrade

# Run application
python src/main.py
```

**Note:** If you don't need to regenerate icons, the new dependencies (cairosvg, etc.) are optional but recommended for completeness.

---

## File Changes Summary

### Added Files
- `resources/icons/mars_logo.svg`
- `resources/icons/mars_16.png`
- `resources/icons/mars_32.png`
- `resources/icons/mars_64.png`
- `resources/icons/mars_128.png`
- `resources/icons/mars_256.png`
- `resources/icons/mars_512.png`
- `resources/icons/mars_icon.ico`
- `resources/icons/generate_icons.py`
- `resources/icons/README.md`
- `RELEASE_NOTES_v0.95.md` (this file)

### Modified Files
- `src/ui/application_controller.py` - Added icon loading logic
- `src/ui/builders/solver_ui.py` - Disabled IBG combobox item
- `requirements.txt` - Added icon generation dependencies
- `README.md` - Updated version and added status notes
- `PLASTICITY_INTEGRATION_PLAN.md` - Added IBG status notice
- `DELIVERY_MANIFEST.md` - Updated version and verification checklist
- `tests/MANUAL_TESTING_CHECKLIST.md` - Updated version and title

---

## Testing

### Manual Testing Required

1. **Application Launch:**
   - Verify window title shows "MARS: Modal Analysis Response Solver - v0.95"
   - Verify Mars-themed icon appears in title bar and taskbar

2. **Plasticity Correction:**
   - Open plasticity correction options
   - Verify "Neuber" and "Glinka" methods are selectable
   - Verify "Incremental Buczynski-Glinka (IBG)" is greyed out and unselectable
   - Verify successful runs with Neuber method
   - Verify successful runs with Glinka method

3. **Existing Features:**
   - Run full manual testing checklist (see `tests/MANUAL_TESTING_CHECKLIST.md`)
   - Verify all workflows remain functional

### Automated Testing

```bash
# Run unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## Migration Notes

### For Existing Users

- **No Breaking Changes:** All existing workflows continue to function as before
- **Window Title Changed:** Scripts or automation checking window titles should be updated
- **IBG Disabled:** If you were using IBG plasticity (experimental), switch to Neuber or Glinka

### For Developers

- Icon loading code is in `src/ui/application_controller.py` (`_set_window_icon()` method)
- IBG UI disabling is in `src/ui/builders/solver_ui.py` (line ~300)
- Icon resources are in `resources/icons/` directory

---

## Future Roadmap

### Planned for v1.0.0

1. **IBG Plasticity Algorithm:**
   - Complete verification against test cases
   - Validation with experimental data
   - Algorithm robustness improvements
   - Re-enable in UI

2. **Final Testing:**
   - Comprehensive regression testing
   - Performance benchmarking
   - Documentation review

3. **Release Preparation:**
   - Installer creation
   - Deployment documentation
   - User training materials

### Under Consideration

- Additional plasticity correction methods
- Enhanced visualization options
- Batch processing improvements
- Advanced export formats

---

## Support & Feedback

For questions, issues, or feedback regarding this release:

1. Check the documentation in the project root
2. Review `PLASTICITY_INTEGRATION_PLAN.md` for IBG status updates
3. See `START_HERE.md` for onboarding guidance
4. Refer to `ARCHITECTURE.md` for technical details

---

## Acknowledgments

This release represents continued refinement of the MARS codebase with focus on:
- Professional presentation (application icon)
- Quality assurance (feature gating)
- Clear communication (documentation updates)
- User trust (accurate version numbering)

Thank you for using MARS!

---

**Version:** 0.95  
**Release:** November 2025  
**Previous Version:** 1.0.0 (renumbered to reflect pre-release status)

