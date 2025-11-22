import numpy as np
import pandas as pd
import os

def generate_mcf(filename, num_modes, num_time_points):
    """Generates a synthetic Modal Coordinate File (.mcf)."""
    with open(filename, 'w') as f:
        f.write("Modal Coordinates File - Synthetic\n")
        f.write("Synthetic Generator\n")
        f.write("01/01/2024      00:00:00\n")
        f.write("Title: Synthetic Data\n")
        f.write(f"Number of Modes:   {num_modes}\n")
        
        # Mode header
        f.write("  Mode:                " + "              ".join([f"{i+1}" for i in range(num_modes)]) + "\n")
        
        # Frequency header (dummy frequencies)
        freqs = [f"{100.0 * (i+1):.7E}" for i in range(num_modes)]
        f.write("  Frequency:     " + "  ".join(freqs) + "\n")
        
        f.write("      Time          Coordinates...\n")
        
        # Data generation
        time_values = np.linspace(0, 1.0, num_time_points)
        # Generate random modal coordinates
        coords = np.random.randn(num_time_points, num_modes) * 1e-4
        
        for i, t in enumerate(time_values):
            line = f"  {t:.7E}  " + "  ".join([f"{c:.7E}" for c in coords[i]])
            f.write(line + "\n")

def generate_modal_stress(filename, num_nodes, num_modes):
    """Generates a synthetic modal stress CSV file."""
    # Generate Node IDs and Coordinates
    node_ids = np.arange(1, num_nodes + 1)
    coords = np.random.rand(num_nodes, 3) * 100.0
    
    data = {
        'NodeID': node_ids,
        'X': coords[:, 0],
        'Y': coords[:, 1],
        'Z': coords[:, 2]
    }
    
    # Generate stress components for each mode
    components = ['sx', 'sy', 'sz', 'sxy', 'syz', 'sxz']
    for mode in range(1, num_modes + 1):
        for comp in components:
            col_name = f"{comp}_Mode{mode}"
            data[col_name] = np.random.randn(num_nodes) * 100.0
            
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

def generate_modal_deformation(filename, num_nodes, num_modes):
    """Generates a synthetic modal deformation CSV file."""
    node_ids = np.arange(1, num_nodes + 1)
    
    data = {'NodeID': node_ids}
    
    # Generate deformation components for each mode
    components = ['ux', 'uy', 'uz']
    for mode in range(1, num_modes + 1):
        for comp in components:
            col_name = f"{comp}_Mode{mode}"
            data[col_name] = np.random.randn(num_nodes) * 0.1
            
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

def generate_steady_state(filename, num_nodes):
    """Generates a synthetic steady-state stress file."""
    node_ids = np.arange(1, num_nodes + 1)
    
    # Columns based on load_steady_state_stress loader
    # It expects: Node Number, SX (MPa), SY (MPa), SZ (MPa), SXY (MPa), SYZ (MPa), SXZ (MPa)
    # And it uses tab delimiter or whitespace based on the loader logic, but let's stick to tab as per loader hint
    
    data = {
        'Node Number': node_ids,
        'SX (MPa)': np.random.randn(num_nodes) * 50.0,
        'SY (MPa)': np.random.randn(num_nodes) * 50.0,
        'SZ (MPa)': np.random.randn(num_nodes) * 50.0,
        'SXY (MPa)': np.random.randn(num_nodes) * 20.0,
        'SYZ (MPa)': np.random.randn(num_nodes) * 20.0,
        'SXZ (MPa)': np.random.randn(num_nodes) * 20.0
    }
    
    df = pd.DataFrame(data)
    df.to_csv(filename, sep='\t', index=False)
