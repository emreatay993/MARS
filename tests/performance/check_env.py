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

# Check path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, '../../src'))
print(f"Calculated src path: {src_path}")

if os.path.exists(src_path):
    print("src path exists")
    sys.path.append(src_path)
    try:
        import core.computation
        print("Successfully imported core.computation")
    except ImportError as e:
        print(f"Error importing core.computation: {e}")
else:
    print("src path does not exist")
