# DETAILED USER MANUAL · MARS: Modal Analysis Response Solver (GUI Edition)

> Audience: Mechanical/structural engineers using MARS via the desktop GUI
> Purpose: Step-by-step, click-by-click guidance with mock-up image placeholders

---

## Page 1 – Welcome & What You Can Do

MARS turns modal analysis inputs into stress maps, time histories, animations, and fatigue indicators. This guide shows exactly where to click to: load inputs, run analyses, visualize results, export CSVs and videos, detect hotspots, and focus on specific nodes.

- No programming required.
- Assumes you have modal coordinate, modal stress, and optional deformation/steady-state files.

[Image Placeholder: Main Window overview — tabs, navigator, menu]

---

## Page 2 – Quick Tour of the Interface

- Menu bar: File, View, Settings
- Left: Navigator (file browser)
- Tabs: Main Window (Solver) and Display

Key idea: Load and run on the Main Window tab, explore and export on the Display tab.

[Image Placeholder: UI callouts — 1) Menu, 2) Navigator, 3) Tabs]

---

## Page 3 – Before You Start

Have the following ready:
- Modal coordinates file (.mcf)
- Modal stress file (.csv)
- Optional: Deformation file (.csv)
- Optional: Steady-state stress (.txt)

Tip: Keep Node IDs and units consistent across files.

[Image Placeholder: Example file set in a project folder]

---

## Page 4 – Set the Project Directory

1) Click File → Select Project Directory
2) Choose the folder that contains your .mcf/.csv/.txt files
3) The Navigator updates to that folder

[Image Placeholder: File menu — Select Project Directory]

---

## Page 5 – Navigator Basics

- Double-click files to load them into appropriate fields.
- Sort by name or type; resize columns.
- Use View → Navigator to hide/show the panel.

[Image Placeholder: Navigator with .mcf, .csv, .txt highlighted]

---

## Page 6 – Load Modal Coordinates (.mcf)

On the Main Window tab:
1) Click Read Modal Coordinate File (.mcf)
2) Pick your .mcf file
3) The path box fills and the Console notes success

The SOLVE button will be enabled after you also load stress.

[Image Placeholder: Buttons and path fields on Main Window]

---

## Page 7 – Load Modal Stress (.csv)

1) Click Read Modal Stress File (.csv)
2) Select the stress CSV
3) Stress-dependent outputs (e.g., Von-Mises, Principal) become available

Tip: If your CSV also contains X,Y,Z, hover on the Display tab will show Node IDs with coordinates.

[Image Placeholder: Stress file loaded — checkboxes enabled]

---

## Page 8 – Optional: Include Steady-State Stress

1) Tick Include Steady-State Stress Field (Optional)
2) Click Read Full Stress Tensor File (.txt)
3) Select the steady-state file

This adds static bias to the reconstructed stresses.

[Image Placeholder: Steady-state toggle revealing file input]

---

## Page 9 – Optional: Include Deformations

1) Tick Include Deformations (Optional)
2) Click Read Modal Deformations File (.csv)
3) Select the deformation CSV

This unlocks Deformation, Velocity, and Acceleration outputs and enables deformed animations.

[Image Placeholder: Deformation toggle revealing file input]

---

## Page 10 – Choose Outputs

Under Outputs:
- Time History Mode (Single Node) — for a single node time plot
- Max Principal Stress — s1 envelope
- Min Principal Stress — s3 envelope
- Von-Mises Stress — standard ductile metric
- Deformation / Velocity / Acceleration — require deformations loaded
- Damage Index / Potential Damage — appears when Von-Mises is selected (if enabled)

Use Skip first n modes to exclude initial modes if desired.

[Image Placeholder: Outputs group with checkboxes annotated]

---

## Page 11 – Time History Mode (Single Node)

1) Tick Time History Mode (Single Node)
2) In Scoping, enter the Node ID
3) Select one time-history quantity (e.g., Von-Mises or s1)
4) Click SOLVE to plot

The Time History plot appears in the Plot (Time History) tab.

[Image Placeholder: Scoping group and time history checkbox]

---

## Page 12 – Fatigue Parameters (If Damage Enabled)

When Damage Index / Potential Damage is available:
1) Tick Damage Index / Potential Damage
2) In Fatigue Parameters, enter σ'f and b
3) Click SOLVE

Interpret damage maps carefully and verify material constants.

[Image Placeholder: Fatigue parameters σ'f and b]

---

## Page 13 – Run the Analysis

1) Ensure both .mcf and stress .csv are loaded
2) Select desired outputs
3) Click SOLVE
4) Watch Console messages and the Progress Bar

When finished, proceed to the Display tab to explore results.

[Image Placeholder: SOLVE button and progress bar]

---

## Page 14 – Console & Plot Tabs (Main Window)

- Console: shows load/validation messages and processing steps
- Plot (Time History): appears when Time History mode is active
- Plot (Modal Coordinates): used to inspect coordinate amplitudes

Use these for quick validation before switching to the Display tab.

[Image Placeholder: Console and plot tabs]

---

## Page 15 – Switch to Display Tab

Click the Display tab to see the 3D view and controls:
- Load Visualization File (for CSV-based meshes)
- Visualization Controls (point size, legend range, deformation scale)
- Initialization & Time Point Controls (time selection, save CSV, export APDL IC)
- Animation Controls (playback and export)

[Image Placeholder: Display tab at first view]

---

## Page 16 – Hover, Colorbar, and Point Size

- Hover over points to see Node ID and current scalar value
- Adjust Node Point Size for clarity
- Set Legend Range Min/Max to focus the color scale

Tip: Reset camera after large changes for a clean view.

[Image Placeholder: Hover tooltip showing NodeID and value]

---

## Page 17 – Compute a Time Point Field

When initialization is complete (after SOLVE), enable time point workflows:
1) In Initialization & Time Point Controls, set Time (seconds)
2) Click Update to compute node-wise values for that instant
3) Use Save Time Point as CSV to export what you see

If deformations exist, you can also Export Velocity as Initial Condition in APDL.

[Image Placeholder: Time point panel with callouts]

---

## Page 18 – Load External CSV Results

To visualize an external CSV:
1) Click Load Visualization File
2) Select a CSV with X, Y, Z, optional NodeID, and at least one scalar column
3) The first scalar column becomes active; adjust legend and point size

Use this to compare alternatives or post-process snapshots.

[Image Placeholder: External CSV loaded into plotter]

---

## Page 19 – Animate Your Results

1) Choose Time Step Mode:
   - Custom Time Step (enter Step in seconds)
   - Actual Data Time Steps (throttle with Every nth)
2) Set Interval (ms)
3) Set Start and End times
4) Click Play; Pause or Stop as needed
5) Click Save as Video/GIF to export (MP4 needs ffmpeg)

If deformations were provided, geometry deforms during playback.

[Image Placeholder: Animation controls — play/pause/stop]

---

## Page 20 – Right-Click Context Menu (Display)

Right-click anywhere on the 3D view to access:
- Selection Tools: Add/Remove Selection Box, Pick Box Center
- Hotspot Analysis: Find Hotspots (current view) or in Selection
- Point-Based Analysis: Plot Time History for Selected Node
- View Control: Go To Node, Lock Camera for Animation, Reset Camera

[Image Placeholder: Context menu with sections labeled]

---

## Page 21 – Find Hotspots

1) Right-click → Find Hotspots (on current view) or in Selection
2) Enter how many top nodes to find
3) A dialog lists the nodes with highest values
4) Click a node to label and zoom to it

Use hotspots to shortlist critical regions for detailed checks.

[Image Placeholder: Hotspot dialog with table]

---

## Page 22 – Select an Area with a Box

1) Right-click → Add Selection Box
2) Right-click → Pick Box Center, then click to position
3) Drag handles to resize
4) Run Find Hotspots in Selection

Use box selection to focus on sub-assemblies.

[Image Placeholder: Selection box around a region]

---

## Page 23 – Go To Node & Track During Animation

1) Right-click → Go To Node
2) Enter a Node ID to fly the camera there
3) Right-click → Lock Camera for Animation (freeze node) to keep focus during playback
4) Right-click → Reset Camera to restore the default view

[Image Placeholder: Node target marker and label]

---

## Page 24 – Batch Workflow (Checklist)

1) Load .mcf
2) Load stress .csv
3) (Optional) Load steady-state .txt
4) (Optional) Load deformations .csv
5) Choose outputs
6) (Optional) Set Skip first n modes
7) SOLVE
8) Display → adjust legend → hotspots → screenshots/exports

[Image Placeholder: Batch flow diagram]

---

## Page 25 – Time History Workflow (Checklist)

1) Load .mcf and stress .csv
2) Tick Time History Mode
3) Enter Node ID
4) Select a time-history metric
5) SOLVE → review plot
6) Display → compute time point snapshots, export CSV if needed

[Image Placeholder: Time history flow diagram]

---

## Page 26 – Export Your Results

- Save Time Point as CSV — includes NodeID, coordinates, and active scalar
- Export Velocity as Initial Condition in APDL — generates velocity IC commands
- Save as Video/GIF — exports playback to file (ensure ffmpeg for MP4)

Keep exports in project-specific folders for traceability.

[Image Placeholder: Export buttons and example outputs]

---

## Page 27 – Troubleshooting (At a Glance)

| Symptom | Cause | What to try |
| --- | --- | --- |
| SOLVE disabled | Missing .mcf or stress .csv | Load both files |
| No deformation outputs | Deformations not included/loaded | Tick Include Deformations and load .csv |
| Empty scalar bar | CSV lacks scalar column | Use a CSV with at least one scalar field |
| Animation won’t save | ffmpeg missing | Install ffmpeg or choose GIF |
| Hotspots disabled | No active scalar | Apply a scalar via CSV or results |

[Image Placeholder: Troubleshooting grid]

---

## Page 28 – Tips for Clear Visuals

- Keep deformation scale ≤ 5 for realistic visuals
- Use consistent color ranges across comparisons
- Label key nodes for reports
- Take screenshots at the same camera angle for each variant

[Image Placeholder: Good vs poor visualization examples]

---

## Page 29 – Keyboard & Mouse Basics

- Left-drag: Rotate
- Right-drag: Pan
- Mouse wheel: Zoom
- Right-click: Context menu
- Tabs: Click to switch (Main Window, Display)

[Image Placeholder: Mouse diagram]

---

## Page 30 – Review Checklist Before Reporting

- [ ] Inputs validated; Node IDs consistent
- [ ] Outputs selected match the report scope
- [ ] Peaks make sense vs loading events
- [ ] Legends readable; units correct
- [ ] Exports saved (CSV/video) as needed

[Image Placeholder: Final review poster]

---

## Page 31 – File Format Notes (For Reference)

- .mcf: Modal coordinates with a Time column
- Stress .csv: NodeID (+ optional X,Y,Z) and component series
- Deformation .csv: NodeID with ux_, uy_, uz_ series
- Steady-state .txt: Tab-delimited with labeled components

[Image Placeholder: File snippet samples]

---

## Page 32 – FAQs

Q: Which outputs require deformations?
A: Deformation, Velocity, and Acceleration.

Q: How do I compare runs with the same color scale?
A: Manually set Legend Range min/max to fixed values.

Q: How do I focus on a specific node?
A: Right-click → Go To Node; then Lock Camera for Animation if needed.

[Image Placeholder: FAQ cards]

---

## Page 33 – Getting Help

If you encounter issues:
- Note buttons clicked and inputs used
- Copy messages from the Console
- Share a minimal set of files if possible

Contact your MARS maintainer for assistance.

[Image Placeholder: Support footer]

