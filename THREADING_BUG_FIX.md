# Critical Threading Bug Fix - Qt Widget Access from Background Thread

## Date
November 22, 2025

## Bug Report

**Error:** `'PlotlyMaxWidget' object has no attribute 'plotting_handler'`

**Traceback:**
```
File "analysis_handler.py", line 55, in run
  result = self.analysis_handler._execute_analysis(self.config)
File "analysis_handler.py", line 416, in _execute_analysis
  self._handle_batch_results(config)
File "analysis_handler.py", line 550, in _handle_batch_results
  self.tab.plot_max_over_time_tab.update_plot(
File "plotting.py", line 551, in update_plot
  main_win.plotting_handler.load_fig_to_webview(resfig, self.web_view)
AttributeError: 'PlotlyMaxWidget' object has no attribute 'plotting_handler'
```

## Root Cause

**Qt Thread Safety Violation:** Qt widgets can ONLY be created and updated from the **main GUI thread**.

When we implemented `SolverThread`, the entire `_execute_analysis()` method ran in the background thread, including:
- ❌ `_handle_batch_results()` - Creates/updates `PlotlyMaxWidget`
- ❌ `_handle_time_history_result()` - Updates plot widgets
- ❌ Widget creation and updates

This violated Qt's threading rules and caused the AttributeError.

## Solution

**Separate Computation from UI Updates:**

### Thread Separation Strategy
- **Background Thread:** Heavy computation ONLY (number crunching)
- **Main Thread:** All Qt widget operations (plots, UI updates)

### Implementation

#### 1. Modified `_execute_analysis()` - Computation Only
```python
def _execute_analysis(self, config):
    """
    Execute ONLY the computation (no UI updates).
    Safe to call from background thread.
    """
    # Create solver
    self.tab.analysis_engine.create_solver(config)
    
    # Connect progress signal (Qt signals are thread-safe)
    if self.tab.analysis_engine.solver:
        self.tab.analysis_engine.solver.progress_signal.connect(
            self.tab.update_progress_bar
        )
    
    # Run analysis (computation only - no Qt widget operations)
    if config.time_history_mode:
        result = self.tab.analysis_engine.run_single_node_analysis(
            config.selected_node_id, config
        )
    else:
        self.tab.analysis_engine.run_batch_analysis(config)
        result = None
    
    return result  # No UI updates here!
```

#### 2. Updated `SolverThread` - Emit Config
```python
class SolverThread(QThread):
    finished = pyqtSignal(object, object)  # Emits (result, config)
    
    def run(self):
        # Configure and execute
        self.analysis_handler._configure_analysis_engine()
        result = self.analysis_handler._execute_analysis(self.config)
        
        # Emit both result AND config for main thread
        self.finished.emit(result, self.config)
```

#### 3. Updated `_on_solve_complete()` - Handle Results on Main Thread
```python
def _on_solve_complete(self, result, config):
    """
    Handle successful solve completion (runs on main thread).
    This is where all Qt widget operations happen safely.
    """
    # Re-enable UI
    self.tab.setEnabled(True)
    
    # Hide progress bar
    self.tab.progress_bar.setVisible(False)
    
    # Handle results (NOW on main thread - safe for Qt widgets!)
    if config.time_history_mode:
        self._handle_time_history_result(result, config)
    else:
        self._handle_batch_results(config)  # ← Now safe!
    
    # Log completion
    self._log_solve_complete()
    
    # Restore tab index
    self.tab.show_output_tab_widget.setCurrentIndex(self._current_tab_index)
```

## Key Changes

### Before (Broken)
```
Background Thread:
  ├─ Computation
  ├─ _handle_batch_results()  ← Qt widget operations! ❌
  └─ _handle_time_history_result()  ← Qt widget operations! ❌

Main Thread:
  └─ Waiting...
```

### After (Fixed)
```
Background Thread:
  └─ Computation ONLY ✅

Main Thread (via signal):
  ├─ _handle_batch_results()  ← Qt widget operations ✅
  └─ _handle_time_history_result()  ← Qt widget operations ✅
```

## Qt Threading Rules

### ✅ Safe from Any Thread
- Reading data
- Number crunching (numpy, torch)
- File I/O
- **Qt Signals** (thread-safe communication)

### ❌ MUST be on Main Thread
- Creating Qt widgets
- Updating Qt widgets (setText, append, etc.)
- Accessing widget properties
- Layout operations
- Any QWidget method calls

## Files Modified

**`src/ui/handlers/analysis_handler.py`:**
1. Modified `SolverThread` class
   - Changed signal to emit `(result, config)` instead of just `result`
   - Removed `current_tab_index` parameter (not needed in thread)

2. Modified `_execute_analysis()` method
   - Removed all result handling code
   - Removed progress bar hide operation
   - Now returns result only (pure computation)

3. Modified `_on_solve_complete()` handler
   - Now receives both `result` and `config` parameters
   - Moved all result handling here (main thread)
   - Moved progress bar hide here
   - All Qt widget operations now safe

4. Modified `solve()` method
   - Updated signal connection to handle both parameters
   - Moved progress bar show to main thread
   - Simplified thread creation

## Testing Checklist

To verify the fix works:
- [ ] Batch mode analysis (von Mises, principal stresses)
- [ ] Time history mode (single node)
- [ ] Deformation calculations
- [ ] Velocity/acceleration calculations
- [ ] Plasticity corrections
- [ ] Progress bar updates during solve
- [ ] Console updates during solve
- [ ] Plot creation/updates after solve
- [ ] Error handling

## Expected Behavior After Fix

1. **Click Solve** → UI disables, "Running in background..." appears
2. **During Solve** → Progress bar updates, console shows progress
3. **After Solve** → Results appear, plots update, UI re-enables
4. **No Errors** → PlotlyMaxWidget updates correctly on main thread

## Why This Fix Works

✅ **Thread Safety:** Qt widgets only accessed from main thread  
✅ **Responsive GUI:** Heavy computation still in background  
✅ **Progress Updates:** Qt signals work across threads  
✅ **Proper Separation:** Computation vs UI clearly separated  
✅ **Error Handling:** Exceptions caught in both threads  

## Lessons Learned

When threading Qt applications:
1. **Never** access Qt widgets from background threads
2. **Always** use signals to communicate back to main thread
3. **Separate** computation (thread-safe) from UI (main-thread-only)
4. **Test** both success and error paths
5. **Document** which methods are thread-safe

## Related Documentation

- `SOLVE_BUTTON_THREADING.md` - Original threading implementation
- `THREADING_FIX_SUMMARY.md` - File loading threading
- Qt Documentation: [Thread-Support in Qt Modules](https://doc.qt.io/qt-5/threads-modules.html)

## Conclusion

This fix resolves the critical threading bug by ensuring all Qt widget operations happen on the main thread via signal/slot connections. The solver computation runs in the background (keeping GUI responsive), but all UI updates happen safely on the main thread.

**Status:** ✅ Fixed and ready for testing

