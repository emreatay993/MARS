# Performance Optimization Guide for MARS Solver

Based on profiling results from `solver_profile.stats`, this guide provides actionable optimization strategies.

## 📊 Current Performance Baseline

**Total Runtime:** 41.56 seconds  
**Function Calls:** 6.1 million  

### Top Bottlenecks (62% of total time)
1. `compute_principal_stresses` - **12.79s** (30.8%)
2. `torch.matmul` - **9.61s** (23.1%)
3. `process_results_in_batch` - **5.78s** (13.9%)
4. `compute_von_mises_stress` - **3.59s** (8.6%)
5. NumPy `reduce` operations - **2.84s** (6.8%)

---

## 🎯 Optimization Strategies (Prioritized by Impact)

### **Priority 1: GPU Acceleration for Principal Stress Calculation** ⚡
**Expected Speedup:** 5-10x (reduce from 12.79s to ~1.5-2.5s)

#### Current Issue
`compute_principal_stresses` uses Numba's CPU parallelization (`@njit(parallel=True)`) with nested loops. This is inefficient for large arrays.

#### Solution: Vectorize with NumPy/CuPy
Replace the nested loop approach with vectorized operations that can run on GPU.

**Implementation Options:**

**Option A: NumPy Vectorization (CPU, easier)**
```python
@staticmethod
def compute_principal_stresses_vectorized(sx, sy, sz, sxy, syz, sxz):
    """Fully vectorized principal stress calculation."""
    # Calculate invariants (vectorized - no loops!)
    I1 = sx + sy + sz
    I2 = (sx * sy + sy * sz + sz * sx - sxy**2 - syz**2 - sxz**2)
    I3 = (sx * sy * sz + 2 * sxy * syz * sxz 
          - sx * syz**2 - sy * sxz**2 - sz * sxy**2)
    
    # Depressed cubic coefficients
    p = I2 - I1**2 / 3.0
    q = (2.0 * I1**3) / 27.0 - (I1 * I2) / 3.0 + I3
    
    # Trigonometric solution (vectorized)
    minus_p_over_3 = -p / 3.0
    sqrt_m = np.sqrt(np.maximum(minus_p_over_3, 0))  # Ensure non-negative
    
    # Handle division by zero
    denom = 2.0 * sqrt_m**3
    cos_arg = np.where(denom != 0, q / denom, 0)
    cos_arg = np.clip(cos_arg, -1.0, 1.0)  # Ensure valid range for arccos
    
    theta = np.arccos(cos_arg) / 3.0
    two_pi_3 = 2.0943951023931953
    
    # Calculate all three principal stresses at once
    s1 = I1 / 3.0 + 2.0 * sqrt_m * np.cos(theta)
    s2 = I1 / 3.0 + 2.0 * sqrt_m * np.cos(theta + two_pi_3)
    s3 = I1 / 3.0 + 2.0 * sqrt_m * np.cos(theta - two_pi_3)
    
    return s1, s2, s3
```

**Option B: CuPy (GPU, maximum performance)**
```python
import cupy as cp

@staticmethod
def compute_principal_stresses_gpu(sx, sy, sz, sxy, syz, sxz):
    """GPU-accelerated principal stress calculation using CuPy."""
    # Convert to GPU arrays
    sx_gpu = cp.asarray(sx)
    sy_gpu = cp.asarray(sy)
    sz_gpu = cp.asarray(sz)
    sxy_gpu = cp.asarray(sxy)
    syz_gpu = cp.asarray(syz)
    sxz_gpu = cp.asarray(sxz)
    
    # Same vectorized logic as above, but runs on GPU
    I1 = sx_gpu + sy_gpu + sz_gpu
    I2 = (sx_gpu * sy_gpu + sy_gpu * sz_gpu + sz_gpu * sx_gpu 
          - sxy_gpu**2 - syz_gpu**2 - sxz_gpu**2)
    I3 = (sx_gpu * sy_gpu * sz_gpu + 2 * sxy_gpu * syz_gpu * sxz_gpu 
          - sx_gpu * syz_gpu**2 - sy_gpu * sxz_gpu**2 - sz_gpu * sxy_gpu**2)
    
    p = I2 - I1**2 / 3.0
    q = (2.0 * I1**3) / 27.0 - (I1 * I2) / 3.0 + I3
    
    minus_p_over_3 = -p / 3.0
    sqrt_m = cp.sqrt(cp.maximum(minus_p_over_3, 0))
    
    denom = 2.0 * sqrt_m**3
    cos_arg = cp.where(denom != 0, q / denom, 0)
    cos_arg = cp.clip(cos_arg, -1.0, 1.0)
    
    theta = cp.arccos(cos_arg) / 3.0
    two_pi_3 = 2.0943951023931953
    
    s1 = I1 / 3.0 + 2.0 * sqrt_m * cp.cos(theta)
    s2 = I1 / 3.0 + 2.0 * sqrt_m * cp.cos(theta + two_pi_3)
    s3 = I1 / 3.0 + 2.0 * sqrt_m * cp.cos(theta - two_pi_3)
    
    # Transfer back to CPU
    return s1.get(), s2.get(), s3.get()
```

**Installation:**
```bash
pip install cupy-cuda12x  # Replace with your CUDA version
```

---

### **Priority 2: Keep Data on GPU Longer** 🔄
**Expected Speedup:** 2-3x for torch.matmul operations

#### Current Issue
In `compute_normal_stresses`, you compute on GPU with PyTorch, then immediately transfer to CPU:
```python
return actual_sx.cpu().numpy(), actual_sy.cpu().numpy(), ...
```

This causes:
1. **GPU → CPU transfer overhead** (slow)
2. **Subsequent CPU computations** instead of GPU

#### Solution: GPU-Native Pipeline
Keep tensors on GPU through the entire stress calculation pipeline.

**Modified `compute_normal_stresses`:**
```python
def compute_normal_stresses(self, start_idx, end_idx):
    """Compute actual stresses - keep on GPU."""
    actual_sx = torch.matmul(self.modal_sx[start_idx:end_idx, :], self.modal_coord)
    actual_sy = torch.matmul(self.modal_sy[start_idx:end_idx, :], self.modal_coord)
    actual_sz = torch.matmul(self.modal_sz[start_idx:end_idx, :], self.modal_coord)
    actual_sxy = torch.matmul(self.modal_sxy[start_idx:end_idx, :], self.modal_coord)
    actual_syz = torch.matmul(self.modal_syz[start_idx:end_idx, :], self.modal_coord)
    actual_sxz = torch.matmul(self.modal_sxz[start_idx:end_idx, :], self.modal_coord)

    if self.is_steady_state_included:
        actual_sx += self.steady_sx[start_idx:end_idx].unsqueeze(1)
        actual_sy += self.steady_sy[start_idx:end_idx].unsqueeze(1)
        actual_sz += self.steady_sz[start_idx:end_idx].unsqueeze(1)
        actual_sxy += self.steady_sxy[start_idx:end_idx].unsqueeze(1)
        actual_syz += self.steady_syz[start_idx:end_idx].unsqueeze(1)
        actual_sxz += self.steady_sxz[start_idx:end_idx].unsqueeze(1)

    # Return GPU tensors, not CPU numpy arrays
    return actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz
```

**Modified stress calculations (PyTorch versions):**
```python
@staticmethod
def compute_von_mises_stress_torch(sx, sy, sz, sxy, syz, sxz):
    """GPU-accelerated von Mises stress using PyTorch."""
    sigma_vm = torch.sqrt(
        0.5 * ((sx - sy)**2 + (sy - sz)**2 + (sz - sx)**2) +
        3 * (sxy**2 + syz**2 + sxz**2)
    )
    return sigma_vm

@staticmethod
def compute_principal_stresses_torch(sx, sy, sz, sxy, syz, sxz):
    """GPU-accelerated principal stresses using PyTorch."""
    # Same vectorized logic as NumPy version, but with torch operations
    I1 = sx + sy + sz
    I2 = (sx * sy + sy * sz + sz * sx - sxy**2 - syz**2 - sxz**2)
    I3 = (sx * sy * sz + 2 * sxy * syz * sxz 
          - sx * syz**2 - sy * sxz**2 - sz * sxy**2)
    
    p = I2 - I1**2 / 3.0
    q = (2.0 * I1**3) / 27.0 - (I1 * I2) / 3.0 + I3
    
    minus_p_over_3 = -p / 3.0
    sqrt_m = torch.sqrt(torch.clamp(minus_p_over_3, min=0))
    
    denom = 2.0 * sqrt_m**3
    cos_arg = torch.where(denom != 0, q / denom, torch.zeros_like(q))
    cos_arg = torch.clamp(cos_arg, -1.0, 1.0)
    
    theta = torch.acos(cos_arg) / 3.0
    two_pi_3 = 2.0943951023931953
    
    s1 = I1 / 3.0 + 2.0 * sqrt_m * torch.cos(theta)
    s2 = I1 / 3.0 + 2.0 * sqrt_m * torch.cos(theta + two_pi_3)
    s3 = I1 / 3.0 + 2.0 * sqrt_m * torch.cos(theta - two_pi_3)
    
    return s1, s2, s3
```

**Only transfer to CPU when writing to memmap:**
```python
job['max_memmap'][start_idx:end_idx] = torch.max(sigma_vm, dim=1)[0].cpu().numpy()
```

---

### **Priority 3: Fused Operations** 🔗
**Expected Speedup:** 1.5-2x

#### Current Issue
Separate function calls for von Mises and principal stresses recalculate invariants.

#### Solution: Compute Both Simultaneously
```python
@staticmethod
def compute_all_stress_metrics_torch(sx, sy, sz, sxy, syz, sxz):
    """Compute von Mises AND principal stresses in one pass."""
    # Calculate invariants once
    I1 = sx + sy + sz
    I2 = (sx * sy + sy * sz + sz * sx - sxy**2 - syz**2 - sxz**2)
    I3 = (sx * sy * sz + 2 * sxy * syz * sxz 
          - sx * syz**2 - sy * sxz**2 - sz * sxy**2)
    
    # Von Mises (uses same stress components)
    sigma_vm = torch.sqrt(
        0.5 * ((sx - sy)**2 + (sy - sz)**2 + (sz - sx)**2) +
        3 * (sxy**2 + syz**2 + sxz**2)
    )
    
    # Principal stresses (uses invariants)
    p = I2 - I1**2 / 3.0
    q = (2.0 * I1**3) / 27.0 - (I1 * I2) / 3.0 + I3
    
    minus_p_over_3 = -p / 3.0
    sqrt_m = torch.sqrt(torch.clamp(minus_p_over_3, min=0))
    
    denom = 2.0 * sqrt_m**3
    cos_arg = torch.where(denom != 0, q / denom, torch.zeros_like(q))
    cos_arg = torch.clamp(cos_arg, -1.0, 1.0)
    
    theta = torch.acos(cos_arg) / 3.0
    two_pi_3 = 2.0943951023931953
    
    s1 = I1 / 3.0 + 2.0 * sqrt_m * torch.cos(theta)
    s2 = I1 / 3.0 + 2.0 * sqrt_m * torch.cos(theta + two_pi_3)
    s3 = I1 / 3.0 + 2.0 * sqrt_m * torch.cos(theta - two_pi_3)
    
    return sigma_vm, s1, s2, s3
```

**Modified `_process_stress_chunk`:**
```python
def _process_stress_chunk(self, jobs, time_values, start_idx, end_idx, 
                          actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz):
    """Process all stress metrics in one fused operation."""
    
    # Compute everything at once
    sigma_vm, s1, s2, s3 = self.compute_all_stress_metrics_torch(
        actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz
    )
    
    # Now just extract what's needed for each job
    if 'von_mises' in jobs:
        job = jobs['von_mises']
        job['max_memmap'][start_idx:end_idx] = torch.max(sigma_vm, dim=1)[0].cpu().numpy()
        job['time_memmap'][start_idx:end_idx] = time_values[torch.argmax(sigma_vm, dim=1).cpu().numpy()]
    
    if 's1_max' in jobs:
        job = jobs['s1_max']
        job['max_memmap'][start_idx:end_idx] = torch.max(s1, dim=1)[0].cpu().numpy()
        job['time_memmap'][start_idx:end_idx] = time_values[torch.argmax(s1, dim=1).cpu().numpy()]
    
    if 's3_min' in jobs:
        job = jobs['s3_min']
        job['min_memmap'][start_idx:end_idx] = torch.min(s3, dim=1)[0].cpu().numpy()
        job['time_memmap'][start_idx:end_idx] = time_values[torch.argmin(s3, dim=1).cpu().numpy()]
```

---

### **Priority 4: Reduce NumPy Reduce Operations** 📉
**Expected Speedup:** 1.3-1.5x

#### Current Issue
`np.max`, `np.argmax` are called separately and repeatedly.

#### Solution: Use `torch.max` with `return_indices=True`
```python
# Instead of:
max_vals = np.max(sigma_vm, axis=1)
max_indices = np.argmax(sigma_vm, axis=1)

# Use:
max_vals, max_indices = torch.max(sigma_vm, dim=1)
# Transfer to CPU only once
max_vals_cpu = max_vals.cpu().numpy()
max_indices_cpu = max_indices.cpu().numpy()
```

---

### **Priority 5: Optimize Batch Processing** 🔧
**Expected Speedup:** 1.2-1.5x

#### Current Issues
1. Garbage collection takes 0.3s per iteration (5 iterations = 1.5s total)
2. Memory checking overhead
3. Progress signal overhead

#### Solutions

**A. Reduce GC frequency:**
```python
# Only run GC every N iterations, not every iteration
if (i + 1) % 3 == 0:  # Every 3 iterations instead of every iteration
    gc.collect()
```

**B. Batch progress updates:**
```python
# Update progress less frequently
if (i + 1) % max(1, num_iterations // 20) == 0:  # Only 20 updates total
    progress_percentage = ((i + 1) / num_iterations) * 100
    self.progress_signal.emit(int(progress_percentage))
    QApplication.processEvents()
```

**C. Remove redundant memory checks:**
```python
# Only check memory at start and end, not every iteration
if i == 0 or i == num_iterations - 1:
    current_available_memory = psutil.virtual_memory().available
    print(f"Available RAM: {current_available_memory / (1024 ** 3):.2f} GB")
```

---

## 📋 Implementation Checklist

### Phase 1: Quick Wins (1-2 hours)
- [ ] Replace nested loops in `compute_principal_stresses` with vectorized NumPy
- [ ] Implement fused stress calculation function
- [ ] Reduce GC and progress update frequency
- [ ] Use `torch.max` with indices instead of separate calls

**Expected Total Speedup:** 3-5x (41s → 8-14s)

### Phase 2: GPU Optimization (2-4 hours)
- [ ] Keep PyTorch tensors on GPU through pipeline
- [ ] Convert von Mises to PyTorch
- [ ] Convert principal stresses to PyTorch
- [ ] Only transfer to CPU for memmap writes

**Expected Total Speedup:** 8-12x (41s → 3-5s)

### Phase 3: Advanced (Optional, 4-8 hours)
- [ ] Install and test CuPy
- [ ] Implement CuPy versions of stress calculations
- [ ] Profile and compare PyTorch vs CuPy performance
- [ ] Implement mixed precision (float16) for non-critical calculations

**Expected Total Speedup:** 15-20x (41s → 2-3s)

---

## 🧪 Testing Strategy

1. **Create benchmark script:**
```python
# tests/performance/benchmark_optimizations.py
import time
from tests.performance.profile_solver import run_profiling

def benchmark():
    times = []
    for i in range(3):  # Run 3 times
        start = time.time()
        run_profiling()
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"Run {i+1}: {elapsed:.2f}s")
    
    print(f"Average: {sum(times)/len(times):.2f}s")
    print(f"Best: {min(times):.2f}s")

if __name__ == "__main__":
    benchmark()
```

2. **Compare before/after:**
   - Baseline: 41.56s
   - After each phase, run benchmark
   - Document speedup in this file

---

## 🎓 Key Principles

1. **Vectorization > Parallelization** - NumPy/PyTorch vectorized ops beat Numba parallel loops
2. **GPU > CPU** - For large arrays, GPU is 5-10x faster
3. **Minimize Transfers** - GPU↔CPU transfers are expensive
4. **Fuse Operations** - Compute multiple things in one pass when they share data
5. **Profile After Each Change** - Verify your optimizations actually help

---

## 📚 Additional Resources

- [PyTorch Performance Tuning](https://pytorch.org/tutorials/recipes/recipes/tuning_guide.html)
- [CuPy User Guide](https://docs.cupy.dev/en/stable/user_guide/index.html)
- [NumPy Performance Tips](https://numpy.org/doc/stable/user/performance.html)
- [Numba vs Vectorization](https://numba.pydata.org/numba-doc/latest/user/performance-tips.html)

---

## 📊 Expected Final Performance

| Metric | Baseline | Phase 1 | Phase 2 | Phase 3 |
|--------|----------|---------|---------|---------|
| **Total Time** | 41.56s | ~10s | ~4s | ~2.5s |
| **Speedup** | 1x | 4x | 10x | 16x |
| **Principal Stress** | 12.79s | ~3s | ~1s | ~0.8s |
| **Von Mises** | 3.59s | ~1s | ~0.3s | ~0.2s |
| **MatMul** | 9.61s | 9.61s | ~1s | ~0.8s |

**Target:** Under 5 seconds for full analysis (10x improvement)
