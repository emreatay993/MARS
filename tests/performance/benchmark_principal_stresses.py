
import time
import math
import numpy as np
import torch
from numba import njit, prange
import pandas as pd

# ---- Constants ----
NP_DTYPE = np.float64
TORCH_DTYPE = torch.float64

# ---- Numba Implementation (Reference) ----
@njit(parallel=True)
def compute_principal_stresses_numba(actual_sx, actual_sy, actual_sz, actual_sxy, actual_syz, actual_sxz):
    """
    Calculates the three principal stresses from the six components of stress using Numba.
    Reference implementation from src/solver/engine.py.
    """
    num_nodes, num_time_points = actual_sx.shape

    s1_out = np.zeros((num_nodes, num_time_points), dtype=NP_DTYPE)
    s2_out = np.zeros_like(s1_out)
    s3_out = np.zeros_like(s1_out)

    two_pi_3 = 2.0943951023931953
    tiny_p = 1.0e-12

    for i in prange(num_nodes):
        for j in range(num_time_points):
            s_x = actual_sx[i, j]
            s_y = actual_sy[i, j]
            s_z = actual_sz[i, j]
            s_xy = actual_sxy[i, j]
            s_yz = actual_syz[i, j]
            s_xz = actual_sxz[i, j]

            I1 = s_x + s_y + s_z
            I2 = (s_x * s_y + s_y * s_z + s_z * s_x
                  - s_xy ** 2 - s_yz ** 2 - s_xz ** 2)
            I3 = (s_x * s_y * s_z
                  + 2 * s_xy * s_yz * s_xz
                  - s_x * s_yz ** 2
                  - s_y * s_xz ** 2
                  - s_z * s_xy ** 2)

            p = I2 - I1 ** 2 / 3.0
            q = (2.0 * I1 ** 3) / 27.0 - (I1 * I2) / 3.0 + I3

            if abs(p) < tiny_p and abs(q) < tiny_p:
                s_hydro = I1 / 3.0
                s1_out[i, j] = s_hydro
                s2_out[i, j] = s_hydro
                s3_out[i, j] = s_hydro
                continue

            minus_p_over_3 = -p / 3.0
            sqrt_m = math.sqrt(minus_p_over_3)
            cos_arg = q / (2.0 * sqrt_m ** 3)

            if cos_arg > 1.0:
                cos_arg = 1.0
            elif cos_arg < -1.0:
                cos_arg = -1.0

            phi = math.acos(cos_arg) / 3.0
            amp = 2.0 * sqrt_m

            s1 = I1 / 3.0 + amp * math.cos(phi)
            s2 = I1 / 3.0 + amp * math.cos(phi - two_pi_3)
            s3 = I1 / 3.0 + amp * math.cos(phi + two_pi_3)

            if s1 < s2:
                s1, s2 = s2, s1
            if s2 < s3:
                s2, s3 = s3, s2
            if s1 < s2:
                s1, s2 = s2, s1

            s1_out[i, j] = s1
            s2_out[i, j] = s2
            s3_out[i, j] = s3

    return s1_out, s2_out, s3_out

# ---- PyTorch Implementation (Eigvalsh) ----
def compute_principal_stresses_torch_eig(sx, sy, sz, sxy, syz, sxz):
    """
    Computes principal stresses using torch.linalg.eigvalsh.
    Constructs a batch of symmetric matrices (N, T, 3, 3).
    """
    # Stack components to form (N, T, 3, 3) matrices
    # [[sx, sxy, sxz],
    #  [sxy, sy, syz],
    #  [sxz, syz, sz]]
    
    # Shape: (N, T) -> (N, T, 1)
    zeros = torch.zeros_like(sx)
    
    # We can construct the matrix efficiently
    # Row 0: sx, sxy, sxz
    # Row 1: sxy, sy, syz
    # Row 2: sxz, syz, sz
    
    # It's faster to stack last dimension
    row1 = torch.stack([sx, sxy, sxz], dim=-1)
    row2 = torch.stack([sxy, sy, syz], dim=-1)
    row3 = torch.stack([sxz, syz, sz], dim=-1)
    
    stress_matrices = torch.stack([row1, row2, row3], dim=-2) # (N, T, 3, 3)
    
    # Compute eigenvalues (returned in ascending order)
    eigenvalues = torch.linalg.eigvalsh(stress_matrices)
    
    # Sort descending (s1 >= s2 >= s3)
    # eigvalsh returns ascending, so flip
    s3 = eigenvalues[..., 0]
    s2 = eigenvalues[..., 1]
    s1 = eigenvalues[..., 2]
    
    return s1, s2, s3

# ---- PyTorch Implementation (Cardano / Analytical) ----
def compute_principal_stresses_torch_cardano(sx, sy, sz, sxy, syz, sxz):
    """
    Computes principal stresses using the analytical Cardano method with PyTorch operations.
    Fully vectorized.
    """
    two_pi_3 = 2.0943951023931953
    tiny_p = 1.0e-12

    I1 = sx + sy + sz
    I2 = (sx * sy + sy * sz + sz * sx - sxy**2 - syz**2 - sxz**2)
    I3 = (sx * sy * sz + 2 * sxy * syz * sxz - sx * syz**2 - sy * sxz**2 - sz * sxy**2)

    p = I2 - I1**2 / 3.0
    q = (2.0 * I1**3) / 27.0 - (I1 * I2) / 3.0 + I3

    # Mask for hydrostatic case
    # We use a mask to avoid division by zero or sqrt of negative numbers in the general case
    # although mathematically p should be <= 0 for symmetric matrices.
    
    # p is usually negative or zero. 
    # minus_p_over_3 = -p / 3.0. 
    # If p is positive (due to numerical noise), we clamp it to 0.
    
    minus_p_over_3 = -p / 3.0
    # Ensure non-negative for sqrt
    minus_p_over_3 = torch.clamp(minus_p_over_3, min=0.0)
    
    sqrt_m = torch.sqrt(minus_p_over_3)
    
    # Avoid division by zero
    # If sqrt_m is very small, it means p is very small -> hydrostatic or close to it.
    # We can add a tiny epsilon to denominator or handle via mask.
    # Let's use a safe denominator.
    safe_sqrt_m = torch.where(sqrt_m < 1e-15, torch.ones_like(sqrt_m), sqrt_m)
    
    cos_arg = q / (2.0 * safe_sqrt_m**3)
    
    # Clamp cos_arg to [-1, 1]
    cos_arg = torch.clamp(cos_arg, min=-1.0, max=1.0)
    
    phi = torch.acos(cos_arg) / 3.0
    amp = 2.0 * sqrt_m
    
    s1_raw = I1 / 3.0 + amp * torch.cos(phi)
    s2_raw = I1 / 3.0 + amp * torch.cos(phi - two_pi_3)
    s3_raw = I1 / 3.0 + amp * torch.cos(phi + two_pi_3)
    
    # Sort results
    # Manual sorting network for 3 elements (descending)
    # 1. Compare s1, s2
    mx = torch.maximum(s1_raw, s2_raw)
    mn = torch.minimum(s1_raw, s2_raw)
    s1_raw = mx
    s2_raw = mn
    
    # 2. Compare s2, s3
    mx = torch.maximum(s2_raw, s3_raw)
    mn = torch.minimum(s2_raw, s3_raw)
    s2_raw = mx
    s3_raw = mn
    
    # 3. Compare s1, s2
    mx = torch.maximum(s1_raw, s2_raw)
    mn = torch.minimum(s1_raw, s2_raw)
    s1_raw = mx
    s2_raw = mn
    
    return s1_raw, s2_raw, s3_raw

def run_benchmark():
    print("--- Principal Stress Calculation Benchmark ---")
    
    # Settings
    num_nodes = 300
    num_time_points = 50000
    
    print(f"Dataset Size: {num_nodes} Nodes x {num_time_points} Time Points")
    print(f"Total Elements per Component: {num_nodes * num_time_points:,}")
    
    # Check CUDA
    if not torch.cuda.is_available():
        print("Error: CUDA not available. Cannot benchmark GPU performance.")
        return
    
    device = torch.device("cuda")
    print(f"GPU: {torch.cuda.get_device_name(device)}")
    
    # Generate Data
    print("Generating random data...")
    # Use float64 for fair comparison
    sx_np = np.random.rand(num_nodes, num_time_points).astype(NP_DTYPE) * 100
    sy_np = np.random.rand(num_nodes, num_time_points).astype(NP_DTYPE) * 100
    sz_np = np.random.rand(num_nodes, num_time_points).astype(NP_DTYPE) * 100
    sxy_np = np.random.rand(num_nodes, num_time_points).astype(NP_DTYPE) * 50
    syz_np = np.random.rand(num_nodes, num_time_points).astype(NP_DTYPE) * 50
    sxz_np = np.random.rand(num_nodes, num_time_points).astype(NP_DTYPE) * 50
    
    # Move to GPU
    sx_torch = torch.tensor(sx_np, device=device, dtype=TORCH_DTYPE)
    sy_torch = torch.tensor(sy_np, device=device, dtype=TORCH_DTYPE)
    sz_torch = torch.tensor(sz_np, device=device, dtype=TORCH_DTYPE)
    sxy_torch = torch.tensor(sxy_np, device=device, dtype=TORCH_DTYPE)
    syz_torch = torch.tensor(syz_np, device=device, dtype=TORCH_DTYPE)
    sxz_torch = torch.tensor(sxz_np, device=device, dtype=TORCH_DTYPE)
    
    # ---- Correctness Check ----
    print("\n--- Verifying Correctness ---")
    
    # Numba (Reference)
    print("Running Numba (Reference)...")
    s1_ref, s2_ref, s3_ref = compute_principal_stresses_numba(sx_np, sy_np, sz_np, sxy_np, syz_np, sxz_np)
    
    # Torch Eigvalsh
    print("Running Torch Eigvalsh...")
    try:
        s1_eig, s2_eig, s3_eig = compute_principal_stresses_torch_eig(sx_torch, sy_torch, sz_torch, sxy_torch, syz_torch, sxz_torch)
        eig_success = True
    except Exception as e:
        print(f"Torch Eigvalsh failed: {e}")
        eig_success = False
        s1_eig = None

    # Torch Cardano
    print("Running Torch Cardano...")
    try:
        s1_car, s2_car, s3_car = compute_principal_stresses_torch_cardano(sx_torch, sy_torch, sz_torch, sxy_torch, syz_torch, sxz_torch)
        car_success = True
    except Exception as e:
        print(f"Torch Cardano failed: {e}")
        car_success = False
        s1_car = None
    
    # Compare
    # Move torch results to CPU
    tol = 1e-5
    
    if eig_success:
        s1_eig_np = s1_eig.cpu().numpy()
        diff_eig = np.abs(s1_ref - s1_eig_np)
        max_diff_eig = np.max(diff_eig)
        match_eig = np.allclose(s1_ref, s1_eig_np, atol=tol)
        print(f"Torch Eigvalsh vs Numba (S1): Max Diff = {max_diff_eig:.2e}, Match = {match_eig}")
    else:
        print("Skipping Eigvalsh comparison due to failure.")
    
    if car_success:
        s1_car_np = s1_car.cpu().numpy()
        diff_car = np.abs(s1_ref - s1_car_np)
        max_diff_car = np.max(diff_car)
        match_car = np.allclose(s1_ref, s1_car_np, atol=tol)
        print(f"Torch Cardano vs Numba (S1): Max Diff = {max_diff_car:.2e}, Match = {match_car}")
    
    # ---- Performance Benchmark ----
    print("\n--- Running Performance Benchmark ---")
    n_runs = 5
    
    # 1. Numba
    print("Benchmarking Numba...")
    start_time = time.time()
    for _ in range(n_runs):
        _ = compute_principal_stresses_numba(sx_np, sy_np, sz_np, sxy_np, syz_np, sxz_np)
    numba_time = (time.time() - start_time) / n_runs
    print(f"Numba (CPU): {numba_time:.4f} s")
    
    # 2. Torch Eigvalsh
    if eig_success:
        print("Benchmarking Torch Eigvalsh...")
        # Warmup
        for _ in range(2):
            _ = compute_principal_stresses_torch_eig(sx_torch, sy_torch, sz_torch, sxy_torch, syz_torch, sxz_torch)
        torch.cuda.synchronize()
        
        start_time = time.time()
        for _ in range(n_runs):
            _ = compute_principal_stresses_torch_eig(sx_torch, sy_torch, sz_torch, sxy_torch, syz_torch, sxz_torch)
        torch.cuda.synchronize()
        eig_time = (time.time() - start_time) / n_runs
        print(f"Torch Eigvalsh (GPU): {eig_time:.4f} s (Speedup: {numba_time/eig_time:.2f}x)")
    else:
        print("Skipping Torch Eigvalsh benchmark.")
    
    # 3. Torch Cardano
    if car_success:
        print("Benchmarking Torch Cardano...")
        # Warmup
        for _ in range(2):
            _ = compute_principal_stresses_torch_cardano(sx_torch, sy_torch, sz_torch, sxy_torch, syz_torch, sxz_torch)
        torch.cuda.synchronize()
        
        start_time = time.time()
        for _ in range(n_runs):
            _ = compute_principal_stresses_torch_cardano(sx_torch, sy_torch, sz_torch, sxy_torch, syz_torch, sxz_torch)
        torch.cuda.synchronize()
        car_time = (time.time() - start_time) / n_runs
        print(f"Torch Cardano (GPU): {car_time:.4f} s (Speedup: {numba_time/car_time:.2f}x)")

    # ---- Full Pipeline Comparison (Data Transfer + Compute) ----
    print("\n--- Full Pipeline Comparison (Transfer + Compute) ---")
    
    # Increase dataset size for this test if possible, or use existing
    # 300 * 50000 * 6 * 8 bytes = ~720 MB. 
    # Let's try to simulate a larger batch by looping or just measuring this batch accurately.
    # The user asked for "larger scale data". 
    # Let's try to allocate a larger tensor for this specific test if VRAM allows.
    
    try:
        large_nodes = 300
        print(f"Allocating larger dataset: {large_nodes} Nodes x {num_time_points} Time Points (~0.7 GB raw data)...")
        
        # We only need the GPU tensors for the "Proposed" and "Current" (source)
        # We need CPU arrays for "Current" (destination)
        
        # Generate on GPU directly to save time/memory
        sx_large = torch.rand((large_nodes, num_time_points), device=device, dtype=TORCH_DTYPE) * 100
        sy_large = torch.rand((large_nodes, num_time_points), device=device, dtype=TORCH_DTYPE) * 100
        sz_large = torch.rand((large_nodes, num_time_points), device=device, dtype=TORCH_DTYPE) * 100
        sxy_large = torch.rand((large_nodes, num_time_points), device=device, dtype=TORCH_DTYPE) * 50
        syz_large = torch.rand((large_nodes, num_time_points), device=device, dtype=TORCH_DTYPE) * 50
        sxz_large = torch.rand((large_nodes, num_time_points), device=device, dtype=TORCH_DTYPE) * 50
        
        torch.cuda.synchronize()
        mem_alloc = torch.cuda.memory_allocated() / (1024**3)
        print(f"Allocation successful. GPU Memory Allocated: {mem_alloc:.2f} GB")
        
        # --- Scenario A: Current (GPU -> CPU Transfer -> CPU Compute) ---
        print("\nScenario A: Current (Transfer Raw -> CPU Compute)")
        
        start_time = time.time()
        
        # 1. Transfer Raw Data (GPU to CPU)
        t0 = time.time()
        sx_cpu = sx_large.cpu().numpy()
        sy_cpu = sy_large.cpu().numpy()
        sz_cpu = sz_large.cpu().numpy()
        sxy_cpu = sxy_large.cpu().numpy()
        syz_cpu = syz_large.cpu().numpy()
        sxz_cpu = sxz_large.cpu().numpy()
        t_transfer_raw = time.time() - t0
        
        # 2. CPU Compute
        t0 = time.time()
        s1_cpu, _, _ = compute_principal_stresses_numba(sx_cpu, sy_cpu, sz_cpu, sxy_cpu, syz_cpu, sxz_cpu)
        t_compute_cpu = time.time() - t0
        
        total_time_current = time.time() - start_time
        print(f"  Transfer Raw: {t_transfer_raw:.4f} s")
        print(f"  CPU Compute:  {t_compute_cpu:.4f} s")
        print(f"  Total Time:   {total_time_current:.4f} s")
        
        # Clean up CPU memory
        del sx_cpu, sy_cpu, sz_cpu, sxy_cpu, syz_cpu, sxz_cpu, s1_cpu
        
        # --- Scenario B: Proposed (GPU Compute -> Transfer Result) ---
        print("\nScenario B: Proposed (GPU Compute -> Transfer Result)")
        
        if car_success:
            start_time = time.time()
            
            # 1. GPU Compute
            t0 = time.time()
            s1_gpu, _, _ = compute_principal_stresses_torch_cardano(sx_large, sy_large, sz_large, sxy_large, syz_large, sxz_large)
            torch.cuda.synchronize()
            t_compute_gpu = time.time() - t0
            
            # 2. Transfer Result (GPU to CPU)
            # Usually we transfer the MAX over time, or the full history depending on what we need.
            # The current code calculates max/min and time of max/min.
            # Let's assume we transfer the full history for a fair comparison with Scenario A's output,
            # OR we can simulate the actual use case which is reducing to max/min.
            # The user wants to improve "solver performance". The solver usually writes full history to memmap 
            # OR reduces it. 
            # Looking at engine.py: 
            #   self.max_over_time_s1 = ...
            #   job['max_memmap'][start_idx:end_idx] = np.max(s1, axis=1)
            # So it DOES reduce to max before writing (mostly). 
            # BUT it also writes to memmap.
            # If we keep full history on GPU, we can do the reduction on GPU too.
            
            # Let's measure transferring the FULL result first (worst case for GPU pipeline)
            t0 = time.time()
            s1_gpu_cpu = s1_gpu.cpu().numpy()
            t_transfer_result = time.time() - t0
            
            total_time_proposed_full = time.time() - start_time
            print(f"  GPU Compute:      {t_compute_gpu:.4f} s")
            print(f"  Transfer Result:  {t_transfer_result:.4f} s")
            print(f"  Total Time (Full):{total_time_proposed_full:.4f} s")
            print(f"  Speedup (Full):   {total_time_current / total_time_proposed_full:.2f}x")
            
            # --- Scenario C: Proposed Optimized (GPU Compute -> Reduce -> Transfer Max) ---
            print("\nScenario C: Proposed Optimized (GPU Compute -> Reduce -> Transfer Max)")
            
            start_time = time.time()
            
            # 1. GPU Compute
            t0 = time.time()
            s1_gpu, _, _ = compute_principal_stresses_torch_cardano(sx_large, sy_large, sz_large, sxy_large, syz_large, sxz_large)
            
            # 2. GPU Reduce
            s1_max_gpu, _ = torch.max(s1_gpu, dim=1)
            torch.cuda.synchronize()
            t_compute_reduce = time.time() - t0
            
            # 3. Transfer Reduced (GPU to CPU)
            t0 = time.time()
            s1_max_cpu = s1_max_gpu.cpu().numpy()
            t_transfer_reduced = time.time() - t0
            
            total_time_proposed_opt = time.time() - start_time
            print(f"  GPU Compute+Reduce: {t_compute_reduce:.4f} s")
            print(f"  Transfer Reduced:   {t_transfer_reduced:.4f} s")
            print(f"  Total Time (Opt):   {total_time_proposed_opt:.4f} s")
            print(f"  Speedup (Opt):      {total_time_current / total_time_proposed_opt:.2f}x")
            
        else:
            print("Skipping Scenario B/C due to Cardano failure.")

    except torch.cuda.OutOfMemoryError:
        print("Error: GPU Out of Memory. Try reducing the node count.")
    except Exception as e:
        print(f"An error occurred during full pipeline test: {e}")

if __name__ == "__main__":
    run_benchmark()
