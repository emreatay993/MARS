# MARS: Modal Analysis Response Solver - Architecture Documentation

## Overview

This document provides a comprehensive guide to the MARS application's modular architecture, design decisions, and implementation details.

---

## 🏗️ Architecture Layers

### Layer 1: Application Entry (`src/main.py`)

**Purpose**: Application initialization and lifecycle management

**Responsibilities**:
- Initialize Qt application
- Configure high-DPI scaling
- Apply global stylesheets
- Create and show main window
- Handle application exit

**Key Components**:
- `main()` function - Entry point

---

### Layer 2: Application Controller (`src/ui/application_controller.py`)

**Purpose**: Top-level application window and mediator between tabs and handlers

**Responsibilities**:
- Configure menu bar (File, View, Settings) and advanced settings dialog
- Host the project navigator dock through `NavigatorHandler`
- Instantiate solver and display tabs plus their shared plotting handler
- Route signals between tabs (`time_point_result_ready`, `animation_data_ready`, etc.)
- Surface warnings (e.g., animation precomputation failures) and restore UI state

**Key Components**:
- `ApplicationController` class (~233 lines)
- `NavigatorHandler`, `SettingsHandler`, and `PlottingHandler` collaborators
- Dock widget and menu construction helpers

**Design Pattern**: Mediator/Facade (centralises cross-tab coordination while delegating specialised logic to handlers)

---

### Layer 3: UI Tabs

#### Solver Tab (`src/ui/solver_tab.py`)

**Purpose**: Main interface for configuring and running analyses

**Responsibilities**:
- File loading (coordinates, stress, deformations, steady-state)
- Mode skipping configuration
- Output selection (von Mises, principal stresses, deformation, etc.)
- Fatigue parameter input
- Time history mode (single node analysis)
- Batch mode (all nodes analysis)
- Progress monitoring
- Result visualization

**Key Components**:
- `SolverTab` class (~566 lines) focused on UI wiring, signal emission, and console surfaces
- `SolverAnalysisHandler` (1108 lines) executes solves, builds configurations, monitors resources, and coordinates plotting
- `SolverFileHandler` (file dialogs and modal data life cycle)
- `SolverUIHandler` (checkbox state, visibility, and plot refresh)
- `SolverLogHandler` (routes stdout to the embedded console widget)
- Integration with `file_io` loaders and `core` managers

**Refactoring Impact**: 
- Original: Monolithic 1,700+ line widget with deeply nested handler logic
- Refactored: View class trimmed to ~566 lines; long-running flows moved into dedicated handler modules
- Solve orchestration consolidated inside `SolverAnalysisHandler`
- UI state changes captured in `SolverUIHandler` for easier testing and reuse

#### Display Tab (`src/ui/display_tab.py`)

**Purpose**: 3D visualization and animation

**Responsibilities**:
- 3D point cloud visualization (PyVista)
- Time point analysis display
- Animation precomputation and playback
- Hotspot detection
- Node picking and tracking
- Result export (CSV, APDL)

**Key Components**:
- `DisplayTab` class (650 lines) handles widget construction, signal wiring, and high-level state
- Display handler suite (~1,730 lines across 6 modules) drives file loading, rendering, animation (with absolute/relative deformation modes), interaction, exporting, and results application (`display_file_handler`, `display_visualization_handler`, `display_animation_handler`, `display_interaction_handler`, `display_export_handler`, `display_results_handler`)
- `DisplayState` dataclass coordinates shared state between handlers and the tab
- Visualization methods delegate to `VisualizationManager`, `AnimationManager`, and `HotspotDetector`

**Refactoring Impact**:
- Original: 2000+ lines, monolithic with mixed concerns
- Refactored: View logic reduced to ~650 lines while specialised handlers encapsulate hover annotations, node tracking, hotspot detection, exports, and animation workflows
- Visualization delegated to `VisualizationManager`
- Animation delegated to `AnimationManager`
- Hotspot detection delegated to `HotspotDetector`
- All features from legacy + critical bug fixes retained

---

### Layer 4: UI Components

#### Widgets (`src/ui/widgets/`)

**Purpose**: Reusable UI components

**Modules**:
1. `console.py` - Logger widget (64 lines)
   - Redirects stdout to QTextEdit
   - Buffers output for performance
   - Auto-scrolling

2. `plotting.py` - Plot widgets (689 lines)
   - MatplotlibWidget: Interactive plots with tables
   - PlotlyWidget: Modal coordinate visualization
   - PlotlyMaxWidget: Multi-trace plots

3. `dialogs.py` - Dialog windows (202 lines)
   - AdvancedSettingsDialog: Solver configuration
   - HotspotDialog: Hotspot analysis results

**Design Pattern**: Component pattern (reusable, independent)

#### Builders (`src/ui/builders/`)

**Purpose**: Construct complex UI layouts

**Modules**:
1. `solver_ui.py` - SolverTabUIBuilder (499 lines - includes plasticity options with IBG disabled)
   - Builds: file inputs, outputs, fatigue params, node selection
   - 8 builder methods, each <25 lines

2. `display_ui.py` - DisplayTabUIBuilder (324 lines)
   - Builds: file controls, visualization, time point, animation
   - 6 builder methods, each <25 lines

**Design Pattern**: Builder pattern (separates construction from representation)

**Benefits**:
- 327-line init_ui → Clean builder method calls
- Each section independently testable
- Easy to modify individual sections
- Consistent styling and layout

#### Styles (`src/ui/styles/style_constants.py`)

**Purpose**: Centralised Qt stylesheet strings that reproduce the legacy MSUP look and feel

**Highlights**:
- Menu bar, dock, tab, button, and group box styles applied by builders and controllers
- Shared colour palette constants (e.g., theme blue, background tones)
- Keeps visual customisation in one place alongside the rest of the UI package

---

### Layer 5: Business Logic

#### Computation (`src/core/computation.py`)

**Purpose**: High-level analysis orchestration

**Key Components**:
- `AnalysisEngine` class (291 lines)
  - Wraps MSUPSmartSolverTransient
  - Handles mode filtering
  - Orchestrates batch and single-node analysis
  - Manages solver lifecycle

**Methods**:
- `configure_data()` - Setup analysis data
- `create_solver()` - Instantiate solver with config
- `run_batch_analysis()` - Execute batch processing
- `run_single_node_analysis()` - Execute single-node analysis
- `compute_time_point_stresses()` - Compute at specific time

**Design Pattern**: Facade (simplifies solver interaction)

#### Visualization (`src/core/visualization.py`)

**Purpose**: Visualization business logic

**Key Components**:

1. `VisualizationManager` (7 methods)
   - Mesh creation and updates
   - Scalar field operations
   - Deformation application

2. `AnimationManager` (7 methods)
   - Frame precomputation
   - Playback control
   - Export functionality

3. `HotspotDetector` (4 methods)
   - Hotspot identification
   - Regional filtering
   - Threshold filtering

**Design Pattern**: Manager pattern (encapsulates complex logic)

#### Plasticity Utilities (`src/core/plasticity.py`)

**Purpose**: Prepare material and temperature inputs for the plasticity solvers.

**Key Components**:
- `build_material_db_from_profile()` converts UI material profiles into the numerical tables used by the solver.
- `map_temperature_field_to_nodes()` aligns temperature datasets with solver node ordering, honouring defaults when provided.
- `extract_poisson_ratio()` picks a representative Poisson ratio (with safe fallbacks).
- `PlasticityDataError` communicates validation issues back to UI layers.

**Design Pattern**: Functional utilities focused on pure data transformation.

#### Data Models (`src/core/data_models.py`)

**Purpose**: Structured data containers

**Key Classes**:
- `ModalData` - Modal coordinates and time values
- `ModalStressData` - Stress components and node info
- `DeformationData` - Deformation components
- `SteadyStateData` - Steady-state stress data
- `SolverConfig` - Analysis configuration
- `AnalysisResult` - Analysis results

**Design Pattern**: Data Transfer Objects (structured, type-safe data)

**Benefits**:
- Type safety with @dataclass
- Properties for computed values
- Clear data contracts
- Easy serialization

---

### Layer 6: I/O Operations

#### Validators (`src/file_io/validators.py`)

**Purpose**: Validate input files before loading

**Functions** (all <30 lines):
- `validate_mcf_file()` - Modal coordinates
- `validate_modal_stress_file()` - Stress data
- `validate_deformation_file()` - Deformations
- `validate_steady_state_file()` - Steady-state stress

**Returns**: Tuple of (is_valid, error_message)

#### Loaders (`src/file_io/loaders.py`)

**Purpose**: Load and parse input files

**Functions** (all <40 lines):
- `load_modal_coordinates()` → ModalData
- `load_modal_stress()` → ModalStressData
- `load_modal_deformations()` → DeformationData
- `load_steady_state_stress()` → SteadyStateData

**Pattern**: Each loader calls validator first, then returns structured data

#### Exporters (`src/file_io/exporters.py`)

**Purpose**: Export results to various formats

**Functions**:
- `export_to_csv()` - Generic CSV export
- `export_apdl_ic()` - APDL initial conditions
- `export_time_point_results()` - Time point data
- `export_mesh_to_csv()` - PyVista mesh export
- `export_results_with_headers()` - Custom headers

---

### Layer 7: Utilities

#### Constants (`src/utils/constants.py`)

**Purpose**: Centralized solver configuration and runtime settings

**Categories**:
1. Solver configuration (RAM, precision)
2. Data types (NumPy, result dtypes)
3. Environment toggles (OpenBLAS threads)
4. Display defaults (point size, colours, animation intervals)

> UI stylesheet strings now live in `src/ui/styles/style_constants.py` to keep visual theming alongside the rest of the UI package.

**Benefits**: 
- Single source of truth
- Easy configuration changes
- No magic numbers in code

#### File Utilities (`src/utils/file_utils.py`)

**Purpose**: File manipulation helpers

**Functions**:
- `unwrap_mcf_file()` - Unwrap wrapped MCF files

#### Node Utilities (`src/utils/node_utils.py`)

**Purpose**: Node ID mapping

**Functions**:
- `get_node_index_from_id()` - Map node ID to array index

---

### Layer 8: Solver Engine (`src/solver/engine.py`)

**Purpose**: Core numerical computation (minimal changes from legacy)

**Key Class**:
- `MSUPSmartSolverTransient` (1319 lines, preserved)
  - JIT-compiled kernels for performance
  - Memory management
  - Batch processing
  - Stress/deformation calculations

**Changes from Legacy**: Torch/GPU paths removed; tensor operations converted to NumPy while preserving numerical kernels

**Risk Level**: HIGH - Therefore minimal changes made

---

## 🔄 Data Flow

### Batch Analysis Flow

```
User Interface (SolverTab)
    ↓ (user clicks SOLVE)
1. Validate inputs → SolverConfig
    ↓
2. Load data → Data Models (if not loaded)
    ↓
3. Configure AnalysisEngine
    ↓
4. Create solver with mode filtering
    ↓
5. Run batch analysis
    ↓
6. Solver processes nodes in chunks
    ↓ (progress signals)
7. Update progress bar
    ↓
8. Results saved to CSV files
    ↓
9. Display completion message
```

### Time History Analysis Flow

```
User Interface (SolverTab)
    ↓ (user enters node ID, clicks SOLVE)
1. Validate node ID
    ↓
2. Get node index (utils.node_utils)
    ↓
3. Configure AnalysisEngine
    ↓
4. Run single-node analysis
    ↓
5. AnalysisEngine → Solver → Compute stresses
    ↓
6. Return AnalysisResult
    ↓
7. Update MatplotlibWidget plot
    ↓
8. Display in "Plot (Time History)" tab
```

### 3D Visualization Flow

```
Display Tab
    ↓ (user loads CSV file)
1. Load file → DataFrame
    ↓
2. Extract coordinates, node IDs, scalars
    ↓
3. Create mesh (VisualizationManager)
    ↓
4. Add scalars to mesh
    ↓
5. Display in PyVista plotter
    ↓ (user adjusts controls)
6. Update point size / scalar range
    ↓
7. Render changes
```

### Animation Flow

```
Display Tab
    ↓ (user clicks Play)
1. Gather animation parameters
    ↓
2. Request precomputation (signal to SolverTab)
    ↓
3. SolverTab computes frames
    ↓
4. Store in AnimationManager
    ↓
5. Signal back to DisplayTab
    ↓
6. Start QTimer for playback
    ↓
7. For each frame:
   - Get frame data from AnimationManager
   - Update mesh scalars
   - Update mesh coordinates (if deformation)
   - Render
    ↓
8. Loop until complete or stopped
```

---

## 🎨 Design Patterns Used

### 1. Builder Pattern (UI Construction)

**Where**: `ui/builders/solver_ui.py`, `ui/builders/display_ui.py`

**Why**: Separate complex UI construction from business logic

**Example**:
```python
builder = SolverTabUIBuilder()
layout, components = builder.build_complete_layout()
self.setLayout(layout)
```

**Benefits**:
- Clean separation of concerns
- Reusable components
- Easy to modify individual sections
- Testable in isolation

### 2. Manager Pattern (Business Logic)

**Where**: `core/visualization.py`

**Why**: Encapsulate complex operations in dedicated managers

**Example**:
```python
self.viz_manager = VisualizationManager()
mesh = self.viz_manager.create_mesh_from_coords(coords, node_ids)
```

**Benefits**:
- Single responsibility
- Testable without UI
- Reusable across tabs
- Clear API

### 3. Data Transfer Objects (Data Structures)

**Where**: `core/data_models.py`

**Why**: Type-safe, structured data passing

**Example**:
```python
@dataclass
class ModalData:
    modal_coord: np.ndarray
    time_values: np.ndarray
```

**Benefits**:
- Type safety
- Clear data contracts
- Properties for computed values
- Easy to serialize

### 4. Facade Pattern (Simplified Interface)

**Where**: `core/computation.py`, `io/loaders.py`

**Why**: Hide complex subsystem behind simple interface

**Example**:
```python
# Complex operation hidden behind simple call
modal_data = load_modal_coordinates(filename)
```

**Benefits**:
- Simple client code
- Hides complexity
- Easy to change implementation
- Clear API boundaries

### 5. Strategy Pattern (Validation)

**Where**: `io/validators.py`

**Why**: Consistent validation interface

**Example**:
```python
is_valid, error = validate_mcf_file(filename)
if not is_valid:
    show_error(error)
```

**Benefits**:
- Consistent error handling
- Reusable validation logic
- Easy to add new validators

---

## 📦 Package Dependencies

### External Dependencies

```
numpy, pandas  → Data manipulation
numba          → JIT compilation for performance
PyQt5          → GUI framework
matplotlib     → 2D plotting
plotly         → Interactive plots
pyvista        → 3D visualization
psutil         → System resource monitoring
imageio        → Animation export
```

### Internal Dependencies

```
ui.main_window
  ├─> ui.solver_tab
  │     ├─> ui.builders.solver_ui
  │     ├─> ui.widgets.{console, plotting}
  │     ├─> core.computation (AnalysisEngine)
  │     ├─> core.data_models
  │     ├─> io.loaders
  │     └─> utils.{constants, node_utils}
  │
  └─> ui.display_tab
        ├─> ui.builders.display_ui
        ├─> ui.widgets.{plotting, dialogs}
        ├─> core.visualization (Managers)
        ├─> core.data_models
        ├─> io.exporters
        └─> utils.constants

core.computation
  └─> solver.engine (MSUPSmartSolverTransient)
        └─> utils.constants

All modules use utils.constants for configuration
```

**Note**: No circular dependencies. Clear hierarchical structure.

---

## 🔧 Configuration Management

### Global Configuration

**File**: `utils/constants.py`

**Categories**:

1. **Solver Configuration**
   - `RAM_PERCENT` - Memory allocation (default: 0.9)
   - `DEFAULT_PRECISION` - Single or Double (default: Double)

2. **Data Types** (derived from precision)
   - `NP_DTYPE` - NumPy dtype
   - `RESULT_DTYPE` - Result file dtype

3. **UI Styles** (centralized CSS)
   - `BUTTON_STYLE` - Button appearance
   - `GROUP_BOX_STYLE` - GroupBox appearance
   - `TAB_STYLE` - Tab widget appearance
   - And more...

### Runtime Configuration

**Method 1**: Edit `utils/constants.py` before running

**Method 2**: Use Advanced Settings dialog (runtime, doesn't persist)
- Settings → Advanced
- Adjust RAM, Precision
- Click OK
- Settings apply to next solve

### Per-Analysis Configuration

**Method**: Use SolverConfig dataclass
```python
config = SolverConfig(
    calculate_von_mises=True,
    skip_n_modes=2,
    output_directory='/path/to/output'
)
```

---

## 💾 Data Management

### Data Flow

1. **File → Validator → Loader → Data Model**
   ```
   file.mcf → validate_mcf_file() → load_modal_coordinates() → ModalData
   ```

2. **Data Model → Analysis Engine → Solver**
   ```
   ModalData + ModalStressData → configure_data() → create_solver()
   ```

3. **Solver → Results → Export**
   ```
   compute() → memmap arrays → convert_dat_to_csv() → .csv files
   ```

### Memory Management

**Strategy**: Chunked processing for large datasets

1. **Memory Estimation**:
   - Calculate memory per node
   - Determine chunk size based on available RAM
   - Process nodes in chunks

2. **Garbage Collection**:
   - Explicit `gc.collect()` after each chunk
   - Memory freed before next chunk

3. **Memory-Mapped Files**:
   - Large results stored as memmap
   - Converted to CSV at end
   - Prevents RAM overflow

### State Management

**Tab-Level State**:
- Each tab manages its own state
- No global variables (except constants)
- Data passed via signals

**Application State**:
- Project directory in MainWindow
- Shared via attributes to tabs

---

## 🎯 Key Design Decisions

### 1. Minimal Solver Changes

**Decision**: Keep `solver/engine.py` nearly unchanged

**Rationale**:
- High-risk numerical code
- JIT-compiled kernels
- Extensively tested legacy code

**Implementation**:
- Replaced torch tensors/matmul with NumPy arrays and `np.matmul`
- Removed GPU memory management paths
- Preserved core numerical computations

### 2. Builder Pattern for UI

**Decision**: Extract UI construction to builder classes

**Rationale**:
- 327-line init_ui methods unmaintainable
- Mixed UI creation with business logic
- Hard to test

**Implementation**:
- `SolverTabUIBuilder` with 8 methods
- `DisplayTabUIBuilder` with 6 methods
- Each method <25 lines

**Impact**: Init methods reduced from 327 lines to ~20 lines

### 3. Manager Classes for Logic

**Decision**: Extract complex logic to manager classes

**Rationale**:
- DisplayTab was 2000+ lines
- Mixed visualization logic with UI
- Impossible to test

**Implementation**:
- `VisualizationManager` for mesh operations
- `AnimationManager` for animation logic
- `HotspotDetector` for analysis

**Impact**: DisplayTab reduced from 2000+ to ~650 lines

### 4. Data Models for Structure

**Decision**: Use dataclasses for all data

**Rationale**:
- Dict passing was error-prone
- No type safety
- Unclear data contracts

**Implementation**:
- 7 dataclass models
- Type hints on all attributes
- Properties for computed values

**Impact**: Type-safe data flow, clear contracts

### 5. I/O Layer Separation

**Decision**: Complete separation of file I/O

**Rationale**:
- File loading duplicated across methods
- Validation mixed with loading
- Hard to test

**Implementation**:
- Validators return consistent format
- Loaders call validators, return data models
- Exporters handle all output formats

**Impact**: Reusable, testable I/O operations

---

## 🧪 Testing Strategy

### Unit Tests

**Target**: Core utilities, I/O, data models

**Coverage**: >80% for non-UI code

**Tools**: pytest, pytest-cov

### Integration Tests

**Target**: Complete workflows

**Approach**: Programmatic UI interaction, output comparison

### Manual Tests

**Target**: GUI behavior, user experience

**Approach**: Comprehensive checklist (~200 items)

### Regression Tests

**Target**: Ensure no behavior changes

**Approach**: Compare outputs with legacy code

---

## 📈 Performance Considerations

### Optimization Points

1. **JIT Compilation** (Numba)
   - Von Mises calculation
   - Principal stress calculation
   - Velocity/acceleration derivatives
   - Rainflow counting

2. **Memory Efficiency**
   - Chunked processing
   - Memory-mapped files for large results
   - Explicit garbage collection

3. **UI Responsiveness**
   - Buffered console output
   - Progress signals every chunk
   - QApplication.processEvents()

### Performance Targets

- File loading: <5s for typical files
- Time history: <1s per node
- Batch analysis: Scales linearly with node count
- Animation: >30 FPS playback
- Memory: Stays within configured RAM limit

---

## 🔒 Error Handling

### Validation Errors

**Location**: File loading phase

**Handling**:
- Validators return error messages
- QMessageBox warnings shown to user
- Console logs error details
- Operation cancelled, no partial state

### Runtime Errors

**Location**: During analysis

**Handling**:
- Try-except in solve methods
- Traceback logged to console
- Progress bar hidden
- User-friendly error dialog

### Resource Errors

**Location**: Memory/disk operations

**Handling**:
- Memory estimation before processing
- Check disk space before export
- Graceful degradation if resources low

---

## 🚀 Extension Points

### Adding New Analysis Types

1. Add computation method to `solver/engine.py`
2. Add flag to `SolverConfig`
3. Add UI checkbox to `SolverTabUIBuilder`
4. Add result handling to `SolverTab`

### Adding New Visualizations

1. Add manager method to `VisualizationManager`
2. Add UI controls to `DisplayTabUIBuilder`
3. Add event handler to `DisplayTab`

### Adding New File Formats

1. Add validator to `io/validators.py`
2. Add loader to `io/loaders.py`
3. Add data model to `core/data_models.py` (if needed)
4. Add UI controls to builder
5. Add handler to SolverTab

---

## 📝 Coding Standards

### Function Guidelines

- **Length**: <30 lines (strict)
- **Complexity**: <10 (cyclomatic)
- **Parameters**: ≤5 (use config objects if more)
- **Indentation**: ≤2 levels
- **Type hints**: Required on all functions
- **Docstrings**: Required (Google style)

### Module Guidelines

- **Length**: <400 lines preferred (some modules larger for comprehensive UI)
- **Classes**: ≤3 per module (exceptions for UI tabs with full feature sets)
- **Functions**: ≤20 per module (UI modules may have more for complete functionality)
- **Purpose**: Single, clear responsibility
- **Naming**: Descriptive, follows PEP 8

**Note**: UI modules (display_tab.py, solver_tab.py) are larger due to comprehensive feature implementation including all legacy functionality plus bug fixes. These maintain clean separation through use of manager classes and builder patterns.

### Class Guidelines

- **Methods**: ≤15 per class
- **Attributes**: ≤7 per class
- **Inheritance**: ≤3 levels deep
- **Responsibility**: Single, clear purpose

---

## 🎓 Lessons Learned

### What Worked Well

1. **Phased Approach**: Low-risk first (utils, I/O) → High-risk last (UI)
2. **Builder Pattern**: Dramatically simplified UI code
3. **Manager Pattern**: Cleaned up complex business logic
4. **Data Models**: Provided structure and type safety
5. **Extract, Don't Rewrite**: Preserved behavior perfectly

### Challenges Overcome

1. **Large Files**: 2000+ line classes → Broken into manageable modules
2. **Mixed Concerns**: I/O, UI, logic → Clearly separated
3. **Code Duplication**: File loading → Reusable loaders
4. **Testing**: Tightly coupled → Dependency injection enabled testing
5. **Maintainability**: Locate code → Clear structure, easy to find

---

## 🔮 Future Enhancements

### Short Term

1. ✅ ~~Complete animation save functionality~~ - **DONE**
2. ✅ ~~Complete hotspot detection context menu~~ - **DONE**
3. ✅ ~~Complete node picking and tracking~~ - **DONE**
4. ✅ ~~Fix hover annotation for node information~~ - **DONE** (Bug Fix #6)
5. ✅ ~~Fix scalar bar title and range updates~~ - **DONE** (Bug Fix #7)
6. Add more unit tests (target >80% coverage)
7. Performance profiling and optimization
8. Add comprehensive error logging

### Medium Term

1. Add configuration file support (YAML/JSON)
2. Add result caching for faster re-analysis
3. Add parallel processing for batch mode
4. Add more export formats (VTK, HDF5)
5. Add plot export (PDF, PNG)

### Long Term

1. Plugin architecture for custom analyses
2. Web-based interface option
3. Distributed computing support
4. Machine learning integration
5. Real-time collaboration features

---

## 📚 Further Reading

- [PyQt5 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [PyVista Documentation](https://docs.pyvista.org/)
- [Numba Documentation](https://numba.pydata.org/)
- [Pytest Documentation](https://docs.pytest.org/)

---

**Document Version**: 1.4  
**Last Updated**: January 2026  
**Status**: ✅ Complete and Current

**Recent Updates (v0.97+)**:
- Fixed node hover detection to accurately identify nodes under cursor
- Added visual pick indicator (black marker with red label) for time history node selection
- Fixed camera reset issues during node picking and hotspot navigation
- Fixed camera orientation widget sizing on first Display tab load
- Updated FILE_INDEX with accurate line counts and new modules
- Removed PyTorch/GPU acceleration paths; solver is NumPy-only

**Previous Updates (v0.96)**:
- Added application icon system in `resources/icons/`
- Updated application_controller.py to 233 lines (added icon loading)
- Updated solver_ui.py to 499 lines (added IBG disable logic)
- Documented IBG plasticity algorithm status (disabled pending validation)
- Updated version numbering to v0.96
- Overall codebase: ~13,100 lines
