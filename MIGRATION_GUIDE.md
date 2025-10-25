# Migration Guide: Legacy MSUP Smart Solver to MARS

Use this guide to transition legacy MSUP Smart Solver integrations to the refactored MARS (Modal Analysis Response Solver) architecture.

---

## 📋 Quick Reference

### Import Changes (new modular locations)

| Legacy | Modular |
|--------|---------|
| `from solver_engine import MSUPSmartSolverTransient` | `from solver.engine import MSUPSmartSolverTransient` |
| `from display_tab import DisplayTab` | `from ui.display_tab import DisplayTab` |
| `from fea_utilities import generate_apdl_ic` | `from file_io.exporters import generate_apdl_ic` |
| Global `RAM_PERCENT` | `from utils.constants import RAM_PERCENT` |
| Global `unwrap_mcf_file()` | `from utils.file_utils import unwrap_mcf_file` |

### Class Name Changes / Equivalents

| Legacy | Modular |
|--------|---------|
| `MSUPSmartSolverGUI` | `SolverTab` |
| `DisplayTab` | `DisplayTab` (same name, refactored) |
| `MainWindow` | `MainWindow` (same name, refactored) |

---

## 🔄 Code Migration Examples

### Example 1: Loading a File

**Legacy**:
```python
def process_modal_stress_file(self, filename):
    # Inline validation
    df_val = pd.read_csv(filename)
    if 'NodeID' not in df_val.columns:
        raise ValueError("...")
    # ... more validation ...
    
    # Inline data extraction
    global df_node_ids, node_coords
    df_node_ids = df_val['NodeID'].to_numpy().flatten()
    node_coords = df_val[['X', 'Y', 'Z']].to_numpy()
    # ... extract all components ...
```

**Modular**:
```python
def _load_stress_file(self, filename):
    try:
        # Validation and loading in one call
        stress_data = load_modal_stress(filename)
        
        # Store as structured data model
        self.stress_data = stress_data
        
        # Update UI
        self._log_stress_load(filename, stress_data)
        
    except ValueError as e:
        QMessageBox.warning(self, "Invalid File", str(e))
```

### Example 2: Creating Solver

**Legacy**:
```python
solver = MSUPSmartSolverTransient(
    modal_sx[:, mode_slice],
    modal_sy[:, mode_slice],
    # ... many parameters ...
)
if calculate_damage:
    solver.fatigue_A = fatigue_A
    solver.fatigue_m = fatigue_m
```

**Modular**:
```python
# Build configuration
config = SolverConfig(
    calculate_von_mises=True,
    calculate_damage=True,
    fatigue_A=1000.0,
    fatigue_m=-3.0,
    skip_n_modes=2
)

# Let engine handle details
engine = AnalysisEngine()
engine.configure_data(modal_data, stress_data)
solver = engine.create_solver(config)
```

### Example 3: Building UI

**Legacy**:
```python
def init_ui(self):
    # 327 lines of inline UI creation
    self.coord_file_button = QPushButton('...')
    self.coord_file_button.setStyleSheet(button_style)
    self.coord_file_button.setFont(QFont('Arial', 8))
    # ... 320 more lines ...
```

**Modular**:
```python
def _build_ui(self):
    builder = SolverTabUIBuilder()
    layout, self.components = builder.build_complete_layout()
    self.setLayout(layout)
    self._setup_component_references()
    self._connect_signals()
```

### Example 4: Mesh Operations

**Legacy**:
```python
def _visualize_data(self, filename):
    # 80 lines of inline mesh creation and styling
    df = pd.read_csv(filename)
    coords = df[['X', 'Y', 'Z']].to_numpy()
    mesh = pv.PolyData(coords)
    mesh["NodeID"] = df['NodeID'].to_numpy()
    # ... many more operations ...
    self.plotter.add_mesh(mesh, ...)
```

**Modular**:
```python
def _visualize_data(self, filename):
    df = pd.read_csv(filename)
    coords = df[['X', 'Y', 'Z']].to_numpy()
    node_ids = df['NodeID'].to_numpy() if 'NodeID' in df else None
    
    # Manager handles complexity
    mesh = self.viz_manager.create_mesh_from_coords(coords, node_ids)
    
    # Manager handles scalar updates
    mesh = self.viz_manager.update_mesh_scalars(mesh, scalars, name)
    
    self.current_mesh = mesh
    self.update_visualization()
```

---

## 🔍 Finding Code in New Structure

### "Where did X go?"

**File Loading Logic**:
- Validation: `src/file_io/validators.py`
- Loading: `src/file_io/loaders.py`
- UI: `src/ui/solver_tab.py` (methods like `_load_stress_file`)

**UI Creation**:
- Solver Tab: `src/ui/builders/solver_ui.py`
- Display Tab: `src/ui/builders/display_ui.py`
- Tab classes: `src/ui/solver_tab.py`, `src/ui/display_tab.py`

**Plotting**:
- Matplotlib/Plotly widgets: `src/ui/widgets/plotting.py`
- Plot data handling: In respective tab classes

**3D Visualization**:
- Display tab: `src/ui/display_tab.py`
- Managers: `src/core/visualization.py`
- Mesh operations: `VisualizationManager`
- Animation: `AnimationManager`

**Solver/Computation**:
- Engine: `src/solver/engine.py` (mostly unchanged)
- Wrapper: `src/core/computation.py` (AnalysisEngine)

**Configuration**:
- All constants: `src/utils/constants.py`
- Styles: `src/utils/constants.py`

**Utilities**:
- File operations: `src/utils/file_utils.py`
- Node operations: `src/utils/node_utils.py`

---

## 🎯 Common Migration Tasks

### Task 1: Modify Solver Settings

**Legacy**: Edit global variables in `main_app.py`

**Modular**: Edit `src/utils/constants.py`
```python
RAM_PERCENT = 0.8  # Changed from 0.9
DEFAULT_PRECISION = 'Single'  # Changed from 'Double'
```

### Task 2: Add New Output Type

**Steps**:
1. Add checkbox in `src/ui/builders/solver_ui.py` → `build_output_selection_section()`
2. Add field to `SolverConfig` in `src/core/data_models.py`
3. Add computation in `src/solver/engine.py` (if new calculation needed)
4. Add result handling in `src/ui/solver_tab.py` → `_handle_batch_results()`

### Task 3: Change UI Styling

**Legacy**: Edit inline stylesheets in `init_ui()`

**Modular**: Edit `src/utils/constants.py`
```python
BUTTON_STYLE = """
    QPushButton {
        background-color: #YOUR_COLOR;
        ...
    }
"""
```

All buttons automatically use new style.

### Task 4: Add File Format Support

**Steps**:
1. Add validator: `src/file_io/validators.py` → `validate_new_format()`
2. Add loader: `src/file_io/loaders.py` → `load_new_format()` 
3. Add data model: `src/core/data_models.py` (if needed)
4. Add UI: `src/ui/builders/solver_ui.py` → Add button
5. Add handler: `src/ui/solver_tab.py` → `_load_new_format()`

---

## 🐛 Troubleshooting Migration Issues

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'utils'`

**Solution**: Ensure you're in correct directory
```bash
cd src
python main.py
```

Or use module execution:
```bash
python -m src.main
```

### Missing Global Variables

**Problem**: `NameError: name 'modal_sx' is not defined`

**Solution**: Legacy used globals, modular uses data models
```python
# Legacy
global modal_sx
modal_sx = df['sx'].to_numpy()

# Modular
stress_data = load_modal_stress(filename)
modal_sx = stress_data.modal_sx
```

### UI Changes Not Reflecting

**Problem**: Changed constants but UI looks same

**Solution**: 
1. Check you edited `src/utils/constants.py` (not legacy)
2. Restart application
3. Clear Python cache: `del src/__pycache__`

### Solver Not Found

**Problem**: `ImportError: cannot import name 'MSUPSmartSolverTransient'`

**Solution**: Update import
```python
# Old
from solver_engine import MSUPSmartSolverTransient

# New
from solver.engine import MSUPSmartSolverTransient
```

---

## ✅ Migration Checklist

For team members migrating to modular code:

- [ ] Read README.md
- [ ] Read ARCHITECTURE.md
- [ ] Understand new package structure
- [ ] Update development environment
- [ ] Install dependencies from requirements.txt
- [ ] Run unit tests to verify setup
- [ ] Try running the application
- [ ] Load test files and verify functionality
- [ ] Read code in src/ directory
- [ ] Understand data models
- [ ] Understand analysis engine
- [ ] Understand UI builders
- [ ] Run manual testing checklist
- [ ] Compare outputs with legacy code
- [ ] Bookmark this migration guide

---

## 📞 Getting Help

### Documentation Hierarchy

1. **README.md** - Start here, quick start guide
2. **ARCHITECTURE.md** - Detailed architecture documentation
3. **This file** - Migration from legacy to modular
4. **Module docstrings** - Specific implementation details

### For Specific Questions

- **"How do I...?"** → Check README Usage Guide
- **"Where is...?"** → Check "Finding Code" section above
- **"Why was...?"** → Check ARCHITECTURE Key Design Decisions
- **"How to test...?"** → Check tests/TESTING_GUIDE.md

---

## 🎉 Benefits of New Architecture

### For Developers

- ✅ **Easy to locate code**: Clear structure, predictable locations
- ✅ **Easy to understand**: Short functions, clear names, good docs
- ✅ **Easy to modify**: Change one module, others unaffected
- ✅ **Easy to test**: Pure functions, dependency injection
- ✅ **Easy to extend**: Clear extension points

### For Users

- ✅ **Identical interface**: No learning curve
- ✅ **Same features**: Everything still works
- ✅ **Better reliability**: More testing, better error handling
- ✅ **Better performance**: Same algorithms, better structure

### For Maintainers

- ✅ **Faster onboarding**: Clear architecture, good docs
- ✅ **Faster bug fixes**: Easy to locate issues
- ✅ **Faster feature development**: Modular structure
- ✅ **Lower risk**: Changes isolated to modules
- ✅ **Higher confidence**: Comprehensive testing

---

**Need Help?** Check documentation or create an issue!

**Contributing?** Follow coding standards and submit a PR!

**Upgrading?** This guide has you covered!

