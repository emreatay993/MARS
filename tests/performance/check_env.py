import sys
import os

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

try:
    import numpy
    print(f"Numpy version: {numpy.__version__}")
except ImportError as e:
    print(f"Error importing numpy: {e}")

try:
    import pandas
    print(f"Pandas version: {pandas.__version__}")
except ImportError as e:
    print(f"Error importing pandas: {e}")

try:
    import numba
    print(f"Numba version: {numba.__version__}")
except ImportError as e:
    print(f"Error importing required numba dependency: {e}")
    raise

# Check path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, '../../src'))
print(f"Calculated src path: {src_path}")

if os.path.exists(src_path):
    print("src path exists")
    sys.path.append(src_path)
    try:
        import mars_solver.core.computation
        print("Successfully imported mars_solver.core.computation")
    except ImportError as e:
        print(f"Error importing mars_solver.core.computation: {e}")
else:
    print("src path does not exist")
