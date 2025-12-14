# MARS: Modal Analysis Response Solver
## Complete User Manual

> **Audience**: Mechanical and structural engineers using MARS via the desktop GUI  
> **Format**: Designed for Microsoft Word with font size 10 and mockup images for each section

---

# PART I: INTRODUCTION AND GETTING STARTED

---

## Chapter 1 – Welcome to MARS

MARS (Modal Analysis Response Solver) is a desktop application designed for post-processing modal analysis results from finite element simulations. The software transforms modal coordinates and modal stress data into comprehensive engineering outputs including stress field reconstruction, time history analysis, animations, and data exports.

### What MARS Can Do For You

| Capability | Description |
|------------|-------------|
| **Stress Reconstruction** | Combine modal coordinates with modal stress to reconstruct full stress tensor fields at any time instant |
| **Principal Stress Analysis** | Calculate maximum and minimum principal stresses (σ₁ and σ₃) across all nodes |
| **Von Mises Stress** | Compute equivalent von Mises stress for ductile material failure analysis |
| **Kinematic Analysis** | Extract deformation, velocity, and acceleration from modal displacement data |
| **Time History Plots** | Generate time series plots for any selected node |
| **3D Visualization** | Interactive PyVista-based 3D viewing with scalar field color mapping |
| **Animations** | Create animated visualizations showing stress or deformation evolution over time |
| **Hotspot Detection** | Automatically identify nodes with critical stress values |
| **Data Export** | Save results to CSV and export velocity initial conditions in APDL format |
| **Plasticity Correction** | Apply Neuber or Glinka correction for localized yielding at stress concentrations |

[**Image Placeholder**: MARS main window screenshot showing the complete interface with tabs, navigator, and console]

---

## Chapter 2 – System Requirements and Installation

### Prerequisites

- **Python**: Version 3.10 or higher
- **Operating System**: Windows 10/11 (primary), Linux/macOS (compatible)
- **RAM**: Minimum 8 GB; 16+ GB recommended for large models
- **GPU (Optional)**: NVIDIA GPU with CUDA support for acceleration

### Installation Steps

1. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   ```

2. **Activate the virtual environment**:
   - Windows: `.venv\Scripts\activate`
   - Linux/macOS: `source .venv/bin/activate`

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch MARS**:
   ```bash
   python -m src.main
   ```

[**Image Placeholder**: Terminal showing successful launch of MARS application]

---

## Chapter 3 – Interface Overview

The MARS interface consists of several key components that work together to provide a seamless analysis workflow.

### Main Window Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Menu Bar** | Top | Access File, View, and Settings menus |
| **Navigator Panel** | Left side | Browse and select project files |
| **Main Window Tab** | Center (Tab 1) | Load files, configure analysis, run solver |
| **Display Tab** | Center (Tab 2) | 3D visualization, animation, exports |
| **Console** | Bottom of Main Window | View status messages and processing logs |

### Tab Navigation

- **Main Window Tab**: This is your primary workspace for setting up and running analyses
- **Display Tab**: Switch here after running the solver to visualize and export results

[**Image Placeholder**: Annotated interface image with numbered callouts:
1. Menu Bar
2. Navigator Panel  
3. Tab Buttons (Main Window / Display)
4. File Input Section
5. Output Options Section
6. Console/Plot Tabs
7. Progress Bar
8. SOLVE Button]

---

# PART II: MAIN WINDOW TAB – INPUT AND SOLVER CONFIGURATION

---

## Chapter 4 – Setting Up Your Project Directory

The Navigator panel provides quick access to your project files. MARS automatically filters the view to show only relevant file types.

### Selecting a Project Directory

1. Click **File → Select Project Directory** from the menu bar
2. Navigate to the folder containing your analysis files
3. Click **Select Folder** to confirm

The Navigator will update to display files in the selected directory.

### Supported File Types

The Navigator displays only these file types:

| Extension | Description |
|-----------|-------------|
| `.mcf` | Modal Coordinate Files |
| `.csv` | Modal Stress Files, Deformation Files |
| `.txt` | Steady-State Stress Files |

### Navigator Features

- **Double-click** any file to load it into the appropriate input field
- **Sort** by name or type by clicking column headers
- **Resize** columns by dragging the header borders
- Toggle visibility via **View → Navigator**

[**Image Placeholder**: Navigator panel showing example project files with .mcf, .csv, and .txt files listed]

---

## Chapter 5 – Loading Modal Coordinate Files (.mcf)

The modal coordinate file contains the time-varying amplitudes of each mode shape from your transient analysis.

### Loading Procedure

1. In the **File Inputs** section, click **Read Modal Coordinate File (.mcf)**
2. Select your `.mcf` file from the file dialog
3. The file path appears in the text field next to the button
4. Check the Console for validation messages

### File Format Requirements

- Must contain a `Time` column (in seconds)
- Additional columns represent modal coordinates (one per mode)
- First row contains headers

**Example Format**:
```
Time,Mode1,Mode2,Mode3,...
0.0000,1.23e-4,2.45e-5,3.67e-6,...
0.0001,1.25e-4,2.42e-5,3.70e-6,...
```

### What Happens After Loading

- The **Skip first n modes** dropdown becomes available
- Stress-related output checkboxes become enabled (if stress file is also loaded)
- The number of modes and time steps is recorded

[**Image Placeholder**: File Input section with modal coordinate file loaded, showing the file path and success message in console]

---

## Chapter 6 – Loading Modal Stress Files (.csv)

The modal stress file contains stress tensors for each mode at every node in your model.

### Loading Procedure

1. Click **Read Modal Stress File (.csv)**
2. Select your stress CSV file
3. Verify the file path appears in the text field
4. Check Console for validation confirmation

### File Format Requirements

**Required Columns**:
- `NodeID` – Unique identifier for each node
- Stress component columns following the naming pattern:
  - `sx_1, sx_2, ...` (normal stress in X)
  - `sy_1, sy_2, ...` (normal stress in Y)
  - `sz_1, sz_2, ...` (normal stress in Z)
  - `sxy_1, sxy_2, ...` (shear stress XY)
  - `syz_1, syz_2, ...` (shear stress YZ)
  - `sxz_1, sxz_2, ...` (shear stress XZ)

**Optional Columns**:
- `X, Y, Z` – Node coordinates for 3D visualization

### Understanding Mode Indexing

The suffix number (e.g., `sx_1`, `sx_2`) corresponds to mode numbers. These must align with the modal coordinate file columns.

[**Image Placeholder**: Example stress CSV structure showing NodeID, coordinates, and stress component columns]

---

## Chapter 7 – Optional: Including Steady-State Stress

If your structure has a static pre-stress condition (thermal stress, bolt preload, etc.), you can include it in the analysis.

### Enabling Steady-State Stress

1. Check the box **Include Steady-State Stress Field (Optional)**
2. The steady-state file input section appears
3. Click **Read Full Stress Tensor File (.txt)**
4. Select your steady-state stress file

### File Format Requirements

The file should be tab-delimited with the following columns:
```
NodeID	SX	SY	SZ	SXY	SYZ	SXZ
1001	100.5	200.3	150.2	25.1	30.5	15.2
1002	98.7	195.4	148.9	24.8	29.9	14.8
...
```

### Effect on Results

- Steady-state stress is added to the reconstructed transient stress at each time step
- Affects all stress-based outputs (Von Mises, Principal Stresses)
- Important for accurate fatigue analysis with mean stress effects

[**Image Placeholder**: Steady-state stress toggle checked, with file input field showing loaded file path]

---

## Chapter 8 – Optional: Including Deformations

Loading modal deformations unlocks kinematic analysis capabilities including deformation magnitude, velocity, and acceleration.

### Enabling Deformations

1. Check the box **Include Deformations (Optional)**
2. The deformation file input section appears
3. Click **Read Modal Deformations File (.csv)**
4. Select your deformation CSV file

### File Format Requirements

**Required Columns**:
- `NodeID` – Must match the stress file's Node IDs
- Displacement columns following the pattern:
  - `ux_1, ux_2, ...` (displacement in X, per mode)
  - `uy_1, uy_2, ...` (displacement in Y, per mode)
  - `uz_1, uz_2, ...` (displacement in Z, per mode)

### Unlocked Outputs

After loading deformations, these outputs become available:
- **Deformation** – Displacement magnitude over time
- **Velocity** – Time derivative of displacement
- **Acceleration** – Time derivative of velocity
- **Animated deformed shape** – Visual mesh deformation in Display tab

[**Image Placeholder**: Deformation toggle checked, showing the deformation file input section]

---

## Chapter 9 – Selecting Analysis Outputs

The Output Options section allows you to specify which results to compute. Multiple outputs can be selected simultaneously.

### Available Outputs

| Output | Description | Requirements |
|--------|-------------|--------------|
| **Max Principal Stress** | Maximum principal stress (σ₁) envelope | Stress file |
| **Min Principal Stress** | Minimum principal stress (σ₃) envelope | Stress file |
| **Von-Mises Stress** | Equivalent stress for ductile failure | Stress file |
| **Deformation** | Displacement magnitude | Deformation file |
| **Velocity** | Velocity magnitude | Deformation file |
| **Acceleration** | Acceleration magnitude | Deformation file |
| **Enable Time History Mode** | Plot time series for a single node | Any output |
| **Enable Plasticity Correction** | Apply notch plasticity methods | Von-Mises selected |

### Selecting Multiple Outputs

You may select any combination of outputs:
- All stress outputs can be computed together
- Kinematic outputs (Deformation, Velocity, Acceleration) require the deformation file
- Time History Mode can be combined with any output type

### Output File Generation

Each selected output produces a CSV file in the project directory containing:
- `NodeID`
- Maximum value over time
- Time instant of maximum value

[**Image Placeholder**: Output Options section with checkboxes, some checked (Von-Mises, Max Principal Stress, Deformation)]

---

## Chapter 10 – Skip First n Modes

This feature allows you to exclude the first n modes from the analysis – useful for omitting rigid-body modes or modes with erroneous data.

### When to Use This Feature

| Scenario | Recommended Setting |
|----------|---------------------|
| Fixed boundary model (no rigid-body motion) | 0 (include all modes) |
| Free-free model (6 rigid-body modes) | 6 (skip rigid-body modes) |
| First mode has corrupted data | 1 or more as needed |

### How to Use

1. Load the modal coordinate file
2. The **Skip first n modes** dropdown appears
3. Select the number of modes to skip (0 to n)

### Important Notes

- Skipped modes are completely excluded from stress/displacement reconstruction
- Verify with your FEA tool which modes are rigid-body modes
- Over-skipping will miss significant modal contributions

[**Image Placeholder**: Skip first n modes dropdown showing options 0-6]

---

## Chapter 11 – Time History Mode (Single Node Analysis)

Time History Mode computes and plots the time series of a selected output quantity for a specific node.

### Enabling Time History Mode

1. Check **Enable Time History Mode (Single Node)**
2. The **Scoping** section becomes active
3. Enter the desired **Node ID** in the input field
4. Select exactly one output type (Von-Mises, Max Principal, etc.)

### Running Time History Analysis

1. Click **SOLVE**
2. The solver computes the full time history for the specified node
3. Results appear in the **Plot (Time History)** tab

### Plot Features

- X-axis: Time (seconds)
- Y-axis: Selected output quantity (stress in MPa, displacement in mm, etc.)
- Interactive pan and zoom
- Data table showing time-value pairs

### Use Cases

- Verify peak stress timing at critical locations
- Examine stress waveform for fatigue analysis
- Validate results against reference calculations

[**Image Placeholder**: Time History plot showing Von-Mises stress over time for a selected node, with peak value labeled]

---

## Chapter 12 – Plasticity Correction (Advanced Feature)

For structures with stress concentrations where elastic stress exceeds yield, plasticity correction provides more realistic stress and strain estimates.

### Available Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| **Neuber** | Classic hyperbolic correction | General notches, faster computation |
| **Glinka** | Energy-based ESED method | More conservative, thick sections |

### Enabling Plasticity Correction

1. Select **Von-Mises Stress** as an output (required)
2. Check **Enable Plasticity Correction**
3. The plasticity options section appears
4. Select a method (Neuber or Glinka)
5. Click **Enter Material Profile** to define stress-strain curves
6. Load a **Temperature Field File** (CSV with NodeID and Temperature)

### Material Profile Dialog

The material profile defines the true stress-strain curve at various temperatures:

1. Enter temperature values (e.g., 25°C, 200°C, 400°C)
2. For each temperature, add (True Stress, Plastic Strain) pairs:
   - Start at yield stress with ~0 plastic strain
   - Add hardening curve points
3. Select **Extrapolation Mode**:
   - **Linear**: For strain-hardening materials
   - **Plateau**: For limited-hardening materials

### Temperature Field File Format

```csv
NodeID,Temperature
1001,25.0
1002,150.5
1003,300.0
```

### Iteration Controls

For convergence issues, access advanced settings:
- **Max Iterations**: Default 60 (increase if solver fails to converge)
- **Tolerance**: Default 1e-10 (numerical convergence threshold)

### Plasticity Diagnostics

For detailed validation in Time History Mode:
- Enable **Show plasticity diagnostics (Δεp, εp)**
- Overlays incremental and cumulative plastic strain on secondary axis

### Output Files

When plasticity is enabled, MARS produces:
- `corrected_von_mises.csv` – Corrected stress values
- `plastic_strain.csv` – Equivalent plastic strain at each node
- `time_of_max_corrected_von_mises.csv` – Time of peak corrected stress

[**Image Placeholder**: Plasticity Correction panel showing method selection, material profile button, and temperature field input]

---

## Chapter 13 – Running the Solver

After configuring all inputs and options, the SOLVE button initiates the computation.

### Pre-Run Checklist

- [ ] Modal coordinate file loaded
- [ ] Modal stress file loaded
- [ ] (Optional) Steady-state stress file loaded
- [ ] (Optional) Deformation file loaded
- [ ] At least one output selected
- [ ] Skip modes set appropriately
- [ ] (If Time History) Node ID entered

### Running the Analysis

1. Click the **SOLVE** button
2. Monitor the **Progress Bar** for completion status
3. Watch the **Console** for processing messages
4. Wait for the "Analysis complete" confirmation

### Console Messages

The Console provides real-time feedback:
- File loading confirmations
- Validation warnings
- Processing steps and timing
- Any errors encountered

### What Happens After Solving

- Output CSV files are written to the project directory
- The Display tab is initialized with visualization data
- Time controls become active
- Animation controls become available (if deformations were included)

[**Image Placeholder**: SOLVE button with progress bar at 75%, console showing processing messages]

---

## Chapter 14 – Advanced Settings (Performance Tuning)

Access advanced settings via **Settings → Advanced** in the menu bar.

### RAM Allocation

| Setting | Range | Recommendation |
|---------|-------|----------------|
| **RAM Allocation (%)** | 10% - 95% | Default: 70% |

- **Increase to 90%**: For very large models (>1M data points)
- **Decrease to 50%**: When running other memory-intensive applications

### Solver Precision

| Option | Accuracy | Memory | Speed |
|--------|----------|--------|-------|
| **Single Precision** | ~7 digits | Lower | Faster |
| **Double Precision** | ~15 digits | 2x | Slower |

**Use Double Precision for**:
- High-cycle fatigue (>10⁶ cycles)
- Very sensitive stress gradients
- Critical aerospace components

### GPU Acceleration

| Setting | Requirements |
|---------|--------------|
| **Enable GPU Acceleration** | NVIDIA GPU + CUDA toolkit installed |

- Provides 2-10x speedup for large models (>100k nodes)
- Automatic fallback to CPU if GPU unavailable

### Applying Settings

1. Modify desired parameters
2. Click **OK**
3. Settings apply to the next SOLVE operation
4. Settings persist across sessions

[**Image Placeholder**: Advanced Settings dialog showing RAM slider, precision radio buttons, and GPU checkbox]

---

# PART III: DISPLAY TAB – 3D VISUALIZATION AND ANALYSIS

---

## Chapter 15 – Display Tab Overview

The Display tab provides an interactive 3D visualization environment powered by PyVista. This is where you explore, analyze, and export your results.

### Display Tab Layout

| Section | Location | Purpose |
|---------|----------|---------|
| **Load Visualization File** | Top | Load external CSV for visualization |
| **Visualization Controls** | Below file controls | Adjust point size, color scale, deformation |
| **Time Point Controls** | Middle | Select time instant, update/save results |
| **Animation Controls** | Below time controls | Configure and run animations |
| **PyVista 3D Viewer** | Right side | Interactive 3D point cloud display |

### Initial State

After a successful SOLVE:
- The 3D viewer displays your node point cloud
- Scalar values (e.g., Max Von-Mises) are color-mapped
- Time controls are enabled with the full time range
- Animation controls become visible

[**Image Placeholder**: Display tab after solver completion, showing 3D point cloud with color-mapped stress values]

---

## Chapter 16 – Visualization Controls (Detailed)

The Visualization Controls group provides fine-grained control over the 3D display appearance.

### Node Point Size

**Purpose**: Adjust the rendered size of each node point in the 3D view.

**Controls**:
- **Size Spin Box**: Range 1-100 pixels
- Default: 5 pixels

**Guidelines**:
| Model Size | Recommended Point Size |
|------------|------------------------|
| < 10,000 nodes | 5-10 |
| 10,000 - 100,000 nodes | 3-5 |
| > 100,000 nodes | 1-3 |

### Legend Range (Min/Max)

**Purpose**: Set the color scale boundaries for the active scalar field.

**Controls**:
- **Min Spin Box**: Sets the lower bound (blue end of spectrum)
- **Max Spin Box**: Sets the upper bound (red end of spectrum)

**Use Cases**:
- Focus on a specific stress range by narrowing the bounds
- Compare results across different analyses using fixed bounds
- Highlight values above/below a threshold

### Deformation Scale Factor

**Purpose**: Amplify or reduce the visual displacement magnitude for animations.

**Appears**: Only when deformations are loaded

**Guidelines**:
| Actual Displacement | Recommended Scale |
|---------------------|-------------------|
| < 1% of model size | 10 - 100 |
| 1-5% of model size | 1 - 10 |
| > 5% of model size | 0.1 - 1 |

**Tip**: Keep scale ≤ 5 for realistic-looking visualizations in presentations.

### Show Absolute Deformations Checkbox

**Purpose**: Control how deformed mesh coordinates are displayed during animation.

| Mode | When to Use |
|------|-------------|
| **Unchecked (Relative)** | Visualizing dynamics, vibration patterns |
| **Checked (Absolute)** | Quantitative analysis, pre-loading effects |

**Relative Mode (Default)**:
- First animation frame appears at "zero" position
- Shows motion pattern relative to animation start time
- Better for presentations and mode shape visualization

**Absolute Mode**:
- Shows true deformation from undeformed geometry
- Preserves absolute displacement magnitudes
- Better for engineering quantitative analysis

[**Image Placeholder**: Visualization Controls group showing all options: point size spinner, min/max legend spinners, deformation scale input, and absolute deformations checkbox]

---

## Chapter 17 – Time Point Controls (Detailed)

The Time Point Controls allow you to compute and export results at any specific time instant.

### Time Selection

**Purpose**: Choose the exact time instant for result calculation.

**Controls**:
- **Time (seconds) Spin Box**: 5-decimal precision, covers full analysis time range

**Workflow**:
1. Enter or scroll to desired time value
2. Click **Update** to compute results at that instant
3. The 3D view updates with computed scalar values

### Update Button

**Purpose**: Trigger computation of stress/displacement fields at the selected time.

**Process**:
1. Interpolates modal coordinates to selected time
2. Reconstructs stress tensor field
3. Computes selected output (Von-Mises, Principal, etc.)
4. Updates 3D visualization with new scalar values

### Save Time Point as CSV

**Purpose**: Export the current 3D view data to a CSV file.

**Output Format**:
```csv
NodeID,X,Y,Z,VonMises
1001,10.5,20.3,5.2,234.5
1002,10.8,20.1,5.5,219.8
...
```

**Use Cases**:
- Archive critical time instant results
- Import into other analysis tools
- Create documentation snapshots

### Export Velocity as Initial Condition in APDL

**Purpose**: Generate ANSYS APDL commands for velocity initial conditions.

**Appears**: Only when velocity data is available (deformations loaded)

**Output Format (.inp)**:
```
IC,1001,UX,,-0.00234
IC,1001,UY,,0.00156
IC,1001,UZ,,-0.00089
IC,1002,UX,,-0.00241
...
```

**Use Case**: Restart transient analysis from a specific time point in ANSYS.

[**Image Placeholder**: Time Point Controls showing time spinbox at 0.05234 seconds, Update button, Save CSV button, and APDL export button]

---

## Chapter 18 – Animation Controls (Detailed)

The Animation Controls section provides comprehensive options for creating animated visualizations of your results.

### Time Step Mode

**Purpose**: Choose how animation frames are generated.

| Mode | Description |
|------|-------------|
| **Custom Time Step** | Uniform time intervals you specify |
| **Actual Data Time Steps** | Uses exact times from modal coordinate file |

#### Custom Time Step Mode

**Step (secs)**: Specify the time increment between frames

**Example Settings**:
| Desired Animation | Step Value |
|------------------|------------|
| 100 frames over 1 second | 0.01 |
| 50 frames over 0.5 seconds | 0.01 |
| Fine detail view | 0.001 |

#### Actual Data Time Steps Mode

**Every nth**: Skip frames to reduce total frame count

**Guidelines**:
| Data Points | Every nth | Result |
|-------------|-----------|--------|
| 10,000 | 1 | 10,000 frames (slow) |
| 10,000 | 10 | 1,000 frames |
| 10,000 | 100 | 100 frames (fast) |

### Playback Interval

**Interval (ms)**: Delay between animation frames

| Interval | Frame Rate | Use Case |
|----------|------------|----------|
| 50 ms | 20 fps | Smooth presentations |
| 100 ms | 10 fps | Balanced viewing |
| 200 ms | 5 fps | Slow-motion analysis |

### Time Range (Start/End)

**Purpose**: Focus animation on a specific time window.

**Controls**:
- **Start**: Beginning time of animation (seconds)
- **End**: Ending time of animation (seconds)

**Use Cases**:
- Focus on peak stress period
- Isolate specific loading event
- Create shorter, focused animations

### Playback Controls

| Button | Action |
|--------|--------|
| **Play** | Start or resume animation |
| **Pause** | Pause at current frame |
| **Stop** | Stop and reset to beginning |

### Save as Video/GIF

**Purpose**: Export the precomputed animation to a video file.

**Supported Formats**:
| Format | Requirements | File Size |
|--------|--------------|-----------|
| MP4 | ffmpeg installed | Smaller |
| GIF | Always available | Larger |

**Workflow**:
1. Configure and play animation
2. Click **Save as Video/GIF**
3. Choose format and filename
4. Wait for export to complete

[**Image Placeholder**: Animation Controls showing all options: time step mode dropdown, step value, interval spinner, start/end time, play/pause/stop buttons, and save button]

---

## Chapter 19 – PyVista 3D Viewer Interaction

The PyVista 3D Viewer provides an interactive canvas for exploring your results. Understanding the controls is essential for effective analysis.

### Mouse Controls

| Action | Result |
|--------|--------|
| **Left-click + Drag** | Rotate the view around the focal point |
| **Right-click + Drag** | Pan the view (translate camera) |
| **Scroll Wheel** | Zoom in/out |
| **Middle-click + Drag** | Alternative pan method |

### Hover Information

When you hover over a node point:
- A tooltip displays the **Node ID** and current **scalar value**
- Useful for quick identification of specific nodes
- Works with any active scalar field

### Color Scale (Scalar Bar)

The color scale legend on the right side of the 3D view shows:
- Color gradient from minimum (blue) to maximum (red)
- Numerical values at key intervals
- Active scalar field name (e.g., "VonMises")

### View Orientation

The 3D view includes an orientation widget showing X, Y, Z axes:
- Red = X axis
- Green = Y axis  
- Blue = Z axis

[**Image Placeholder**: PyVista 3D viewer showing a stress-colored point cloud with:
1. Color scale bar on the right
2. Hover tooltip showing "Node 12345: 234.5 MPa"
3. Orientation widget in corner
4. Mouse cursor indicating rotation]

---

## Chapter 20 – Right-Click Context Menu (Complete Reference)

Right-clicking anywhere on the 3D viewer opens a context menu with powerful analysis tools organized into four sections.

### Section 1: Selection Tools

These tools help you select and isolate regions of interest.

#### Add/Remove Selection Box

**Purpose**: Create a 3D bounding box to define a region of interest.

**Workflow**:
1. Right-click → **Add Selection Box**
2. An orange wireframe box appears in the view
3. **Drag the box handles** to resize
4. Use **Pick Box Center** to reposition
5. Right-click → **Remove Selection Box** when done

**Box Handle Colors**:
- Orange handles: Normal state
- Bright orange: Selected/active handle

#### Pick Box Center

**Purpose**: Interactively position the selection box center by clicking in the view.

**Workflow**:
1. First add a selection box
2. Right-click → **Pick Box Center** (toggle on)
3. Click on a location in the 3D view
4. The box moves to center on that point
5. Pick mode disables after the click

[**Image Placeholder**: Selection box around a group of nodes, with handles visible and an arrow pointing to a resize handle]

---

### Section 2: Hotspot Analysis

These tools identify nodes with critical (extreme) scalar values.

#### Find Hotspots (on current view)

**Purpose**: Find nodes with highest scalar values among all currently visible nodes.

**Workflow**:
1. Rotate/zoom to show the region of interest
2. Right-click → **Find Hotspots (on current view)**
3. Enter the number of top nodes to find (e.g., 10)
4. A dialog appears with ranked results

**Hotspot Dialog Features**:
- Ranked table showing: Rank, NodeID, Value, Coordinates
- Click any row to navigate to that node in the 3D view
- The node is highlighted and labeled

#### Find Hotspots in Selection

**Purpose**: Find nodes with highest scalar values within the selection box.

**Requirements**: Selection box must be active

**Workflow**:
1. Add and position a selection box
2. Right-click → **Find Hotspots in Selection**
3. Enter the number of top nodes to find
4. Results show only nodes inside the box

**Use Case**: Focus hotspot analysis on a specific component or region.

[**Image Placeholder**: Hotspot Results dialog showing top 5 nodes ranked by Von-Mises stress, with columns for Rank, NodeID, Value (MPa), X, Y, Z]

---

### Section 3: Point-Based Analysis

These tools enable detailed single-node analysis directly from the Display tab.

#### Plot Time History for Selected Node

**Purpose**: Generate a time history plot for a node you select.

**Workflow**:
1. Right-click → **Plot Time History for Selected Node**
2. If a node is already tracked (from Go To Node), you'll be asked to use it
3. Otherwise, click on a node to select it
4. A popup window displays the time history plot

**Behavior**:
- If you previously used "Go To Node", MARS asks if you want to use that node
- Click "Yes" to plot the tracked node
- Click "No" to pick a different node

**Plot Window Features**:
- Full time history of selected output type
- Interactive zoom and pan
- Data table with time-value pairs
- Resizable and movable window

[**Image Placeholder**: Time History popup window showing stress vs. time plot for Node 12345, with the 3D view visible behind it]

---

### Section 4: View Control

These tools help you navigate and control the camera.

#### Go To Node

**Purpose**: Fly the camera to a specific node by entering its ID.

**Workflow**:
1. Right-click → **Go To Node**
2. Enter the Node ID in the dialog
3. Click OK
4. The camera smoothly flies to that node
5. A marker and label appear at the node location

**Visual Indicators**:
- **Black sphere**: Marks the target node position
- **Red label**: Shows "Node [ID]" next to the marker
- Both remain visible until you navigate elsewhere

**Memory**: MARS remembers your last entered Node ID for convenience.

#### Lock Camera for Animation (freeze node)

**Purpose**: Keep the camera focused on a tracked node during animation playback.

**Requirements**: A node must be tracked (via Go To Node)

**Workflow**:
1. First use "Go To Node" to select a target
2. Right-click → **Lock Camera for Animation** (toggle on)
3. Start the animation
4. The camera follows the node as it moves with deformation

**Use Cases**:
- Watch a specific node's motion during vibration
- Track stress changes at a critical location
- Create focused animations for presentations

#### Reset Camera

**Purpose**: Return the camera to the default overview position.

**Workflow**:
1. Right-click → **Reset Camera**
2. The view zooms out to show the entire model
3. Camera orientation resets to isometric view

**When to Use**:
- After detailed inspection to return to overview
- If you get "lost" in the model
- Before taking screenshots for documentation

[**Image Placeholder**: 3D view showing "Go To Node" result with:
1. Black sphere marker at Node 12345
2. Red "Node 12345" label
3. Arrow pointing to the node
4. Context menu showing "Lock Camera for Animation" checked]

---

## Chapter 21 – Hotspot Analysis Workflow

Hotspot analysis is a powerful workflow for identifying and investigating critical locations. This chapter provides a complete step-by-step guide.

### Step 1: Run the Solver

Before hotspot analysis, you need computed results:
1. Load modal coordinate and stress files
2. Select desired output (e.g., Von-Mises Stress)
3. Click SOLVE
4. Switch to Display tab

### Step 2: Adjust Visualization

Prepare the view for analysis:
1. Set appropriate point size for your model
2. Adjust legend range to highlight critical values
3. Rotate to view the region of interest

### Step 3: Find Global Hotspots

For an overview of critical locations:
1. Right-click → **Find Hotspots (on current view)**
2. Enter a reasonable number (e.g., 10-20)
3. Review the ranked results

### Step 4: Investigate Specific Regions

For detailed analysis of a component:
1. Right-click → **Add Selection Box**
2. Position and size the box around the region
3. Right-click → **Find Hotspots in Selection**
4. Review results for that specific region

### Step 5: Examine Individual Nodes

For detailed node analysis:
1. Click on a node in the Hotspot Dialog
2. The view flies to that node
3. Right-click → **Plot Time History for Selected Node**
4. Review the time history plot

### Step 6: Document Results

Capture your findings:
1. Use legend range to set consistent scales
2. Take screenshots at each critical location
3. Use Save Time Point as CSV for numerical data

[**Image Placeholder**: Complete hotspot workflow montage showing:
1. Full model view with color map
2. Selection box around component
3. Hotspot dialog
4. Time history popup
5. Exported CSV snippet]

---

## Chapter 22 – Animation Workflow

Creating professional-quality animations requires a systematic approach. This chapter guides you through the complete process.

### Preparation Checklist

Before starting animation:
- [ ] Solver completed with deformations loaded
- [ ] Desired output type computed
- [ ] Time range of interest identified
- [ ] Display tab active

### Step 1: Configure Display

Set up the visualization:
1. Adjust **Point Size** for clarity
2. Set **Legend Range** for consistent colors
3. Set **Deformation Scale Factor** for visible motion
4. Choose **Absolute vs. Relative** deformation mode

### Step 2: Configure Animation

Set playback parameters:
1. Select **Time Step Mode**:
   - Custom: Enter step size in seconds
   - Actual: Set "Every nth" value
2. Set **Interval (ms)** for playback speed
3. Adjust **Start** and **End** times

### Step 3: Preview Animation

Test your settings:
1. Click **Play**
2. Watch for smooth playback
3. Click **Pause** to examine specific frames
4. Click **Stop** to reset

### Step 4: Adjust as Needed

Fine-tune settings:
- If animation is too fast, increase Interval
- If motion is too small, increase Deformation Scale
- If too many frames, increase "Every nth" or time step

### Step 5: Position Camera

Choose the best viewing angle:
1. Use mouse to position camera
2. Optionally use **Go To Node** to focus on a region
3. Consider **Lock Camera for Animation** to track a node

### Step 6: Export Animation

Save to file:
1. Ensure animation runs correctly
2. Click **Save as Video/GIF**
3. Choose format:
   - **MP4**: Smaller files, requires ffmpeg
   - **GIF**: Larger files, always available
4. Enter filename and save

### Recommended Settings by Use Case

| Use Case | Time Step | Interval | Deformation Scale |
|----------|-----------|----------|-------------------|
| Quick preview | Every 10th | 100 ms | 5 |
| Presentation | 0.01s custom | 50 ms | 3 |
| High-detail | 0.001s custom | 100 ms | 2 |
| Slow-motion | Every 1st | 200 ms | 1 |

[**Image Placeholder**: Animation export sequence showing:
1. Animation controls with settings
2. 3D view with animation frame
3. Save dialog with format options
4. Success message]

---

# PART IV: EXPORT AND DATA MANAGEMENT

---

## Chapter 23 – Exporting Results to CSV

MARS provides multiple ways to export computational results for further processing or documentation.

### Automatic Exports After Solving

After clicking SOLVE, these files are automatically created in the project directory:

| Output Type | Filename Pattern |
|------------|------------------|
| Von-Mises Stress | `von_mises.csv`, `time_of_max_von_mises.csv` |
| Max Principal | `max_principal.csv`, `time_of_max_principal.csv` |
| Min Principal | `min_principal.csv`, `time_of_min_principal.csv` |
| Deformation | `deformation.csv`, `time_of_max_deformation.csv` |
| Velocity | `velocity.csv`, `time_of_max_velocity.csv` |
| Acceleration | `acceleration.csv`, `time_of_max_acceleration.csv` |

### Manual Time Point Export

Export results at a specific time instant:
1. Go to Display tab
2. Set desired time in Time Point Controls
3. Click **Update**
4. Click **Save Time Point as CSV**
5. Choose filename and location

### CSV File Format

All exported CSVs follow this structure:
```csv
NodeID,X,Y,Z,[ScalarName]
1001,10.5,20.3,5.2,234.5
1002,10.8,20.1,5.5,219.8
...
```

### Tips for Working with Exported Data

- Use consistent Node IDs across all your files
- Exported coordinates can be used for mesh recreation
- Combine multiple exports in Excel/Python for comparative analysis

[**Image Placeholder**: File explorer showing exported CSV files in project directory, with one file open in a text editor showing the format]

---

## Chapter 24 – APDL Initial Condition Export

The APDL Initial Condition export allows you to restart ANSYS transient analyses from any time point computed in MARS.

### Purpose

Create velocity initial conditions at a specific time instant for use in ANSYS MechanicalAPDL.

### Requirements

- Deformation file must be loaded
- Solver must complete successfully
- Time point must be computed with velocity data

### Export Procedure

1. Go to Display tab
2. Set the desired time in Time Point Controls
3. Click **Update** to compute velocity at that instant
4. Click **Export Velocity as Initial Condition in APDL**
5. Choose filename (default: `initial_conditions.inp`)
6. Click Save

### Output File Format

```
! MARS-generated Initial Conditions
! Time: 0.05234 seconds
IC,1001,UX,,-0.002345
IC,1001,UY,,0.001568
IC,1001,UZ,,-0.000892
IC,1002,UX,,-0.002412
IC,1002,UY,,0.001534
IC,1002,UZ,,-0.000921
...
```

### Using in ANSYS

1. Copy the `.inp` file to your ANSYS working directory
2. Before SOLVE, use: `*USE,initial_conditions.inp`
3. Run transient analysis with IC applied

### Use Cases

- Restart transient from critical time point
- Transfer results between different model variants
- Create "smart restart" workflows

[**Image Placeholder**: APDL export dialog and snippet of generated .inp file content]

---

# PART V: TROUBLESHOOTING AND REFERENCE

---

## Chapter 25 – Troubleshooting Guide

This chapter provides solutions to common issues encountered while using MARS.

### File Loading Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| "Invalid MCF file" | Missing Time header | Ensure first column is "Time" |
| "Required column not found" | Wrong column naming | Check stress columns match `sx_1`, `sy_1`, etc. |
| File won't load | File encoding issue | Re-save as UTF-8 CSV |
| NodeID mismatch | Different node sets | Ensure same nodes in all files |

### Solver Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| SOLVE button disabled | Missing input files | Load both .mcf and stress .csv |
| Solver stalls at 0% | Very large dataset | Wait, or reduce model size |
| "Out of memory" error | Exceeded RAM | Increase RAM allocation in Settings |
| Very slow performance | Using double precision | Switch to single precision if acceptable |

### Display Tab Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Blank 3D view | No data loaded | Run solver or load visualization CSV |
| No color on nodes | Missing scalar column | Ensure output was selected before solving |
| Animation won't play | No deformations | Load deformation file and re-solve |
| Animation very slow | Too many frames | Increase "Every nth" value |

### Export Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| MP4 export fails | ffmpeg not installed | Install ffmpeg or use GIF format |
| Empty CSV | No results computed | Click Update in Time Point Controls first |
| IC export button hidden | No velocity data | Load deformations and enable velocity output |

### Plasticity Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Plasticity won't enable | Von Mises not selected | Select Von Mises output first |
| "Temperature file error" | Wrong file format | Use CSV with NodeID, Temperature columns |
| Corrected stress > elastic | Material data issue | Check stress-strain curve data |
| Convergence failure | Difficult problem | Increase max iterations |

[**Image Placeholder**: Troubleshooting flowchart for "SOLVE button disabled" showing decision tree with solutions]

---

## Chapter 26 – File Format Reference

### Modal Coordinate File (.mcf)

**Purpose**: Time-varying modal amplitudes

**Required Structure**:
```
Time,Mode1,Mode2,Mode3,...,ModeN
0.0000,1.23e-4,2.45e-5,3.67e-6,...
0.0001,1.25e-4,2.42e-5,3.70e-6,...
```

**Requirements**:
- First column MUST be "Time"
- Column count = 1 + number of modes
- Time values in seconds
- No missing values

---

### Modal Stress File (.csv)

**Purpose**: Modal stress tensors per node

**Required Columns**:
| Column Pattern | Description |
|----------------|-------------|
| `NodeID` | Unique node identifier |
| `sx_1, sx_2, ...` | Normal stress X per mode |
| `sy_1, sy_2, ...` | Normal stress Y per mode |
| `sz_1, sz_2, ...` | Normal stress Z per mode |
| `sxy_1, sxy_2, ...` | Shear stress XY per mode |
| `syz_1, syz_2, ...` | Shear stress YZ per mode |
| `sxz_1, sxz_2, ...` | Shear stress XZ per mode |

**Optional Columns**:
| Column | Description |
|--------|-------------|
| `X, Y, Z` | Node coordinates for visualization |

---

### Modal Deformation File (.csv)

**Purpose**: Modal displacements per node

**Required Columns**:
| Column Pattern | Description |
|----------------|-------------|
| `NodeID` | Same IDs as stress file |
| `ux_1, ux_2, ...` | X displacement per mode |
| `uy_1, uy_2, ...` | Y displacement per mode |
| `uz_1, uz_2, ...` | Z displacement per mode |

---

### Steady-State Stress File (.txt)

**Purpose**: Static stress field to superimpose

**Format**: Tab-delimited

```
NodeID	SX	SY	SZ	SXY	SYZ	SXZ
1001	100.5	200.3	150.2	25.1	30.5	15.2
```

---

### Temperature Field File (.csv)

**Purpose**: Node temperatures for plasticity correction

**Required Columns**:
| Column | Description |
|--------|-------------|
| `NodeID` | Must match stress file |
| `Temperature` | Temperature in consistent units |

**Example**:
```csv
NodeID,Temperature
1001,25.0
1002,150.5
1003,300.0
```

---

## Chapter 27 – Keyboard and Mouse Reference

### Mouse Controls (PyVista 3D Viewer)

| Action | Mouse Operation |
|--------|-----------------|
| Rotate view | Left-click + drag |
| Pan view | Right-click + drag |
| Zoom | Scroll wheel |
| Show tooltip | Hover over node |
| Context menu | Right-click (no drag) |

### General UI Controls

| Action | Control |
|--------|---------|
| Switch tabs | Click tab button |
| Enter value | Type in field + Enter |
| Toggle checkbox | Click checkbox |
| Multi-select | Not applicable |

---

## Chapter 28 – FAQs

**Q: Which outputs require the deformation file?**  
A: Deformation, Velocity, and Acceleration outputs require the modal deformation file to be loaded.

**Q: Can I compare results with the same color scale?**  
A: Yes. Manually set Legend Range min/max to fixed values across different analyses.

**Q: How do I focus on a single node?**  
A: Right-click → Go To Node, enter the Node ID, then optionally Lock Camera for Animation.

**Q: When should I use plasticity correction?**  
A: When elastic stress at notches, holes, or fillets exceeds the material yield stress.

**Q: Which plasticity method should I choose?**  
A: Start with Neuber (faster). Use Glinka if you need more conservative energy-based results.

**Q: How can I speed up large analyses?**  
A: Go to Settings → Advanced. Increase RAM allocation, use Single precision, or enable GPU acceleration.

**Q: What does "Skip first n modes" do?**  
A: It excludes the first n modes from reconstruction. Use this to skip rigid-body modes (typically 6 for free-free structures).

**Q: Why can't I see all files in Navigator?**  
A: Navigator automatically filters to show only .mcf, .csv, and .txt files relevant to MARS.

**Q: How do I track a node during animation?**  
A: Use Go To Node to target it, then enable Lock Camera for Animation from the context menu.

**Q: What if ffmpeg is not installed?**  
A: Export animations as GIF instead of MP4. GIF export is always available but produces larger files.

---

## Chapter 29 – Getting Help

### Before Submitting a Support Request

Gather this information:
1. **Error messages** from the Console
2. **Steps to reproduce** the issue
3. **Input files** (if you can share them)
4. **Screenshots** of the state when the error occurred

### Diagnostic Information

MARS logs helpful information to the Console. When reporting issues, include:
- The complete console output
- Contents of any error dialogs
- MARS version information

### Contact

For assistance with MARS, contact your designated maintainer or system administrator.

---

*End of MARS User Manual*
