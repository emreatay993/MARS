# Quick User Guide: Animation Deformation Modes

## What is This?

A new checkbox that lets you choose how deformations are displayed in animations.

## Where to Find It

**Location:** Visualization Controls → "Show Absolute Deformations" checkbox

![Checkbox Location]
- Located next to the "Deformation Scale Factor" input
- Appears when you load a mesh and animation controls become available
- Initially hidden, becomes visible with animation controls

## Two Modes Explained

### 🔄 Relative Mode (Checkbox UNCHECKED - Default)

**What you see:**
- Animation starts from "zero" position
- Shows how the structure MOVES during the animation time window
- First frame appears undeformed

**Best for:**
- 👁️ Visualizing motion patterns
- 🌊 Seeing vibration and oscillation behavior
- 📊 Presentations where clarity of motion is important

**Example:**
```
Your animation runs from t=0.3s to t=0.8s
┌─────────────────────────────────┐
│ t=0.3s: Structure at "zero"     │  ← Appears undeformed
│ t=0.5s: +1.5mm from start       │
│ t=0.8s: +3.0mm from start       │
└─────────────────────────────────┘
```

### 📍 Absolute Mode (Checkbox CHECKED)

**What you see:**
- Animation shows TRUE deformation from original geometry
- First frame shows any pre-existing deformation
- Preserves absolute position information

**Best for:**
- 📐 Accurate deformation measurements
- ⚙️ When pre-loading or steady-state effects matter
- ✅ Validation against reference data
- 📊 Understanding total accumulated deformation

**Example:**
```
Your animation runs from t=0.3s to t=0.8s
┌─────────────────────────────────┐
│ t=0.3s: Structure at +2.5mm     │  ← Shows accumulated deformation
│ t=0.5s: Structure at +4.0mm     │
│ t=0.8s: Structure at +5.5mm     │
└─────────────────────────────────┘
```

## Quick Decision Guide

### Use Relative Mode (Leave Unchecked) If:

- ✅ You want to see motion patterns clearly
- ✅ Starting time doesn't matter much
- ✅ Making animations for presentations
- ✅ Studying vibration behavior
- ✅ Large initial offsets would hide small motions

### Use Absolute Mode (Check the Box) If:

- ✅ Animation doesn't start at t=0
- ✅ You have steady-state loading
- ✅ Absolute deformation values matter
- ✅ Pre-stress or pre-deformation is present
- ✅ Need to see total accumulated displacement

## Step-by-Step Instructions

### To Use Relative Mode (Default):

1. Load your mesh and data files
2. Set your animation time range
3. **Leave the checkbox UNCHECKED** ⬜
4. Click "Play" to start animation
5. Console will show: `Animation mode: Relative deformations (zero-referenced to start frame)`

### To Use Absolute Mode:

1. Load your mesh and data files
2. Set your animation time range
3. **CHECK the "Show Absolute Deformations" box** ✅
4. Click "Play" to start animation
5. Console will show: `Animation mode: Absolute deformations (from undeformed geometry)`

## Common Scenarios

### Scenario 1: Viewing an Impact Event (t=0.2s to t=0.5s)

**Relative Mode:** Shows the motion during impact clearly
**Absolute Mode:** Shows the structure was already deformed before impact started

**Recommendation:** Use **Relative** for motion visualization, **Absolute** for quantitative analysis

### Scenario 2: Thermal Expansion + Vibration

**Relative Mode:** Removes thermal expansion, shows only vibration
**Absolute Mode:** Shows thermal expansion + vibration combined

**Recommendation:** Use **Absolute** to see total effect, **Relative** to isolate vibration

### Scenario 3: Exporting IC at t=0.5s for Another Analysis

**Important Note:** IC export uses TIME POINT calculation (via "Update" button), NOT animation data.
The checkbox does NOT affect IC export - velocity values are always computed correctly.

**Relative Mode:** ✅ Works fine - IC export unaffected
**Absolute Mode:** ✅ Works fine - IC export unaffected

**Recommendation:** Use either mode - the checkbox only affects visualization coordinates, not exported IC values

### Scenario 4: Making a Video for Presentation

**Relative Mode:** ✅ Better! Motion is clearer when starting from "zero"
**Absolute Mode:** ⚠️ Might work, but could be less visually clear

**Recommendation:** Use **Relative** for most presentations

## Troubleshooting

### Problem: "My animation looks different than before!"

**Solution:** The default behavior hasn't changed. If animations look different, check:
1. Is the checkbox checked? (It should be unchecked for old behavior)
2. Did your animation start time change?
3. Check console output to confirm which mode is active

### Problem: "I can't see the checkbox"

**Solution:** The checkbox only appears when:
1. A mesh is loaded
2. Animation controls are visible
3. Check the Visualization Controls section (same row as Deformation Scale Factor)

### Problem: "My exported initial conditions are wrong"

**Solution:** IC export uses TIME POINT calculations, not animation data. The checkbox does NOT affect IC export. To export IC:
1. Select the desired time point using the spinbox
2. Choose "Velocity" in the solver tab
3. Click "Update" button (not "Play")
4. Click "Export Velocity as Initial Condition in APDL"

The checkbox only affects animation visualization, not IC export values.

### Problem: "The first frame looks weird in absolute mode"

**Explanation:** This is normal! Absolute mode shows the structure's true state at the animation start time, which may already be deformed due to:
- Prior loading history (t=0 to t=start)
- Steady-state effects (thermal, static loads)
- Prestress conditions

This is the correct physical behavior.

## Tips and Tricks

💡 **Tip 1:** Check the console output after clicking "Play" to confirm which mode is active

💡 **Tip 2:** For zoom/scale issues, adjust the "Deformation Scale Factor" - it works in both modes

💡 **Tip 3:** The mode is set when you click "Play" - you can't change it during playback. Stop and restart to change modes.

💡 **Tip 4:** When in doubt, try both modes! The computation is fast, and seeing both helps understand your data.

💡 **Tip 5:** For publications and reports, document which mode you used. The mode choice affects quantitative interpretations.

## Technical Notes

- **Memory:** No additional memory used - just a different processing of the same data
- **Performance:** No performance difference between modes
- **Compatibility:** Default behavior matches previous versions for backward compatibility

## Questions?

**Q: Which mode is "correct"?**  
A: Both are correct! They show different aspects of the same data. Choose based on your analysis needs.

**Q: Can I change modes during playback?**  
A: No. Stop the animation and restart with the new setting.

**Q: Does this affect saved videos?**  
A: Yes! The video will show whatever mode was active when you saved it. Choose carefully.

**Q: What about the deformation magnitude values shown?**  
A: In relative mode, they show displacement from start frame. In absolute mode, they show total displacement from undeformed geometry.

## Summary Table

| Feature | Relative Mode | Absolute Mode |
|---------|--------------|---------------|
| **Checkbox** | Unchecked ⬜ | Checked ✅ |
| **First Frame** | Appears undeformed | Shows true state |
| **Mesh Position** | Relative to start | Absolute from origin |
| **Best For** | Motion patterns | Quantitative analysis |
| **IC Export** | ✅ Unaffected | ✅ Unaffected |
| **Presentations** | ✅ Recommended | ⚠️ Case-dependent |
| **Steady-State** | Removes offset | Preserves offset |
| **Velocity/Accel Values** | ✅ Correct | ✅ Correct |
| **Default** | Yes | No |

---

**Remember:** When in doubt, check the console output and try both modes to see which makes sense for your analysis! 🎯

