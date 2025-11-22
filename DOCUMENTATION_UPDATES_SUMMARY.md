# DOCUMENTATION UPDATES SUMMARY

## Overview

This document summarizes comprehensive updates made to MARS user documentation to address previously undocumented or under-documented features discovered through code inspection.

**Date**: November 22, 2025  
**Version**: MARS v0.96  
**Scope**: All user-facing manuals

---

## Files Updated

1. **DETAILED_USER_MANUAL_20_Pages.md** (now 35 pages)
2. **QUICK_USER_MANUAL.md** 
3. **DETAILED_THEORY_MANUAL.md**

---

## Major Additions

### 1. Advanced Settings Dialog (NEW SECTION)

**Added to all three manuals**

Previously, the Settings menu was mentioned but never explained. Now fully documented:

#### Controls Documented:
- **RAM Allocation (%)**: 10-95% range, default 70%
  - When to increase (large datasets)
  - When to decrease (multitasking)
  - Impact on chunking behavior

- **Solver Precision**: Single vs. Double
  - Accuracy trade-offs (~7 vs ~15 significant digits)
  - Speed differences (2-4× faster for single)
  - Memory usage (2× for double)
  - When to use each

- **GPU Acceleration**: NVIDIA CUDA toggle
  - Requirements (CUDA toolkit, compatible GPU)
  - Expected speedup (2-10× for large models)
  - Automatic CPU fallback behavior

#### Location in Manuals:
- **Detailed Manual**: New Page 15 (all subsequent pages renumbered)
- **Quick Manual**: New Section 4
- **Theory Manual**: New Section 10 "Computational Precision and Performance"

---

### 2. Plasticity Correction Enhancements

**Enhanced in all three manuals**

#### New Sub-features Documented:

##### A. Temperature Field File Format
**Previously**: Mentioned in passing  
**Now**: Fully specified

- File format: **CSV** (corrected from misleading .txt button label)
- Required columns: `NodeID`, `Temperature`
- Units consistency requirements
- Common mistakes section
- Example file snippet

**Location**: 
- Detailed Manual: Page 13 (new subsection)
- Quick Manual: Section 6
- Theory Manual: Section 8.6.3 (expanded)

##### B. Iteration Controls
**Previously**: Not mentioned  
**Now**: Fully documented

- **Max Iterations** parameter (default 60, range 1-10000)
- **Tolerance** parameter (default 1e-10)
- When to adjust each
- Trade-offs (accuracy vs. robustness)
- Warning label behavior

**Location**:
- Detailed Manual: Page 13
- Theory Manual: Section 8.5.4 (new subsection)

##### C. Plasticity Diagnostics
**Previously**: Not mentioned  
**Now**: Documented as advanced feature

- Purpose: Overlay Δεₚ and εₚ on Time History plots
- When to use (validation, debugging)
- How to interpret the curves

**Location**:
- Detailed Manual: Page 13
- Quick Manual: Section 6
- Theory Manual: Section 8.6.4

---

### 3. "Skip First n Modes" Feature

**Enhanced from one-liner to full explanation**

**Previously**: "Use Skip first n modes to exclude initial modes if desired"  
**Now**: Complete guidance including:

- When to use (rigid-body modes, erroneous data)
- Typical values (0 for fixed structures, 6 for free-free)
- Warning about accuracy impact
- How to determine from modal participation factors

**Location**:
- Detailed Manual: Page 10 (expanded)
- Quick Manual: Step 7 (clarified)
- FAQ: New entry

---

### 4. Animation Controls: "Every nth" Throttling

**Enhanced from brief mention to detailed explanation**

**Previously**: "Actual Data Time Steps (throttle with Every nth)"  
**Now**: Full documentation:

- What "Every nth" does (frame skipping)
- When to use (large datasets, smoother playback)
- Example values and their effects
- Comparison with Custom Time Step mode

**Location**:
- Detailed Manual: Page 21 (completely rewritten)
- Quick Manual: Section 5 (clarified)

---

### 5. Navigator File Filtering

**New documentation of hidden behavior**

**Previously**: Not mentioned  
**Now**: Documented that Navigator automatically filters to `.mcf`, `.csv`, `.txt` files only

**Location**:
- Detailed Manual: Page 5 (note added)
- FAQ: New entry

---

## Troubleshooting Updates

### New Entries Added:

| Issue | Fix | Manual(s) |
|-------|-----|-----------|
| GPU not being used | Check Settings → Advanced; install CUDA or disable | Detailed (Page 29), Quick (Section 8) |
| Solver very slow | Increase RAM %, switch to Single precision, or enable GPU | Detailed (Page 29), Quick (Section 8) |
| Temperature file error | Use CSV format with NodeID, Temperature columns | Detailed (Page 29), Quick (Section 8) |

---

## FAQ Updates

### New Questions Added to Detailed Manual (Page 34):

1. **Q**: How do I speed up large analyses?  
   **A**: Go to Settings → Advanced. Increase RAM allocation to 90%, switch to Single precision, or enable GPU acceleration if you have NVIDIA CUDA.

2. **Q**: What does "Skip first n modes" do?  
   **A**: Excludes the first n modes from analysis. Use this to skip rigid-body modes (usually 6 for free-free structures) or modes with bad data.

3. **Q**: Why can't I see all files in the Navigator?  
   **A**: Navigator automatically filters to show only .mcf, .csv, and .txt files relevant to MARS workflows.

---

## File Format Reference Updates

### Page 33 (Detailed Manual)

Added **Temperature field .csv** to file format reference:
- Format specification
- Required columns
- Example snippet

---

## Theory Manual Enhancements

### New Section 10: "Computational Precision and Performance"

Comprehensive technical discussion of:

#### 10.1 Floating-Point Precision
- Single vs. Double precision characteristics
- Significand digits, range, memory
- Speed comparisons
- Suitability criteria

#### 10.2 Memory Management
- RAM allocation impact
- Chunking behavior
- Typical memory requirements by model size

#### 10.3 GPU Acceleration
- Which operations are accelerated
- Expected speedup profiles
- CUDA requirements
- Fallback behavior

### Section 8.5.4: Iteration Control Parameters (NEW)

Technical deep dive on Newton-Raphson solver tuning:
- Max Iterations: purpose, range, when to adjust
- Tolerance: definition, trade-offs
- Accuracy impact of relaxed settings

### Section 8.6.3: Temperature Field File (EXPANDED)

- Format requirements (CSV, not .txt)
- Common mistakes
- Unit consistency
- Node coverage requirements

### Section 8.6.4: Advanced Tuning (NEW)

- Iteration controls in workflow context
- Plasticity diagnostics interpretation
- Debugging non-convergence

---

## Page Number Changes (Detailed Manual)

Due to insertion of new Page 15 (Advanced Settings), all subsequent pages renumbered:

| Old Page | New Page | Section |
|----------|----------|---------|
| 15 | 16 | Console & Plot Tabs |
| 16 | 17 | Switch to Display Tab |
| 17 | 18 | Hover, Colorbar, Point Size |
| 18 | 19 | Compute Time Point Field |
| 19 | 20 | Load External CSV |
| 20 | 21 | Animate Your Results |
| 21 | 22 | Right-Click Context Menu |
| 22 | 23 | Find Hotspots |
| 23 | 24 | Select Area with Box |
| 24 | 25 | Go To Node & Track |
| 25 | 26 | Batch Workflow |
| 26 | 27 | Time History Workflow |
| 27 | 28 | Export Results |
| 28 | 29 | Troubleshooting |
| 29 | 30 | Tips for Clear Visuals |
| 30 | 31 | Keyboard & Mouse |
| 31 | 32 | Review Checklist |
| 32 | 33 | File Format Notes |
| 33 | 34 | FAQs |
| 34 | 35 | Getting Help |

**Result**: Manual grew from **34 pages to 35 pages** with substantial content additions throughout.

---

## Quick Manual Section Renumbering

| Old Section | New Section | Title |
|-------------|-------------|-------|
| 4 | 5 | Display Tab Fast Facts |
| 5 | 6 | Plasticity Correction Quick Reference (NEW) |
| 6 | 7 | Exports at a Glance |
| 7 | 8 | Quick Troubleshooting |
| (none) | 4 | Advanced Settings (NEW) |
| 8 | 9 | Need More Detail? |

---

## Theory Manual Section Renumbering

| Old Section | New Section | Title |
|-------------|-------------|-------|
| 10 | 11 | Assumptions & Limitations |
| 11 | 12 | Verification Checklist |
| 12 | 13 | Further Study Resources |
| 13 | 14 | Glossary |
| (none) | 10 | Computational Precision and Performance (NEW) |

---

## Glossary Additions (Theory Manual)

Four new terms added:

1. **Single precision**: Floating-point format with ~7 significant digits; faster but less accurate.
2. **Double precision**: Floating-point format with ~15 significant digits; slower but more accurate.
3. **GPU acceleration**: Use of NVIDIA CUDA for parallel matrix operations; requires compatible hardware.
4. **RAM allocation**: Percentage of system memory MARS is allowed to use for solver operations.

---

## Cross-References Added

Throughout updates, added cross-references between manuals:

- Detailed Manual → Theory Manual (Section 8.5.4 for iteration controls)
- Quick Manual → Detailed Manual (Page 13 for temperature field format)
- Troubleshooting → Advanced Settings (Page 15)
- FAQ → Multiple sections

---

## Quality Improvements

### Consistency Fixes

1. **Temperature Field File Extension**: 
   - Corrected documentation to specify **CSV format**
   - Noted discrepancy with UI button label (.txt)
   - Added warning in troubleshooting

2. **Terminology Standardization**:
   - "Plasticity Diagnostics" (consistent naming)
   - "Advanced Settings" (not "Global Settings")
   - "RAM Allocation" (not "Memory Limit")

3. **Parameter Naming**:
   - Fatigue parameters: Changed from "A and m" to "σ'f and b" (matches Coffin-Manson notation)
   - Clarified context in all three manuals

---

## User Impact Assessment

### High Impact (Critical for user success):
✅ **Advanced Settings**: Performance tuning is now discoverable  
✅ **Temperature Field Format**: Prevents setup errors  
✅ **Iteration Controls**: Enables handling difficult convergence cases

### Medium Impact (Improves user experience):
✅ **Skip Modes Guidance**: Prevents accuracy degradation  
✅ **Animation Throttling**: Enables working with large datasets  
✅ **Plasticity Diagnostics**: Supports advanced validation

### Low Impact (Nice to have):
✅ **Navigator Filtering**: Explains observed behavior  
✅ **Glossary Additions**: Reference completeness

---

## Validation Checklist

- [x] All three manuals updated consistently
- [x] Page numbers corrected throughout Detailed Manual
- [x] Cross-references validated
- [x] New sections integrated into existing flow
- [x] Troubleshooting table expanded
- [x] FAQ section updated
- [x] Glossary expanded
- [x] File format reference complete
- [x] No contradictions introduced
- [x] Technical accuracy verified against code

---

## Recommendations for Next Steps

### Short Term:
1. **Update UI Button Label**: Change "Read Temperature Field File (.txt)" to "Read Temperature Field File (.csv)"
2. **Add Material Profile Import/Export**: Consider adding CSV import for material curves (currently manual entry only)
3. **Tooltips**: Add hover tooltips to Advanced Settings dialog matching manual explanations

### Medium Term:
4. **Percentile Presets**: If planned for scalar range (mentioned in code search but not found), document when added
5. **IBG Method**: When re-enabled, update all three manuals with full workflow
6. **Video Tutorials**: Create screencast for Advanced Settings configuration

### Long Term:
7. **Case Studies**: Add example analyses demonstrating when to use each Advanced Setting
8. **Benchmark Data**: Include performance benchmarks for Single vs. Double, CPU vs. GPU
9. **Material Database**: Provide example temperature-dependent material profiles for common alloys

---

## Files Ready for Review

All three updated manuals are ready for:
- Technical review by developers
- User acceptance testing
- Inclusion in next release documentation package

---

## Conclusion

These updates address **10 major documentation gaps** discovered through systematic code inspection:

1. Advanced Settings dialog (complete feature)
2. Plasticity iteration controls (GUI parameters)
3. Plasticity diagnostics (advanced feature)
4. Temperature field format (file specification)
5. Skip modes guidance (when/why/how)
6. Animation throttling (Every nth)
7. Navigator filtering (hidden behavior)
8. GPU acceleration details (requirements, behavior)
9. Precision selection (trade-offs)
10. RAM allocation (performance tuning)

**Total content added**: ~2,500 words across three manuals  
**New sections**: 3 major sections + 8 subsections  
**Pages added**: 1 (Detailed Manual: 34 → 35 pages)  
**Troubleshooting entries**: +3  
**FAQ entries**: +3  
**Glossary terms**: +4

All updates maintain consistency with existing documentation style, technical accuracy verified against implementation code.

