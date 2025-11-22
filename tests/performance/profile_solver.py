import time
import os
import argparse
import tempfile
import shutil
import cProfile
import pstats
import sys

# Add project root and src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

from core.computation import AnalysisEngine
from core.data_models import SolverConfig
from file_io.loaders import (
    load_modal_coordinates,
    load_modal_stress,
    load_modal_deformations,
    load_steady_state_stress
)
from tests.performance.input_generator import (
    generate_mcf,
    generate_modal_stress,
    generate_modal_deformation,
    generate_steady_state
)

def profile_solver(num_nodes, num_modes, num_time_points, output_dir=None, keep_files=False,
                   include_deformation=False, include_steady_state=False):
    """
    Generates synthetic data and profiles the solver execution.
    """
    
    if output_dir:
        work_dir = output_dir
        if not os.path.exists(work_dir):
            os.makedirs(work_dir)
    else:
        work_dir = tempfile.mkdtemp()
        
    print(f"Working directory: {work_dir}")
    
    try:
        # 1. Generate Data
        print("Generating synthetic data...")
        mcf_file = os.path.join(work_dir, "test.mcf")
        stress_file = os.path.join(work_dir, "stress.csv")
        
        print(f"  - Generating MCF file: {mcf_file}")
        generate_mcf(mcf_file, num_modes, num_time_points)
        
        print(f"  - Generating Modal Stress file: {stress_file}")
        generate_modal_stress(stress_file, num_nodes, num_modes)
        
        deform_file = None
        if include_deformation:
            deform_file = os.path.join(work_dir, "deform.csv")
            print(f"  - Generating Modal Deformation file: {deform_file}")
            generate_modal_deformation(deform_file, num_nodes, num_modes)
            
        steady_file = None
        if include_steady_state:
            steady_file = os.path.join(work_dir, "steady.txt")
            print(f"  - Generating Steady State file: {steady_file}")
            generate_steady_state(steady_file, num_nodes)
        
        # 2. Load Data
        print("Loading data...")
        start_load = time.time()
        modal_data = load_modal_coordinates(mcf_file)
        stress_data = load_modal_stress(stress_file)
        
        deform_data = None
        if deform_file:
            print("  - Loading Modal Deformation data...")
            deform_data = load_modal_deformations(deform_file)
            
        steady_data = None
        if steady_file:
            print("  - Loading Steady State data...")
            steady_data = load_steady_state_stress(steady_file)
            
        print(f"Data loading took: {time.time() - start_load:.4f} seconds")
        
        # 3. Configure Solver
        config = SolverConfig(
            calculate_von_mises=True,
            calculate_max_principal_stress=True,
            calculate_deformation=include_deformation,
            include_steady_state=include_steady_state,
            output_directory=work_dir
        )
        
        engine = AnalysisEngine()
        engine.configure_data(
            modal_data=modal_data,
            stress_data=stress_data,
            deformation_data=deform_data,
            steady_state_data=steady_data
        )
        
        # 4. Run Analysis with Profiling
        print(f"Running analysis (Nodes: {num_nodes}, Modes: {num_modes}, Time Points: {num_time_points})...")
        print(f"  - Include Deformation: {include_deformation}")
        print(f"  - Include Steady State: {include_steady_state}")
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        start_analysis = time.time()
        
        engine.run_batch_analysis(config)
        
        end_analysis = time.time()
        profiler.disable()
        
        print(f"Analysis took: {end_analysis - start_analysis:.4f} seconds")
        
        # 5. Save Profile Stats
        stats_file = os.path.join(work_dir, "solver_profile.stats")
        stats = pstats.Stats(profiler)
        stats.strip_dirs()
        stats.sort_stats('cumulative')
        stats.dump_stats(stats_file)
        
        print(f"Profile stats saved to: {stats_file}")
        stats.print_stats(20)
        
    finally:
        if not keep_files and not output_dir:
            print("Cleaning up temporary files...")
            shutil.rmtree(work_dir)
        elif keep_files:
            print(f"Files kept in: {work_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Profile MARS Solver")
    parser.add_argument("--nodes", type=int, default=1000, help="Number of nodes")
    parser.add_argument("--modes", type=int, default=10, help="Number of modes")
    parser.add_argument("--time-points", type=int, default=100, help="Number of time points")
    parser.add_argument("--output-dir", type=str, help="Directory to save output files")
    parser.add_argument("--keep-files", action="store_true", help="Keep generated files")
    parser.add_argument("--include-deformation", action="store_true", help="Include modal deformation data")
    parser.add_argument("--include-steady-state", action="store_true", help="Include steady state stress data")
    
    args = parser.parse_args()
    
    profile_solver(
        num_nodes=args.nodes,
        num_modes=args.modes,
        num_time_points=args.time_points,
        output_dir=args.output_dir,
        keep_files=args.keep_files,
        include_deformation=args.include_deformation,
        include_steady_state=args.include_steady_state
    )
