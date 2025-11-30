# MARS v0.97 Release Notes

**Release Date:** November 2025

## Overview

Version 0.97 focuses on improving the user experience in the Display tab, particularly around node interaction and camera behavior. Several bugs related to node picking, hover detection, and camera widget initialization have been fixed.

---

## Bug Fixes

### Node Hover Detection
- **Fixed:** Node hover tooltips now accurately display the node directly under the cursor
- **Changed:** Increased picker tolerance from 0.01 to 0.025 for better zoom-level compatibility
- **Technical:** Reverted to using `vtkPointPicker.GetPointId()` directly for more reliable node identification

### Time History Node Picking
- **Added:** Visual confirmation when picking a node for time history plotting
  - Black semi-transparent marker appears at selected node
  - Red "Node XXXXX" label displays the selected node ID
- **Fixed:** Camera no longer resets when picking a node - current view is preserved

### Hotspot Navigation
- **Fixed:** Camera now flies smoothly from current position to hotspot nodes
- **Fixed:** No unwanted camera reset when clicking nodes in the hotspot dialog table
- **Changed:** Added `reset_camera=False` to all `add_point_labels` calls during navigation

### Camera Orientation Widget
- **Fixed:** Camera orientation widget no longer appears oversized on first Display tab load
- **Technical:** Implemented deferred widget initialization using `showEvent` and `QTimer`
- **Changed:** Widget creation now waits for Qt layout to settle before rendering

---

## Files Modified

### Source Code
| File | Changes |
|------|---------|
| `src/ui/application_controller.py` | Version bump to v0.97 |
| `src/ui/display_tab.py` | Added `showEvent` handler for camera widget timing |
| `src/ui/handlers/display_visualization_handler.py` | Fixed hover detection, deferred camera widget |
| `src/ui/handlers/display_interaction_handler.py` | Added pick indicator, fixed camera reset issues |
| `src/ui/handlers/display_state.py` | Added `pick_indicator_actor` state field |

### Documentation
| File | Changes |
|------|---------|
| `FILE_INDEX.md` | Complete refresh with accurate line counts |
| `README.md` | Version bump, added v0.97 changelog entry |
| `ARCHITECTURE.md` | Version bump, documented v0.97 changes |
| `START_HERE.md` | Version bump |
| `MARS_UAT_Tests.txt` | Updated expected results for node picking |
| `MARS_UAT_Tests_User_Focused.txt` | Updated expected results for node picking |
| `MARS_UAT_Tests_Turkish.txt` | Updated expected results for node picking |

---

## Testing Recommendations

1. **Node Hover Test:** Load results, hover over nodes at various zoom levels, verify accurate NodeID display
2. **Time History Pick Test:** Use "Plot Time History for Selected Node", verify visual indicator appears and camera doesn't reset
3. **Hotspot Navigation Test:** Find hotspots, click table rows, verify smooth camera fly-to without reset
4. **Camera Widget Test:** Fresh application launch, navigate to Display tab, verify widget appears at correct size

---

## Compatibility

- No breaking changes from v0.96
- All existing functionality preserved
- Settings and file formats remain unchanged

---

## Known Issues

None specific to this release.

---

## Upgrade Instructions

1. Replace the `src/` folder with the updated version
2. No configuration changes required
3. No data migration needed

