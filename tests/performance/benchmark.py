"""
Benchmark Script for Solver Optimizations
==========================================

This script helps you measure the performance impact of optimizations.

Usage:
    python tests/performance/benchmark.py [--runs 3] [--profile]

Options:
    --runs N       Number of benchmark runs (default: 3)
    --profile      Generate profiling stats file
"""

import sys
import time
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.performance.profile_solver import run_profiling


def benchmark(num_runs=3, enable_profiling=False):
    """Run benchmark multiple times and report statistics."""
    
    print("=" * 80)
    print("MARS SOLVER PERFORMANCE BENCHMARK")
    print("=" * 80)
    print(f"Number of runs: {num_runs}")
    print(f"Profiling enabled: {enable_profiling}")
    print("=" * 80)
    
    times = []
    
    for i in range(num_runs):
        print(f"\n{'=' * 80}")
        print(f"RUN {i + 1}/{num_runs}")
        print(f"{'=' * 80}")
        
        start = time.time()
        
        if enable_profiling and i == 0:  # Only profile first run
            run_profiling()
        else:
            # Import and run without profiling for faster benchmarks
            from src.solver.computation import run_batch_analysis
            from tests.performance.input_generator import InputGenerator
            
            # Generate test data
            generator = InputGenerator(
                num_nodes=10000,
                num_modes=50,
                num_time_points=100
            )
            
            modal_sx, modal_sy, modal_sz, modal_sxy, modal_syz, modal_sxz = generator.generate_modal_stresses()
            modal_coord = generator.generate_modal_coordinates()
            df_node_ids, node_coords = generator.generate_node_data()
            time_values = generator.generate_time_values()
            
            # Run analysis
            run_batch_analysis(
                modal_sx=modal_sx,
                modal_sy=modal_sy,
                modal_sz=modal_sz,
                modal_sxy=modal_sxy,
                modal_syz=modal_syz,
                modal_sxz=modal_sxz,
                modal_coord=modal_coord,
                time_values=time_values,
                df_node_ids=df_node_ids,
                node_coords=node_coords,
                calculate_von_mises=True,
                calculate_max_principal_stress=True,
                calculate_min_principal_stress=True,
                calculate_damage=False,
                calculate_deformation=False,
                calculate_velocity=False,
                calculate_acceleration=False
            )
        
        elapsed = time.time() - start
        times.append(elapsed)
        
        print(f"\n{'=' * 80}")
        print(f"Run {i + 1} completed in {elapsed:.2f} seconds")
        print(f"{'=' * 80}")
    
    # Calculate statistics
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    if len(times) > 1:
        variance = sum((t - avg_time) ** 2 for t in times) / (len(times) - 1)
        std_dev = variance ** 0.5
    else:
        std_dev = 0
    
    # Print summary
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS")
    print("=" * 80)
    print(f"Average time:  {avg_time:.2f} seconds")
    print(f"Best time:     {min_time:.2f} seconds")
    print(f"Worst time:    {max_time:.2f} seconds")
    print(f"Std deviation: {std_dev:.2f} seconds")
    print("=" * 80)
    
    # Individual run times
    print("\nIndividual runs:")
    for i, t in enumerate(times, 1):
        deviation = ((t - avg_time) / avg_time) * 100
        print(f"  Run {i}: {t:.2f}s ({deviation:+.1f}% from average)")
    
    # Performance rating
    print("\n" + "=" * 80)
    print("PERFORMANCE RATING")
    print("=" * 80)
    
    if avg_time < 5:
        rating = "⭐⭐⭐⭐⭐ EXCELLENT"
        comment = "Phase 2+ optimizations achieved!"
    elif avg_time < 10:
        rating = "⭐⭐⭐⭐ VERY GOOD"
        comment = "Phase 1 optimizations working well!"
    elif avg_time < 20:
        rating = "⭐⭐⭐ GOOD"
        comment = "Some optimizations applied, more gains possible."
    elif avg_time < 35:
        rating = "⭐⭐ FAIR"
        comment = "Partial optimizations, significant room for improvement."
    else:
        rating = "⭐ NEEDS OPTIMIZATION"
        comment = "Baseline performance, apply Phase 1 optimizations."
    
    print(f"{rating}")
    print(f"{comment}")
    print("=" * 80)
    
    # Comparison to baseline
    baseline_time = 41.56  # From original profiling
    speedup = baseline_time / avg_time
    improvement = ((baseline_time - avg_time) / baseline_time) * 100
    
    print("\n" + "=" * 80)
    print("COMPARISON TO BASELINE")
    print("=" * 80)
    print(f"Baseline time:     {baseline_time:.2f}s")
    print(f"Current time:      {avg_time:.2f}s")
    print(f"Speedup:           {speedup:.2f}x")
    print(f"Improvement:       {improvement:.1f}%")
    print(f"Time saved:        {baseline_time - avg_time:.2f}s")
    print("=" * 80)
    
    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if avg_time > 35:
        print("✓ Apply Phase 1 optimizations (vectorization)")
        print("  Expected result: ~10s (4x speedup)")
        print("  See: tests/performance/optimizations_phase1.py")
    elif avg_time > 10:
        print("✓ Phase 1 optimizations complete or partial")
        print("✓ Apply Phase 2 optimizations (GPU pipeline)")
        print("  Expected result: ~4s (10x speedup)")
        print("  See: tests/performance/OPTIMIZATION_GUIDE.md (Priority 2)")
    elif avg_time > 5:
        print("✓ Phase 1 & 2 optimizations complete")
        print("✓ Consider Phase 3 optimizations (CuPy, mixed precision)")
        print("  Expected result: ~2.5s (16x speedup)")
        print("  See: tests/performance/OPTIMIZATION_GUIDE.md (Priority 3)")
    else:
        print("✓ Excellent performance achieved!")
        print("✓ Focus on other bottlenecks or features")
        print("✓ Consider profiling other parts of the application")
    
    print("=" * 80)
    
    return {
        'times': times,
        'average': avg_time,
        'min': min_time,
        'max': max_time,
        'std_dev': std_dev,
        'speedup': speedup,
        'improvement': improvement
    }


def main():
    parser = argparse.ArgumentParser(
        description='Benchmark MARS solver performance',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--runs',
        type=int,
        default=3,
        help='Number of benchmark runs (default: 3)'
    )
    parser.add_argument(
        '--profile',
        action='store_true',
        help='Generate profiling stats file for first run'
    )
    
    args = parser.parse_args()
    
    try:
        results = benchmark(num_runs=args.runs, enable_profiling=args.profile)
        
        if args.profile:
            print("\n" + "=" * 80)
            print("PROFILING DATA GENERATED")
            print("=" * 80)
            print("View detailed profiling report:")
            print("  python tests/performance/view_stats_detailed.py")
            print("=" * 80)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n\nError during benchmark: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
