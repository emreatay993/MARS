import os
import sys
import time

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.append(project_root)

from tests.performance.input_generator import (
    generate_mcf,
    generate_modal_stress,
    generate_modal_deformation
)

def generate_data():
    output_dir = os.path.join(project_root, 'tests', 'performance', 'large_dataset')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Generating files in {output_dir}...")
    
    # Parameters
    num_nodes = 1000000
    num_modes = 300
    num_time_points = 50000
    
    start_time = time.time()
    
    # MCF
    print(f"Generating MCF ({num_modes} modes, {num_time_points} time points)...")
    mcf_path = os.path.join(output_dir, 'large_dataset.mcf')
    generate_mcf(mcf_path, num_modes, num_time_points)
    print(f"MCF generated at: {mcf_path}")
    
    # Stress
    print(f"Generating Modal Stress ({num_nodes} nodes, {num_modes} modes)...")
    print("Warning: This requires significant memory (~15GB+).")
    stress_path = os.path.join(output_dir, 'large_dataset_stress.csv')
    try:
        generate_modal_stress(stress_path, num_nodes, num_modes)
        print(f"Modal Stress generated at: {stress_path}")
    except MemoryError:
        print("Error: Not enough memory to generate modal stress file.")
    
    # Deformation
    print(f"Generating Modal Deformation ({num_nodes} nodes, {num_modes} modes)...")
    deform_path = os.path.join(output_dir, 'large_dataset_deform.csv')
    try:
        generate_modal_deformation(deform_path, num_nodes, num_modes)
        print(f"Modal Deformation generated at: {deform_path}")
    except MemoryError:
        print("Error: Not enough memory to generate modal deformation file.")
    
    print(f"Total time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    generate_data()
