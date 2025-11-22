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
- **Note**: The Navigator automatically filters to show only `.mcf`, `.csv`, and `.txt` files. Other file types in the project directory will be hidden.

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

### Skip First n Modes

Use **Skip first n modes** to exclude initial modes from the analysis. The dropdown appears after loading the modal coordinate file.

**When to use:**
- Skip **rigid-body modes** (modes with near-zero frequency that represent free translation/rotation)
- Skip modes with erroneous data from FEA export
- Typical values: 0 (include all), 6 (skip 6 rigid-body modes for free-free structures)

**Warning**: Skipping modes that contribute to the response will reduce accuracy. Review modal participation factors from your FEA tool before deciding.

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

## Page 13 – Plasticity Correction (Optional, Advanced)

### When to Use Plasticity Correction

If your structure has **stress concentrations** (notches, holes, fillets) where elastic stress exceeds yield, enable **Plasticity Correction** to obtain more realistic stress values and plastic strain estimates.

### Steps to Enable

1) Tick **Plasticity Correction** on the Main Window tab
2) Select a method:
   - **Neuber** — Classic notch correction (faster)
   - **Glinka** — Energy-based correction (more conservative)
   - ~~Incremental Buczynski-Glinka (IBG)~~ — Currently disabled (experimental)
3) Click **Enter Material Profile** to define stress-strain curves at multiple temperatures
4) Load a **Temperature Field File** (CSV with NodeID and Temperature columns)
5) Ensure **Von Mises Stress** output is selected (required for plasticity correction)

### Material Profile Dialog

- Enter temperature values (e.g., 25, 200, 400°C)
- For each temperature, add rows of **(True Stress, Plastic Strain)** pairs
- First point ≈ yield stress at ~zero plastic strain
- Subsequent points trace the hardening curve
- Choose **Extrapolation Mode**:
  - **Linear** (default) — for strain-hardening alloys
  - **Plateau** — for limited-hardening materials

### Temperature Field File Format

The temperature field file must be a **CSV** with the following structure:
- **Required columns**: `NodeID`, `Temperature`
- Temperature units must match those used in the Material Profile
- Node IDs must match those in your modal stress file
- Example:
  ```
  NodeID,Temperature
  1001,25.0
  1002,150.5
  1003,300.0
  ```

### Iteration Controls (Advanced)

For difficult convergence cases, adjust:
- **Max Iterations** (default: 60) — increase if solver fails to converge
- **Tolerance** (default: 1e-10) — numerical convergence threshold

A warning appears if you change these from defaults. Relaxed settings may reduce accuracy.

### Plasticity Diagnostics

For advanced validation, tick **Show plasticity diagnostics (Δεp, εp)**:
- When Time History Mode is active, this overlays incremental plastic strain (Δεp) and cumulative plastic strain (εp) on a secondary axis
- Useful for debugging convergence or validating material models

### Output Files

When plasticity is enabled, MARS produces:
- `corrected_von_mises.csv` — Reduced stress accounting for plasticity
- `plastic_strain.csv` — Equivalent plastic strain at each node
- `time_of_max_corrected_von_mises.csv` — Time of corrected peak

### Tips

- Corrected stress will be **lower** than elastic stress at notches
- Plastic strain indicates local yielding severity
- Use corrected results for **strain-based fatigue** (Coffin-Manson)
- Validate critical nodes with detailed nonlinear FEA

[Image Placeholder: Plasticity correction panel and material profile dialog]

---

## Page 14 – Run the Analysis

1) Ensure both .mcf and stress .csv are loaded
2) Select desired outputs
3) Click SOLVE
4) Watch Console messages and the Progress Bar

When finished, proceed to the Display tab to explore results.

[Image Placeholder: SOLVE button and progress bar]

---

## Page 15 – Advanced Settings (Performance Tuning)

Access via **Settings → Advanced** in the menu bar. This dialog controls global solver performance parameters.

### RAM Allocation

- **Set RAM Allocation (%)**: Control how much system memory MARS can use (default: 70%)
- Range: 10% to 95%
- **When to adjust**:
  - Increase to 90% for large datasets (millions of data points)
  - Decrease to 50% if running other memory-intensive applications simultaneously
- Changes apply to the next SOLVE operation

### Solver Precision

- **Single Precision**: Faster, uses less memory, sufficient for most engineering analyses (~7 significant digits)
- **Double Precision**: Slower, uses 2× memory, provides maximum accuracy (~15 significant digits)
- **When to use Double**: Extremely sensitive stress gradients, fatigue life > 10⁶ cycles, or critical aerospace components

### GPU Acceleration

- **Enable GPU Acceleration**: Uses NVIDIA CUDA for matrix operations
- **Requirements**: NVIDIA GPU with CUDA support, CUDA toolkit installed
- **Speed improvement**: 2-10× faster for large models (>100k nodes)
- If GPU is not detected, solver automatically falls back to CPU

### Applying Changes

1) Modify desired settings
2) Click OK
3) Settings take effect on the next SOLVE operation
4) Current settings are saved and persist across sessions

**Tip**: Start with default settings. Only adjust if experiencing performance issues or running very large models.

[Image Placeholder: Advanced Settings dialog with labeled sections]

---

## Page 16 – Console & Plot Tabs (Main Window)

- Console: shows load/validation messages and processing steps
- Plot (Time History): appears when Time History mode is active
- Plot (Modal Coordinates): used to inspect coordinate amplitudes

Use these for quick validation before switching to the Display tab.

[Image Placeholder: Console and plot tabs]

---

## Page 17 – Switch to Display Tab

Click the Display tab to see the 3D view and controls:
- Load Visualization File (for CSV-based meshes)
- Visualization Controls (point size, legend range, deformation scale)
- Initialization & Time Point Controls (time selection, save CSV, export APDL IC)
- Animation Controls (playback and export)

[Image Placeholder: Display tab at first view]

---

## Page 18 – Hover, Colorbar, and Point Size

- Hover over points to see Node ID and current scalar value
- Adjust Node Point Size for clarity
- Set Legend Range Min/Max to focus the color scale

Tip: Reset camera after large changes for a clean view.

[Image Placeholder: Hover tooltip showing NodeID and value]

---

## Page 19 – Compute a Time Point Field

When initialization is complete (after SOLVE), enable time point workflows:
1) In Initialization & Time Point Controls, set Time (seconds)
2) Click Update to compute node-wise values for that instant
3) Use Save Time Point as CSV to export what you see

If deformations exist, you can also Export Velocity as Initial Condition in APDL.

[Image Placeholder: Time point panel with callouts]

---

## Page 20 – Load External CSV Results

To visualize an external CSV:
1) Click Load Visualization File
2) Select a CSV with X, Y, Z, optional NodeID, and at least one scalar column
3) The first scalar column becomes active; adjust legend and point size

Use this to compare alternatives or post-process snapshots.

[Image Placeholder: External CSV loaded into plotter]

---

## Page 21 – Animate Your Results

### Time Step Modes

1) **Custom Time Step**: Specify a uniform time step in seconds
   - Enter desired **Step (secs)** value (e.g., 0.01 for 100 frames/second)
   - MARS interpolates values at these uniform intervals
   
2) **Actual Data Time Steps**: Use the exact time values from your modal coordinate file
   - Use **Every nth** to reduce frame count (e.g., "Every 2nd" shows every other frame)
   - Recommended for large datasets: set "Every 10th" or "Every 20th" for smoother playback
   - Lower "Every nth" values = more frames = slower playback but smoother

### Animation Controls

1) Set **Interval (ms)**: Delay between frames (50ms = 20 fps, 100ms = 10 fps)
2) Set **Start** and **End** times to focus on a time window of interest
3) Click **Play**; use **Pause** or **Stop** as needed
4) Click **Save as Video/GIF** to export:
   - **MP4**: Requires ffmpeg installed on your system
   - **GIF**: Always available, larger file size

If deformations were provided, geometry deforms during playback.

**Tip**: For presentations, use Custom Time Step with 0.01s intervals and 50ms playback interval for smooth 20fps animations.

[Image Placeholder: Animation controls — play/pause/stop]

---

## Page 22 – Right-Click Context Menu (Display)

Right-click anywhere on the 3D view to access:
- Selection Tools: Add/Remove Selection Box, Pick Box Center
- Hotspot Analysis: Find Hotspots (current view) or in Selection
- Point-Based Analysis: Plot Time History for Selected Node
- View Control: Go To Node, Lock Camera for Animation, Reset Camera

[Image Placeholder: Context menu with sections labeled]

---

## Page 23 – Find Hotspots

1) Right-click → Find Hotspots (on current view) or in Selection
2) Enter how many top nodes to find
3) A dialog lists the nodes with highest values
4) Click a node to label and zoom to it

Use hotspots to shortlist critical regions for detailed checks.

[Image Placeholder: Hotspot dialog with table]

---

## Page 24 – Select an Area with a Box

1) Right-click → Add Selection Box
2) Right-click → Pick Box Center, then click to position
3) Drag handles to resize
4) Run Find Hotspots in Selection

Use box selection to focus on sub-assemblies.

[Image Placeholder: Selection box around a region]

---

## Page 25 – Go To Node & Track During Animation

1) Right-click → Go To Node
2) Enter a Node ID to fly the camera there
3) Right-click → Lock Camera for Animation (freeze node) to keep focus during playback
4) Right-click → Reset Camera to restore the default view

[Image Placeholder: Node target marker and label]

---

## Page 26 – Batch Workflow (Checklist)

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

## Page 27 – Time History Workflow (Checklist)

1) Load .mcf and stress .csv
2) Tick Time History Mode
3) Enter Node ID
4) Select a time-history metric
5) SOLVE → review plot
6) Display → compute time point snapshots, export CSV if needed

[Image Placeholder: Time history flow diagram]

---

## Page 28 – Export Your Results

- Save Time Point as CSV — includes NodeID, coordinates, and active scalar
- Export Velocity as Initial Condition in APDL — generates velocity IC commands
- Save as Video/GIF — exports playback to file (ensure ffmpeg for MP4)

Keep exports in project-specific folders for traceability.

[Image Placeholder: Export buttons and example outputs]

---

## Page 29 – Troubleshooting (At a Glance)

| Symptom | Cause | What to try |
| --- | --- | --- |
| SOLVE disabled | Missing .mcf or stress .csv | Load both files |
| No deformation outputs | Deformations not included/loaded | Tick Include Deformations and load .csv |
| Empty scalar bar | CSV lacks scalar column | Use a CSV with at least one scalar field |
| Animation won't save | ffmpeg missing | Install ffmpeg or choose GIF |
| Hotspots disabled | No active scalar | Apply a scalar via CSV or results |
| Plasticity won't enable | Von Mises not selected or temp field missing | Select Von Mises output and load temperature file |
| Corrected stress > elastic | Material data incorrect or solver didn't converge | Check material curves and increase max iterations |
| GPU not being used | CUDA not installed or no NVIDIA GPU | Check Settings → Advanced; install CUDA toolkit or disable GPU option |
| Solver very slow | RAM allocation too low or precision too high | Go to Settings → Advanced; increase RAM % or switch to Single precision |
| Temperature file error | Wrong format or missing columns | Ensure CSV format with NodeID and Temperature columns (see Page 13) |

[Image Placeholder: Troubleshooting grid]

---

## Page 30 – Tips for Clear Visuals

- Keep deformation scale ≤ 5 for realistic visuals
- Use consistent color ranges across comparisons
- Label key nodes for reports
- Take screenshots at the same camera angle for each variant

[Image Placeholder: Good vs poor visualization examples]

---

## Page 31 – Keyboard & Mouse Basics

- Left-drag: Rotate
- Right-drag: Pan
- Mouse wheel: Zoom
- Right-click: Context menu
- Tabs: Click to switch (Main Window, Display)

[Image Placeholder: Mouse diagram]

---

## Page 32 – Review Checklist Before Reporting

- [ ] Inputs validated; Node IDs consistent
- [ ] Outputs selected match the report scope
- [ ] Peaks make sense vs loading events
- [ ] Legends readable; units correct
- [ ] Exports saved (CSV/video) as needed

[Image Placeholder: Final review poster]

---

## Page 33 – File Format Notes (For Reference)

- **.mcf**: Modal coordinates with a Time column
- **Stress .csv**: NodeID (+ optional X,Y,Z) and component series (sx_1, sy_1, etc.)
- **Deformation .csv**: NodeID with ux_, uy_, uz_ series
- **Steady-state .txt**: Tab-delimited with labeled components
- **Temperature field .csv**: NodeID, Temperature columns (for plasticity correction)
  - Example:
    ```
    NodeID,Temperature
    1001,25.0
    1002,150.5
    ```

[Image Placeholder: File snippet samples]

---

## Page 34 – FAQs

Q: Which outputs require deformations?
A: Deformation, Velocity, and Acceleration.

Q: How do I compare runs with the same color scale?
A: Manually set Legend Range min/max to fixed values.

Q: How do I focus on a specific node?
A: Right-click → Go To Node; then Lock Camera for Animation if needed.

Q: When should I use plasticity correction?
A: When elastic stress exceeds yield at notches/holes and you need realistic stress and plastic strain for fatigue.

Q: Which plasticity method should I choose?
A: Start with Neuber (faster); use Glinka if you need energy-based conservatism. IBG is currently experimental.

Q: How do I speed up large analyses?
A: Go to Settings → Advanced. Increase RAM allocation to 90%, switch to Single precision, or enable GPU acceleration if you have NVIDIA CUDA.

Q: What does "Skip first n modes" do?
A: Excludes the first n modes from analysis. Use this to skip rigid-body modes (usually 6 for free-free structures) or modes with bad data.

Q: Why can't I see all files in the Navigator?
A: Navigator automatically filters to show only .mcf, .csv, and .txt files relevant to MARS workflows.

[Image Placeholder: FAQ cards]

---

## Page 35 – Getting Help

If you encounter issues:
- Note buttons clicked and inputs used
- Copy messages from the Console
- Share a minimal set of files if possible

Contact your MARS maintainer for assistance.

[Image Placeholder: Support footer]

